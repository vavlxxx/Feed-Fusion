from typing import Sequence

from asyncpg import DataError
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import DBAPIError

from src.models import DenormalizedNews
from src.models.news import News
from src.repos.base import BaseRepo
from src.repos.mappers.mappers import NewsMapper, DenormNewsMapper
from src.schemas.news import AddNewsDTO, NewsDTO, DenormalizedNewsDTO
from src.utils.exceptions import ValueOutOfRangeError



class DenormNewsRepo(BaseRepo[DenormalizedNews, DenormalizedNewsDTO]):
    model = DenormalizedNews
    mapper = DenormNewsMapper


class NewsRepo(BaseRepo[News, NewsDTO]):
    model = News
    mapper = NewsMapper

    async def get_recent(
        self,
        channel_id: int,
        gt: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[NewsDTO]:
        query = (
            select(self.model)
            .filter_by(channel_id=channel_id)
            .order_by(self.model.published.desc())
        )

        if gt:
            query = query.filter(self.model.id > gt)
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)

        try:
            result = await self.session.execute(query)
        except DBAPIError as exc:
            if isinstance(exc.orig.__cause__, DataError):  # type: ignore
                raise ValueOutOfRangeError(detail=exc.orig.__cause__.args[0]) from exc  # type: ignore
            raise exc

        return [self.mapper.map_to_domain_entity(obj) for obj in result.scalars().all()]

    async def get_hashes_by_hashes(self, hashes) -> list[str]:
        stmt = select(self.model.content_hash).where(
            self.model.content_hash.in_(hashes)
        )
        result = await self.session.execute(stmt)
        return list(set(row[0] for row in result.all()))

    async def add_bulk_upsert(self, data: Sequence[AddNewsDTO]) -> list[NewsDTO]:
        add_obj_stmt = (
            pg_insert(self.model)
            .values([item.model_dump() for item in data])
            .returning(self.model)
        )
        # excluded = add_obj_stmt.excluded
        add_obj_stmt = add_obj_stmt.on_conflict_do_nothing(  # type: ignore[attr-defined]
            constraint="uq_news_content_hash",
        )

        result = await self.session.execute(add_obj_stmt)
        return [self.mapper.map_to_domain_entity(obj) for obj in result.scalars().all()]

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
