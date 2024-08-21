from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from api.admin.custom_baseview import APIBaseView


async def get_url_for_related_object(
    cls: type["APIBaseView"], key: str
) -> Optional[str]:
    """Method looking for the match key in ApiUrls.detail_path

    Args:
        key (str): key like "author_id"

    Returns:
        Optional[str]: Path to make request for object detail
    """
    children_classes = cls.__subclasses__()
    for child_class in children_classes:
        if key in child_class.urls.detail_path:
            return child_class.urls.base_url + child_class.urls.detail_path
    return None


async def insert_params_to_path(url: str, params: dict) -> str:
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
            new_elems.append(str(params.get(elem.strip("{}"))))
        else:
            new_elems.append(elem)
    url = prefix + "://" + "/".join(new_elems)
    if not url.endswith("/"):
        url += "/"
    return url
