from typing import Any, Iterable

import torch

from src.ml.artifacts import ArtifactStore
from src.ml.network import TextClassifier
from src.ml.schemas import (
    PredictionInput,
    PredictionResult,
    TopPrediction,
)
from src.ml.text import normalize_prediction_input, tokenize


def _encode_texts(
    texts: Iterable[str],
    vocab,
) -> tuple[torch.Tensor, torch.Tensor]:
    input_ids: list[int] = []
    offsets: list[int] = []
    offset = 0
    for text in texts:
        token_ids = vocab.encode(tokenize(text))
        if not token_ids:
            token_ids = [vocab.unk_idx]
        offsets.append(offset)
        input_ids.extend(token_ids)
        offset += len(token_ids)

    return (
        torch.tensor(input_ids, dtype=torch.long),
        torch.tensor(offsets, dtype=torch.long),
    )


class ModelPredictor:
    def __init__(
        self,
        model_dir: str = "artifacts",
        device: str = "auto",
        autoload: bool = True,
    ):
        self.store = ArtifactStore(model_dir=model_dir)
        self.device = device
        self.model: TextClassifier | None = None  # type: ignore
        self.vocab = None
        self.labels: list[str] = []
        self.device_obj = None
        if autoload:
            self.reload()

    def reload(self) -> None:
        loaded_model, vocab, labels, _, device_obj = (
            self.store.load_predictor_bundle(self.device)
        )
        self.model = loaded_model
        self.vocab = vocab
        self.labels = labels
        self.device_obj = device_obj

    def _require_loaded(self) -> None:
        if (
            self.model is None
            or self.vocab is None
            or self.device_obj is None
        ):
            raise RuntimeError(
                "Model is not loaded. Call reload() first."
            )

    def predict_raw(
        self,
        inputs: list[PredictionInput],
    ) -> list[dict[str, Any]]:
        if not inputs:
            raise ValueError("Provide at least one input model.")

        self._require_loaded()
        self.model: TextClassifier

        texts: list[str] = []
        for index, item in enumerate(inputs):
            normalized = normalize_prediction_input(item)
            if not normalized:
                raise ValueError(
                    f"Input at index {index} is empty after normalization."
                )
            texts.append(normalized)

        input_ids, offsets = _encode_texts(
            texts=texts, vocab=self.vocab
        )
        input_ids = input_ids.to(self.device_obj)
        offsets = offsets.to(self.device_obj)

        with torch.inference_mode():
            logits = self.model(input_ids, offsets)
            probs = torch.softmax(logits, dim=-1).cpu().tolist()

        results: list[dict[str, Any]] = []
        for input_, row in zip(inputs, probs):
            best_index = int(
                max(range(len(row)), key=lambda idx: row[idx])
            )
            results.append(
                {
                    "news_id": input_.news_id,
                    "category": self.labels[best_index],
                    "confidence": float(row[best_index]),
                    "probabilities": {
                        self.labels[index]: float(row[index])
                        for index in range(len(self.labels))
                    },
                }
            )
        return results

    def predict(
        self,
        payload: PredictionInput,
        top_k: int = 3,
        min_confidence: float | None = None,
        allowed_labels: set[str] | None = None,
        include_probabilities: bool = False,
    ) -> PredictionResult:
        raw = self.predict_raw([payload])[0]
        return self.filter_prediction(
            raw=raw,
            allowed_labels=allowed_labels,
            top_k=top_k,
            min_confidence=min_confidence,
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
        raw_results = self.predict_raw(payloads)
        return [
            self.filter_prediction(
                raw=raw,
                allowed_labels=allowed_labels,
                top_k=top_k,
                min_confidence=min_confidence,
                include_probabilities=include_probabilities,
            )
            for raw in raw_results
        ]

    @staticmethod
    def filter_prediction(
        raw: dict[str, Any],
        allowed_labels: set[str] | None,
        top_k: int,
        min_confidence: float | None,
        include_probabilities: bool = False,
    ) -> PredictionResult:
        probabilities = dict(raw["probabilities"])
        raw_category = raw.get("category")

        if allowed_labels is not None:
            probabilities = {
                label: value
                for label, value in probabilities.items()
                if label in allowed_labels
            }

        if not probabilities:
            return PredictionResult(
                category=None,
                confidence=0.0,
                top_k=[],
                raw_category=raw_category,
                reason="no_allowed_labels",
                probabilities={} if include_probabilities else None,
            )

        total = sum(probabilities.values())
        if total <= 0:
            return PredictionResult(
                category=None,
                confidence=0.0,
                top_k=[],
                raw_category=raw_category,
                reason="zero_probability",
                probabilities={} if include_probabilities else None,
            )

        normalized = {
            label: value / total
            for label, value in probabilities.items()
        }
        ordered = sorted(
            normalized.items(),
            key=lambda item: item[1],
            reverse=True,
        )
        safe_top_k = max(int(top_k), 1)
        best_label, best_confidence = ordered[0]

        threshold = None
        if min_confidence is not None:
            threshold = min(max(float(min_confidence), 0.0), 1.0)

        if threshold is not None and best_confidence < threshold:
            selected_category = None
            reason = "low_confidence"
        else:
            selected_category = best_label
            reason = None

        return PredictionResult(
            category=selected_category,
            confidence=float(best_confidence),
            top_k=[
                TopPrediction(
                    category=label, confidence=float(confidence)
                )
                for label, confidence in ordered[:safe_top_k]
            ],
            raw_category=raw_category,
            reason=reason,
            probabilities=normalized
            if include_probabilities
            else None,
        )
