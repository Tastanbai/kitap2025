import pandas as pd
from .models import Book

def create_books_from_excel(file, user):
    # Если загружается файл из Django, нужно использовать buffer или аналогичный подход
    df = pd.read_excel(file)

    for index, row in df.iterrows():
        Book.objects.create(
            ISBN=row['Книжный номер'],
            author=row['Автор'],
            name=row['Название книги'],
            bbk=row['BBK'],
            quantity=row['Количество'],
            balance_quantity=row['Остаток книг'],
            year_published=row['Год издания'],
            user=user  # Теперь user определён в параметрах функции
        )