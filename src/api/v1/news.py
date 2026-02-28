import math

from fastapi import APIRouter, Query, UploadFile
from fastapi.responses import ORJSONResponse
from fastapi_cache.decorator import cache
from starlette import status

from src.api.v1.dependencies.auth import AdminAllowedDep
from src.api.v1.dependencies.db import DBDep
from src.api.v1.dependencies.pagination import PaginationDep
from src.api.v1.responses.news import NEWS_RESPONSES
from src.schemas.news import (
    NewsResponse,
    PagingInfo,
    NewsCategory,
    DatasetUploadDTO,
)
from src.services.news import NewsService
from src.utils.exceptions import (
    ChannelNotFoundError,
    ChannelNotFoundHTTPError,
    ValueOutOfRangeError,
    ValueOutOfRangeHTTPError,
    DenormalizedNewsAlreadyExistsError,
    DenormalizedNewsAlreadyExistsHTTPError,
    AlreadyAssignedCategoryError,
    NewsNotFoundHTTPError,
    NewsNotFoundError,
    AlreadyAssignedCategoryHTTPError,
    CSVDecodeError,
    CSVDecodeHTTPError,
    BrokerUnavailableError,
    BrokerUnavailableHTTPError,
    MissingCSVHeadersHTTPError,
    MissingCSVHeadersError,
    UploadNotFoundError,
    UploadNotFoundHTTPError,
)

router = APIRouter(prefix="/news", tags=["Новости"])


@router.get(
    "/uploads",
    summary="Просмотреть статусы загрузок данных",
)
async def check_uploads_statuses(
    db: DBDep,
    _: AdminAllowedDep,
):
    uploads = await NewsService(db).get_uploads()
    return {
        "total": len(uploads),
        "data": uploads,
    }


@router.get(
    "/uploads/{upload_id}",
    summary="Просмотреть статусы конкрнтной загрузки",
)
async def check_single_upload(
    db: DBDep,
    upload_id: int,
    _: AdminAllowedDep,
):
    try:
        upload: DatasetUploadDTO = await NewsService(db).get_upload(
            upload_id
        )
    except UploadNotFoundError as exc:
        raise UploadNotFoundHTTPError from exc
    except ValueOutOfRangeError as exc:
        raise ValueOutOfRangeHTTPError(detail=exc.detail) from exc
    return upload


@router.post(
    "/uploads",
    summary="Загрузить размеченные данные для обучения",
)
async def upload_denormalized_news(
    db: DBDep,
    file: UploadFile,
    _: AdminAllowedDep,
):
    content = await file.read()
    try:
        upload = await NewsService(db).upload_denormalized_news(
            content
        )
    except CSVDecodeError as exc:
        raise CSVDecodeHTTPError from exc
    except MissingCSVHeadersError as exc:
        raise MissingCSVHeadersHTTPError(detail=exc.detail) from exc
    except BrokerUnavailableError as exc:
        raise BrokerUnavailableHTTPError from exc

    return ORJSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={
            "upload_id": upload.id,
        },
    )


@router.post(
    "/{news_id}",
    summary="Скорректировать категорию для новости и добавить в обучающую выборку",
)
async def add_denormalized_news(
    db: DBDep,
    news_id: int,
    category: NewsCategory,
    _: AdminAllowedDep,
):
    try:
        return await NewsService(db).add_denormalized_news(
            news_id, category
        )
    except DenormalizedNewsAlreadyExistsError as exc:
        raise DenormalizedNewsAlreadyExistsHTTPError from exc
    except AlreadyAssignedCategoryError as exc:
        raise AlreadyAssignedCategoryHTTPError from exc
    except NewsNotFoundError as exc:
        raise NewsNotFoundHTTPError from exc



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
