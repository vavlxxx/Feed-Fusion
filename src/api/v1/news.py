import math

from fastapi import APIRouter, Query
from fastapi_cache.decorator import cache

from src.api.v1.dependencies.db import DBDep
from src.api.v1.dependencies.pagination import PaginationDep
from src.api.v1.responses.news import NEWS_RESPONSES
from src.schemas.news import (
    NewsResponse,
    PagingInfo,
)
from src.schemas.enums import NewsCategory
from src.services.news import NewsService
from src.utils.exceptions import (
    ChannelNotFoundError,
    ChannelNotFoundHTTPError,
    ValueOutOfRangeError,
    ValueOutOfRangeHTTPError,
    NewsNotFoundHTTPError,
    NewsNotFoundError,
)

router = APIRouter(prefix="/news", tags=["Новости"])


@router.get(
    "/{news_id}",
    summary="Получить конкретную новость",
)
@cache(expire=60)
async def get_news(
    db: DBDep,
    news_id: int,
):
    try:
        return await NewsService(db).get_single_news(id=news_id)
    except NewsNotFoundError as exc:
        raise NewsNotFoundHTTPError from exc
    except ValueOutOfRangeError as exc:
        raise ValueOutOfRangeHTTPError from exc

@router.get(
    "/",
    summary="Получить все новости",
    responses=NEWS_RESPONSES,
)
@cache(expire=60)
async def get_all_news(
    db: DBDep,
    pagination: PaginationDep,
    search_after: str | None = Query(
        None, description="Курсор для пагинации"
    ),
    categories: list[NewsCategory] | None = Query(
        None, description="Категории новостей"
    ),
    without_category: bool = Query(
        False, description="???????? ??????? ??? ?????????"
    ),
    channel_ids: list[int] | None = Query(
        None, description="ID каналов"
    ),
    query: str | None = Query(None, description="Поисковый запрос"),
    recent_first: bool = Query(True, description="Сначала новые"),
) -> NewsResponse:
    """
    ## 🗞️ Получить список всех новостей
    """
    try:
        total_count, news, search_after, offset = await NewsService(
            db
        ).get_news_list(
            query_string=query,
            # offset=pagination.offset,
            categories=categories,
            without_category=without_category,
            limit=pagination.limit,
            channel_ids=channel_ids,
            search_after=search_after,
            recent_first=recent_first,
        )
    except ValueOutOfRangeError as exc:
        raise ValueOutOfRangeHTTPError(detail=exc.detail) from exc
    except ChannelNotFoundError as exc:
        raise ChannelNotFoundHTTPError from exc

    return NewsResponse(
        news=news,  # type: ignore
        meta=PagingInfo(
            page=(offset // pagination.limit + 1),
            per_page=pagination.limit,
            has_next=(len(news) == pagination.limit),
            total_count=total_count,
            recent_first=recent_first,
            cursor=search_after,
            total_pages=math.ceil(total_count / pagination.limit),
            offset=offset,
        ),
    )
