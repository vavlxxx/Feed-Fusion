from celery import Celery
from src.config import settings

celery_app = Celery(
    "tasks",
    broker=settings.rabbit_url,
    backend=settings.redis_url,  # Добавляем backend для отслеживания результатов
    include=[
        "src.tasks.parser",
        "src.tasks.processor",  # Добавляем модуль обработчика
    ],
)

# Настройки Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Almaty",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,  # Подтверждение после выполнения (важно для надёжности)
    worker_prefetch_multiplier=1,  # Воркер берёт по одной задаче (для равномерной нагрузки)
)

# Расписание для периодического парсинга
celery_app.conf.beat_schedule = {
    "parse_feed": {
        "task": "parse_feed",
        "schedule": 60.0,  # Каждую минуту
    }
}
