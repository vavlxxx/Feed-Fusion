from datetime import datetime

from src.schemas.base import BaseDTO


class PredictionInput(BaseDTO):
    news_id: int
    title: str
    summary: str


class TrainingSample(BaseDTO):
    title: str
    summary: str | None = None
    category: str


class TrainConfig(BaseDTO):
    seed: int = 42
    epochs: int = 10
    batch_size: int = 64
    lr: float = 1e-3
    weight_decay: float = 0.0
    val_split: float = 0.1
    embed_dim: int = 128
    dropout: float = 0.2
    min_freq: int = 2
    max_vocab: int = 50000
    balance: bool = False


class TopPrediction(BaseDTO):
    category: str
    confidence: float


class PredictionResult(BaseDTO):
    category: str | None = None
    confidence: float
    top_k: list[TopPrediction]
    raw_category: str | None = None
    reason: str | None = None
    probabilities: dict[str, float] | None = None


class TrainingAddDTO(BaseDTO):
    config: TrainConfig
    model_dir: str
    device: str


class TrainingDTO(TrainingAddDTO):
    in_progress: bool
    id: int
    details: str | None = None
    created_at: datetime
    updated_at: datetime


class TrainingUpdateDTO(BaseDTO):
    in_progress: bool | None = None
    metrics: dict | None = None
    details: str | None = None


class TrainingResult(BaseDTO):
    model_dir: str
    labels: list[str]
    metrics: dict
    config: TrainConfig
    device: str
