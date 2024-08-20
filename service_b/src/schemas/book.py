from typing import Optional

from pydantic import BaseModel

from constants.book import BookGenre


class BookBase(BaseModel):
    title: str

    class Config:
        from_attributes = True


class BookCreateDB(BookBase):
    genre: BookGenre
    extra_genre: Optional[BookGenre] = None
    author_id: int


class BookUpdateDB(BookBase):
    pass


class BookResponse(BookBase):
    id: int
    author_id: int
    genre: BookGenre
    extra_genre: Optional[BookGenre] = None


class BookPaginatedResponse(BaseModel):
    objects: list[BookResponse]
    total_count: int

    class Config:
        arbitrary_types_allowed = True
