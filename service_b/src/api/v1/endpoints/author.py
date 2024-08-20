from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_filter import FilterDepends

from api.dependencies.database import get_async_db
from crud.author import crud_author
from schemas.author import (
    AuthorCreateDB,
    AuthorUpdateDB,
    AuthorResponse,
    AuthorPaginatedResponse,
)
from api.filters.author import AuthorFilter


router = APIRouter()


@router.get("/list/", response_model=AuthorPaginatedResponse)
async def read_authors(
    db: AsyncSession = Depends(get_async_db),
    skip: int = 0,
    limit: int = 20,
    filters: AuthorFilter = FilterDepends(AuthorFilter),
):
    return await crud_author.get_multi_with_total(
        db=db, filters=filters, skip=skip, limit=limit
    )


@router.get(
    "/{author_id}/",
    response_model=Optional[AuthorResponse],
)
async def read_author(
    author_id: int,
    db: AsyncSession = Depends(get_async_db),
):
    if found_book := await crud_author.get_by_id(db=db, obj_id=author_id):
        return found_book
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Author with id={author_id} not found",
    )


@router.post(
    "/",
    response_model=AuthorResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_author(
    create_data: AuthorCreateDB,
    db: AsyncSession = Depends(get_async_db),
):
    return await crud_author.create(db=db, create_schema=create_data)


@router.patch(
    "/{author_id}/",
    response_model=AuthorResponse,
)
async def update_author(
    author_id: int,
    update_data: AuthorUpdateDB,
    db: AsyncSession = Depends(get_async_db),
):
    if found_book := await crud_author.get_by_id(db=db, obj_id=author_id):
        return await crud_author.update(
            db=db, db_obj=found_book, update_data=update_data
        )
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Author with id={author_id} not found",
    )


@router.delete(
    "/{author_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_author(
    author_id: int,
    db: AsyncSession = Depends(get_async_db),
):
    if found_book := await crud_author.get_by_id(db=db, obj_id=author_id):
        return await crud_author.remove(db=db, obj_id=found_book.id)
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Author with id={author_id} not found",
    )
