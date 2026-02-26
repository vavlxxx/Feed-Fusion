import json
import logging.config
from pathlib import Path

from celery import Celery
from celery.signals import setup_logging

from src.config import settings


@setup_logging.connect
def config_loggers(*args, **kwargs):
    basepath = Path(__file__).resolve().parent.parent.parent
    with open(basepath / "logging_config.json", "r") as f:
        config = json.load(f)
    logging.config.dictConfig(config)


celery_app = Celery(
    "tasks",
    broker=settings.rabbit_url,
    include=[
        "src.tasks.parser",
        "src.tasks.processor",
        "src.tasks.subs",
        "src.tasks.ml",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # beat_scheduler="redbeat.RedBeatScheduler",
    # redbeat_redis_url=settings.redis_url,
)

celery_app.conf.beat_schedule = {
    "parse_rss": {
        "task": "parse_rss",
        "schedule": 60.0,
    },
    "check_subs": {
        "task": "check_subs",
        "schedule": 30.0,
    },
}
