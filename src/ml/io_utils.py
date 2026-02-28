import csv
import json
import logging
import os
import random
from typing import Any

import torch
from pydantic import ValidationError

from src.schemas.news import DenormalizedNewsAddDTO, NewsCategory
from src.utils.exceptions import (
    MissingCSVHeadersError,
    MissingDatasetClassesError,
)

logger = logging.getLogger(__name__)


def seed_everything(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def save_json(payload: Any, path: str) -> None:
    with open(path, "w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def resolve_device(device: str) -> torch.device:
    resolved = device
    if resolved == "auto":
        resolved = "cuda" if torch.cuda.is_available() else "cpu"
    return torch.device(resolved)


def load_samples_from_csv(
    path: str,
) -> list[DenormalizedNewsAddDTO]:
    samples: list[DenormalizedNewsAddDTO] = []

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        required_fields = DenormalizedNewsAddDTO.model_fields.keys()
        actual_fields = set(reader.fieldnames or ())
        missing_fields = required_fields - actual_fields

        if missing_fields:
            raise MissingCSVHeadersError(detail=missing_fields)

        count = 0
        for row in reader:
            count += 1
            title = (row.get("title") or "").strip()
            summary = (row.get("summary") or "").strip()
            category = (row.get("category") or "").strip()
            try:
                obj = DenormalizedNewsAddDTO(
                    title=title,
                    summary=summary,
                    category=NewsCategory(category),
                )
                samples.append(obj)
            except ValidationError as exc:
                logger.error(
                    "Failed to parse sample #%d: %s", count, exc
                )

    logger.info(
        "Successfully loaded %d samples from initial count: %d",
        len(samples),
        count,
    )

    allowed = {c.value for c in NewsCategory}
    present = {s.category for s in samples}
    missing = allowed - present

    if missing:
        raise MissingDatasetClassesError(detail=missing)

    return samples
