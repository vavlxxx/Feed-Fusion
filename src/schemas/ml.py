from src.schemas.base import BaseModel

class PredictionInput(BaseModel):
    news_id: int
    title: str
    summary: str


class TrainingSample(BaseModel):
    title: str
    summary: str | None = None
    category: str


class TrainConfig(BaseModel):
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


class TopPrediction(BaseModel):
    category: str
    confidence: float


class PredictionResult(BaseModel):
    category: str | None = None
    confidence: float
    top_k: list[TopPrediction]
    raw_category: str | None = None
    reason: str | None = None
    probabilities: dict[str, float] | None = None
