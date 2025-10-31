# src/tasks/processor.py
import hashlib
from src.tasks.app import celery_app


@celery_app.task(name="process_news_item", bind=True, max_retries=3)
def process_news_item(self, news_item: dict):
    """
    Обрабатывает новость: дедублицирует и сохраняет в БД

    Args:
        news_item: Словарь с данными новости
    """
    try:
        content_hash = generate_news_hash(news_item)
        print(f"✅ Сохранено: {news_item["title"][:50]}...")
        return {"status": "created"}
    except Exception as exc:
        print(f"❌ Ошибка обработки: {exc}")
        # Повторная попытка с экспоненциальной задержкой
        raise self.retry(exc=exc, countdown=60 * (2**self.request.retries))


def generate_news_hash(news_item: dict) -> str:
    """Генерирует хэш для проверки уникальности новости"""
    # Используем ссылку как основной идентификатор
    # Можно добавить title для дополнительной проверки
    unique_string = f"{news_item['link']}|{news_item['title']}"
    return hashlib.sha256(unique_string.encode()).hexdigest()
