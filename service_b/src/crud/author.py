from typing import Optional, Sequence, Union

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select, update, func
from pydantic import BaseModel

from models import Author
from schemas.author import AuthorCreateDB, AuthorUpdateDB
from api.filters.author import AuthorFilter


class CRUDAuthor:
    async def create(
        self,
        db: AsyncSession,
        *,
        create_schema: AuthorCreateDB,
        commit: bool = True,
    ) -> Author:
        data = create_schema.model_dump(exclude_unset=True)
        stmt = insert(Author).values(**data).returning(Author)
        res = await db.execute(stmt)
        obj = res.scalars().first()
        if commit:
            await db.commit()
            await db.refresh(obj)
        return obj

    async def remove(
        self, db: AsyncSession, *, obj_id: int, commit: bool = True
    ) -> Optional[Author]:
        obj = await db.get(Author, obj_id)
        if not obj:
            return None

        await db.delete(obj)
        if commit:
            await db.commit()
        return obj

    async def get_by_id(
        self, db: AsyncSession, *, obj_id: int
    ) -> Optional[Author]:
        statement = select(Author).where(Author.id == obj_id)
        result = await db.execute(statement)
        return result.scalars().first()

    async def get_multi(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> Sequence[Author]:
        statement = select(Author).offset(skip).limit(limit)
        result = await db.execute(statement)
        return result.scalars().all()

    async def get_multi_with_total(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[AuthorFilter] = None,
    ) -> Sequence[Author]:
        statement = (
            select(Author, func.count().over().label("total_count"))
            .offset(skip)
            .limit(limit)
        )
        if filters:
            statement = filters.sort(statement)
        result = await db.execute(statement)
        rows = result.mappings().all()
        return {
            "total_count": rows[0]["total_count"] if rows else 0,
            "objects": [r["Author"] for r in rows],
        }

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: Author,
        update_data: Union[AuthorUpdateDB, dict],
        commit: bool = True,
    ) -> Author:
        if isinstance(update_data, BaseModel):
            update_data = update_data.model_dump(exclude_unset=True)
        stmt = (
            update(Author)
            .where(Author.id == db_obj.id)
            .values(**update_data)
            .returning(Author)
        )
        res = await db.execute(stmt)
        obj = res.scalars().first()
        if commit:
            await db.commit()
            await db.refresh(obj)
        return obj


crud_author = CRUDAuthor()
