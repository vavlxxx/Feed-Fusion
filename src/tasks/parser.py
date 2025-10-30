import feedparser
from src.tasks.app import celery_app


RSS_FEEDS: tuple[str, ...] = (
    "https://rssexport.rbc.ru/rbcnews/news/30/full.rss",
    "https://russian.rt.com/rss",
    "https://tass.ru/rss/v2.xml",
)


@celery_app.task(name="parse_feed")
def parse_rss_feeds():
    for feed_url in RSS_FEEDS:
        print(f"\n{'='*80}")
        print(f"Парсинг ленты: {feed_url}")
        print(f"{'='*80}\n")

        # Парсим RSS-ленту
        feed = feedparser.parse(feed_url)

        # Информация об источнике
        print(f"Источник: {feed.feed.get('title', 'Неизвестно')}")
        print(f"Описание: {feed.feed.get('description', 'Нет описания')}")
        print(f"Количество новостей: {len(feed.entries)}\n")

        # Выводим первые 5 новостей
        for i, entry in enumerate(feed.entries[:5], 1):
            print(f"--- Новость {i} ---")
            print(f"Заголовок: {entry.get('title', 'Без заголовка')}")
            print(f"Ссылка: {entry.get('link', 'Нет ссылки')}")
            print(f"Дата: {entry.get('published', 'Дата не указана')}")

            # Краткое описание (если есть)
            summary = entry.get("summary", "")
            if summary:
                # Обрезаем до 200 символов
                summary = summary[:200] + "..." if len(summary) > 200 else summary
                print(f"Описание: {summary}")

            print()
