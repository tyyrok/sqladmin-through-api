from pydantic import BaseModel


class AuthorBase(BaseModel):
    class Config:
        from_attributes = True


class AuthorCreateDB(AuthorBase):
    first_name: str
    last_name: str


class AuthorUpdateDB(AuthorBase):
    first_name: str
    last_name: str


class AuthorResponse(AuthorBase):
    id: int
    first_name: str
    last_name: str


class AuthorPaginatedResponse(BaseModel):
    objects: list[AuthorResponse]
    total_count: int

    class Config:
        arbitrary_types_allowed = True
