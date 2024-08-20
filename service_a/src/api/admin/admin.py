from api.admin.custom_admin import CustomAdmin

from api.admin.views.author import AuthorAdmin
from api.admin.views.book import BookAdmin
from api.admin.views.flower import FlowerAdmin


def load_admin_site(admin: CustomAdmin) -> None:
    admin.add_base_view(BookAdmin)
    admin.add_base_view(AuthorAdmin)
    admin.add_model_view(FlowerAdmin)
