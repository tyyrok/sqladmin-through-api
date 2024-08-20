from fastapi import APIRouter

from .endpoints.author import router as author_router
from .endpoints.book import router as book_router

router = APIRouter(prefix="/v1")

router.include_router(author_router, prefix="/author", tags=["Author"])
router.include_router(book_router, prefix="/book", tags=["Book"])
