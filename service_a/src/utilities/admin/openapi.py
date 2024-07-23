from typing import Union
import logging

import httpx

from constants.admin import RequestMethod


async def get_schema_for_form_from_api(
    openapi_schema: dict, target_path: str, method: RequestMethod
) -> Union[list[dict], None]:
    """Function to get request body schema fro third-party API

    Args:
        - open_api_url (str): url for openapi.json file
        - target_path (str): path for target endpoint
        - method (RequestMethod): GET, POST etc

    Returns:
        - Union[list[dict], None]: request body schema
        for target endpoint
    """
    return await get_body_schema(openapi_schema, target_path, method)


async def get_open_api_json(openapi_url: str) -> Union[dict, None]:
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(url=openapi_url)
            r.raise_for_status()
        except httpx.HTTPError as ex:
            logging.exception(ex)  # noqa: TRY401
            return None
    return r.json()


async def get_body_schema(
    openapi_schema: dict, target_path: str, method: RequestMethod
) -> Union[list[dict], None]:
    """Different Open API standards have different schemas for requst
    body content. This fuctions is aplicable for 'openapi': '3.1.0'
    Adjust code if you deal with different openapi version.

    Args:
        - openapi_schema (dict): json response with openapi schema

    Returns:
        - Union[list[dict], None]: request body schema
        for target endpoint
    """
    schemas_names = []
    if "paths" in openapi_schema:
        if path_dict := openapi_schema["paths"].get(target_path):  # noqa: SIM102
            if method_dict := path_dict.get(method.lower()):  # noqa: SIM102
                if body_dict := method_dict.get("requestBody"):  # noqa: SIM102
                    if content_dict := body_dict.get("content"):
                        for media_schema in content_dict.values():
                            if "schema" in media_schema:
                                if isinstance(media_schema["schema"], dict):
                                    schemas_names.extend(
                                        [
                                            e.split("/")[-1]
                                            for e in media_schema[
                                                "schema"
                                            ].values()
                                        ]
                                    )
                                else:
                                    schema = media_schema["schema"].split("/")[
                                        -1
                                    ]
                                    schemas_names.append(schema)
    else:
        return None
    return await extract_schemas(
        openapi_schema=openapi_schema, schemas_names=schemas_names
    )


async def extract_schemas(
    openapi_schema: dict, schemas_names: list[str]
) -> list[dict]:
    """Extract schemas from OpenAPI 'components'"""
    schemas_list = []
    if "components" in openapi_schema:
        schemas_dict = openapi_schema["components"].get("schemas", None)
        if schemas_dict:
            for name in schemas_names:
                if schema := schemas_dict.get(name, None):
                    schemas_list.append(schema)  # noqa: PERF401
    else:
        return None
    return schemas_list
