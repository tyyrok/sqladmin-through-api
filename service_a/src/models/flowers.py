from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class Flower(Base):
    __tablename__ = "flower"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str]
