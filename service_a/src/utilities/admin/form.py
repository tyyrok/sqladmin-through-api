from typing import Type, Union

import wtforms
from wtforms import fields as wtform_fields

ANY_OF = "anyOf"
TYPE = "type"
REF = "$ref"
FIELDS_STYLE_CLASS = "form-control"


async def create_form(
    form_name: str, form_schema: dict, openapi_schema: dict
) -> Type[wtforms.Form]:
    field_dict = {}
    schema = form_schema[0]  # TODO("Pavel Zubko"): adjust for multiple form
    for field_key, field_value in schema.get("properties").items():
        field_type = await get_field_type(field_value)
        field_validators, choices = await get_field_validators(
            field_description=field_value, openapi_schema=openapi_schema
        )
        if field_type is wtforms.SelectField and choices:
            field_dict[field_key] = field_type(
                field_key.title(),
                validators=field_validators,
                choices=[(x, x) for x in choices],
                render_kw={"class": FIELDS_STYLE_CLASS},
            )
        else:
            field_dict[field_key] = field_type(
                field_key.title(),
                validators=field_validators,
                render_kw={"class": FIELDS_STYLE_CLASS},
            )

    return type(form_name, (wtforms.Form,), field_dict)


async def get_field_type(field_description: dict) -> Type[wtforms.Field]:
    """This is simple field parser, it doesn't work with allOf
    or oneOf of OPENAPI schema

    Args:
        field_description (dict): description of field in OpenAPI 3.1

    Returns:
        Type[Field]: wtforms Field type
    """
    if TYPE in field_description and "format" not in field_description:
        return await get_field_type_by_param_type(field_description[TYPE])
    if TYPE in field_description and "format" in field_description:
        return await get_field_type_by_param_type(field_description["format"])
    if REF in field_description:
        return await get_field_type_by_param_type("enum")
    if ANY_OF in field_description:
        for types in field_description[ANY_OF]:
            for type_key, type_value in types.items():
                if type_key == TYPE and type_value != "null":
                    return await get_field_type_by_param_type(type_value)
                if type_key == REF:
                    return await get_field_type_by_param_type("enum")


async def get_field_type_by_param_type(param_type: str) -> Type[wtforms.Field]:
    types_dict = {
        "string": wtform_fields.StringField,
        "date-time": wtform_fields.DateTimeField,
        "date": wtform_fields.DateField,
        "password": wtform_fields.PasswordField,
        "email": wtform_fields.EmailField,
        "integer": wtform_fields.IntegerField,
        "enum": wtform_fields.SelectField,
        "float": wtform_fields.FloatField,
        "boolean": wtform_fields.BooleanField,
    }
    return types_dict.get(param_type)


async def get_field_validators(
    field_description: dict, openapi_schema: dict
) -> Union[
    list[
        Union[
            wtforms.validators.DataRequired,
            wtforms.validators.Optional,
            wtforms.validators.AnyOf,
        ]
    ],
    list,
]:
    """This is simple realisation that parse openapi data only for optional
    , required and AnyOf validators

    Args:
        - field_description (dict):  description of field in OpenAPI 3.1
        - openapi_schema (dict): openapi.json dict

    Returns:
        - list[ Union[ wtforms.validators.DataRequired,
        wtforms.validators.Optional ] ]: _description_
    """
    validators = []
    field_choices = None
    is_optional = None
    if ANY_OF in field_description:
        for types in field_description[ANY_OF]:
            for type_key, type_value in types.items():
                if type_key == TYPE and type_value == "null":
                    validators.append(wtforms.validators.Optional())
                    is_optional = True
                elif type_key == REF:
                    component_name = type_value.split("/")[-1]
                    choices = await get_component_choices(
                        component_name, openapi_schema
                    )
                    if choices:
                        choices = [None, *choices]
                        validators.append(wtforms.validators.Optional())
                        field_choices = choices
    elif REF in field_description:
        component_name = field_description[REF].split("/")[-1]
        choices = await get_component_choices(component_name, openapi_schema)
        if choices:
            validators.append(wtforms.validators.AnyOf(values=choices))
            field_choices = choices
    if not is_optional:
        validators.append(wtforms.validators.DataRequired())

    return validators, field_choices


async def get_component_choices(
    component_name: str, openapi_schema: dict
) -> Union[list[str], None]:
    components = openapi_schema.get("components")
    if components:
        schemas = components.get("schemas")
        if schemas:
            component = schemas.get(component_name)
            if component:
                enum = component.get("enum")
                if enum:
                    return enum
    return None
