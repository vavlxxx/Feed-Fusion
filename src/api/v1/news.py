import math
from fastapi import APIRouter, Query
from fastapi_cache.decorator import cache

from src.api.v1.dependencies.pagination import PaginationDep
from src.api.v1.dependencies.db import DBDep
from src.services.news import NewsService
from src.utils.exceptions import (
    ChannelNotFoundError,
    ChannelNotFoundHTTPError,
    ValueOutOfRangeError,
    ValueOutOfRangeHTTPError,
)

router = APIRouter(prefix="/news", tags=["News"])


@router.get("/")
@cache(expire=60)
async def get_all_news(
    db: DBDep,
    pagination: PaginationDep,
    channel_id: int | None = Query(None),
    query: str | None = Query(None),
):
    try:
        total_count, news = await NewsService(db).get_news_list(
            query_string=query,
            offset=pagination.offset,
            limit=pagination.limit,
            channel_id=channel_id,
        )
    except ValueOutOfRangeError as exc:
        raise ValueOutOfRangeHTTPError(detail=exc.detail) from exc
    except ChannelNotFoundError as exc:
        raise ChannelNotFoundHTTPError from exc

    return {
        "page": pagination.page,
        "per_page": pagination.limit,
        "total_count": total_count,
        "total_pages": math.ceil(total_count / pagination.limit),
        "offset": pagination.offset,
        "data": news,
    }
