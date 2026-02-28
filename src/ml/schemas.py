from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class PredictionInput:
    news_id: int
    title: str
    summary: str


@dataclass(slots=True)
class TrainingSample:
    title: str
    summary: str | None
    category: str


@dataclass(slots=True)
class TrainConfig:
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


@dataclass(slots=True)
class TopPrediction:
    category: str
    confidence: float


@dataclass(slots=True)
class PredictionResult:
    category: Optional[str]
    confidence: float
    top_k: list[TopPrediction]
    raw_category: Optional[str]
    reason: Optional[str]
    probabilities: Optional[dict[str, float]] = None
