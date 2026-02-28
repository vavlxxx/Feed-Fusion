from fastapi import APIRouter, UploadFile
from fastapi.responses import ORJSONResponse
from starlette import status

from src.api.v1.dependencies.auth import AdminAllowedDep
from src.api.v1.dependencies.db import DBDep
from src.schemas.samples import DatasetUploadDTO
from src.schemas.enums import NewsCategory
from src.services.news import NewsService
from src.utils.exceptions import (
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

router = APIRouter(prefix="/samples", tags=["Новости"])


@router.get(
    "/",
    summary="Просмотреть статусы импорта обучающих данных",
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
    "/{upload_id}",
    summary="Просмотреть статусы конкретного импорта обучающих данных",
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
    "/",
    summary="Импортировать размеченные данные для обучения из CSV",
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
            "link": f"/api/v1/uploads/{upload.id}"
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
