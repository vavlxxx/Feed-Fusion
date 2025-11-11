from src.schemas.news import NewsDTO
from src.services.base import BaseService
from src.services.channels import ChannelService
from src.schemas.subscriptions import SubscriptionAddDTO
from src.utils.exceptions import (
    ObjectExistsError,
    ObjectNotFoundError,
    SubNotFoundError,
    EmptyChannelError,
    MisingTelegramError,
    SubExistsError,
)


class SubsService(BaseService):

    async def get_subscriptions(self, uid: str) -> list[str]:
        return await self.db.subs.get_all_filtered(user_id=uid)

    async def create_subscription(self, uid: str, channel_id: int) -> str:
        user = await self.db.auth.get_one(id=uid)
        if user.telegram_id is None:
            raise MisingTelegramError

        await ChannelService(self.db).get_channel_by_id(channel_id)

        last_news: list[NewsDTO] = await self.db.news.get_recent(
            limit=1,
            offset=0,
            channel_id=channel_id,
        )

        if not last_news:
            raise EmptyChannelError

        data = SubscriptionAddDTO(
            channel_id=channel_id,
            last_news_id=last_news[0].id,
            user_id=uid,
        )
        try:
            sub = await self.db.subs.add(data)
        except ObjectExistsError as exc:
            raise SubExistsError from exc

        await self.db.commit()
        return sub

    async def delete_subscription(self, sub_id: int) -> None:
        try:
            await self.db.subs.delete(id=sub_id)
            await self.db.commit()
        except ObjectNotFoundError as exc:
            raise SubNotFoundError from exc
