RELATED_OBJECTS_TITLE = ["fullname", "full_name", "name", "title"]


async def get_related_object_title(data: dict) -> str:
    """Method looping through constant RELATED_OBJECTS_TITLE and
    return the first match with response data dict
    """
    for elem in RELATED_OBJECTS_TITLE:
        if elem in data:
            return data[elem]
    return data["id"]
