from src.config import settings
from src.schemas.ml import TrainConfig, TrainingAddDTO, TrainingDTO
from src.services.base import BaseService
from src.tasks.ml import retrain_model
from src.utils.exceptions import (
    ModelAlreadyTrainingError,
    TrainingNotFoundError,
    ObjectNotFoundError,
)


class TrainingService(BaseService):
    async def train_model(self, config: TrainConfig) -> TrainingDTO:
        training = await self.db.trains.get_one_or_none(
            model_dir=settings.model_dir,
            in_progress=True,
        )
        if training:
            raise ModelAlreadyTrainingError

        train = TrainingAddDTO(
            device=settings.DEVICE,
            model_dir=settings.model_dir,
            config=config,
        )
        training_ = await self.db.trains.add(train)
        retrain_model.delay(config.model_dump())  # pyright: ignore
        await self.db.commit()
        return training_

    async def get_training(self, id: int) -> TrainingDTO:
        try:
            return await self.db.trains.get_one(id=id)
        except ObjectNotFoundError as exc:
            raise TrainingNotFoundError from exc

    async def get_trainings(self) -> list[TrainingDTO]:
        return await self.db.trains.get_all()
