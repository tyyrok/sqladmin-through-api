from abc import abstractmethod, ABC
import io
from typing import Optional, Union, NamedTuple, Type, Any, List, Tuple

import httpx
from urllib.parse import urlencode
from sqladmin import BaseView, expose
from starlette import status
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse, Response
from starlette.datastructures import URL, FormData, UploadFile
from sqladmin.pagination import Pagination
from wtforms import Form

from constants.admin import RequestMethod, AdminFormType
from utilities.admin.form import create_form
from utilities.admin.openapi import (
    get_schema_for_form_from_api,
    get_open_api_json,
)


class ApiUrls(NamedTuple):
    base_url: str
    list_path: str
    create_path: str
    update_path: str
    detail_path: str
    delete_path: str
    openapi_path: str
    admin_login_path: str


class APIBaseView(BaseView, ABC):
    """Class provides models from third-party API to slqadmin.
    For creating new model from API inherit from this class and set up
    some attributes (API urls, identity, name). Also you need to override
    at least one method (usually list) for adding your new model fro API
    to sqladmin menu.

    ???+ usage
        ```python
        class BookAdmin(APIBaseView):
            name = "Book"
            icon = "fa-solid fa-chart-line"

            @expose("/book/list", methods=["GET"], identity="book")
            async def list(self, request: Request):
                ...
                return await self.templates.TemplateResponse(
                    request, self.list_template, context=context
                )

        admin.add_base_view(BookAdmin)
        ```
    """

    name = "Model name"
    icon = "fa"
    page_size = 50
    page_size_options = [5, 10, 50]

    identity = "identity"
    """ Obligatory attribute. Should be unique"""

    column_list = []
    """ You can set up manually, or values will be get from openapi """

    column_labels = []
    column_detail_list = []
    """ You can set up manually, or values will be get from openapi """

    column_detail_labels = {}
    column_sortable_list = []

    urls = ApiUrls(
        base_url="http://localhost/",
        list_path="api/list/",
        create_path="api/create/",
        update_path="api/update/{object_id}/",
        detail_path="api/detail/{object_id}/",
        delete_path="api/list/",
        openapi_path="openapi.json/",
        admin_login_path="/admin/login",
    )
    """ Obligatory attribute for making request to third-party API"""

    create_form = None
    """ By default created from parsed openapi, but you can set up form
    by youself using WTForms, for example:
        ???+ usage
        ```python
        from wtforms import Form, StringField
        class BookCreateForm(Form):
            author = StringField(
                'Author', validators=[validators.input_required()]
            )
            title  = StringField(
                'Title', validators=[validators.input_required()]
                )

        ```
    """
    create_form_schema = {}
    """ Attr for storing parsed from openapi schema for create"""

    update_form = None
    """ By default created from parsed openapi, but you can set up form
    by youself using WTForms"""

    update_form_schema = {}
    """ Attr for storing parsed from openapi schema for update"""

    openapi_schema = None
    """ Attr for storing parsed openapi schema"""

    create_template = "custom_create.html"
    list_template = "custom_list.html"
    details_template = "custom_details.html"

    @abstractmethod
    @expose("/identity/list/", methods=["GET"], identity="identity")
    async def list(self, request: Request) -> HTMLResponse:
        """Abstract method that provides objects list with sort and
        pagination.

        Please override it to add model to sqladmin menu.

        Args:
            request (Request): Starlette Request

        Returns:
            HTMLResponse: html response
        """
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

    async def details(self, request: Request) -> HTMLResponse:
        obj_id = request.path_params.get("pk", None)
        if not obj_id:
            return RedirectResponse(
                str(request.url_for("admin:list", identity=self.identity))
            )
        data = await self._get_object_for_details(
            request=request, params={f"{self.identity}_id": obj_id}
        )
        context = {}
        if data is None:
            context["service_unavailable"] = True
        else:
            context["service_unavailable"] = False
            data = await self._filter_data_by_column_list(data)
        context.update(
            {
                "record": data,
                "name_plural": self.name,
                "column_detail_list": self.column_detail_list,
                "column_detail_labels": self.column_detail_labels,
                "get_url_for_delete": self._url_for_delete,
                "get_url_for_update": self._url_for_update,
            }
        )
        request.path_params["identity"] = self.identity
        return await self.templates.TemplateResponse(
            request, self.details_template, context=context
        )

    async def create(self, request: Request) -> Response:
        identity = request.path_params["identity"]
        if not self.openapi_schema:
            self.openapi_schema = await get_open_api_json(
                self.urls.base_url + self.urls.openapi_path
            )
        if self.openapi_schema:
            self.create_form_schema = await get_schema_for_form_from_api(
                openapi_schema=self.openapi_schema,
                target_path=self.urls.create_path,
                method=RequestMethod.post,
            )
            form = await self._scaffold_form(AdminFormType.create)
            form_data = await self._handle_form_data(request)
            form = form(form_data)
            context = {
                "form": form,
                "name_plural": self.name,
                "service_unavailable": False,
            }
            if request.method == "GET":
                return await self.templates.TemplateResponse(
                    request, self.create_template, context=context
                )
            if not form.validate():
                return await self.templates.TemplateResponse(
                    request=request,
                    name=self.create_template,
                    context=context,
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            token = await self._get_token(request)
            result = await self._send_request_to_api(
                url=(self.urls.base_url + self.urls.create_path),
                method=RequestMethod.post,
                token=token,
                json=form.data,
            )
            if result and result.status_code == status.HTTP_201_CREATED:
                pk = result.json().get("id")
                if pk:
                    url = self._url_for_details(
                        request=request, pk=pk, identity=identity
                    )
                    return RedirectResponse(
                        url=url, status_code=status.HTTP_302_FOUND
                    )
            elif result:
                context["error"] = result.json()
                return await self.templates.TemplateResponse(
                    request=request, name=self.create_template, context=context
                )
        else:
            context = {
                "form": None,
                "name_plural": self.name,
                "service_unavailable": True,
            }
            return await self.templates.TemplateResponse(
                request, self.create_template, context=context
            )

    async def update(self, request: Request, pk: int) -> Response:
        identity = request.path_params["identity"]
        if not self.openapi_schema:
            self.openapi_schema = await get_open_api_json(
                self.urls.base_url + self.urls.openapi_path
            )
        if self.openapi_schema:
            self.update_form_schema = await get_schema_for_form_from_api(
                openapi_schema=self.openapi_schema,
                target_path=self.urls.update_path,
                method=RequestMethod.patch,
            )
            form = await self._scaffold_form(AdminFormType.update)
            data = await self._get_object_for_details(
                request=request, params={f"{identity}_id": pk}
            )
            context = {
                "form": form(data=data),
                "name_plural": self.name,
                "service_unavailable": False,
            }
            if request.method == "GET":
                return await self.templates.TemplateResponse(
                    request, self.create_template, context=context
                )
            form_data = await self._handle_form_data(request)
            form = form(form_data)
            if not form.validate():
                return await self.templates.TemplateResponse(
                    request=request,
                    name=self.create_template,
                    context=context,
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            token = await self._get_token(request)
            url = await self.insert_params_to_path(
                (self.urls.base_url + self.urls.update_path),
                {f"{identity}_id": pk},
            )
            result = await self._send_request_to_api(
                url=url,
                method=RequestMethod.patch,
                token=token,
                json=form.data,
            )
            if result and result.status_code == status.HTTP_200_OK:
                pk = result.json().get("id")
                if pk:
                    url = self._url_for_details(
                        request=request, pk=pk, identity=identity
                    )
                    return RedirectResponse(
                        url=url, status_code=status.HTTP_302_FOUND
                    )
            elif result:
                context["error"] = result.json()
                return await self.templates.TemplateResponse(
                    request=request, name=self.create_template, context=context
                )
        else:
            context = {
                "form": None,
                "name_plural": self.name,
                "service_unavailable": True,
            }
            return await self.templates.TemplateResponse(
                request, self.create_template, context=context
            )

    async def delete(self, request: Request, pks: List[int]) -> Response:
        token = await self._get_token(request)
        for pk in pks:
            url = await self.insert_params_to_path(
                (self.urls.base_url + self.urls.delete_path),
                {f"{self.identity}_id": pk},
            )
            r = await self._send_request_to_api(
                url=f"{url}",
                method=RequestMethod.delete,
                token=token,
            )
            if not (r and r.status_code == status.HTTP_204_NO_CONTENT):
                logger.exception(r.json())
        request.path_params["identity"] = self.identity
        return Response(
            str(request.url_for("admin:list", identity=self.identity))
        )

    async def _get_token(self, request: Request) -> str:
        """Method to get token from session in case third-party API is private.
        Override this method for your circumstances

        Args:
            request (Request): Fastapi request

        Returns:
            str: returns token string
        """
        try:
            token = request.session.get("token")
        except KeyError as ex:
            logger.exception(ex)
            return RedirectResponse(self.urls.admin_login_path)
        return token

    async def _get_data_from_api(
        self,
        url: str,
        method: RequestMethod,
        token: Optional[str] = None,
        params: Optional[dict] = None,
    ) -> Union[dict, list, None]:
        """Simple method to make request using httpx library
        to third-party API by urls (self.urls) and get json response

        Args:
            url (str): url to make request.
            method (RequestMethod): requst method (GET, POST etc).
            token (Optional[str], optional): Token Bearer if third-party
            API is private. Defaults to None.
            params (dict, optional): Parameters for request such as order_by,
            skip and limit etc. Defaults to None.

        Returns:
            Union[dict, list, None]: List of objects or objects itself
        """
        if not params:
            params = {}
        headers = {}
        async with httpx.AsyncClient() as client:
            if token:
                headers.update({"Authorization": f"Bearer {token}"})
            try:
                r = await client.request(
                    method=method, url=url, headers=headers, params=params
                )
                r.raise_for_status()
            except httpx.HTTPError as ex:
                logger.exception(ex)
                return None
            return r.json()

    async def _send_request_to_api(
        self,
        url: str,
        method: RequestMethod,
        token: Optional[str] = None,
        params: Optional[dict] = None,
        json: Optional[dict] = None,
    ) -> httpx.Response:
        """General method to make request using httpx library
        to third-party API by urls (self.urls) and get response

        Args:
            - url (str): url to make request.
            - method (RequestMethod): requst method (GET, POST etc).
            - token (Optional[str], optional): Token Bearer if third-party
            API is private. Defaults to None.
            - params (dict, optional): Parameters for request such as order_by,
            skip and limit etc. Defaults to None.
            - json (dict, optional): Json for body. Defaults to {}.

        Returns:
            - response (httpx.Response): Response instance
        """
        if not params:
            params = {}
        if not json:
            json = {}
        headers = {}
        async with httpx.AsyncClient() as client:
            if token:
                headers.update({"Authorization": f"Bearer {token}"})
            try:
                r = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json,
                )
                r.raise_for_status()
            except httpx.RequestError as ex:
                logger.exception(ex)
                return None
            except httpx.HTTPStatusError as ex:
                logger.exception(ex)
            return r

    async def _filter_data_by_column_list(
        self, data: Union[dict, list]
    ) -> Union[dict, list]:
        """Method to filter response by column_list (self.column_list)
        if it set up. Otherwise add all keys from response to column list
        (or column detail list).

        Args:
            data (Union[dict, list]): response data from third-party API

        Returns:
            Union[dict, list]: List of objects or objects itself
        """
        if data and isinstance(data, list):
            if self.column_list:
                keys_to_remove = set(self.column_list) - set(data[0].keys())
                for elem in data:
                    for key in keys_to_remove:
                        elem.pop(key, None)
            else:
                self.column_list = data[0].keys()
        elif data and isinstance(data, dict):
            if self.column_detail_list:
                keys_to_remove = set(self.column_detail_list) - set(
                    data.keys()
                )
                for key in keys_to_remove:
                    data.pop(key, None)
            else:
                self.column_detail_list = data.keys()
        return data

    async def _get_paginated_data(self, request: Request) -> Pagination:
        """Overriden method from SQLadmin to deal with api
        request instead of sqlachemy queries

        Args:
            request (Request): Fastapi request

        Returns:
            Pagination: dataclass from sqladmin
        """
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("pageSize", 0))
        page_size = min(
            page_size or self.page_size, max(self.page_size_options)
        )
        sort_by_filter = request.query_params.get("sortBy", None)
        sort_filter = request.query_params.get("sort", None)
        params = {}
        if sort_by_filter:
            try:
                sort_by_filter = sort_by_filter.split(".")[-1]
                if sort_by_filter in self.column_list:
                    if sort_filter and sort_filter == "desc":
                        params["order_by"] = sort_by_filter
                    else:
                        params["order_by"] = "-" + sort_by_filter
            except AttributeError as ex:
                logger.exception(ex.args)
        else:
            params["order_by"] = "id"
        token = await self._get_token(request)
        params.update({"skip": (page - 1) * page_size, "limit": page_size})
        data = await self._get_data_from_api(
            url=(self.urls.base_url + self.urls.list_path),
            method=RequestMethod.get,
            token=token,
            params=params,
        )
        return await self._make_pagination(
            page=page, page_size=page_size, data=data
        )

    async def _make_pagination(
        self, page: int, page_size: int, data: Union[dict, list]
    ) -> Pagination:
        """Override this method to process response data from third-party API.
        By default method deal with response like that:

        {
            "objects": [
                {
                "id": 1,
                ...
                }
            ],
            "total_count": 1
        }

        Returns:
            Pagination: dataclass from sqladmin
        """
        return Pagination(
            rows=data["objects"] if data else None,
            page=page,
            page_size=page_size,
            count=data["total_count"] if data else 0,
        )

    async def _get_object_for_details(
        self, request: Request, params: dict
    ) -> dict:
        """Method to get object info from third-party API

        Args:
            request (Request): Starlette response
            params (dict): paramaters to insert into url.
            For example
            {"object_id": 1} for `http://localhost/book/{object_id}/`

        Returns:
            dict: object from third-party response
        """
        token = await self._get_token(request)
        url = await self.insert_params_to_path(
            (self.urls.base_url + self.urls.detail_path), params
        )
        return await self._get_data_from_api(
            url=url,
            method=RequestMethod.get,
            token=token,
        )

    def _url_for_details(
        self, request: Request, pk: int, identity: str
    ) -> Union[str, URL]:
        spacename = "admin"
        return request.url_for(
            f"{spacename}:details",
            identity=identity,
            pk=pk,
        )

    def _url_for_create(
        self, request: Request, identity: str
    ) -> Union[str, URL]:
        spacename = "admin"
        return request.url_for(
            f"{spacename}:create",
            identity=identity,
        )

    def _url_for_update(
        self, request: Request, pk: int, identity: str
    ) -> Union[str, URL]:
        spacename = "admin"
        return request.url_for(f"{spacename}:edit", identity=identity, pk=pk)

    def _url_for_delete(
        self, request: Request, identity: str, pks: List[int]
    ) -> Union[str, URL]:
        spacename = "admin"
        query_params = urlencode({"pks": pks[0]})
        url = request.url_for(
            f"{spacename}:delete",
            identity=identity,
        )
        return str(url) + "?" + query_params

    async def _scaffold_form(self, form_type: AdminFormType) -> Type[Form]:
        """Generate wtforms.Form by parsing openapi schema. Method implemented
        very limited list for Fields, so you if is needed more you can override
        create_form method or set self.create_form attr of class.

        Args:
            form_type (AdminFormType): enum

        Returns:
            Type[Form]: class of wtforms.Form
        """
        if form_type == AdminFormType.create:
            if self.create_form is not None:
                return self.create_form
            form = await create_form(
                form_name=f"{self.identity}{AdminFormType.create}",
                form_schema=self.create_form_schema,
                openapi_schema=self.openapi_schema,
            )
            self.create_form = form
        elif form_type == AdminFormType.update:
            if self.update_form is not None:
                return self.update_form
            form = await create_form(
                form_name=f"{self.identity}{AdminFormType.update}",
                form_schema=self.update_form_schema,
                openapi_schema=self.openapi_schema,
            )
        return form

    async def _handle_form_data(
        self, request: Request, obj: Any = None
    ) -> FormData:
        """
        This method is almost taken from sqladmin.application.Admin

        Handle form data and modify in case of UploadFile.
        This is needed since in edit page
        there's no way to show current file of object.
        """

        form = await request.form()
        form_data: List[Tuple[str, Union[str, UploadFile]]] = []
        for key, value in form.multi_items():
            if not isinstance(value, UploadFile):
                form_data.append((key, value))
                continue

            should_clear = form.get(key + "_checkbox")
            empty_upload = len(await value.read(1)) != 1
            await value.seek(0)
            if should_clear:
                form_data.append((key, UploadFile(io.BytesIO(b""))))
            elif empty_upload and obj and getattr(obj, key):
                f = getattr(obj, key)  # In case of update, imitate UploadFile
                form_data.append(
                    (key, UploadFile(filename=f.name, file=f.open()))
                )
            else:
                form_data.append((key, value))
        return FormData(form_data)

    async def insert_params_to_path(self, url: str, params: dict) -> str:
        """Method that puts params in url http://localhost/book/{book_id}/ ->
        http://localhost/book/1/

        Args:
            url (str): url
            params (dict): parameters that should be put in url,
            for example {"object_id": 1}

        Returns:
            str: url
        """
        prefix, path = url.split("://")
        elems = path.split("/")
        new_elems = []
        for elem in elems:
            if params.get(elem):
                new_elems.append(params.get(elem))
            elif params.get(elem.strip("{}")):
                new_elems.append(params.get(elem.strip("{}")))
            else:
                new_elems.append(elem)
        url = prefix + "://" + "/".join(new_elems)
        if not url.endswith("/"):
            url += "/"
        return url
