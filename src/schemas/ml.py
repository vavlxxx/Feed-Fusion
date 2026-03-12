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


# конфиг для обучения модели
class TrainConfig(BaseDTO):
    seed: int = 42  # Сид для фиксации случайности (воспроизводимость результатов)
    epochs: int = 10  # Общее количество проходов по всему датасету
    batch_size: int = (
        64  # Количество примеров, обрабатываемых за одну итерацию
    )
    lr: float = 1e-3  # Скорость обучения (шаг оптимизатора)
    weight_decay: float = 0.0  # Коэффициент L2-регуляризации для борьбы с переобучением
    val_split: float = (
        0.1  # Доля данных, выделяемая для валидации (от 0.0 до 1.0)
    )
    embed_dim: int = (
        128  # Размерность вектора признаков (эмбеддинга)
    )
    dropout: float = (
        0.2  # Вероятность «выключения» нейронов для регуляризации
    )
    min_freq: int = (
        2  # Минимальная частота слова для включения в словарь
    )
    max_vocab: int = 50000  # Максимальное количество слов в словаре
    balance: bool = False  # Флаг для балансировки классов


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
