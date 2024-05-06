import pandas as pd
from .models import Book

def create_books_from_excel(file, user):
    # Если загружается файл из Django, нужно использовать buffer или аналогичный подход
    df = pd.read_excel(file)

    for index, row in df.iterrows():
        Book.objects.create(
            ISBN=row.get('Книжный номер', None),
            author=row.get('Автор', None),
            name=row.get('Название книги', None),
            bbk=row.get('BBK', None),
            quantity=row.get('Количество', None),
            balance_quantity=row.get('Остаток книг', None),
            year_published=row.get('Год издания', None),
            user=user
    )
