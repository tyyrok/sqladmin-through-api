from typing import Optional

from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import ENUM

from constants.book import BookGenre
from models.base import Base


class Book(Base):
    __tablename__ = "book"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str]
    genre: Mapped[BookGenre] = mapped_column(
        ENUM(BookGenre, create_type=False)
    )
    extra_genre: Mapped[Optional[BookGenre]] = mapped_column(
        ENUM(BookGenre, create_type=False)
    )
