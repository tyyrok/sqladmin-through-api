from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_filter import FilterDepends

from api.dependencies.database import get_async_db
from crud.book import crud_book
from schemas.book import (
    BookCreateDB,
    BookUpdateDB,
    BookResponse,
    BookPaginatedResponse,
)
from api.filters.book import BookFilter


router = APIRouter()


@router.get("/list/", response_model=BookPaginatedResponse)
async def read_books(
    db: AsyncSession = Depends(get_async_db),
    skip: int = 0,
    limit: int = 20,
    filters: BookFilter = FilterDepends(BookFilter),
):
    return await crud_book.get_multi_with_total(
        db=db, filters=filters, skip=skip, limit=limit
    )


@router.get(
    "/{book_id}/",
    response_model=Optional[BookResponse],
)
async def read_book(
    book_id: int,
    db: AsyncSession = Depends(get_async_db),
):
    if found_book := await crud_book.get_by_id(db=db, obj_id=book_id):
        return found_book
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Book with id={book_id} not found",
    )


@router.post(
    "/",
    response_model=BookResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_book(
    create_data: BookCreateDB,
    db: AsyncSession = Depends(get_async_db),
):
    return await crud_book.create(db=db, create_schema=create_data)


@router.patch(
    "/{book_id}/",
    response_model=BookResponse,
)
async def update_book(
    book_id: int,
    update_data: BookUpdateDB,
    db: AsyncSession = Depends(get_async_db),
):
    if found_book := await crud_book.get_by_id(db=db, obj_id=book_id):
        return await crud_book.update(
            db=db, db_obj=found_book, update_data=update_data
        )
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Book with id={book_id} not found",
    )


@router.delete(
    "/{book_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_question(
    book_id: int,
    db: AsyncSession = Depends(get_async_db),
):
    if found_book := await crud_book.get_by_id(db=db, obj_id=book_id):
        return await crud_book.remove(db=db, obj_id=found_book.id)
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Book with id={book_id} not found",
    )
