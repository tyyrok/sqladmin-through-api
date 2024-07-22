from sqladmin import expose
from api.admin.custom_baseview import APIBaseView
from starlette.requests import Request
from starlette.responses import HTMLResponse

from configs.config import services_settings as setting
from api.admin.custom_baseview import ApiUrls


urls = ApiUrls(
    base_url=setting.API_GATEWAY_URL,
    list_path=(setting.GAME_SERVICE_PATH + "v1/admin/question/list/"),
    detail_path=(
        setting.GAME_SERVICE_PATH + "v1/admin/question/{question_id}/"
    ),
    create_path=(setting.GAME_SERVICE_PATH + "v1/admin/question/"),
    update_path=(
        setting.GAME_SERVICE_PATH + "v1/admin/question/{question_id}/"
    ),
    delete_path=(
        setting.GAME_SERVICE_PATH + "v1/admin/question/{question_id}/"
    ),
    openapi_path=setting.GAME_SERVICE_PATH + "openapi.json/",
    admin_login_path=setting.USER_SERVICE_PATH + "admin/login",
)


class QuestionAdmin(APIBaseView):
    create_template = "custom_create.html"
    list_template = "custom_list.html"
    details_template = "custom_details.html"
    page_size = 50
    identity = "question"
    urls = urls
    name = "Question"
    icon = "fa"
    column_list = [
        "id",
        "title",
        "difficulty",
        "game_id",
        "round",
        "image",
        "category_id",
        "created_at",
        "updated_at",
    ]
    column_labels = {
        "id": "id",
        "title": "название",
        "difficulty": "сложность",
        "game_id": "id игры",
        "round": "раунд",
        "image": "изображение",
        "category_id": "категория",
        "created_at": "дата создания",
        "updated_at": "дата обновления",
    }
    column_detail_list = []
    column_detail_labels = {}
    column_sortable_list = [
        "id",
        "title",
        "difficulty",
        "game_id",
        "round",
        "image",
        "category_id",
        "created_at",
        "updated_at",
    ]

    @expose("/question/list", methods=["GET"], identity="question")
    async def list(self, request: Request) -> HTMLResponse:
        context = {
            "page_size": self.page_size,
            "page_size_options": self.page_size_options,
            "name_plural": self.name,
            "column_list": self.column_list,
            "column_labels": self.column_labels,
            "column_sortable_list": self.column_sortable_list,
            "get_url_for_details": self._url_for_details,
            "get_url_for_create": self._url_for_create,
            "get_url_for_delete": self._url_for_delete,
            "get_url_for_update": self._url_for_update,
            "request": request,
        }
        pagination = await self._get_paginated_data(request)
        pagination.add_pagination_urls(request.url)
        if pagination.rows is None:
            context["service_unavailable"] = True
        else:
            context["service_unavailable"] = False
            pagination.rows = await self._filter_data_by_column_list(
                pagination.rows
            )
        context["pagination"] = pagination
        request.path_params["identity"] = self.identity
        return await self.templates.TemplateResponse(
            request, self.list_template, context=context
        )
