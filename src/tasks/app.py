from celery import Celery

from src.config import settings

celery_app = Celery(
    "tasks",
    broker=settings.rabbit_url,
    include=[
        "src.tasks.parser",
    ],
)

celery_app.conf.beat_schedule = {
    "parse_feed": {
        "task": "parse_feed",
        "schedule": 60.0,
    }
}
