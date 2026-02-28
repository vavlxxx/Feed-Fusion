import torch

from src.ml.io_utils import (
    ensure_dir,
    load_json,
    resolve_device,
    save_json,
)
from src.ml.network import TextClassifier
from src.schemas.ml import TrainConfig
from src.ml.vocab import Vocab


class ArtifactStore:
    def __init__(self, model_dir: str = "artifacts"):
        self.model_dir = model_dir

    @property
    def model_path(self) -> str:
        return f"{self.model_dir}/model.pt"

    @property
    def vocab_path(self) -> str:
        return f"{self.model_dir}/vocab.json"

    @property
    def labels_path(self) -> str:
        return f"{self.model_dir}/labels.json"

    @property
    def config_path(self) -> str:
        return f"{self.model_dir}/config.json"

    @property
    def metrics_path(self) -> str:
        return f"{self.model_dir}/metrics.json"

    def save_metadata(
        self,
        vocab: Vocab,
        labels: list[str],
        config: TrainConfig,
        metrics: dict,
    ) -> None:
        ensure_dir(self.model_dir)
        save_json(vocab.to_dict(), self.vocab_path)
        save_json(labels, self.labels_path)
        save_json(config.model_dump(), self.config_path)
        save_json(metrics, self.metrics_path)

    def save_model_state(self, model: TextClassifier) -> None:
        ensure_dir(self.model_dir)
        torch.save(model.state_dict(), self.model_path)

    def load_predictor_bundle(self, device: str):
        device_obj = resolve_device(device)
        vocab = Vocab.from_dict(load_json(self.vocab_path))
        labels = load_json(self.labels_path)
        config = load_json(self.config_path)

        model = TextClassifier(
            vocab_size=len(vocab.token_to_idx),
            embed_dim=int(config["embed_dim"]),
            num_classes=len(labels),
            dropout=float(config["dropout"]),
        )
        state = torch.load(self.model_path, map_location=device_obj)
        model.load_state_dict(state)
        model.to(device_obj)
        model.eval()
        return model, vocab, labels, config, device_obj

    def load_resume_bundle(self, device: str):
        device_obj = resolve_device(device)
        vocab = Vocab.from_dict(load_json(self.vocab_path))
        labels = load_json(self.labels_path)
        config = load_json(self.config_path)
        state = torch.load(self.model_path, map_location=device_obj)
        return vocab, labels, config, state, device_obj
