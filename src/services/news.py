import base64
import json
import csv
import io

from fastapi import HTTPException
from pydantic import ValidationError

from src.schemas.news import NewsCategory, DenormalizedNewsAddDTO, NewsUpdateDTO
from src.config import settings
from src.services.base import BaseService
from src.utils.es_manager import ESManager
from src.utils.exceptions import ChannelNotFoundError, ObjectNotFoundError


class CursorEncoder:
    @staticmethod
    def encode_cursor(cursor: dict | None = None) -> str | None:
        if not cursor:
            return ""
        json_str = json.dumps(cursor)
        return base64.b64encode(json_str.encode()).decode()

    @staticmethod
    def decode_cursor(cursor: str | None = None) -> dict:
        if not cursor:
            return {}

        try:
            json_str = base64.b64decode(cursor).decode()
            decoded_cursor = json.loads(json_str)
        except Exception:
            return {}

        return decoded_cursor


class NewsService(BaseService):
    async def add_denormalized_news(self, news_id: int, category: NewsCategory):
        news = await self.db.news.get_one(id=news_id)
        if news.category == category:
            raise HTTPException()
        await  self.db.news.edit(id=news_id, data=NewsUpdateDTO(category=category))
        denorm_news = await self.db.denorm_news.add(DenormalizedNewsAddDTO(
            title=news.title,
            summary=news.summary,
            category=category,
        ))
        await self.db.commit()
        return denorm_news

    async def upload_denormalized_news(self, content: bytes):
        try:
            text_data = content.decode("utf-8-sig")
            dict_reader = csv.DictReader(io.StringIO(text_data))
        except UnicodeDecodeError as e:
            raise HTTPException(status_code=400, detail="Кодировка должна быть UTF-8")

        required_fields = DenormalizedNewsAddDTO.model_fields.keys()
        actual_fields = set(dict_reader.fieldnames or [])
        missing_fields = required_fields - actual_fields
        if missing_fields:
            raise HTTPException(
                status_code=400,
                detail=f"В CSV отсутствуют обязательные колонки: {', '.join(missing_fields)}"
            )

        validated_data = []
        errors = []

        for i, row in enumerate(dict_reader, start=1):
            try:
                clean_row = {k.strip(): v.strip() for k, v in row.items() if k}
                dto = DenormalizedNewsAddDTO.model_validate(clean_row)
                validated_data.append(dto)
            except ValidationError as e:
                errors.append(f"Строка {i}: {e.json()}")
                continue
        if validated_data:
            await self.db.denorm_news.add_bulk(validated_data)
            await self.db.commit()

        return {
            "status": "success",
            "uploaded": len(validated_data),
            "failed": len(errors),
            "details": errors[:10]
        }

    async def get_news_list(
            self,
            limit: int,
            # offset: int,
            query_string: str | None = None,
            channel_ids: list[int] | None = None,
            search_after: str | None = None,
            recent_first: bool = True,
    ) -> tuple[int, list[dict], str | None, int]:
        try:
            if channel_ids:
                for channel_id in channel_ids:
                    await self.db.channels.get_one(id=channel_id)
        except ObjectNotFoundError as exc:
            raise ChannelNotFoundError from exc

        current_cursor = CursorEncoder().decode_cursor(search_after)
        sort_param = current_cursor.get("sort", None)

        async with ESManager(index_name=settings.ES_INDEX_NAME) as es:
            total, news, last_hit_sort = await es.search(
                query_string=query_string,
                channel_ids=channel_ids,
                limit=limit,
                search_after=sort_param,
                recent_first=recent_first,
                # offset=offset,
            )

        new_cursor = None
        offset = current_cursor.get("offset", 0)

        if len(news) == limit:
            new_cursor = CursorEncoder().encode_cursor(
                cursor={
                    "sort": last_hit_sort,
                    "offset": offset + len(news),
                }
            )

        return total, news, new_cursor, offset
