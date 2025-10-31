import math
from fastapi import APIRouter
from fastapi_cache.decorator import cache

from src.api.v1.dependencies.pagination import PaginationDep
from src.api.v1.dependencies.db import DBDep
from src.services.news import NewsService
from src.utils.exceptions import ValueOutOfRangeError, ValueOutOfRangeHTTPError

router = APIRouter(prefix="/news", tags=["News"])


@cache(expire=300)
@router.get("/")
async def get_all_news(
    db: DBDep,
    pagination: PaginationDep,
):
    try:
        total_count, news = await NewsService(db).get_news_list(
            offset=pagination.offset,
            limit=pagination.limit,
        )
    except ValueOutOfRangeError as exc:
        raise ValueOutOfRangeHTTPError(detail=exc.detail) from exc

    return {
        "page": pagination.page,
        "per_page": pagination.limit,
        "total_count": total_count,
        "total_pages": math.ceil(total_count / pagination.limit),
        "offset": pagination.offset,
        "data": news,
    }
