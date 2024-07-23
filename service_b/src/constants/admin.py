import enum


class RequestMethod(enum.StrEnum):
    get = "GET"
    post = "POST"
    patch = "PATCH"
    put = "PUT"
    delete = "DELETE"


class AdminFormType(enum.StrEnum):
    create = "CreateForm"
    update = "UpdateForm"
