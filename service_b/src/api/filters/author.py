from typing import Optional

from fastapi_filter.contrib.sqlalchemy import Filter
from models import Author


class AuthorFilter(Filter):
    order_by: Optional[list[str]] = None

    class Constants(Filter.Constants):
        model = Author
