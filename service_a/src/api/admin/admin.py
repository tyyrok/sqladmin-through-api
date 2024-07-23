from api.admin.custom_admin import CustomAdmin

from api.admin.views.book import BookAdmin


def load_admin_site(admin: CustomAdmin) -> None:
    admin.add_base_view(BookAdmin)
