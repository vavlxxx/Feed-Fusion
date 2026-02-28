import re

from src.ml.schemas import PredictionInput, TrainingSample

TOKEN_RE = re.compile(r"\w+", flags=re.UNICODE)


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall((text or "").lower())


def normalize_title_summary(title: str, summary: str | None) -> str:
    normalized_title = (title or "").strip()
    normalized_summary = (summary or "").strip()
    if normalized_title and normalized_summary:
        return f"{normalized_title} {normalized_summary}"
    return normalized_title or normalized_summary


def normalize_prediction_input(payload: PredictionInput) -> str:
    return normalize_title_summary(payload.title, payload.summary)


def normalize_training_sample(
    sample: TrainingSample,
) -> tuple[str, str]:
    text = normalize_title_summary(sample.title, sample.summary)
    category = (sample.category or "").strip()
    return text, category
