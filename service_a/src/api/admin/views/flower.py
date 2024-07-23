from sqladmin import ModelView

from models import Flower


class FlowerAdmin(ModelView, model=Flower):
    page_size = 100
    column_default_sort = ("id", True)
    column_list = [
        Flower.id,
        Flower.title,
    ]
