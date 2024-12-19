import pandas as pd
from .models import Book

# def create_books_from_excel(file, user):
#     # Если загружается файл из Django, нужно использовать buffer или аналогичный подход
#     df = pd.read_excel(file)

#     for index, row in df.iterrows():
#         Book.objects.create(
#             ISBN=row['Книжный номер'],
#             author=row['Автор'],
#             name=row['Название книги'],
#             bbk=row['BBK'],
#             quantity=row['Количество'],
#             balance_quantity=row['Остаток книг'],
#             year_published=row['Год издания'],
#             user=user  # Теперь user определён в параметрах функции
#         )


def create_books_from_excel(file, user):
    df = pd.read_excel(file)

    # Обработка NaN и преобразование в числовой формат
    df['Количество'] = pd.to_numeric(df['Количество'], errors='coerce').fillna(0).astype(int)
    df['Остаток книг'] = pd.to_numeric(df['Остаток книг'], errors='coerce').fillna(0).astype(int)

    for index, row in df.iterrows():
        Book.objects.create(
            ISBN=row['Книжный номер'],
            author=row['Автор'],
            name=row['Название книги'],
            bbk=row['BBK'],
            quantity=row['Количество'],
            balance_quantity=row['Остаток книг'],
            year_published=row['Год издания'],
            user=user
        )


import pandas as pd
import logging
from .models import Book

logger = logging.getLogger(__name__)

def create_books_from_excel(file, user):
    df = pd.read_excel(file)

    for index, row in df.iterrows():
        try:
            balance_quantity = pd.to_numeric(row['Остаток книг'], errors='coerce')
            quantity = pd.to_numeric(row['Количество'], errors='coerce')

            if pd.isna(balance_quantity) or pd.isna(quantity):
                logger.error(f"Некорректные данные в строке {index}: {row}")
                continue

            Book.objects.create(
                ISBN=row['Книжный номер'],
                author=row['Автор'],
                name=row['Название книги'],
                bbk=row['BBK'],
                quantity=int(quantity),
                balance_quantity=int(balance_quantity),
                year_published=row['Год издания'],
                user=user
            )
        except Exception as e:
            logger.error(f"Ошибка обработки строки {index}: {row}. Ошибка: {e}")
