from kombu.exceptions import OperationalError

from src.config import settings
from src.schemas.ml import (
    TrainConfig,
    TrainingAddDTO,
    TrainingDTO,
    TrainingUpdateDTO,
)
from src.services.base import BaseService
from src.tasks.ml import retrain_model
from src.utils.exceptions import (
    BrokerUnavailableError,
    ModelAlreadyTrainingError,
    ObjectNotFoundError,
    TrainingNotFoundError,
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
        await self.db.commit()

        try:
            retrain_model.delay(  # pyright: ignore
                {
                    "config": config.model_dump(),
                    "training_id": training_.id,
                }
            )
        except OperationalError as exc:
            await self.db.trains.edit(
                data=TrainingUpdateDTO(
                    in_progress=False,
                    details="Failed to enqueue training task",
                ),
                id=training_.id,
                ensure_existence=False,
            )
            await self.db.commit()
            raise BrokerUnavailableError from exc

        return training_

    async def get_training(self, id: int) -> TrainingDTO:
        try:
            return await self.db.trains.get_one(id=id)
        except ObjectNotFoundError as exc:
            raise TrainingNotFoundError from exc

    async def get_trainings(self) -> list[TrainingDTO]:
        return await self.db.trains.get_all()
