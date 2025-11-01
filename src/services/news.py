from src.schemas.news import NewsDTO
from src.services.base import BaseService
from src.utils.exceptions import ChannelNotFoundError, ObjectNotFoundError


class NewsService(BaseService):
    async def get_news_list(
        self,
        limit: int,
        offset: int,
        channel_id: int | None = None,
    ) -> tuple[int, list[NewsDTO]]:
        try:
            if channel_id is not None:
                await self.db.channels.get_one(id=channel_id)
        except ObjectNotFoundError as exc:
            raise ChannelNotFoundError from exc

        total, news = await self.db.news.get_all_filtered_with_pagination(
            limit=limit,
            offset=offset,
            channel_id=channel_id,
        )
        return total, news
