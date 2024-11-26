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
    sort = request.GET.get('sort', 'name')  # Устанавливаем 'name' как значение по умолчанию для сортировки
    search_query = request.GET.get('q', '')  # Получаем поисковый запрос

    # Получаем все книги
    #books = Book.objects.all()
    books = Book.objects.filter(user=request.user)

    total_quantity = books.aggregate(total_quantity=models.Sum('quantity'))['total_quantity'] or 0
    total_balance = books.aggregate(total_balance=models.Sum('balance_quantity'))['total_balance'] or 0

    # Фильтруем книги по поисковому запросу, если он предоставлен
    if search_query:
        books = books.filter(
            Q(name__icontains=search_query) | 
            Q(bbk__icontains=search_query)  |
            Q(ISBN__icontains=search_query) |
            Q(author__icontains=search_query)
        )

    # Применяем сортировку
    if sort in ['name', 'quantity', 'balance_quantity', 'bbk' ]:
        books = books.order_by(sort)

    return render(request, 'myapp/index.html', {'books': books, 
                                                'current_sort': sort, 
                                                'total_quantity': total_quantity,
                                                'total_balance': total_balance})


@login_required  # Убедитесь, что только аутентифицированные пользователи могут добавлять книги
def add_book(request):
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            book = form.save(commit=False)  # Сохраняем модель, но пока не коммитим в базу данных
            book.user = request.user  # Присваиваем книге пользователя, который ее добавляет
            book.save()  # Теперь коммитим в базу данных
            return redirect(reverse('myapp:index'))  # Перенаправление на главную страницу после добавления книги
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
        # Получаем все книги из базы данных
        all_books = Book.objects.all()
        
        # Создаем список идентификаторов всех книг
        selected_books_ids = [str(book.pk) for book in all_books]

        # Возвращаем список идентификаторов в формате JSON
        return JsonResponse({'selected_books_ids': selected_books_ids})
    else:
        # Если запрос не GET, возвращаем ошибку
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



# def reg(request):
#     if request.method == 'POST':
#         form = RegForm(request.POST)
#         if form.is_valid():
#             name = request.POST.get('name')
#             pwd = request.POST.get('pwd')
#             r_pwd = request.POST.get('r_pwd')
#             email = request.POST.get('email')

#             # Добавляем проверку на совпадение введенных паролей
#             if pwd == r_pwd:
#                 user = User.objects.create_user(
#                     username=name,
#                     password=pwd,
#                     email=email,
#                 )
#                 # Автоматический вход после регистрации
#                 user.backend = 'django.contrib.auth.backends.ModelBackend'
#                 auth_login(request, user)
#                 return redirect('myapp:index')  # Перенаправление на главную страницу после регистрации
#             else:
#                 # Если пароли не совпадают, добавляем ошибку к форме
#                 form.add_error('r_pwd', 'Пароли не совпадают.')

#         errors = form.errors.get('__all__')

#         context = {
#             'form': form,
#             'errors': errors
#         }

#         return render(request, 'myapp/reg.html', context=context)

#     form = RegForm()
#     context = {
#         'form': form
#     }

#     return render(request, 'myapp/reg.html', context=context)

def reg(request):
    if request.method == 'POST':
        form = RegForm(request.POST)
        if form.is_valid():
            name = request.POST.get('name')
            lastname = request.POST.get('lastname')
            pwd = request.POST.get('pwd')
            r_pwd = request.POST.get('r_pwd')
            email = request.POST.get('email')

            # Проверяем совпадение паролей
            if pwd == r_pwd:
                user = User.objects.create_user(
                    username=name,
                    first_name=lastname,  # Сохраняем фамилию в поле first_name
                    password=pwd,
                    email=email,
                )
                # Автоматический вход после регистрации
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                auth_login(request, user)
                return redirect('myapp:index')  # Перенаправление на главную страницу после регистрации
            else:
                form.add_error('r_pwd', 'Пароли не совпадают.')

        context = {'form': form, 'errors': form.errors.get('__all__')}
        return render(request, 'myapp/reg.html', context=context)

    form = RegForm()
    context = {'form': form}
    return render(request, 'myapp/reg.html', context=context)

# def add_publish(request):
#     user_books = Book.objects.filter(user=request.user)
#     if request.method == 'POST':
#         form = PublishForm(request.POST)
#         form.fields['book'].queryset = user_books

#         if form.is_valid():
#             publish_instance = form.save(commit=False)
#             publish_instance.user = request.user

#             # Проверяем наличие книги перед сохранением
#             if publish_instance.book.balance_quantity < form.cleaned_data['quantity']:
#                 form.add_error('quantity', f"Только {publish_instance.book.balance_quantity} книг доступно.")
#                 return render(request, 'myapp/add_publish.html', {'form': form})

#             publish_instance.save()

#             # Отправляем уведомление на email, указанный в форме
#             recipient_email = form.cleaned_data['email']  # Убедитесь, что поле email корректно настроено в форме
#             send_mail(
#                 'Подтверждение аренды книги',
#                 f"Уважаемый {form.cleaned_data['name']}, вы успешно арендовали книгу '{publish_instance.book.name}' на дату {publish_instance.date_out}. Возврат до {publish_instance.date_in}.",
#                 'kitaphana@oqz.kz',  # Измените на ваш активный email
#                 [recipient_email],
#                 fail_silently=False,
#             )

#             return redirect(reverse('myapp:rent_book'))

#         return render(request, 'myapp/add_publish.html', {'form': form})
    
#     else:
#         form = PublishForm()
#         form.fields['book'].queryset = user_books
#         return render(request, 'myapp/add_publish.html', {'form': form})



@login_required
def return_book(request, publish_id):
    
    # Получаем объект Publish, или возвращаем 404, если он не найден
    publish = get_object_or_404(Publish, id=publish_id, user=request.user)

    if request.method == 'POST':
        # Создаем запись в ReturnedBook с сохранением полной информации из Publish
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

        # Отправка уведомления на email, если у записи есть email
        if publish.email:
            send_mail(
                'Возврат книги подтвержден',
                f'Уважаемый(ая) {publish.name}, ваша книга {publish.book.name} успешно возвращена. Спасибо, что пользуетесь нашей библиотекой!',
                settings.EMAIL_HOST_USER,
                [publish.email],
                fail_silently=False,
            )

        # Удаляем объект Publish после успешного сохранения в ReturnedBook
        publish.delete()
        messages.success(request, 'Книга успешно возвращена и сохранена для учёта.')
        return redirect('myapp:rent_book')
    else:
        # Если метод запроса не POST, выводим сообщение об ошибке
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


from .utils import create_books_from_excel


@login_required
def excel(request):
    if request.method == 'POST':
        if 'file' in request.FILES:
            file = request.FILES['file']
            create_books_from_excel(file, request.user)
            return render(request, 'myapp/excel.html', {'message': 'Excel файл успешно загружен и обработан'})
        else:
            return render(request, 'myapp/excel.html', {'error': 'Файл не найден. Пожалуйста, загрузите файл.'})
    return render(request, 'myapp/excel.html')



# @login_required
# def add_publish(request):
#     user_books = Book.objects.filter(user=request.user)
#     if request.method == 'POST':
#         form = PublishForm(request.POST)
#         form.fields['book'].queryset = user_books

#         if form.is_valid():
#             publish_instances = []
#             for book_data in request.POST.getlist('book'):
#                 quantity = request.POST.getlist('quantity')[request.POST.getlist('book').index(book_data)]
#                 book_instance = get_object_or_404(Book, pk=book_data)
                
#                 if book_instance.balance_quantity < int(quantity):
#                     form.add_error('quantity', f"Только {book_instance.balance_quantity} книг доступно.")
#                     return render(request, 'myapp/add_publish.html', {'form': form})

#                 publish_instance = Publish(
#                     user=request.user,
#                     name=form.cleaned_data['name'],
#                     iin=form.cleaned_data['iin'],
#                     date_out=form.cleaned_data['date_out'],
#                     date_in=form.cleaned_data['date_in'],
#                     city=form.cleaned_data['city'],
#                     email=form.cleaned_data['email'],
#                     phone=form.cleaned_data['phone'],
#                     book=book_instance,
#                     quantity=quantity
#                 )
#                 publish_instances.append(publish_instance)
#                 book_instance.balance_quantity -= int(quantity)
#                 book_instance.save()

#             Publish.objects.bulk_create(publish_instances)

#             recipient_email = form.cleaned_data['email']
#             send_mail(
#                 'Подтверждение аренды книги',
#                 f"Уважаемый {form.cleaned_data['name']}, вы успешно арендовали книги.",
#                 'kitaphana@oqz.kz',
#                 [recipient_email],
#                 fail_silently=False,
#             )

#             return redirect(reverse('myapp:rent_book'))

#         return render(request, 'myapp/add_publish.html', {'form': form})
    
#     else:
#         form = PublishForm()
#         form.fields['book'].queryset = user_books
# #         return render(request, 'myapp/add_publish.html', {'form': form})


# @login_required
# def add_publish(request):
#     user_books = Book.objects.filter(user=request.user)
#     if request.method == 'POST':
#         form = PublishForm(request.POST)
#         form.fields['book'].queryset = user_books

#         if form.is_valid():
#             books_data = request.POST.getlist('book')
#             quantities = request.POST.getlist('quantity')
#             errors = False

#             for book_id, quantity in zip(books_data, quantities):
#                 book_instance = get_object_or_404(Book, pk=book_id)
                
#                 if book_instance.balance_quantity < int(quantity):
#                     form.add_error('quantity', f"Только {book_instance.balance_quantity} книг доступно для книги '{book_instance.name}'.")
#                     errors = True

#             if errors:
#                 return render(request, 'myapp/add_publish.html', {'form': form})

#             publish_instances = []
#             for book_id, quantity in zip(books_data, quantities):
#                 book_instance = get_object_or_404(Book, pk=book_id)

#                 publish_instance = Publish(
#                     user=request.user,
#                     name=form.cleaned_data['name'],
#                     iin=form.cleaned_data['iin'],
#                     date_out=form.cleaned_data['date_out'],
#                     date_in=form.cleaned_data['date_in'],
#                     city=form.cleaned_data['city'],
#                     email=form.cleaned_data['email'],
#                     phone=form.cleaned_data['phone'],
#                     book=book_instance,
#                     quantity=quantity
#                 )
#                 publish_instances.append(publish_instance)
#                 book_instance.balance_quantity -= int(quantity)
#                 book_instance.save()

#             Publish.objects.bulk_create(publish_instances)

#             recipient_email = form.cleaned_data['email']
#             send_mail(
#                 'Подтверждение аренды книги',
#                 f"Уважаемый {form.cleaned_data['name']}, вы успешно арендовали книги.",
#                 'kitaphana@oqz.kz',
#                 [recipient_email],
#                 fail_silently=False,
#             )

#             return redirect(reverse('myapp:rent_book'))

#         return render(request, 'myapp/add_publish.html', {'form': form})
    
#     else:
#         form = PublishForm()
#         form.fields['book'].queryset = user_books
#         return render(request, 'myapp/add_publish.html', {'form': form})

# from django.shortcuts import render
# from django.core.files.storage import FileSystemStorage
# import pandas as pd

# def excel_user(request):
#     if request.method == 'POST' and request.FILES['file']:
#         file = request.FILES['file']
#         fs = FileSystemStorage()
#         filename = fs.save(file.name, file)
#         file_path = fs.path(filename)

#         # Чтение Excel файла с помощью pandas
#         try:
#             df = pd.read_excel(file_path)
#             # Проверка наличия столбца 'ФИО'
#             if 'ФИО' in df.columns:
#                 fio_list = df['ФИО'].tolist()
#                 # Обработка списка ФИО
#                 # Например, сохранение в базу данных или другая обработка
#                 # ...
#                 message = "Файл успешно загружен и обработан."
#             else:
#                 error = "В загруженном файле отсутствует столбец 'ФИО'."
#         except Exception as e:
#             error = f"Произошла ошибка при обработке файла: {str(e)}"

#         # Удаление файла после обработки
#         fs.delete(filename)

#         if 'message' in locals():
#             return render(request, 'myapp/excel_user.html', {'message': message})
#         else:
#             return render(request, 'myapp/excel_user.html', {'error': error})

#     return render(request, 'myapp/excel_user.html')

#---------------------------------------------------------------------------------------------------------------------------------------------
from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.storage import FileSystemStorage
import pandas as pd
from myapp.models import Book, Publish
from myapp.forms import PublishForm
from django.contrib.auth.decorators import login_required

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

# @login_required
# def add_publish(request):
#     user_books = Book.objects.filter(user=request.user)
#     fio_list = request.session.get('fio_list', [])  # Получить список ФИО из сессии

#     if request.method == 'POST':
#         form = PublishForm(request.POST)
#         form.fields['book'].queryset = user_books

#         if form.is_valid():
#             books_data = request.POST.getlist('book')
#             quantities = request.POST.getlist('quantity')
#             errors = False

#             for book_id, quantity in zip(books_data, quantities):
#                 book_instance = get_object_or_404(Book, pk=book_id)
                
#                 if book_instance.balance_quantity < int(quantity):
#                     form.add_error('quantity', f"Только {book_instance.balance_quantity} книг доступно для книги '{book_instance.name}'.")
#                     errors = True

#             if errors:
#                 return render(request, 'myapp/add_publish.html', {'form': form, 'fio_list': fio_list})

#             publish_instances = []
#             for book_id, quantity in zip(books_data, quantities):
#                 book_instance = get_object_or_404(Book, pk=book_id)

#                 publish_instance = Publish(
#                     user=request.user,
#                     name=form.cleaned_data['name'],
#                     iin=form.cleaned_data['iin'],
#                     date_out=form.cleaned_data['date_out'],
#                     date_in=form.cleaned_data['date_in'],
#                     city=form.cleaned_data['city'],
#                     email=form.cleaned_data['email'],
#                     phone=form.cleaned_data['phone'],
#                     book=book_instance,
#                     quantity=quantity
#                 )
#                 publish_instances.append(publish_instance)
#                 book_instance.balance_quantity -= int(quantity)
#                 book_instance.save()

#             Publish.objects.bulk_create(publish_instances)

#             recipient_email = form.cleaned_data['email']
#             send_mail(
#                 'Подтверждение аренды книги',
#                 f"Уважаемый {form.cleaned_data['name']}, вы успешно арендовали книги.",
#                 'kitaphana@oqz.kz',
#                 [recipient_email],
#                 fail_silently=False,
#             )

#             return redirect(reverse('myapp:rent_book'))

#         return render(request, 'myapp/add_publish.html', {'form': form, 'fio_list': fio_list})

#     else:
#         form = PublishForm()
#         form.fields['book'].queryset = user_books
#         return render(request, 'myapp/add_publish.html', {'form': form, 'fio_list': fio_list})

#---------------------------------------------------------------------------------------------------------------------------------------------

# @login_required
# def add_publish(request):
#     user_books = Book.objects.filter(user=request.user)
#     fio_list = request.session.get('fio_list', [])  # Получить список ФИО из сессии

#     if request.method == 'POST':
#         form = PublishForm(request.POST)
#         form.fields['book'].queryset = user_books

#         if form.is_valid():
#             books_data = request.POST.getlist('book')
#             quantities = request.POST.getlist('quantity')
#             name = form.cleaned_data['name']
#             errors = False

#             for book_id, quantity in zip(books_data, quantities):
#                 book_instance = get_object_or_404(Book, pk=book_id)
                
#                 if book_instance.balance_quantity < int(quantity):
#                     form.add_error('quantity', f"Только {book_instance.balance_quantity} книг доступно для книги '{book_instance.name}'.")
#                     errors = True

#             if errors:
#                 return render(request, 'myapp/add_publish.html', {'form': form, 'fio_list': fio_list})

#             publish_instances = []
#             for book_id, quantity in zip(books_data, quantities):
#                 book_instance = get_object_or_404(Book, pk=book_id)

#                 publish_instance = Publish(
#                     user=request.user,
#                     name=name,  # Используйте новое или выбранное ФИО
#                     iin=form.cleaned_data['iin'],
#                     date_out=form.cleaned_data['date_out'],
#                     date_in=form.cleaned_data['date_in'],
#                     city=form.cleaned_data['city'],
#                     email=form.cleaned_data['email'],
#                     phone=form.cleaned_data['phone'],
#                     book=book_instance,
#                     quantity=quantity
#                 )
#                 publish_instances.append(publish_instance)
#                 book_instance.balance_quantity -= int(quantity)
#                 book_instance.save()

#             Publish.objects.bulk_create(publish_instances)

#             recipient_email = form.cleaned_data['email']
#             send_mail(
#                 'Подтверждение аренды книги',
#                 f"Уважаемый {name}, вы успешно арендовали книги.",
#                 'kitaphana@oqz.kz',
#                 [recipient_email],
#                 fail_silently=False,
#             )

#             return redirect(reverse('myapp:rent_book'))

#         return render(request, 'myapp/add_publish.html', {'form': form, 'fio_list': fio_list})
#     else:
#         form = PublishForm()
#         form.fields['book'].queryset = user_books
#         return render(request, 'myapp/add_publish.html', {'form': form, 'fio_list': fio_list})

# from django.db import connection

# @login_required
# def add_publish(request):
#     user_books = Book.objects.filter(user=request.user)
#     fio_list = request.session.get('fio_list', [])  # Получить список ФИО из сессии

#     # Получение последнего ИИН из базы данных
#     last_iin = None
#     with connection.cursor() as cursor:
#         cursor.execute("SELECT card FROM School WHERE card IS NOT NULL ORDER BY id DESC LIMIT 1;")
#         row = cursor.fetchone()
#         if row:
#             last_iin = row[0]

#     if request.method == 'POST':
#         form = PublishForm(request.POST)
#         form.fields['book'].queryset = user_books

#         if form.is_valid():
#             books_data = request.POST.getlist('book')
#             quantities = request.POST.getlist('quantity')
#             name = form.cleaned_data['name']
#             errors = False

#             for book_id, quantity in zip(books_data, quantities):
#                 book_instance = get_object_or_404(Book, pk=book_id)
                
#                 if book_instance.balance_quantity < int(quantity):
#                     form.add_error('quantity', f"Только {book_instance.balance_quantity} книг доступно для книги '{book_instance.name}'.")
#                     errors = True

#             if errors:
#                 return render(request, 'myapp/add_publish.html', {'form': form, 'fio_list': fio_list})

#             publish_instances = []
#             for book_id, quantity in zip(books_data, quantities):
#                 book_instance = get_object_or_404(Book, pk=book_id)

#                 publish_instance = Publish(
#                     user=request.user,
#                     name=name,  # Используйте новое или выбранное ФИО
#                     iin=form.cleaned_data['iin'],
#                     date_out=form.cleaned_data['date_out'],
#                     date_in=form.cleaned_data['date_in'],
#                     city=form.cleaned_data['city'],
#                     email=form.cleaned_data['email'],
#                     phone=form.cleaned_data['phone'],
#                     book=book_instance,
#                     quantity=quantity
#                 )
#                 publish_instances.append(publish_instance)
#                 book_instance.balance_quantity -= int(quantity)
#                 book_instance.save()

#             Publish.objects.bulk_create(publish_instances)

#             recipient_email = form.cleaned_data['email']
#             send_mail(
#                 'Подтверждение аренды книги',
#                 f"Уважаемый {name}, вы успешно арендовали книги.",
#                 'kitaphana@oqz.kz',
#                 [recipient_email],
#                 fail_silently=False,
#             )

#             return redirect(reverse('myapp:rent_book'))

#         return render(request, 'myapp/add_publish.html', {'form': form, 'fio_list': fio_list})
#     else:
#         form = PublishForm(initial={'iin': last_iin})  # Предустановить ИИН
#         form.fields['book'].queryset = user_books
#         return render(request, 'myapp/add_publish.html', {'form': form, 'fio_list': fio_list})
# f

# from django.db import connection
# from django.shortcuts import render, redirect, get_object_or_404
# from django.contrib.auth.decorators import login_required
# from django.urls import reverse
# from django.core.mail import send_mail
# from django.contrib import messages
# from .forms import PublishForm
# from .models import Book, Publish

# @login_required
# def add_publish(request):
#     user_books = Book.objects.filter(user=request.user)
    
#     # Определяем текущую школу
#     current_school = request.user.first_name
#     school_table = f"{current_school}"

#     # Получение последнего card и a1 из таблицы школы
#     last_card = None
#     last_a1 = None
#     try:
#         with connection.cursor() as cursor:
#             query = f"SELECT card, a1 FROM {school_table} WHERE card IS NOT NULL ORDER BY id DESC LIMIT 1;"
#             cursor.execute(query)
#             row = cursor.fetchone()
#             if row:
#                 last_card = row[0]  # card
#                 last_a1 = row[1]    # a1
#     except Exception as e:
#         print(f"Ошибка доступа к таблице {school_table}: {e}")

#     if request.method == 'POST':
#         form = PublishForm(request.POST)
#         form.fields['book'].queryset = user_books

#         # Проверка ISBN
#         isbn = request.POST.get('ISBN')
#         if isbn:
#             existing_book = Book.objects.filter(user=request.user, ISBN=isbn).first()
#             if existing_book:
#                 messages.info(request, f"Книга с ISBN {isbn} найдена: {existing_book.name}")
#                 # Предзаполняем форму найденной книгой
#                 form = PublishForm(request.POST, initial={'book': [existing_book.id]})
#                 form.fields['book'].queryset = user_books
#             else:
#                 messages.error(request, f"Книга с ISBN {isbn} не найдена в вашей библиотеке.")
#                 return render(request, 'myapp/add_publish.html', {'form': form})

#         if form.is_valid():
#             books_data = request.POST.getlist('book')
#             quantities = request.POST.getlist('quantity')
#             name = form.cleaned_data['name']
#             errors = False

#             # Проверка доступного количества книг
#             for book_id, quantity in zip(books_data, quantities):
#                 book_instance = get_object_or_404(Book, pk=book_id)
#                 if book_instance.balance_quantity < int(quantity):
#                     form.add_error('quantity', f"Только {book_instance.balance_quantity} книг доступно для книги '{book_instance.name}'.")
#                     errors = True

#             if errors:
#                 return render(request, 'myapp/add_publish.html', {'form': form})

#             # Создание записей публикации
#             publish_instances = []
#             for book_id, quantity in zip(books_data, quantities):
#                 book_instance = get_object_or_404(Book, pk=book_id)

#                 publish_instance = Publish(
#                     user=request.user,
#                     name=name,
#                     iin=form.cleaned_data['iin'],
#                     date_out=form.cleaned_data['date_out'],
#                     date_in=form.cleaned_data['date_in'],
#                     city=form.cleaned_data['city'],
#                     email=form.cleaned_data['email'],
#                     phone=form.cleaned_data['phone'],
#                     book=book_instance,
#                     quantity=quantity
#                 )
#                 publish_instances.append(publish_instance)
#                 book_instance.balance_quantity -= int(quantity)
#                 book_instance.save()

#             Publish.objects.bulk_create(publish_instances)

#             # Отправка email
#             recipient_email = form.cleaned_data['email']
#             send_mail(
#                 'Подтверждение аренды книги',
#                 f"Уважаемый {name}, вы успешно арендовали книги ",
#                 'kitaphana@oqz.kz',
#                 [recipient_email],
#                 fail_silently=False,
#             )

#             send_mail(
#                 'Подтверждение аренды книги',
#                 f"""Уважаемый {name}, 

#             Вы успешно арендовали следующие книги:

#             {''.join([
#                 f"- Книга: {book_instance.name}\n"
#                 f"  Количество: {quantity}\n"
#                 f"  Дата получения: {form.cleaned_data['date_out']}\n"
#                 f"  Дата возврата: {form.cleaned_data['date_in']}\n\n"
#                 for book_id, quantity in zip(books_data, quantities)
#                 for book_instance in [get_object_or_404(Book, pk=book_id)]
#             ])}

#             Спасибо, что пользуетесь нашей библиотекой!
#             """,
#                 'kitaphana@oqz.kz',  # Измените на ваш реальный адрес отправителя
#                 [recipient_email],
#                 fail_silently=False,
#             )

#             return redirect(reverse('myapp:rent_book'))
#     else:
#         # GET запрос - создаем новую форму с начальными данными
#         form = PublishForm(initial={'iin': last_card, 'name': last_a1})
#         form.fields['book'].queryset = user_books

#     return render(request, 'myapp/add_publish.html', {'form': form})


from django.http import JsonResponse

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

from django.db import connection
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.core.mail import send_mail
from django.contrib import messages
from .forms import PublishForm
from .models import Book, Publish

@login_required
def add_publish(request):
    user_books = Book.objects.filter(user=request.user)
    
    # Определяем текущую школу
    current_school = request.user.first_name
    school_table = f"{current_school}"

    # Получение последнего card, a1 и data из таблицы школы
    last_card = None
    last_a1 = None
    last_data = None
    try:
        with connection.cursor() as cursor:
            query = f"SELECT card, a1, data FROM {school_table} WHERE card IS NOT NULL ORDER BY id DESC LIMIT 1;"
            cursor.execute(query)
            row = cursor.fetchone()
            if row:
                last_card = row[0]  # card
                last_a1 = row[1]    # a1
                last_data = row[2]  # data
                if last_data:
                    last_data = last_data.split('T')[0]  # Взять часть до 'T'
                    last_data = '-'.join(reversed(last_data.split('.')))  # Преобразовать в формат дд.мм.гггг
                    print(f"Значение last_data: {last_data}")  
    except Exception as e: 
        print(f"Ошибка доступа к таблице {school_table}: {e}")

    if request.method == 'POST':
        form = PublishForm(request.POST)
        form.fields['book'].queryset = user_books

        # Проверка ISBN
        isbn = request.POST.get('ISBN')
        if isbn:
            existing_book = Book.objects.filter(user=request.user, ISBN=isbn).first()
            if existing_book:
                messages.info(request, f"Книга с ISBN {isbn} найдена: {existing_book.name}")
                # Предзаполняем форму найденной книгой
                form = PublishForm(request.POST, initial={'book': [existing_book.id]})
                form.fields['book'].queryset = user_books
            else:
                messages.error(request, f"Книга с ISBN {isbn} не найдена в вашей библиотеке.")
                return render(request, 'myapp/add_publish.html', {'form': form})

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
                    iin=form.cleaned_data['iin'],
                    date_out=form.cleaned_data['date_out'] or last_data,
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

            Publish.objects.bulk_create(publish_instances)

            # Отправка email
            recipient_email = form.cleaned_data['email']
            send_mail(
                'Подтверждение аренды книги',
                f"""Уважаемый {name},

            Вы успешно арендовали следующие книги:

            - Книга: {book_instance.name}
            Количество: {quantity}
            Дата получения: {form.cleaned_data['date_out'] or last_data}
            Дата возврата: {form.cleaned_data['date_in']}

            Спасибо, что пользуетесь нашей библиотекой!
            """,
                'kitaphana@oqz.kz',  # Измените на ваш реальный адрес отправителя
                [recipient_email],
                fail_silently=False,
            )

            return redirect(reverse('myapp:rent_book'))
    else:
        # GET запрос - создаем новую форму с начальными данными
        form = PublishForm(initial={'iin': last_card, 
                                    'name': last_a1, 
                                    'date_out': last_data or date.today().strftime('%Y-%m-%d')
                                    })
        form.fields['book'].queryset = user_books

        print(f"Инициализация формы: {form.initial}")

    return render(request, 'myapp/add_publish.html', {'form': form})
