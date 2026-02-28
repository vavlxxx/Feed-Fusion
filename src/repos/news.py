from typing import Sequence

from asyncpg import DataError
from sqlalchemy import func, insert, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import DBAPIError

from src.models.news import DatasetUploads, DenormalizedNews, News
from src.repos.base import BaseRepo
from src.repos.mappers.mappers import (
    DatasetUploadMapper,
    DenormNewsMapper,
    NewsMapper,
)
from src.schemas.news import (
    AddNewsDTO,
    NewsDTO,
)
from schemas.samples import DenormalizedNewsDTO, DatasetUploadDTO
from src.utils.exceptions import ValueOutOfRangeError


class DenormNewsRepo(
    BaseRepo[DenormalizedNews, DenormalizedNewsDTO]
):
    model = DenormalizedNews
    mapper = DenormNewsMapper

    async def convert_to_denormalized(self, news_ids: list[int]):
        query = (
            select(News.title, News.summary, News.category)
            .select_from(News)
            .filter(
                News.id.in_(news_ids),
                News.category.is_not(None),
            )
        )
        insert_stmt = (
            insert(self.model)
            .from_select(["title", "summary", "category"], query)
            .returning(self.model)
        )
        result = await self.session.execute(insert_stmt)
        objs = result.scalars().all()
        return [
            self.mapper.map_to_domain_entity(obj) for obj in objs
        ]


class DatasetUploadRepo(BaseRepo[DatasetUploads, DatasetUploadDTO]):
    model = DatasetUploads
    mapper = DatasetUploadMapper


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
                raise ValueOutOfRangeError(
                    detail=exc.orig.__cause__.args[0]  # type: ignore
                ) from exc
            raise exc

        return [
            self.mapper.map_to_domain_entity(obj)
            for obj in result.scalars().all()
        ]

    async def get_hashes_by_hashes(self, hashes) -> list[str]:
        stmt = select(self.model.content_hash).where(
            self.model.content_hash.in_(hashes)
        )
        result = await self.session.execute(stmt)
        return list(set(row[0] for row in result.all()))

    async def add_bulk_upsert(
        self, data: Sequence[AddNewsDTO]
    ) -> list[NewsDTO]:
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
        return [
            self.mapper.map_to_domain_entity(obj)
            for obj in result.scalars().all()
        ]

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
            select(
                self.model,
                total_count_subquery.label("total_count"),
            )
            .filter_by(**filter_by)
            .order_by(self.model.published.desc())
            .limit(limit)
            .offset(offset)
        )

        try:
            result = await self.session.execute(query)
        except DBAPIError as exc:
            if isinstance(exc.orig.__cause__, DataError):  # type: ignore
                raise ValueOutOfRangeError(
                    detail=exc.orig.__cause__.args[0]  # type: ignore
                ) from exc
            raise exc

        rows = result.fetchall()

        if not rows:
            total_count_result = await self.session.execute(
                select(func.count()).select_from(self.model)
            )
            total_count = total_count_result.scalar() or 0
            return total_count, []

        total_count = rows[0].total_count
        news: list[NewsDTO] = [
            self.mapper.map_to_domain_entity(row[0]) for row in rows
        ]

        return total_count, news

    async def search_with_pagination(
        self,
        limit: int,
        offset: int,
        query_string: str | None = None,
        categories=None,
        channel_ids=None,
        recent_first: bool = True,
    ) -> tuple[int, list[NewsDTO]]:
        filters = []

        if channel_ids:
            filters.append(self.model.channel_id.in_(channel_ids))
        if categories:
            filters.append(self.model.category.in_(categories))
        if query_string:
            pattern = f"%{query_string.strip()}%"
            filters.append(
                or_(
                    self.model.title.ilike(pattern),
                    self.model.summary.ilike(pattern),
                    self.model.source.ilike(pattern),
                )
            )

        order = (
            self.model.published.desc()
            if recent_first
            else self.model.published.asc()
        )
        count_query = select(func.count()).select_from(self.model)
        if filters:
            count_query = count_query.filter(*filters)

        query = select(self.model).order_by(order)
        if filters:
            query = query.filter(*filters)
        query = query.limit(limit).offset(offset)

        try:
            total_count_result = await self.session.execute(count_query)
            result = await self.session.execute(query)
        except DBAPIError as exc:
            if isinstance(exc.orig.__cause__, DataError):  # type: ignore
                raise ValueOutOfRangeError(
                    detail=exc.orig.__cause__.args[0]  # type: ignore
                ) from exc
            raise exc

        total_count = total_count_result.scalar() or 0
        return total_count, [
            self.mapper.map_to_domain_entity(obj)
            for obj in result.scalars().all()
        ]
