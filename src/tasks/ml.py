import asyncio
import csv
import io
import json
import logging
from pathlib import Path

from src.config import settings
from src.db import sessionmaker_null_pool
from src.schemas.ml import (
    PredictionInput,
    TrainingSample,
    TrainingResult,
    TrainingUpdateDTO,
    TrainingAddDTO,
    TrainConfig,
)
from src.ml.service import NewsClassifierService
from src.schemas.news import (
    NewsDTO,
    NewsUpdateDTO,
)
from src.schemas.samples import (
    DenormalizedNewsAddDTO,
    DenormalizedNewsDTO,
    DatasetUploadUpdateDTO,
    DatasetUploadDTO,
)
from src.schemas.enums import NewsCategory
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
        "Finished validating dataset. Errors: %d, Ready to upload: %d",
        len(errors),
        len(validated_data),
    )
    async with DBManager(sessionmaker_null_pool) as db:
        if validated_data:
            try:
                await db.denorm_news.add_bulk(validated_data)
            except Exception as exc:
                logger.error(
                    "Failed to upload dataset to db: %s", exc
                )
                errors.append(str(exc))

        edit_upload = DatasetUploadUpdateDTO(
            is_completed=True,
            errors=len(errors),
            uploads=len(validated_data),
            details=errors,
        )
        await db.uploads.edit(id=upload.id, data=edit_upload)
        logger.info("Successfully saved dataset into db...")
        await db.commit()


def _deserialize_training_payload(
    payload: dict | None,
) -> tuple[TrainConfig | None, int | None]:
    if not payload:
        return None, None

    if "config" in payload or "training_id" in payload:
        config_payload = payload.get("config")
        training_id = payload.get("training_id")
        config = (
            TrainConfig(**config_payload)
            if config_payload
            else None
        )
        if training_id is None:
            return config, None
        return config, int(training_id)

    return TrainConfig(**payload), None


def _load_known_labels() -> set[str]:
    path = Path(settings.model_dir) / "labels.json"
    if not path.exists():
        return set()

    try:
        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
    except Exception as exc:
        logger.warning("Failed to load labels.json: %s", exc)
        return set()

    if not isinstance(payload, list):
        return set()
    return {str(item) for item in payload}


def _to_training_samples(
    rows: list[DenormalizedNewsDTO],
) -> list[TrainingSample]:
    return [
        TrainingSample(
            title=row.title,
            summary=row.summary,
            category=row.category.value,
        )
        for row in rows
    ]


async def _start_training(
    db: DBManager,
    config: TrainConfig,
) -> int:
    train = TrainingAddDTO(
        device=settings.DEVICE,
        model_dir=settings.model_dir,
        config=config,
    )
    training = await db.trains.add(train)
    await db.commit()
    return training.id


async def _finish_training(
    db: DBManager,
    training_id: int,
    *,
    details: str | None = None,
    metrics: dict | None = None,
) -> None:
    await db.trains.edit(
        data=TrainingUpdateDTO(
            in_progress=False,
            details=details,
            metrics=metrics,
        ),
        id=training_id,
        ensure_existence=False,
    )
    await db.commit()


async def _fail_training(
    db: DBManager,
    training_id: int,
    message: str,
    exc: Exception | None = None,
) -> None:
    details = message if exc is None else f"{message}: {exc}"
    logger.error(details)
    await _finish_training(
        db=db,
        training_id=training_id,
        details=details,
    )


async def _select_training_batch(
    db: DBManager,
    new_rows: list[DenormalizedNewsDTO],
) -> tuple[list[DenormalizedNewsDTO], bool, str]:
    model_exists = NewsClassifierService.model_exists()

    if not model_exists:
        return (
            new_rows,
            False,
            "initial_full_training_on_new_samples",
        )

    known_labels = _load_known_labels()
    new_labels = {row.category.value for row in new_rows}
    unseen_labels = new_labels - known_labels

    if unseen_labels:
        all_rows = await db.denorm_news.get_all()
        return (
            all_rows,
            False,
            "full_retrain_due_to_new_labels="
            + ",".join(sorted(unseen_labels)),
        )

    replay_size = int(len(new_rows) * settings.ML_REPLAY_RATIO)
    replay_size = min(
        replay_size,
        settings.ML_MAX_REPLAY_SAMPLES,
    )
    if replay_size <= 0:
        return new_rows, True, "incremental_without_replay"

    replay_rows = await db.denorm_news.get_random_used_samples(
        replay_size
    )
    merged_rows = {row.id: row for row in new_rows}
    for row in replay_rows:
        merged_rows.setdefault(row.id, row)

    return (
        list(merged_rows.values()),
        True,
        f"incremental_with_replay={len(replay_rows)}",
    )


@celery_app.task(name="check_for_uncategorized_news")
def check_for_uncategorized_news():
    if not settings.ENABLE_ML_AUTOCATEGORIZATION:
        logger.info(
            "ML autocategorization disabled. Skipping task."
        )
        return
    logger.info("Started checking for uncategorized news...")
    asyncio.run(handle_uncategorized_news())


async def handle_uncategorized_news():
    if not NewsClassifierService.model_exists():
        logger.info(
            "Model artifacts are missing. Skipping ML categorization."
        )
        return

    async with DBManager(sessionmaker_null_pool) as db:
        uncategorized_news = await db.news.get_all_filtered(
            category=None
        )
        if len(uncategorized_news) == 0:
            logger.info("No uncategorized news. Skipping...")
            return

        logger.info(
            "Found %d uncategorized news...",
            len(uncategorized_news),
        )

        news_to_categorize = []
        for idx, news in enumerate(uncategorized_news, start=1):
            obj = news.model_dump()
            news_to_categorize.append(obj)
            logger.debug("Dump #%d: %s", idx, obj)

        categorize_uncategorized_news.delay(  # pyright: ignore
            news_to_categorize,
        )


@celery_app.task(name="categorize_uncategorized_news")
def categorize_uncategorized_news(news: list[dict]):
    validated_news = [NewsDTO.model_validate(obj) for obj in news]
    try:
        service = NewsClassifierService(
            model_dir=settings.model_dir,
            device=settings.DEVICE,
        )
        logger.info("Successfully loaded model...")
    except Exception as exc:
        logger.error("Failed to load model: %s", exc)
        return
    asyncio.run(assign_categories(validated_news, service))


async def assign_categories(
    news: list[NewsDTO],
    service: NewsClassifierService,
) -> None:
    payloads = [
        PredictionInput(
            news_id=obj.id,
            title=obj.title,
            summary=obj.summary,
        )
        for obj in news
    ]
    result = service.predict_many(payloads)
    predictions_by_id = {
        payload.news_id: prediction
        for payload, prediction in zip(payloads, result)
    }

    async with DBManager(sessionmaker_null_pool) as db:
        updated = 0
        for news_obj in news:
            prediction = predictions_by_id.get(news_obj.id)
            if not prediction or not prediction.category:
                continue

            try:
                category = NewsCategory(prediction.category)
            except ValueError:
                logger.warning(
                    "Unknown category '%s' for news_id '%d'",
                    prediction.category,
                    news_obj.id,
                )
                continue

            to_update = NewsUpdateDTO(category=category)
            await db.news.edit(to_update, id=news_obj.id)
            logger.debug(
                "Assigned category '%s' to news_id '%d'",
                to_update.category.value,  # pyright: ignore
                news_obj.id,
            )
            updated += 1
        await db.commit()
        logger.info(
            "Assigned categories to %d of %d news items",
            updated,
            len(news),
        )


@celery_app.task(name="retrain_model")
def retrain_model(payload: dict | None = None):
    manual_config, training_id = _deserialize_training_payload(
        payload
    )
    asyncio.run(
        retrain_model_async(
            manual_config=manual_config,
            training_id=training_id,
        )
    )


async def retrain_model_async(
    manual_config: TrainConfig | None = None,
    training_id: int | None = None,
):
    config = manual_config or settings.TRAIN_CONFIG

    async with DBManager(sessionmaker_null_pool) as db:
        active_training = await db.trains.get_one_or_none(
            model_dir=settings.model_dir,
            in_progress=True,
        )

        if training_id is None and active_training:
            logger.warning("Model is already training! Skipping...")
            return

        if training_id is not None and active_training:
            if active_training.id != training_id:
                logger.warning(
                    "Another training is active (id=%s). "
                    "Skipping requested id=%s.",
                    active_training.id,
                    training_id,
                )
                return

        if training_id is None:
            training_id = await _start_training(
                db=db,
                config=config,
            )
        elif active_training is None:
            training_id = await _start_training(
                db=db,
                config=config,
            )

        new_samples: list[
            DenormalizedNewsDTO
        ] = await db.denorm_news.get_all_filtered(
            used_in_training=False
        )

        if (
            len(new_samples)
            < settings.ML_MIN_NEW_SAMPLES_FOR_TRAIN
        ):
            await _finish_training(
                db=db,
                training_id=training_id,
                details=(
                    "Not enough new samples to train the model: "
                    f"{len(new_samples)} < "
                    f"{settings.ML_MIN_NEW_SAMPLES_FOR_TRAIN}"
                ),
            )
            return

        logger.info(
            "Loaded %d new samples for model training.",
            len(new_samples),
        )

        training_rows, resume, train_mode = (
            await _select_training_batch(
                db=db,
                new_rows=new_samples,
            )
        )
        logger.info(
            "Training mode: %s. Batch size: %d",
            train_mode,
            len(training_rows),
        )

        model_exists = NewsClassifierService.model_exists()

        try:
            service = NewsClassifierService(
                model_dir=settings.model_dir,
                device=settings.DEVICE,
                autoload_model=model_exists,
            )
            logger.info("Successfully loaded model service...")
        except Exception as exc:
            await _fail_training(
                db=db,
                training_id=training_id,
                message="Failed to load model service",
                exc=exc,
            )
            return

        try:
            result: TrainingResult = service.train(
                samples=_to_training_samples(training_rows),
                config=config,
                resume=resume,
            )
        except Exception as exc:
            await _fail_training(
                db=db,
                training_id=training_id,
                message="Model training failed",
                exc=exc,
            )
            return

        try:
            updated_rows = await db.denorm_news.mark_used_in_training(
                ids=[row.id for row in new_samples]
            )
        except Exception as exc:
            await _fail_training(
                db=db,
                training_id=training_id,
                message=(
                    "Training succeeded, but failed to mark "
                    "samples as used"
                ),
                exc=exc,
            )
            return

        await _finish_training(
            db=db,
            training_id=training_id,
            metrics=result.metrics,
            details=(
                "Training completed successfully "
                f"({train_mode}). Marked used rows: {updated_rows}"
            ),
        )
        logger.info(
            "Successfully trained model. Mode: %s, "
            "new samples: %d, trained batch: %d",
            train_mode,
            len(new_samples),
            len(training_rows),
        )
