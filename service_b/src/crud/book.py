from typing import Optional, Sequence, Union

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select, update, func
from pydantic import BaseModel

from models import Book
from schemas.book import BookCreateDB, BookUpdateDB
from api.filters.book import BookFilter


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

    async def get_multi_with_total(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[BookFilter] = None,
    ) -> Sequence[Book]:
        statement = (
            select(Book, func.count().over().label("total_count"))
            .offset(skip)
            .limit(limit)
        )
        if filters:
            statement = filters.sort(statement)
        result = await db.execute(statement)
        rows = result.mappings().all()
        return {
            "total_count": rows[0]["total_count"] if rows else 0,
            "objects": [r["Book"] for r in rows],
        }

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


crud_book = CRUDBook()
