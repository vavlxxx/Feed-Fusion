import logging
import logging.config
import json
import os
from pathlib import Path


def get_logging_config() -> dict:
    basepath = Path(__file__).resolve().parent.parent.parent
    with open(basepath / "logging_config.json", "r") as f:
        config = json.load(f)
    os.makedirs(basepath / "logs", exist_ok=True)
    return config


def configurate_logging() -> logging.Logger:
    config = get_logging_config()
    logging.config.dictConfig(config)


def get_logger(root_logger_name: str) -> logging.Logger:
    return logging.getLogger(root_logger_name)
