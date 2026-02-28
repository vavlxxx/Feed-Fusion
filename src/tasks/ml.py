import asyncio
import csv
import io
import logging
import pickle

from src.config import settings
from src.db import sessionmaker_null_pool
from src.ml.schemas import PredictionInput, TrainingSample
from src.ml.service import NewsClassifierService
from src.schemas.news import (
    DatasetUploadDTO,
    DatasetUploadUpdateDTO,
    DenormalizedNewsAddDTO,
    DenormalizedNewsDTO,
    NewsCategory,
    NewsDTO,
    NewsUpdateDTO,
)
from src.tasks.app import celery_app
from src.utils.db_tools import DBManager

logger = logging.getLogger("src.tasks.ml")


@celery_app.task(name="upload_training_dataset")
def upload_training_dataset(
    file_text: str,
    upload: dict,
) -> None:
    validated_upload = DatasetUploadDTO.model_validate(upload)
    asyncio.run(upload_dataset(file_text, validated_upload))


async def upload_dataset(
    file_text: str, upload: DatasetUploadDTO
) -> None:
    logger.info("Started uploading dataset...")

    validated_data = []
    errors = []
    dict_reader = csv.DictReader(io.StringIO(file_text))

    for idx, row in enumerate(dict_reader, start=1):
        try:
            clean_row = {
                k.strip(): v.strip()
                for k, v in row.items()
                if k and v
            }
            dto = DenormalizedNewsAddDTO.model_validate(clean_row)
            logger.debug(
                "Successfully validated #%d row, %s", idx, dto
            )
            validated_data.append(dto)
        except Exception as exc:
            logger.warning(
                "Failed to validate #%d row: %s", idx, exc
            )
            errors.append(str(exc))

    logger.info(
        "Finished validating dataset. Errors: %d, Uploads: %d",
        len(errors),
        len(validated_data),
    )
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
        logger.info("Successfully saved dataset into db...")
        await db.commit()


@celery_app.task(name="check_for_uncategorized_news")
def check_for_uncategorized_news():
    logger.info("Started checking for uncategorized news...")
    asyncio.run(handle_uncategorized_news())


async def handle_uncategorized_news():
    async with DBManager(sessionmaker_null_pool) as db:
        uncategorized_news = await db.news.get_all_filtered(
            category=None
        )
        if len(uncategorized_news) == 0:
            logger.info("No uncategorized news. Skipping...")

        logger.info(
            "Found %d uncategorized news...",
            len(uncategorized_news),
        )
        try:
            service = NewsClassifierService(
                model_dir=settings.model_dir,
                device=settings.DEVICE,
            )
            service_bytes = pickle.dumps(
                service,
            )
            logger.info("Successfully loaded model...")
        except Exception as exc:
            logger.error("Failed to load model: %s", exc)
            return

        news_to_categorize = []
        for idx, news in enumerate(uncategorized_news, start=1):
            obj = news.model_dump()
            news_to_categorize.append(obj)
            logger.debug("Dump #%d: %s", idx, obj)

        categorize_uncategorized_news.delay(  # pyright: ignore
            news_to_categorize,
            service_bytes,
        )


@celery_app.task(name="categorize_uncategorized_news")
def categorize_uncategorized_news(
    news: list[dict], service_dump: bytes
):
    validated_news = [NewsDTO.model_validate(obj) for obj in news]
    service: NewsClassifierService = pickle.loads(service_dump)
    asyncio.run(assign_categories(validated_news, service))


async def assign_categories(
    news: list[NewsDTO],
    service: NewsClassifierService,
) -> None:
    news_ = [
        PredictionInput(
            obj.id,
            obj.title,
            obj.summary,
        )
        for obj in news
    ]
    result = service.predict_many(news_)
    news_to_update = [
        NewsUpdateDTO(category=NewsCategory(prediction.category))
        for prediction in result
        if prediction.category
    ]

    if len(news) != len(news_to_update):
        logger.error(
            "Failed to assign new categories: %d",
            len(news_to_update),
        )

    async with DBManager(sessionmaker_null_pool) as db:
        for to_update, news_obj in zip(news_to_update, news):
            await db.news.edit(to_update, id=news_obj.id)
            logger.debug(
                "Assigned category '%s' to news_id '%d'",
                to_update.category.value,  # pyright: ignore
                news_obj.id,
            )
        await db.commit()


@celery_app.task(name="retrain_model")
def retrain_model():
    asyncio.run(retrain_model_async())


async def retrain_model_async():
    async with DBManager(sessionmaker_null_pool) as db:
        dataset: list[
            DenormalizedNewsDTO
        ] = await db.denorm_news.get_all()
        if len(dataset) == 0:
            logger.info(
                "There are no samples to train model. Skipping..."
            )
            return

        logger.info(
            "Successfully loaded %d samples to train model...",
            len(dataset),
        )
        await db.denorm_news.delete_all()
        logger.info(
            "Successfully deleted %d samples...",
            len(dataset),
        )

        try:
            service = NewsClassifierService(
                model_dir=settings.model_dir,
                device=settings.DEVICE,
            )
            logger.info("Successfully loaded model...")
        except Exception as exc:
            logger.error("Failed to load model: %s", exc)
            return

        dataset_ = [
            TrainingSample(
                title=row.title,
                summary=row.summary,
                category=row.category,
            )
            for row in dataset
        ]

        service.train(
            samples=dataset_, config=settings.TRAIN_CONFIG
        )
        logger.info("Successfully trained model...")
        await db.commit()
