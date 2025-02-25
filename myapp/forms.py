from MySQLdb import Date
from django import forms
from django.forms import Select, widgets, DateInput

class LoginForm(forms.Form):
    name = forms.CharField(
        min_length=6,
        label='Имя пользователя',
        error_messages={
            'required': 'Имя пользователя не может быть пустым',
            'min_length': 'Должно быть не менее 6 символов',
        },
        widget=widgets.TextInput(
            attrs={
                'class': 'form-control',
            }
        )
    )

    pwd = forms.CharField(
        min_length=6,
        label='Пароль',
        error_messages={
            'required': 'Это поле обязательно для заполнения',
            'min_length': 'Должно быть не менее 6 символов',
        },
        widget=widgets.TextInput(
            attrs={
                'class': 'form-control'
            }
        )
    )

from django.forms import TextInput, NumberInput
from .models import Book, Publish, News

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = (
            'ISBN', 'name', 'bbk', 'quantity', 'balance_quantity', 'author', 'year_published'
        )

        labels = {
            'ISBN': 'Штрих код',
            'name': 'Название',
            'bbk': 'ББК',
            'quantity': 'Количество',
            'balance_quantity': 'Остаток',
            'author': 'Автор',
            'year_published': 'Год издания'
        }
        widgets = {
            'ISBN': TextInput(attrs={'class': 'form-control'}),
            'name': TextInput(attrs={'class': 'form-control'}),
            'author': TextInput(attrs={'class': 'form-control'}),
            'bbk': TextInput(attrs={'class': 'form-control'}),
            'quantity': NumberInput(attrs={'class': 'form-control'}),
            'balance_quantity': NumberInput(attrs={'class': 'form-control'}),
            'year_published': NumberInput(attrs={'class': 'form-control'}),
        }

        error_messages = {
            'name': {
                "required": "Название книги не может быть пустым",
                'max_length': "Название не может превышать 100 символов",
            },
             'author': {
                "required": "Название автор не может быть пустым",
                'max_length': "Название не может превышать 100 символов",
            },
            'bbk': {
                "required": "Поле ББК не может быть пустым",
            },
            'quantity': {
                "required": "Пожалуйста, укажите количество",
            },
            'balance_quantity': {
                "required": "Поле остаток не может быть пустым",
            },
            'ISBN': {
                "required": "Поле остаток не может быть пустым",
            },
            'year_published': {
                "required": "Поле остаток не может быть пустым",
            }
        }



from django.contrib.auth.models import User


class RegForm(forms.Form):
    name = forms.CharField(
        min_length=5,
        label='Имя Школы',
        error_messages={
            'required': 'Имя пользователя не может быть пустым',
            'min_length': 'Не менее 6 символов',
        },
        widget=widgets.TextInput(
            attrs={
                'class': 'form-control',
            }
        )
    )

    lastname = forms.CharField(
        min_length=2,
        label='БИН Школы',
        required=True,
        error_messages={
            'required': 'Фамилия пользователя не может быть пустой',
            'min_length': 'Не менее 2 символов',
        },
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
            }
        )
    )

    pwd = forms.CharField(
        min_length=6,
        label='Пароль',
        error_messages={
            'required': 'Это поле не может быть пустым',
            'min_length': 'Не менее 6 символов',
        },
        widget=widgets.TextInput(
            attrs={
                'class': 'form-control'
            }
        )
    )
    r_pwd = forms.CharField(
        min_length=6,
        label='Подтвердите пароль',
        error_messages={
            'required': 'Это поле не может быть пустым',
            'min_length': 'Не менее 6 символов',
        },
        widget=widgets.TextInput(
            attrs={
                'class': 'form-control'
            }
        )
    )
    email = forms.EmailField(
        label='Электронная почта',
        error_messages={'required': 'Это поле не может быть пустым', 'invalid': 'Неверный формат'},
        widget=widgets.EmailInput(
            attrs={
                'class': 'form-control'
            }
        )
    )

    def clean_name(self):
        reg_name = self.cleaned_data.get('name')
        db_name = User.objects.filter(username=reg_name)

        if not db_name:
            return reg_name
        else:
            raise forms.ValidationError('Этот пользователь уже зарегистрирован!')

    def clean_email(self):
        reg_email = self.cleaned_data.get('email')
        db_email = User.objects.filter(email=reg_email)

        if not db_email:
            return reg_email
        else:
            raise forms.ValidationError('Этот адрес электронной почты уже зарегистрирован')

    def clean(self):
        pwd = self.cleaned_data.get('pwd')
        r_pwd = self.cleaned_data.get('r_pwd')

        if pwd and r_pwd:
            if pwd == r_pwd:
                return self.cleaned_data
            else:
                raise forms.ValidationError('Пароли не совпадают')

from django import forms
from django.forms import TextInput, NumberInput, DateInput
from datetime import date
from .models import Publish, Book

class PublishForm(forms.ModelForm):
    ISBN = forms.CharField(
        max_length=255,
        label="ISBN",
        required=False,
        widget=TextInput(attrs={"class": "form-control", "placeholder": "Введите штрих код для поиска"}),
        help_text="Введите ISBN книги для автоматического выбора."
    )

    date_out = forms.DateField(
        required=False,
        initial=date.today,
        widget=DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Дата выдачи'
    )

    def clean_date_out(self):
        date_out = self.cleaned_data.get('date_out')
        if not date_out:
            return date.today()
        return date_out

    class Meta:
        model = Publish
        fields = (
            'name', 'iin', 'city', 'email', 'phone', 
            'book', 'quantity', 'date_out', 'date_in'
        )
        labels = {
            'name': 'ФИО',
            'iin': 'ИИН',
            'city': 'Адрес',
            'email': 'Электронная почта',
            'phone': 'Номер телефона',
            'book': 'Книга',
            'quantity': 'Количество',
            'date_out': 'Дата выдачи',
            'date_in': 'Дата возврата',
        }
        widgets = {
            'name': TextInput(attrs={'class': 'form-control'}),
            'iin': TextInput(attrs={'class': 'form-control'}),
            'city': TextInput(attrs={'class': 'form-control'}),
            'email': TextInput(attrs={'class': 'form-control'}),
            'phone': TextInput(attrs={'class': 'form-control'}),
            'book': forms.Select(attrs={'class': 'form-control'}),
            'quantity': NumberInput(attrs={'class': 'form-control'}),
            'date_out': DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_in': DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        } 
        error_messages = {
            'name': {
                'max_length': "Не может превышать 32 символа",
                "required": "Это поле обязательно для заполнения",
            },
            'iin': {
                'max_length': "Не может превышать 12 символов",  # Сообщение об ошибке для ИИН
                "required": "Это поле обязательно для заполнения",
            },
            'city': {
                'max_length': ("Не может превышать 32 символа"),
                "required": "Это поле обязательно для заполнения",
            },
            'phone': {
                'invalid': 'Неправильный формат номера телефона',
                "required": "Это поле обязательно для заполнения",
            },
            'quantity': {
                'invalid': 'Неправильное количество',
                "required": "Это поле обязательно для заполнения",
            },
            'date_out': {
                'invalid': 'Неправильная дата',
                "required": "Это поле обязательно для заполнения",
            },
            'date_in': {
                'invalid': 'Неправильное время',
                "required": "Это поле обязательно для заполнения",
            }
        }

from django import forms
from .models import News

class NewsForm(forms.ModelForm):
    class Meta:
        model = News
        fields = ['title', 'tag', 'text', 'photo', 'publish_date']  # Добавили поле publish_date
        labels = {
            'title': 'Заголовок',
            'tag': 'Тег',
            'text': 'Текст',
            'photo': 'Фото',
            'publish_date': 'Дата публикации',
        }
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'tag': forms.TextInput(attrs={'class': 'form-control'}),
            'text': forms.Textarea(attrs={'class': 'form-control'}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'publish_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),  # Виджет для выбора даты
        }
