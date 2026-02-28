from fastapi import APIRouter

from src.api.v1.dependencies.auth import AdminAllowedDep
from src.schemas.ml import TrainConfig, TrainingDTO
from src.services.training import TrainingService
from src.api.v1.dependencies.db import DBDep
from src.utils.exceptions import (
    BrokerUnavailableError,
    BrokerUnavailableHTTPError,
    ModelAlreadyTrainingError,
    ModelAlreadyTrainingHTTPError,
    ValueOutOfRangeError,
    TrainingNotFoundError,
    TrainingNotFoundHTTPError,
    ValueOutOfRangeHTTPError,
)

router = APIRouter(
    prefix="/trainings", tags=["Тренировка ML модели"]
)


@router.post(
    "/",
    summary="Ручной запуск обучения классификатора новостей",
)
async def make_manual_train(
    db: DBDep,
    config: TrainConfig,
    _: AdminAllowedDep,
) -> dict:
    try:
        training: TrainingDTO = await TrainingService(
            db
        ).train_model(config)
    except BrokerUnavailableError as exc:
        raise BrokerUnavailableHTTPError from exc
    except ModelAlreadyTrainingError as exc:
        raise ModelAlreadyTrainingHTTPError from exc
    return {
        "training_id": training.id,
        "link": f"/api/v1/trainings/{training.id}",
    }


@router.get(
    "/{training_id}",
    summary="Узнать статус обучения модели",
)
async def get_training(
    db: DBDep,
    training_id: int,
    _: AdminAllowedDep,
) -> TrainingDTO:
    try:
        training = await TrainingService(db).get_training(
            id=training_id
        )
    except TrainingNotFoundError as exc:
        raise TrainingNotFoundHTTPError from exc
    except ValueOutOfRangeError as exc:
        raise ValueOutOfRangeHTTPError from exc
    return training


@router.get(
    "/",
    summary="Получить список всех тренеровок модели",
)
async def get_trainings(
    db: DBDep,
    _: AdminAllowedDep,
) -> dict:
    trainings = await TrainingService(db).get_trainings()
    return {
        "total": len(trainings),
        "data": trainings,
    }
