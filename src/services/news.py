from src.schemas.news import NewsDTO
from src.services.base import BaseService
from src.utils.exceptions import ChannelNotFoundError, ObjectNotFoundError
from src.utils.es_manager import ESManager
from src.config import settings


class NewsService(BaseService):
    async def get_news_list(
        self,
        limit: int,
        offset: int,
        query_string: str | None = None,
        channel_id: int | None = None,
    ) -> tuple[int, list[NewsDTO]]:
        try:
            if channel_id is not None:
                await self.db.channels.get_one(id=channel_id)
        except ObjectNotFoundError as exc:
            raise ChannelNotFoundError from exc

        async with ESManager(index_name=settings.ES_INDEX_NAME) as es:
            total, news = await es.search(
                query_string,
                channel_id,
                limit,
                offset,
            )

        return total, news
