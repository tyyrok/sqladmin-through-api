from typing import Optional

from fastapi_filter.contrib.sqlalchemy import Filter
from models import Book


class BookFilter(Filter):
    order_by: Optional[list[str]] = None

    class Constants(Filter.Constants):
        model = Book
