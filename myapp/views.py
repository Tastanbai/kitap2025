from datetime import date
import json
from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, HttpResponse, get_object_or_404
from django.utils import timezone
from .forms import LoginForm, RegForm, PublishForm, BookForm
from django.contrib.auth import authenticate, login as auth_login
from .models import Book, Publish, ReturnedBook
from django.contrib import auth, messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.views.decorators.http import require_POST
from django.db import models
from .utils import create_books_from_excel
from django.core.files.storage import FileSystemStorage
import pandas as pd
from django.http import JsonResponse
from django.db import connection


def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['name']
            password = form.cleaned_data['pwd']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                # Проверка наличия галочки согласия
                if 'agree' in request.POST:
                    auth_login(request, user)
                    return redirect('myapp:index')
                else:
                    form.add_error(None, 'Вы должны согласиться с условиями перед входом в систему.')
    else:
        form = LoginForm()
    return render(request, 'myapp/login.html', {'form': form})


def logout(request):
    auth.logout(request)
    return redirect(reverse('myapp:login'))


@login_required
def view_returned_books(request):
    returned_books = ReturnedBook.objects.filter(user=request.user)
    return render(request, 'myapp/returned_books.html', {'returned_books': returned_books})


@login_required 
def index(request):
    if not request.user.is_authenticated:
        return redirect('myapp:login')
    sort = request.GET.get('sort', 'name')  
    search_query = request.GET.get('q', '')  
    books = Book.objects.filter(user=request.user)

    total_quantity = books.aggregate(total_quantity=models.Sum('quantity'))['total_quantity'] or 0
    total_balance = books.aggregate(total_balance=models.Sum('balance_quantity'))['total_balance'] or 0

    if search_query:
        books = books.filter(
            Q(name__icontains=search_query) | 
            Q(bbk__icontains=search_query)  |
            Q(ISBN__icontains=search_query) |
            Q(author__icontains=search_query)
        )
    if sort in ['name', 'quantity', 'balance_quantity', 'bbk' ]:
        books = books.order_by(sort)

    return render(request, 'myapp/index.html', {'books': books, 
                                                'current_sort': sort, 
                                                'total_quantity': total_quantity,
                                                'total_balance': total_balance})


@login_required  
def add_book(request):
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            book = form.save(commit=False)  
            book.user = request.user  
            book.save()  
            return redirect(reverse('myapp:index'))  
        else:
            context = {
                'form': form
            }
            return render(request, 'myapp/add_book.html', context=context)
    else:
        form = BookForm()
        context = {
            'form': form
        }
        return render(request, 'myapp/add_book.html', context=context)


def select_all_books(request):
    if request.method == 'GET':
        all_books = Book.objects.all()
        selected_books_ids = [str(book.pk) for book in all_books]
        return JsonResponse({'selected_books_ids': selected_books_ids})
    else:
        return HttpResponse(status=400)
    

def edit_book(request, id):
    book_obj = get_object_or_404(Book, pk=id)
    ret = {'status': None, 'message': None}
    if request.method == 'POST':
        form = BookForm(request.POST, instance=book_obj)
        if form.is_valid():
            form.save()
            ret['status'] = 'true'
            return HttpResponse(json.dumps(ret))
        else:
            ret['message'] = form.errors.as_text()
            return HttpResponse(json.dumps(ret))
    form = BookForm(instance=book_obj)

    context = {
        'form': form,
    }
    return render(request, 'myapp/edit_book.html', context=context)
    

@login_required
def delete_books(request):
    book_ids = request.POST.get('ids')
    if book_ids:
        book_ids_list = book_ids.split(',')
        Book.objects.filter(id__in=book_ids_list).delete()
    return HttpResponseRedirect(reverse('myapp:index'))


def reg(request):
    if request.method == 'POST':
        form = RegForm(request.POST)
        if form.is_valid():
            name = request.POST.get('name')
            lastname = request.POST.get('lastname')
            pwd = request.POST.get('pwd')
            r_pwd = request.POST.get('r_pwd')
            email = request.POST.get('email')

            if pwd == r_pwd:
                user = User.objects.create_user(
                    username=name,
                    first_name=lastname,  
                    password=pwd,
                    email=email,
                )
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                auth_login(request, user)
                return redirect('myapp:index') 
            else:
                form.add_error('r_pwd', 'Пароли не совпадают.')

        context = {'form': form, 'errors': form.errors.get('__all__')}
        return render(request, 'myapp/reg.html', context=context)

    form = RegForm()
    context = {'form': form}
    return render(request, 'myapp/reg.html', context=context)


@login_required
def return_book(request, publish_id):
    publish = get_object_or_404(Publish, id=publish_id, user=request.user)
    if request.method == 'POST':
        ReturnedBook.objects.create(
            user=request.user,
            name=publish.name,
            iin=publish.iin,
            date_out=publish.date_out,
            date_in=publish.date_in,
            city=publish.city,
            email=publish.email,
            phone=publish.phone,
            book_name=publish.book.name,
            quantity=publish.quantity,
        )
        if publish.email:
            send_mail(
                'Возврат книги подтвержден',
                f'Уважаемый(ая) {publish.name}, ваша книга {publish.book.name} успешно возвращена. Спасибо, что пользуетесь нашей библиотекой!',
                settings.EMAIL_HOST_USER,
                [publish.email],
                fail_silently=False,
            )
        publish.delete()
        messages.success(request, 'Книга успешно возвращена и сохранена для учёта.')
        return redirect('myapp:rent_book')
    else:
        messages.error(request, 'Действие доступно только через POST запрос.')
        return redirect('myapp:rent_book')


def rent_book(request):
    # Получаем список всех записей о публикации
    publish_list = Publish.objects.filter(user=request.user)

    # Получаем поисковой запрос из GET-параметра
    search_query = request.GET.get('q', '')

    # Фильтруем список публикаций по поисковому запросу, если он предоставлен
    if search_query:
        
        publish_list = publish_list.filter(
            Q(name__icontains=search_query) |
            Q(city__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(iin__icontains=search_query) |
            Q(book__name__icontains=search_query)  # Исправлено на поле в связанной модели
        )

    return render(request, 'myapp/rent_book.html', {'publish_list': publish_list})


@login_required
def blacklist(request):
    query = request.GET.get('q', '')  # Получаем поисковый запрос из GET параметра 'q'
    if query:
        # Фильтруем просроченные публикации по имени пользователя, книге или ИИН
        overdue_publishes = Publish.objects.filter(
            user=request.user,
            date_in__lt=timezone.now().date(),
            date_in__isnull=False
        ).filter(
            Q(name__icontains=query) |  # Поиск по имени
            Q(book__name__icontains=query) |  # Поиск по названию книги
            Q(iin__icontains=query)  # Поиск по ИИН
        )
    else:
        # Выводим все просроченные публикации текущего пользователя
        overdue_publishes = Publish.objects.filter(
            user=request.user,
            date_in__lt=timezone.now().date(),
            date_in__isnull=False
        )

    return render(request, 'myapp/blacklist.html', {
        'overdue_publishes': overdue_publishes,
        'query': query
    })


@login_required
def send_email(request):
    if request.method == 'POST':
        publish_id = request.POST.get('publish_id')
        try:
            # Убеждаемся, что запись принадлежит текущему пользователю
            publish = Publish.objects.get(id=publish_id, user=request.user)
            if publish.email:
                send_mail(
                    'Истек срок возврата',
                    f'У вас есть просроченные записи, пожалуйста, верните книгу {publish.book.name} как можно скорее.',
                    'kitaphana@oqz.kz',
                    [publish.email],
                    fail_silently=False,
                )
                messages.success(request, 'Сообщение успешно отправлено.')
        except Publish.DoesNotExist:
            return HttpResponse("Запись не найдена", status=404)  # Возвращаем ошибку, если запись не найдена или не принадлежит пользователю
        return redirect('myapp:blacklist')
    return redirect('myapp:blacklist')


@login_required
def excel(request):
    if request.method == 'POST':
        if 'file' in request.FILES:
            file = request.FILES['file']
            try:
                create_books_from_excel(file, request.user)
                return render(request, 'myapp/excel.html', {'message': 'Excel файл успешно загружен и обработан'})
            except Exception as e:
                return render(request, 'myapp/excel.html', {'error': f'Ошибка обработки файла: {e}'})
        else:
            return render(request, 'myapp/excel.html', {'error': 'Файл не найден. Пожалуйста, загрузите файл.'})
    return render(request, 'myapp/excel.html')


def excel_user(request):
    if request.method == 'POST' and request.FILES['file']:
        file = request.FILES['file']
        fs = FileSystemStorage()
        filename = fs.save(file.name, file)
        file_path = fs.path(filename)

        try:
            df = pd.read_excel(file_path)
            if 'ФИО' in df.columns:
                fio_list = df['ФИО'].tolist()
                request.session['fio_list'] = fio_list
                message = "Файл успешно загружен и обработан."
            else:
                error = "В загруженном файле отсутствует столбец 'ФИО'."
        except Exception as e:
            error = f"Произошла ошибка при обработке файла: {str(e)}"

        fs.delete(filename)

        if 'message' in locals():
            return render(request, 'myapp/excel_user.html', {'message': message})
        else:
            return render(request, 'myapp/excel_user.html', {'error': error})

    return render(request, 'myapp/excel_user.html')



def check_isbn(request):
    isbn = request.GET.get('isbn')
    if isbn:
        try:
            book = Book.objects.get(user=request.user, ISBN=isbn)
            return JsonResponse({
                'found': True,
                'book_name': book.name,
                'book_id': book.id
            })
        except Book.DoesNotExist:
            pass
    
    return JsonResponse({
        'found': False
    })

from django.shortcuts import render, redirect
from .forms import NewsForm
from .models import News

@login_required
def news_page(request):
    # Фильтруем новости, чтобы показывать только те, которые принадлежат текущему пользователю
    news = News.objects.filter(user=request.user).order_by('-id')
    return render(request, 'myapp/news_page.html', {'news': news})

# View for adding news@login_required
def add_news(request):
    if request.method == 'POST':
        form = NewsForm(request.POST, request.FILES)
        if form.is_valid():
            news_instance = form.save(commit=False)
            news_instance.user = request.user  # Присваиваем текущего пользователя как автора новости
            news_instance.save()
            return redirect('myapp:news_page')
    else:
        form = NewsForm()
    return render(request, 'myapp/add_news.html', {'form': form})

from django.shortcuts import get_object_or_404, redirect
from .models import News

def delete_news(request, news_id):
    news_item = get_object_or_404(News, id=news_id)
    if request.method == 'POST':
        news_item.delete()
        return redirect('myapp:news_page')  # После удаления возвращаемся к списку новостей
    return render(request, 'myapp/confirm_delete.html', {'news_item': news_item})


def edit_news(request, news_id):
    news_item = get_object_or_404(News, id=news_id)
    
    if request.method == 'POST':
        form = NewsForm(request.POST, request.FILES, instance=news_item)
        if form.is_valid():
            form.save()
            return redirect('myapp:news_page')  # После редактирования возвращаемся к списку новостей
    else:
        form = NewsForm(instance=news_item)

    return render(request, 'myapp/edit_news.html', {'form': form, 'news_item': news_item})



@login_required
def add_publish(request):
    user_books = Book.objects.filter(user=request.user)
    
    # Получение значения БИН школы (lastname)
    school_bin = request.user.first_name  # Переданный БИН школы при регистрации
    last_record = None

    try:
        # Получение последней записи из таблицы kitap по совпадению hik с БИН школы
        with connection.cursor() as cursor:
            query = """
                SELECT card, a1, data 
                FROM kitap 
                WHERE hik = %s 
                ORDER BY id DESC 
                LIMIT 1
            """
            print(f"SQL-запрос: {query} с параметром hik = {school_bin}")  # Отладка: SQL-запрос
            cursor.execute(query, [school_bin])
            row = cursor.fetchone()
            if row:
               
                last_record = {
                    'card': row[0],
                    'a1': row[1],
                    'data': row[2].split('T')[0] if row[2] else None
                }
            else:
                print("Нет данных для указанного hik")
    except Exception as e:
        print(f"Ошибка при доступе к таблице 'kitap': {e}")

   

    if request.method == 'POST':
        form = PublishForm(request.POST)
        form.fields['book'].queryset = user_books

        print(f"POST-данные: {request.POST}")  # Отладка: POST-данные

        if form.is_valid():
            books_data = request.POST.getlist('book')
            quantities = request.POST.getlist('quantity')
            name = form.cleaned_data['name']
            errors = False

            # Проверка доступного количества книг
            for book_id, quantity in zip(books_data, quantities):
                book_instance = get_object_or_404(Book, pk=book_id)
                if book_instance.balance_quantity < int(quantity):
                    form.add_error('quantity', f"Только {book_instance.balance_quantity} книг доступно для книги '{book_instance.name}'.")
                    errors = True

            if errors:
                return render(request, 'myapp/add_publish.html', {'form': form})

            # Создание записей публикации
            publish_instances = []
            for book_id, quantity in zip(books_data, quantities):
                book_instance = get_object_or_404(Book, pk=book_id)
                publish_instance = Publish(
                    user=request.user,
                    name=name,
                    iin=form.cleaned_data['iin'] or last_record.get('card'),
                    date_out=form.cleaned_data['date_out'] or last_record.get('data'),
                    date_in=form.cleaned_data['date_in'],
                    city=form.cleaned_data['city'],
                    email=form.cleaned_data['email'],
                    phone=form.cleaned_data['phone'],
                    book=book_instance,
                    quantity=quantity
                )
                publish_instances.append(publish_instance)
                book_instance.balance_quantity -= int(quantity)
                book_instance.save()

            print(f"Публикации на создание: {[{'book': p.book.name, 'quantity': p.quantity} for p in publish_instances]}")  # Отладка: создаваемые записи

            Publish.objects.bulk_create(publish_instances)

            # Отправка email
            recipient_email = form.cleaned_data['email']
            send_mail(
                'Подтверждение аренды книги',
                f"""Уважаемый {name},

Вы успешно арендовали следующие книги:

- Книга: {book_instance.name}
Количество: {quantity}
Дата получения: {form.cleaned_data['date_out'] or last_record.get('data')}
Дата возврата: {form.cleaned_data['date_in']}

Спасибо, что пользуетесь нашей библиотекой!
""",
                'kitaphana@oqz.kz',
                [recipient_email],
                fail_silently=False,
            )

            return redirect(reverse('myapp:rent_book'))
    else:
        # GET-запрос: создаём форму с начальными данными из последней записи
        form = PublishForm(initial={
            'iin': last_record.get('card') if last_record else None,
            'name': last_record.get('a1') if last_record else None,
            'date_out': last_record.get('data') if last_record else date.today().strftime('%Y-%m-%d')
        })
        form.fields['book'].queryset = user_books

        print(f"Инициализация формы: {form.initial}")  # Отладка: Начальные данные формы

    return render(request, 'myapp/add_publish.html', {'form': form})


from django.shortcuts import render
from django.http import HttpResponse
import barcode
from barcode.writer import ImageWriter
import random
from io import BytesIO
import zipfile

def generate_and_download_barcodes(request):
    if request.method == "POST":
        count = int(request.POST.get("count", 1))
        
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            for i in range(count):
                # Генерируем 12-значный случайный номер
                random_number = ''.join(str(random.randint(0, 9)) for _ in range(12))
                ean = barcode.get('ean13', random_number, writer=ImageWriter())
                
                # Генерируем штрих-код в памяти
                barcode_buffer = BytesIO()
                ean.write(barcode_buffer)
                barcode_buffer.seek(0)
                
                # Добавляем изображение штрих-кода в ZIP-архив
                zipf.writestr(f"штрих-код_{i+1}.png", barcode_buffer.read())

        zip_buffer.seek(0)
        response = HttpResponse(zip_buffer.getvalue(), content_type="application/zip")
        response["Content-Disposition"] = 'attachment; filename="штрих-коды.zip"'
        return response

    return render(request, "myapp/barcode.html")


# views_api.py
import base64
from django.utils.dateparse import parse_date
from django.db.models import Sum, Q

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import Publish, Book

# Если хочешь сохранить поддержку Basic параллельно с JWT:
AUTH_CLASSES = [JWTAuthentication, BasicAuthentication]

def _bad_request(msg):
    return Response({'detail': msg}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@authentication_classes(AUTH_CLASSES)
@permission_classes([IsAuthenticated])
def api_school_borrows(request):
    user = request.user

    qs = Publish.objects.filter(user=user).select_related('book')

    # даты
    since_str = request.query_params.get('since') or ''
    until_str = request.query_params.get('until') or ''
    since = parse_date(since_str) if since_str else None
    until = parse_date(until_str) if until_str else None
    if since_str and not since:
        return _bad_request('since must be YYYY-MM-DD')
    if until_str and not until:
        return _bad_request('until must be YYYY-MM-DD')
    if since:
        qs = qs.filter(date_out__gte=since)
    if until:
        qs = qs.filter(date_out__lte=until)

    # сортировка
    order = request.query_params.get('order') or '-date_out'
    allowed_orders = {'date_out', '-date_out', 'date_in', '-date_in'}
    if order not in allowed_orders:
        return _bad_request(f'order must be one of {sorted(allowed_orders)}')
    qs = qs.order_by(order)

    # пагинация (LimitOffsetPagination DRF под капотом)
    try:
        limit = int(request.query_params.get('limit', request.parser_context['view'].paginator.default_limit or 100))
        limit = max(1, min(limit, 500))
    except Exception:
        return _bad_request('limit must be integer')
    try:
        offset = int(request.query_params.get('offset', 0))
        offset = max(0, offset)
    except Exception:
        return _bad_request('offset must be integer')

    total = qs.count()
    items = list(qs[offset:offset+limit])

    next_offset = offset + limit if offset + limit < total else None
    prev_offset = offset - limit if offset > 0 else None

    data = {
        'school': {
            'username': user.username,
            'bin': user.first_name,
            'email': user.email,
        },
        'meta': {
            'total': total,
            'limit': limit,
            'offset': offset,
            'order': order,
            'next': f'?limit={limit}&offset={next_offset}&order={order}' if next_offset is not None else None,
            'prev': f'?limit={limit}&offset={max(prev_offset,0)}&order={order}' if prev_offset is not None else None,
        },
        'borrows': [
            {
                'name': p.name,
                'iin': p.iin,
                'book': {
                    'id': p.book_id,
                    'name': p.book.name,
                    'isbn': p.book.ISBN,
                },
                'quantity': p.quantity,
                'date_out': p.date_out,
                'date_in': p.date_in,
                'city': p.city,
                'email': p.email,
                'phone': p.phone,
            } for p in items
        ]
    }
    return Response(data)

@api_view(['GET'])
@authentication_classes(AUTH_CLASSES)
@permission_classes([IsAuthenticated])
def api_school_books(request):
    user = request.user
    qs = Book.objects.filter(user=user)

    q = request.query_params.get('q') or ''
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(author__icontains=q) | Q(bbk__icontains=q) | Q(ISBN__icontains=q))

    author = request.query_params.get('author')
    if author: qs = qs.filter(author__icontains=author)

    isbn = request.query_params.get('isbn')
    if isbn: qs = qs.filter(ISBN__icontains=isbn)

    bbk = request.query_params.get('bbk')
    if bbk: qs = qs.filter(bbk__icontains=bbk)

    y_min = request.query_params.get('year_min')
    y_max = request.query_params.get('year_max')
    if y_min and y_min.isdigit(): qs = qs.filter(year_published__gte=int(y_min))
    if y_max and y_max.isdigit(): qs = qs.filter(year_published__lte=int(y_max))

    if (request.query_params.get('available') or '').lower() in ('1','true','yes'):
        qs = qs.filter(balance_quantity__gt=0)

    order = request.query_params.get('order') or 'name'
    allowed_orders = {
        'name','-name','author','-author','bbk','-bbk','ISBN','-ISBN',
        'quantity','-quantity','balance_quantity','-balance_quantity',
        'year_published','-year_published'
    }
    if order not in allowed_orders:
        return _bad_request(f'order must be one of {sorted(allowed_orders)}')
    qs = qs.order_by(order)

    # пагинация
    try:
        limit = int(request.query_params.get('limit', request.parser_context['view'].paginator.default_limit or 100))
        limit = max(1, min(limit, 500))
    except Exception:
        return _bad_request('limit must be integer')
    try:
        offset = int(request.query_params.get('offset', 0))
        offset = max(0, offset)
    except Exception:
        return _bad_request('offset must be integer')

    total = qs.count()
    agg = qs.aggregate(total_quantity=Sum('quantity'), total_balance=Sum('balance_quantity'))
    items = list(qs[offset:offset+limit])

    next_offset = offset + limit if offset + limit < total else None
    prev_offset = offset - limit if offset > 0 else None

    data = {
        'school': {
            'username': user.username,
            'bin': user.first_name,
            'email': user.email,
        },
        'meta': {
            'total': total,
            'limit': limit,
            'offset': offset,
            'order': order,
            'next': f'?limit={limit}&offset={next_offset}&order={order}' if next_offset is not None else None,
            'prev': f'?limit={limit}&offset={max(prev_offset,0)}&order={order}' if prev_offset is not None else None,
        },
        'totals': {
            'quantity': agg['total_quantity'] or 0,
            'balance_quantity': agg['total_balance'] or 0,
        },
        'books': [
            {
                'id': b.id,
                'ISBN': b.ISBN,
                'name': b.name,
                'author': b.author,
                'bbk': b.bbk,
                'quantity': b.quantity,
                'balance_quantity': b.balance_quantity,
                'year_published': b.year_published,
            } for b in items
        ]
    }
    return Response(data)
