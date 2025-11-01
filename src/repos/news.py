from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import DBAPIError
from asyncpg import DataError

from src.schemas.news import AddNewsDTO, NewsDTO
from src.repos.base import BaseRepo
from src.models.news import News
from src.repos.mappers.mappers import NewsMapper
from src.utils.exceptions import ValueOutOfRangeError


class NewsRepo(BaseRepo[News, NewsDTO]):
    model = News
    mapper = NewsMapper

    async def add_news(self, data: Sequence[AddNewsDTO]):
        add_obj_stmt = (
            pg_insert(self.model)
            .values(data.model_dump())
            .on_conflict_do_update(
                constraint="uq_news_content_hash",
                set_={"updated_at": datetime.now(timezone.utc).replace(tzinfo=None)},
            )
            .returning(self.model.id)
        )
        result = await self.session.execute(add_obj_stmt)
        return result.scalars().all()

    async def get_all_filtered_with_pagination(
        self,
        limit: int,
        offset: int,
        **filter_by,
    ) -> tuple[int, list[NewsDTO]]:
        if filter_by.get("channel_id") is None:
            del filter_by["channel_id"]

        total_count_subquery = (
            select(func.count())
            .select_from(self.model)
            .filter_by(**filter_by)
            .scalar_subquery()
        )

        query = (
            select(self.model, total_count_subquery.label("total_count"))
            .filter_by(**filter_by)
            .order_by(self.model.published.desc())
            .limit(limit)
            .offset(offset)
        )

        try:
            result = await self.session.execute(query)
        except DBAPIError as exc:
            if isinstance(exc.orig.__cause__, DataError):  # type: ignore
                raise ValueOutOfRangeError(detail=exc.orig.__cause__.args[0]) from exc  # type: ignore
            raise exc

        rows = result.fetchall()

        if not rows:
            total_count_result = await self.session.execute(
                select(func.count()).select_from(self.model)
            )
            total_count = total_count_result.scalar() or 0
            return total_count, []

        total_count = rows[0].total_count
        news: list[NewsDTO] = [self.mapper.map_to_domain_entity(row[0]) for row in rows]

        return total_count, news
