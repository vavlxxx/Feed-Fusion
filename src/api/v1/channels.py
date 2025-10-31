from fastapi import APIRouter

from src.schemas.channels import ChannelAddDTO, ChannelUpdateDTO
from src.services.channels import ChannelService
from src.utils.exceptions import (
    ChannelExistsError,
    ChannelNotFoundError,
    ChannelNotFoundHTTPError,
    ChannelExistsErrorHTTPError,
)
from src.api.v1.dependencies.db import DBDep

router = APIRouter(prefix="/channels", tags=["Channels"])


@router.get("/")
async def get_channels(
    db: DBDep,
) -> None:
    channels = await ChannelService(db).get_channels_list()
    return {
        "message": "Channels found successfully",
        "data": channels,
    }


@router.get("/{channel_id}")
async def get_channel_by_id(
    db: DBDep,
    channel_id: int,
) -> None:
    try:
        channel = await ChannelService(db).get_channel_by_id(channel_id)
    except ChannelNotFoundError as exc:
        raise ChannelNotFoundHTTPError from exc
    return {
        "message": "Channel found successfully",
        "data": channel,
    }


@router.post("/")
async def add_channel(
    db: DBDep,
    data: ChannelAddDTO,
):
    try:
        channel = await ChannelService(db).add_new_channel(data)
    except ChannelExistsError as exc:
        raise ChannelExistsErrorHTTPError from exc
    return {
        "message": "Channel added successfully",
        "data": channel,
    }


@router.put("/{channel_id}")
async def update_channel(
    db: DBDep,
    channel_id: int,
    data: ChannelUpdateDTO,
):
    try:
        await ChannelService(db).update_channel(data, channel_id)
    except ChannelNotFoundError as exc:
        raise ChannelNotFoundHTTPError from exc
    except ChannelExistsError as exc:
        raise ChannelExistsErrorHTTPError from exc
    return {"message": "Channel updated successfully"}


@router.delete("/{channel_id}")
async def delete_channel(
    db: DBDep,
    channel_id: int,
):
    try:
        await ChannelService(db).delete_channel(channel_id)
    except ChannelNotFoundError as exc:
        raise ChannelNotFoundHTTPError from exc
    return {"message": "Channel deleted successfully"}
