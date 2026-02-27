import json
import os
import random
from typing import Any

import torch


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
