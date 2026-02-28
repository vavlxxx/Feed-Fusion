from typing import Any

from src.ml.prediction import ModelPredictor
from src.ml.schemas import (
    PredictionInput,
    PredictionResult,
    TrainConfig,
    TrainingSample,
)
from src.ml.training import ModelTrainer


class NewsClassifierService:
    def __init__(
        self,
        model_dir: str = "artifacts",
        device: str = "auto",
        autoload_model: bool = True,
    ):
        self.trainer = ModelTrainer(
            model_dir=model_dir, device=device
        )
        self.predictor = ModelPredictor(
            model_dir=model_dir,
            device=device,
            autoload=autoload_model,
        )

    def train(
        self,
        samples: list[TrainingSample],
        config: TrainConfig | None = None,
        resume: bool = False,
        reload_model: bool = True,
        verbose: bool = True,
    ) -> dict[str, Any]:
        result = self.trainer.train(
            samples=samples,
            config=config,
            resume=resume,
            verbose=verbose,
        )
        if reload_model:
            self.predictor.reload()
        return result

    def predict(
        self,
        payload: PredictionInput,
        top_k: int = 3,
        min_confidence: float | None = None,
        allowed_labels: set[str] | None = None,
        include_probabilities: bool = False,
    ) -> PredictionResult:
        return self.predictor.predict(
            payload=payload,
            top_k=top_k,
            min_confidence=min_confidence,
            allowed_labels=allowed_labels,
            include_probabilities=include_probabilities,
        )

    def predict_many(
        self,
        payloads: list[PredictionInput],
        top_k: int = 3,
        min_confidence: float | None = None,
        allowed_labels: set[str] | None = None,
        include_probabilities: bool = False,
    ) -> list[PredictionResult]:
        return self.predictor.predict_many(
            payloads=payloads,
            top_k=top_k,
            min_confidence=min_confidence,
            allowed_labels=allowed_labels,
            include_probabilities=include_probabilities,
        )
