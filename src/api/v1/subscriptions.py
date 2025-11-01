from fastapi import APIRouter

from src.schemas.subscriptions import SubscriptionDTO
from src.api.v1.dependencies.db import DBDep
from src.api.v1.dependencies.auth import SubByAccess
from src.services.subscriptions import SubsService
from src.utils.exceptions import (
    ChannelNotFoundError,
    ChannelNotFoundHTTPError,
    EmptyChannelError,
    EmptyChannelHTTPError,
    ValueOutOfRangeError,
    ValueOutOfRangeHTTPError,
    SubNotFoundError,
    SubNotFoundHTTPError,
    MisingTelegramError,
    MisingTelegramErrorHTTPError,
)

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


@router.get("/")
async def get_subscriptions(
    db: DBDep,
    uid: SubByAccess,
):
    subs = await SubsService(db).get_subscriptions(uid=uid)
    return {
        "message": "Subscriptions found successfully",
        "data": subs,
    }


@router.post("/")
async def create_subscription(
    db: DBDep,
    uid: SubByAccess,
    channel_id: int,
):
    try:
        sub: SubscriptionDTO = await SubsService(db).create_subscription(
            uid=uid, channel_id=channel_id
        )
    except ChannelNotFoundError as exc:
        raise ChannelNotFoundHTTPError from exc
    except EmptyChannelError as exc:
        raise EmptyChannelHTTPError from exc
    except MisingTelegramError as exc:
        raise MisingTelegramErrorHTTPError from exc
    except ValueOutOfRangeError as exc:
        raise ValueOutOfRangeHTTPError(detail=exc.detail) from exc
    return {
        "message": "Subscription created successfully",
        "data": sub,
    }


@router.delete("/")
async def delete_subscription(
    db: DBDep,
    _: SubByAccess,
    sub_id: int,
):
    try:
        await SubsService(db).delete_subscription(sub_id=sub_id)
    except SubNotFoundError as exc:
        raise SubNotFoundHTTPError from exc
    except ValueOutOfRangeError as exc:
        raise ValueOutOfRangeHTTPError(detail=exc.detail) from exc
    return {
        "message": "Subscription deleted successfully",
    }
