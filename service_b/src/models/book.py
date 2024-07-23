from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class Book(Base):
    __tablename__ = "book"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str]
