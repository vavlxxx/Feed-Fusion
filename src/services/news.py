import base64
import json
import csv
import io

from kombu.exceptions import OperationalError

from src.schemas.news import (
    NewsUpdateDTO,
)
from src.schemas.samples import DenormalizedNewsAddDTO, DenormalizedNewsDTO, DatasetUploadAddDTO
from src.schemas.enums import NewsCategory
from src.tasks.ml import upload_training_dataset
from src.config import settings
from src.services.base import BaseService
from src.utils.es_manager import ESManager
from src.utils.exceptions import (
    NewsNotFoundError,
    ChannelNotFoundError,
    ObjectNotFoundError,
    AlreadyAssignedCategoryError,
    ObjectExistsError,
    DenormalizedNewsAlreadyExistsError,
    CSVDecodeError,
    MissingCSVHeadersError,
    UploadNotFoundError,
    BrokerUnavailableError,
)


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
            decoded_cursor = {}

        return decoded_cursor


class NewsService(BaseService):
    async def get_uploads(self):
        return await self.db.uploads.get_all()

    async def get_upload(self, upload_id):
        try:
            return await self.db.uploads.get_one(id=upload_id)
        except ObjectNotFoundError as exc:
            raise UploadNotFoundError from exc

    async def get_single_news(self, id: int):
        try:
            return await self.db.news.get_one(id=id)
        except ObjectNotFoundError as exc:
            raise NewsNotFoundError from exc

    async def add_denormalized_news(
        self,
        news_id: int,
        category: NewsCategory,
    ) -> DenormalizedNewsDTO:
        try:
            news = await self.db.news.get_one(id=news_id)
        except ObjectNotFoundError as exc:
            raise NewsNotFoundError from exc

        if news.category and news.category == category:
            raise AlreadyAssignedCategoryError

        to_update = NewsUpdateDTO(category=category)
        await self.db.news.edit(
            id=news_id,
            ensure_existence=False,
            data=to_update,
        )

        try:
            added_news = await self.db.denorm_news.add(
                DenormalizedNewsAddDTO(
                    title=news.title,
                    summary=news.summary,
                    category=category,
                )
            )
        except ObjectExistsError as exc:
            raise DenormalizedNewsAlreadyExistsError from exc

        await self.db.commit()
        return added_news

    async def upload_denormalized_news(self, content: bytes):
        try:
            text_data = content.decode("utf-8")
            dict_reader = csv.DictReader(io.StringIO(text_data))
        except (UnicodeDecodeError, csv.Error) as exc:
            raise CSVDecodeError from exc

        required_fields = DenormalizedNewsAddDTO.model_fields.keys()
        actual_fields = set(dict_reader.fieldnames or ())
        missing_fields = required_fields - actual_fields

        if missing_fields:
            raise MissingCSVHeadersError(detail=missing_fields)

        dataset_upload = DatasetUploadAddDTO()
        upload_resp = await self.db.uploads.add(dataset_upload)
        await self.db.commit()
        try:
            upload_training_dataset.delay(
                text_data, upload_resp.model_dump()
            )  # pyright: ignore
        except OperationalError as exc:
            raise BrokerUnavailableError from exc
        return upload_resp

    async def get_news_list(
        self,
        limit: int,
        # offset: int,
        categories: list[NewsCategory] | None = None,
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
        offset = int(current_cursor.get("offset", 0) or 0)

        if settings.USE_ELASTICSEARCH:
            sort_param = current_cursor.get("sort", None)
            async with ESManager(
                index_name=settings.ES_INDEX_NAME
            ) as es:
                total, news, last_hit_sort = await es.search(
                    query_string=query_string,
                    categories=categories,
                    channel_ids=channel_ids,
                    limit=limit,
                    search_after=sort_param,
                    recent_first=recent_first,
                )

            new_cursor = None
            if len(news) == limit:
                new_cursor = CursorEncoder().encode_cursor(
                    cursor={
                        "sort": last_hit_sort,
                        "offset": offset + len(news),
                    }
                )
            return total, news, new_cursor, offset

        total, news_rows = await self.db.news.search_with_pagination(
            limit=limit,
            offset=offset,
            query_string=query_string,
            categories=categories,
            channel_ids=channel_ids,
            recent_first=recent_first,
        )
        news = [row.model_dump(mode="json") for row in news_rows]
        next_offset = offset + len(news)
        new_cursor = None
        if next_offset < total:
            new_cursor = CursorEncoder().encode_cursor(
                cursor={"offset": next_offset}
            )
        return total, news, new_cursor, offset
