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
    search_after: str | None = Query(None),
    channel_id: int | None = Query(None),
    query: str | None = Query(None),
):
    try:
        total_count, news, search_after, offset = await NewsService(db).get_news_list(
            query_string=query,
            # offset=pagination.offset,
            limit=pagination.limit,
            channel_id=channel_id,
            search_after=search_after,
        )
    except ValueOutOfRangeError as exc:
        raise ValueOutOfRangeHTTPError(detail=exc.detail) from exc
    except ChannelNotFoundError as exc:
        raise ChannelNotFoundHTTPError from exc

    return {
        "page": offset // pagination.limit + 1,
        "per_page": pagination.limit,
        "has_next": len(news) == pagination.limit,
        "total_count": total_count,
        "cursor": search_after,
        "total_pages": math.ceil(total_count / pagination.limit),
        "offset": offset,
        "data": news,
    }
