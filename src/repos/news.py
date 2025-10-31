from typing import Sequence

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert as pg_insert

from src.schemas.news import AddNewsDTO
from src.repos.base import BaseRepo
from src.models.news import News
from src.repos.mappers.mappers import NewsMapper


class NewsRepo(BaseRepo):
    model = News
    mapper = NewsMapper

    async def add(self, data: Sequence[AddNewsDTO]):
        add_obj_stmt = (
            pg_insert(self.model)
            .values(data.model_dump())
            .on_conflict_do_update(
                constraint="uq_news_content_hash",
                set_={"updated_at": func.now()},
            )
            .returning(self.model.id)
        )
        result = await self.session.execute(add_obj_stmt)
        return result.scalars().all()
