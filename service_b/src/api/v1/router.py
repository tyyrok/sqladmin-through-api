from fastapi import APIRouter

from .endpoints.book import router as book_router

router = APIRouter(prefix="/v1")

router.include_router(book_router, prefix="/book")
