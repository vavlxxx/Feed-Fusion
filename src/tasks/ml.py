import asyncio
import csv
import io
import logging

from src.schemas.news import DatasetUploadDTO, DatasetUploadUpdateDTO
from src.db import sessionmaker_null_pool
from src.schemas.news import DenormalizedNewsAddDTO
from src.tasks.app import celery_app
from src.utils.db_tools import DBManager

logger = logging.getLogger("src.tasks.ml")


@celery_app.task(name="upload_training_dataset")
def upload_training_dataset(
    file_text: str, upload: dict,
) -> None:
    asyncio.run(upload_dataset(file_text, upload))


async def upload_dataset(file_text: str, upload: dict) -> None:
    validated_data = []
    errors = []

    upload = DatasetUploadDTO.model_validate(upload)
    dict_reader = csv.DictReader(io.StringIO(file_text))

    for i, row in enumerate(dict_reader, start=1):
        try:
            clean_row = {k.strip(): v.strip() for k, v in row.items() if k and v}
            dto = DenormalizedNewsAddDTO.model_validate(clean_row)
            validated_data.append(dto)
        except Exception as exc:
            errors.append(str(exc))

    async with DBManager(sessionmaker_null_pool) as db:
        if validated_data:
            await db.denorm_news.add_bulk(validated_data)

        edit_upload = DatasetUploadUpdateDTO(
            is_completed=True,
            errors=len(errors),
            uploads=len(validated_data),
            details=errors,
        )
        await db.uploads.edit(id=upload.id, data=edit_upload)
        await db.commit()
