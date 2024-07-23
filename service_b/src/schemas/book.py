from pydantic import BaseModel


class BookBase(BaseModel):
    title: str

    class Config:
        from_attributes = True


class BookCreateDB(BookBase):
    pass


class BookUpdateDB(BookBase):
    pass


class BookResponse(BookBase):
    id: int


class BookPaginatedResponse(BaseModel):
    objects: list[BookResponse]
    total_count: int

    class Config:
        arbitrary_types_allowed = True
