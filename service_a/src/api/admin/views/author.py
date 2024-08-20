from sqladmin import expose
from api.admin.custom_baseview import APIBaseView
from starlette.requests import Request
from starlette.responses import HTMLResponse

from api.admin.custom_baseview import ApiUrls


urls = ApiUrls(
    base_url="http://service-b-core:8000",
    list_path=("/service-b/v1/author/list/"),
    detail_path=("/service-b/v1/author/{author_id}/"),
    create_path=("/service-b/v1/author/"),
    update_path=("/service-b/v1/author/{author_id}/"),
    delete_path=("/service-b/v1/author/{author_id}/"),
    openapi_path="/service-b/openapi.json/",
    admin_login_path="admin",
)


class AuthorAdmin(APIBaseView):
    page_size = 50
    identity = "author"
    urls = urls
    name = "Author"
    icon = "fa"
    column_list = ["id", "first_name", "last_name"]
    column_labels = {
        "id": "id",
        "first_name": "First Name",
        "last_name": "Last Name",
    }
    column_detail_list = []
    column_detail_labels = {}
    column_sortable_list = ["id", "last_name"]
    use_token = False

    @expose("/author/list", methods=["GET"], identity="author")
    async def list(self, request: Request) -> HTMLResponse:
        context = {
            "page_size": self.page_size,
            "page_size_options": self.page_size_options,
            "name_plural": self.name,
            "column_list": self.column_list,
            "column_labels": self.column_labels,
            "column_sortable_list": self.column_sortable_list,
            "get_url_for_details": self.url_for_details,
            "get_url_for_create": self.url_for_create,
            "get_url_for_delete": self.url_for_delete,
            "get_url_for_update": self.url_for_update,
            "request": request,
        }
        pagination = await self.get_paginated_data(request)
        pagination.add_pagination_urls(request.url)
        if pagination.rows is None:
            context["service_unavailable"] = True
        else:
            context["service_unavailable"] = False
            pagination.rows = await self.filter_data_by_column_list(
                pagination.rows
            )
        context["pagination"] = pagination
        request.path_params["identity"] = self.identity
        return await self.templates.TemplateResponse(
            request, self.list_template, context=context
        )
