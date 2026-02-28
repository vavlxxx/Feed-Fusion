from fastapi import APIRouter

from src.api.v1.dependencies.auth import SubByAccess
from src.api.v1.dependencies.db import DBDep
from src.schemas.subscriptions import SubscriptionDTO
from src.services.subscriptions import SubsService
from src.utils.exceptions import (
    ChannelNotFoundError,
    ChannelNotFoundHTTPError,
    EmptyChannelError,
    EmptyChannelHTTPError,
    MisingTelegramError,
    MisingTelegramErrorHTTPError,
    SubExistsError,
    SubExistsErrorHTTPError,
    SubNotFoundError,
    SubNotFoundHTTPError,
    ValueOutOfRangeError,
    ValueOutOfRangeHTTPError,
)

router = APIRouter(prefix="/subscriptions", tags=["Подписки"])


@router.get("/", summary="Получить все подписки")
async def get_subscriptions(
    db: DBDep,
    uid: SubByAccess,
):
    """
    ## 📺 Возвращает подписки на каналы авторизованного пользователя
    """
    subs = await SubsService(db).get_subscriptions(uid=uid)
    return {
        "data": subs,
    }


@router.post("/", summary="Добавить подписку")
async def create_subscription(
    db: DBDep,
    uid: SubByAccess,
    channel_id: int,
):
    """
    ## 📺 Подписаться на новостной канал
    """
    try:
        sub: SubscriptionDTO = await SubsService(
            db
        ).create_subscription(
            uid=int(uid),
            channel_id=channel_id,
        )
    except ChannelNotFoundError as exc:
        raise ChannelNotFoundHTTPError from exc
    except EmptyChannelError as exc:
        raise EmptyChannelHTTPError from exc
    except MisingTelegramError as exc:
        raise MisingTelegramErrorHTTPError from exc
    except SubExistsError as exc:
        raise SubExistsErrorHTTPError from exc
    except ValueOutOfRangeError as exc:
        raise ValueOutOfRangeHTTPError(detail=exc.detail) from exc
    return {
        "data": sub,
    }


@router.delete("/", summary="Удалить подписку")
async def delete_subscription(
    db: DBDep,
    _: SubByAccess,
    sub_id: int,
):
    """
    ## 📺 Отписаться от новостного канала
    """
    try:
        await SubsService(db).delete_subscription(sub_id=sub_id)
    except SubNotFoundError as exc:
        raise SubNotFoundHTTPError from exc
    except ValueOutOfRangeError as exc:
        raise ValueOutOfRangeHTTPError(detail=exc.detail) from exc
    return {
        "message": "Subscription deleted successfully",
    }
