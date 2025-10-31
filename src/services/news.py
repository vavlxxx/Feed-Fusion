from src.services.base import BaseService


class NewsService(BaseService):
    async def get_news_list(
        self,
        limit: int,
        offset: int,
    ):
        return await self.db.news.get_all_filtered_with_pagination(
            limit=limit,
            offset=offset,
        )
