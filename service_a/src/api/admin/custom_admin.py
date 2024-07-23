import logging

from sqladmin.authentication import login_required
from starlette.requests import Request
from starlette.exceptions import HTTPException
from starlette.responses import Response, RedirectResponse
from sqladmin.models import BaseView, ModelView
from sqladmin import Admin

logger = logging.getLogger(__name__)


class CustomAdmin(Admin):
    """Overriden sqladmin.Admin class to handle APIBaseViews with the
    same routes as basic ModelViews.
    """

    @login_required
    async def list(self, request: Request) -> Response:
        """List route to display paginated Model instances."""

        await self._list(request)
        identity = request.path_params["identity"]
        model_view = self._find_model_view(identity)
        if model_view:
            pagination = await model_view.list(request)
            pagination.add_pagination_urls(request.url)

            context = {"model_view": model_view, "pagination": pagination}
            return await self.templates.TemplateResponse(
                request, model_view.list_template, context
            )
        for view in self._views:
            if (
                view.identity == identity
                and isinstance(view, BaseView)
                and hasattr(view, "list")
            ):
                return await view.list(request)
        raise HTTPException(status_code=404)

    @login_required
    async def details(self, request: Request) -> Response:
        """Details route."""

        await self._details(request)
        identity = request.path_params["identity"]
        model_view = self._find_model_view(identity)
        if model_view:
            model = await model_view.get_object_for_details(
                request.path_params["pk"]
            )
            if not model:
                raise HTTPException(status_code=404)
            context = {
                "model_view": model_view,
                "model": model,
                "title": model_view.name,
            }
            return await self.templates.TemplateResponse(
                request, model_view.details_template, context
            )
        for view in self._views:
            if (
                view.identity == identity
                and isinstance(view, BaseView)
                and hasattr(view, "details")
            ):
                return await view.details(request)
        raise HTTPException(status_code=404)

    @login_required
    async def create(self, request: Request) -> Response:
        """Create model endpoint."""

        await self._create(request)

        identity = request.path_params["identity"]
        model_view = self._find_model_view(identity)
        if model_view:
            Form = await model_view.scaffold_form()  # noqa: N806
            form_data = await self._handle_form_data(request)
            form = Form(form_data)
            context = {
                "model_view": model_view,
                "form": form,
            }
            if request.method == "GET":
                return await self.templates.TemplateResponse(
                    request, model_view.create_template, context
                )
            if not form.validate():
                return await self.templates.TemplateResponse(
                    request,
                    model_view.create_template,
                    context,
                    status_code=400,
                )
            form_data_dict = self._denormalize_wtform_data(
                form.data, model_view.model
            )
            try:
                obj = await model_view.insert_model(request, form_data_dict)
            except Exception as e:
                logger.exception(e)  # noqa: TRY401
                context["error"] = str(e)
                return await self.templates.TemplateResponse(
                    request,
                    model_view.create_template,
                    context,
                    status_code=400,
                )

            url = self.get_save_redirect_url(
                request=request,
                form=form_data,
                obj=obj,
                model_view=model_view,
            )
            return RedirectResponse(url=url, status_code=302)
        for view in self._views:
            if (
                view.identity == identity
                and isinstance(view, BaseView)
                and hasattr(view, "create")
            ):
                return await view.create(request)
        raise HTTPException(status_code=404)

    @login_required
    async def delete(self, request: Request) -> Response:
        """Delete route."""

        await self._delete(request)

        identity = request.path_params["identity"]
        model_view = self._find_model_view(identity)
        params = request.query_params.get("pks", "")
        pks = params.split(",") if params else []
        if model_view:
            for pk in pks:
                model = await model_view.get_object_for_delete(pk)
                if not model:
                    raise HTTPException(status_code=404)

                await model_view.delete_model(request, pk)

            return Response(
                content=str(request.url_for("admin:list", identity=identity))
            )
        for view in self._views:
            if (
                view.identity == identity
                and isinstance(view, BaseView)
                and hasattr(view, "delete")
            ):
                return await view.delete(request, pks)
        raise HTTPException(status_code=404)

    @login_required
    async def edit(self, request: Request) -> Response:
        """Edit model endpoint."""

        await self._edit(request)

        identity = request.path_params["identity"]
        model_view = self._find_model_view(identity)
        if model_view:
            model = await model_view.get_object_for_edit(
                request.path_params["pk"]
            )
            if not model:
                raise HTTPException(status_code=404)

            Form = await model_view.scaffold_form()  # noqa: N806
            context = {
                "obj": model,
                "model_view": model_view,
                "form": Form(
                    obj=model, data=self._normalize_wtform_data(model)
                ),
            }

            if request.method == "GET":
                return await self.templates.TemplateResponse(
                    request, model_view.edit_template, context
                )

            form_data = await self._handle_form_data(request, model)
            form = Form(form_data)
            if not form.validate():
                context["form"] = form
                return await self.templates.TemplateResponse(
                    request, model_view.edit_template, context, status_code=400
                )

            form_data_dict = self._denormalize_wtform_data(form.data, model)
            try:
                if model_view.save_as and (
                    form_data.get("save") == "Save as new"
                ):
                    obj = await model_view.insert_model(
                        request, form_data_dict
                    )
                else:
                    obj = await model_view.update_model(
                        request,
                        pk=request.path_params["pk"],
                        data=form_data_dict,
                    )
            except Exception as e:
                logger.exception(e)  # noqa: TRY401
                context["error"] = str(e)
                return await self.templates.TemplateResponse(
                    request, model_view.edit_template, context, status_code=400
                )

            url = self.get_save_redirect_url(
                request=request,
                form=form_data,
                obj=obj,
                model_view=model_view,
            )
            return RedirectResponse(url=url, status_code=302)

        for view in self._views:
            if (
                view.identity == identity
                and isinstance(view, BaseView)
                and hasattr(view, "update")
            ):
                return await view.update(request, request.path_params["pk"])
        raise HTTPException(status_code=404)

    def _find_model_view(self, identity: str) -> ModelView:
        for view in self.views:
            if isinstance(view, ModelView) and view.identity == identity:
                return view
        return None

    async def _list(self, request: Request) -> None:
        model_view = self._find_model_view(request.path_params["identity"])
        if model_view and not model_view.is_accessible(request):
            raise HTTPException(status_code=403)

    async def _details(self, request: Request) -> None:
        model_view = self._find_model_view(request.path_params["identity"])
        if model_view and (
            not model_view.can_view_details
            or not model_view.is_accessible(request)
        ):
            raise HTTPException(status_code=403)

    async def _create(self, request: Request) -> None:
        model_view = self._find_model_view(request.path_params["identity"])
        if model_view and (
            not model_view.can_create or not model_view.is_accessible(request)
        ):
            raise HTTPException(status_code=403)

    async def _delete(self, request: Request) -> None:
        model_view = self._find_model_view(request.path_params["identity"])
        if model_view and (
            not model_view.can_create or not model_view.is_accessible(request)
        ):
            raise HTTPException(status_code=403)

    async def _edit(self, request: Request) -> None:
        model_view = self._find_model_view(request.path_params["identity"])
        if model_view and (
            not model_view.can_edit or not model_view.is_accessible(request)
        ):
            raise HTTPException(status_code=403)
