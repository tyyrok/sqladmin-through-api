from typing import Optional, TYPE_CHECKING

from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ENUM

from constants.book import BookGenre
from models.base import Base

if TYPE_CHECKING:
    from models import Author


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
    author_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("author.id", ondelete="CASCADE"), index=True
    )
    author: Mapped["Author"] = relationship("Author", back_populates="books")
