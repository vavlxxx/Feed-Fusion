from collections import Counter
from typing import Dict, Iterable, Sequence

import torch

from src.ml.text import tokenize


class Vocab:
    def __init__(
        self, token_to_idx: Dict[str, int], unk_token: str = "<unk>"
    ):
        self.token_to_idx = token_to_idx
        self.unk_token = unk_token
        self.unk_idx = token_to_idx[unk_token]

    def encode(self, tokens: Sequence[str]) -> list[int]:
        return [
            self.token_to_idx.get(token, self.unk_idx)
            for token in tokens
        ]

    def to_dict(self) -> dict[str, object]:
        return {
            "token_to_idx": self.token_to_idx,
            "unk_token": self.unk_token,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "Vocab":
        return cls(payload["token_to_idx"], payload["unk_token"])  # type: ignore


def build_label_map(
    labels: Iterable[str],
) -> tuple[dict[str, int], list[str]]:
    label_to_idx: dict[str, int] = {}
    idx_to_label: list[str] = []
    for label in labels:
        if label not in label_to_idx:
            label_to_idx[label] = len(idx_to_label)
            idx_to_label.append(label)
    return label_to_idx, idx_to_label


def build_vocab(
    texts: Iterable[str],
    min_freq: int,
    max_size: int,
    unk_token: str = "<unk>",
) -> Vocab:
    counter: Counter[str] = Counter()
    for text in texts:
        counter.update(tokenize(text))

    tokens = [
        token
        for token, count in counter.items()
        if count >= min_freq
    ]
    tokens.sort(key=lambda token: counter[token], reverse=True)

    if max_size and max_size > 1:
        tokens = tokens[: max_size - 1]

    token_to_idx = {unk_token: 0}
    for token in tokens:
        token_to_idx[token] = len(token_to_idx)
    return Vocab(token_to_idx=token_to_idx, unk_token=unk_token)


def split_samples(
    samples: Sequence[tuple[str, str]],
    val_split: float,
    seed: int,
) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    if val_split <= 0:
        return list(samples), []

    generator = torch.Generator().manual_seed(seed)
    indices = torch.randperm(
        len(samples), generator=generator
    ).tolist()
    val_size = int(len(samples) * val_split)
    val_indices = set(indices[:val_size])

    train_samples: list[tuple[str, str]] = []
    val_samples: list[tuple[str, str]] = []
    for index, sample in enumerate(samples):
        if index in val_indices:
            val_samples.append(sample)
        else:
            train_samples.append(sample)
    return train_samples, val_samples
