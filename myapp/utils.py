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
            # Преобразование данных
            isbn = str(row['Книжный номер']).strip() if not pd.isna(row['Книжный номер']) else ''
            quantity = int(row['Количество']) if not pd.isna(row['Количество']) else 0
            balance_quantity = int(row['Остаток книг']) if not pd.isna(row['Остаток книг']) else 0
            year_published = int(row['Год издания']) if not pd.isna(row['Год издания']) else 0
            bbk = str(row['BBK']).strip() if not pd.isna(row['BBK']) else ''
            name = str(row['Название книги'])[:255] if not pd.isna(row['Название книги']) else ''
            author = str(row['Автор'])[:255] if not pd.isna(row['Автор']) else ''

            # Проверка наличия записи
            if not Book.objects.filter(ISBN=isbn, user=user).exists():
                Book.objects.create(
                    ISBN=isbn,
                    author=author,
                    name=name,
                    bbk=bbk,
                    quantity=quantity,
                    balance_quantity=balance_quantity,
                    year_published=year_published,
                    user=user
                )
                logger.info(f"Добавлена книга: {name}, ISBN: {isbn}")
            else:
                logger.warning(f"Книга с ISBN {isbn} уже существует в базе данных.")
        except Exception as e:
            logger.error(f"Ошибка в строке {index} (ISBN: {row['Книжный номер']}): {e}")
