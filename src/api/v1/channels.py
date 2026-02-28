from fastapi import APIRouter
from fastapi_cache.decorator import cache

from src.api.v1.dependencies.auth import AdminAllowedDep
from src.api.v1.dependencies.db import DBDep
from src.schemas.channels import (
    ChannelAddDTO,
    ChannelDTO,
    ChannelUpdateDTO,
)
from src.services.channels import ChannelService
from src.utils.exceptions import (
    ChannelExistsError,
    ChannelExistsErrorHTTPError,
    ChannelNotFoundError,
    ChannelNotFoundHTTPError,
    ValueOutOfRangeError,
    ValueOutOfRangeHTTPError,
)

router = APIRouter(prefix="/channels", tags=["Работа с каналами"])


@router.get(
    "/",
    summary="Получить новостные каналы",
)
@cache(expire=60)
async def get_channels(
    db: DBDep,
) -> dict[str, str | int | list[ChannelDTO]]:
    """
    ## 🔊 Возвращает список всех новостных каналов
    """
    channels = await ChannelService(db).get_channels_list()
    return {
        "total": len(channels),
        "data": channels,
    }


@router.get(
    "/{channel_id}",
    summary="Получить новостной канал",
)
async def get_channel_by_id(
    db: DBDep,
    channel_id: int,
) -> ChannelDTO:
    """
    ## 🔊 Возвращает один новостной канал по его id
    """
    try:
        channel: ChannelDTO = await ChannelService(
            db
        ).get_channel_by_id(channel_id)
    except ChannelNotFoundError as exc:
        raise ChannelNotFoundHTTPError from exc
    except ValueOutOfRangeError as exc:
        raise ValueOutOfRangeHTTPError(detail=exc.detail) from exc
    return channel


@router.post(
    "/",
    summary="Добавить новый канал",
)
async def add_channel(
    db: DBDep,
    data: ChannelAddDTO,
    _: AdminAllowedDep,
) -> ChannelDTO:
    """
    ## 🔊 Добавить новый канал (только для администраторов)
    """
    try:
        channel: ChannelDTO = await ChannelService(
            db
        ).add_new_channel(data)
    except ChannelExistsError as exc:
        raise ChannelExistsErrorHTTPError from exc
    return channel


@router.put(
    "/{channel_id}",
    summary="Обновить канал",
)
async def update_channel(
    db: DBDep,
    channel_id: int,
    data: ChannelUpdateDTO,
    _: AdminAllowedDep,
) -> ChannelDTO:
    """
    ## 🔊 Обновить канал (только для администраторов)
    """
    try:
        channel: ChannelDTO = await ChannelService(
            db
        ).update_channel(data, channel_id)
    except ChannelNotFoundError as exc:
        raise ChannelNotFoundHTTPError from exc
    except ChannelExistsError as exc:
        raise ChannelExistsErrorHTTPError from exc
    except ValueOutOfRangeError as exc:
        raise ValueOutOfRangeHTTPError(detail=exc.detail) from exc
    return channel


@router.delete(
    "/{channel_id}",
    summary="Удалить канал",
)
async def delete_channel(
    db: DBDep,
    channel_id: int,
    _: AdminAllowedDep,
):
    """
    ## 🔊 Удалить канал (только для администраторов)
    """
    try:
        await ChannelService(db).delete_channel(channel_id)
    except ChannelNotFoundError as exc:
        raise ChannelNotFoundHTTPError from exc
    except ValueOutOfRangeError as exc:
        raise ValueOutOfRangeHTTPError(detail=exc.detail) from exc
    return {
        "message": "Channel deleted successfully",
    }
