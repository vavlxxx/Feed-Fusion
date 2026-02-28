import logging

import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

from src.ml.artifacts import ArtifactStore
from src.ml.io_utils import resolve_device, seed_everything
from src.ml.network import TextClassifier
from src.schemas.ml import TrainConfig, TrainingSample, TrainingResult
from src.ml.text import normalize_training_sample, tokenize
from src.ml.vocab import (
    Vocab,
    build_label_map,
    build_vocab,
    split_samples,
)

logger = logging.getLogger(__file__)


class _TextDataset(Dataset):
    def __init__(
        self,
        samples: list[tuple[str, str]],
        vocab: Vocab,
        label_to_idx: dict[str, int],
    ):
        self._samples = samples
        self._vocab = vocab
        self._label_to_idx = label_to_idx

    def __len__(self) -> int:
        return len(self._samples)

    def __getitem__(self, index: int):
        text, label = self._samples[index]
        token_ids = self._vocab.encode(tokenize(text))
        if not token_ids:
            token_ids = [self._vocab.unk_idx]
        return token_ids, self._label_to_idx[label]


def _collate_batch(batch):
    input_ids: list[int] = []
    offsets: list[int] = []
    labels: list[int] = []
    offset = 0
    for token_ids, label in batch:
        offsets.append(offset)
        input_ids.extend(token_ids)
        offset += len(token_ids)
        labels.append(label)

    return (
        torch.tensor(input_ids, dtype=torch.long),
        torch.tensor(offsets, dtype=torch.long),
        torch.tensor(labels, dtype=torch.long),
    )


def _compute_class_weights(
    samples: list[tuple[str, str]],
    label_to_idx: dict[str, int],
) -> torch.Tensor:
    counts = [0 for _ in range(len(label_to_idx))]
    for _, label in samples:
        counts[label_to_idx[label]] += 1
    total = sum(counts)
    weights = [total / max(count, 1) for count in counts]
    norm = sum(weights) / max(len(weights), 1)
    normalized = [weight / max(norm, 1e-8) for weight in weights]
    return torch.tensor(normalized, dtype=torch.float)


def _train_epoch(model, loader, loss_fn, optimizer, device):
    model.train()
    total_loss = 0.0
    total_correct = 0
    total_samples = 0

    for input_ids, offsets, labels in loader:
        input_ids = input_ids.to(device)
        offsets = offsets.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()
        logits = model(input_ids, offsets)
        loss = loss_fn(logits, labels)
        loss.backward()
        optimizer.step()

        total_loss += loss.item() * labels.size(0)
        total_correct += (
            (torch.argmax(logits, dim=-1) == labels).sum().item()
        )
        total_samples += labels.size(0)

    return total_loss / max(total_samples, 1), total_correct / max(
        total_samples, 1
    )


@torch.inference_mode()
def _evaluate(model, loader, loss_fn, device):
    model.eval()
    total_loss = 0.0
    total_correct = 0
    total_samples = 0

    for input_ids, offsets, labels in loader:
        input_ids = input_ids.to(device)
        offsets = offsets.to(device)
        labels = labels.to(device)
        logits = model(input_ids, offsets)
        loss = loss_fn(logits, labels)

        total_loss += loss.item() * labels.size(0)
        total_correct += (
            (torch.argmax(logits, dim=-1) == labels).sum().item()
        )
        total_samples += labels.size(0)

    return total_loss / max(total_samples, 1), total_correct / max(
        total_samples, 1
    )


def _normalize_samples(
    samples: list[TrainingSample],
) -> list[tuple[str, str]]:
    normalized: list[tuple[str, str]] = []
    for sample in samples:
        text, category = normalize_training_sample(sample)
        if text and category:
            normalized.append((text, category))
    return normalized


class ModelTrainer:
    def __init__(
        self, model_dir: str = "artifacts", device: str = "auto"
    ):
        self.store = ArtifactStore(model_dir=model_dir)
        self.device = device

    def train(
        self,
        samples: list[TrainingSample],
        resume: bool = False,
        config: TrainConfig | None = None,
        verbose: bool = True,
    ) -> TrainingResult:
        normalized_samples = _normalize_samples(samples)
        if not normalized_samples:
            raise ValueError("No training samples found.")

        active_config = config or TrainConfig()
        seed_everything(active_config.seed)
        device_obj = resolve_device(self.device)

        if resume:
            vocab, labels, stored, state, _ = (
                self.store.load_resume_bundle(self.device)
            )
            label_to_idx = {
                label: index for index, label in enumerate(labels)
            }
            missing_labels = {
                label
                for _, label in normalized_samples
                if label not in label_to_idx
            }
            if missing_labels:
                missing = ", ".join(sorted(missing_labels))
                raise ValueError(
                    "New labels detected during resume. "
                    f"Retrain from scratch to include: {missing}"
                )
            active_config.embed_dim = int(stored["embed_dim"])
            active_config.dropout = float(stored["dropout"])
            active_config.min_freq = int(stored["min_freq"])
            active_config.max_vocab = int(stored["max_vocab"])
        else:
            label_to_idx, labels = build_label_map(
                label for _, label in normalized_samples
            )
            vocab = build_vocab(
                texts=(text for text, _ in normalized_samples),
                min_freq=active_config.min_freq,
                max_size=active_config.max_vocab,
            )
            state = None

        train_samples, val_samples = split_samples(
            samples=normalized_samples,
            val_split=active_config.val_split,
            seed=active_config.seed,
        )
        if not train_samples:
            raise ValueError(
                "Train split is empty. Decrease val_split."
            )

        train_loader = DataLoader(
            _TextDataset(train_samples, vocab, label_to_idx),
            batch_size=active_config.batch_size,
            shuffle=True,
            collate_fn=_collate_batch,
        )
        val_loader = DataLoader(
            _TextDataset(val_samples, vocab, label_to_idx),
            batch_size=active_config.batch_size,
            shuffle=False,
            collate_fn=_collate_batch,
        )

        model = TextClassifier(
            vocab_size=len(vocab.token_to_idx),
            embed_dim=active_config.embed_dim,
            num_classes=len(labels),
            dropout=active_config.dropout,
        ).to(device_obj)

        if resume and state is not None:
            model.load_state_dict(state)

        if active_config.balance:
            weights = _compute_class_weights(
                train_samples, label_to_idx
            ).to(device_obj)
            loss_fn = nn.CrossEntropyLoss(weight=weights)
        else:
            loss_fn = nn.CrossEntropyLoss()

        optimizer = torch.optim.AdamW(
            model.parameters(),
            lr=active_config.lr,
            weight_decay=active_config.weight_decay,
        )

        metrics: dict[str, list[dict[str, float]]] = {
            "train": [],
            "val": [],
        }
        best_val_acc = -1.0
        saved = False

        for epoch in range(1, active_config.epochs + 1):
            train_loss, train_acc = _train_epoch(
                model=model,
                loader=train_loader,
                loss_fn=loss_fn,
                optimizer=optimizer,
                device=device_obj,
            )
            metrics["train"].append(
                {
                    "epoch": epoch,
                    "loss": train_loss,
                    "accuracy": train_acc,
                }
            )

            if val_samples:
                val_loss, val_acc = _evaluate(
                    model=model,
                    loader=val_loader,
                    loss_fn=loss_fn,
                    device=device_obj,
                )
                metrics["val"].append(
                    {
                        "epoch": epoch,
                        "loss": val_loss,
                        "accuracy": val_acc,
                    }
                )
                if verbose:
                    logger.info(
                        "Epoch %d: train_loss=%f train_acc=%f val_loss=%f val_acc=%f",
                        epoch,
                        train_loss,
                        train_acc,
                        val_loss,
                        val_acc,
                    )
                if val_acc >= best_val_acc:
                    best_val_acc = val_acc
                    self.store.save_model_state(model)
                    saved = True
            else:
                if verbose:
                    logger.info(
                        "Epoch %d: train_loss=%f train_acc=%f",
                        epoch,
                        train_loss,
                        train_acc,
                    )
                self.store.save_model_state(model)
                saved = True

        if not saved:
            self.store.save_model_state(model)

        self.store.save_metadata(
            vocab=vocab,
            labels=labels,
            config=active_config,
            metrics=metrics,
        )

        if verbose:
            logger.info(
                "Saved model artifacts to %s", self.store.model_dir
            )

        return TrainingResult(
            model_dir=self.store.model_dir,
            metrics=metrics,
            labels=labels,
            config=active_config,
            device=str(device_obj),
        )
