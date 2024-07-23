from typing import Optional, Sequence, Union

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select, update
from pydantic import BaseModel

from models import Book
from schemas.book import BookCreateDB, BookUpdateDB


class CRUDBook:
    async def create(
        self,
        db: AsyncSession,
        *,
        create_schema: BookCreateDB,
        commit: bool = True,
    ) -> Book:
        data = create_schema.model_dump(exclude_unset=True)
        stmt = insert(Book).values(**data).returning(Book)
        res = await db.execute(stmt)
        obj = res.scalars().first()
        if commit:
            await db.commit()
            await db.refresh(obj)
        return obj

    async def remove(
        self, db: AsyncSession, *, obj_id: int, commit: bool = True
    ) -> Optional[Book]:
        obj = await db.get(Book, obj_id)
        if not obj:
            return None

        await db.delete(obj)
        if commit:
            await db.commit()
        return obj

    async def get_by_id(
        self, db: AsyncSession, *, obj_id: int
    ) -> Optional[Book]:
        statement = select(Book).where(Book.id == obj_id)
        result = await db.execute(statement)
        return result.scalars().first()

    async def get_multi(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> Sequence[Book]:
        statement = select(Book).offset(skip).limit(limit)
        result = await db.execute(statement)
        return result.scalars().all()

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: Book,
        update_data: Union[BookUpdateDB, dict],
        commit: bool = True,
    ) -> Book:
        if isinstance(update_data, BaseModel):
            update_data = update_data.model_dump(exclude_unset=True)
        stmt = (
            update(Book)
            .where(Book.id == db_obj.id)
            .values(**update_data)
            .returning(Book)
        )
        res = await db.execute(stmt)
        obj = res.scalars().first()
        if commit:
            await db.commit()
            await db.refresh(obj)
        return obj


crud_book = CRUDBook(Book)
