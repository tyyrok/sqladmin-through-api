from typing import Optional, TYPE_CHECKING

from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

if TYPE_CHECKING:
    from models import Book


class Author(Base):
    __tablename__ = "author"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    first_name: Mapped[str]
    last_name: Mapped[str]
    books: Mapped[Optional[list["Book"]]] = relationship(
        "Book", back_populates="author", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"{self.first_name} {self.last_name}"
