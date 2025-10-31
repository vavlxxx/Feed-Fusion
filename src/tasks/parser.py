import feedparser

from src.tasks.app import celery_app
from src.tasks.processor import process_news_item

RSS_FEEDS: tuple[str, ...] = (
    "https://rssexport.rbc.ru/rbcnews/news/30/full.rss",
    "https://russian.rt.com/rss",
    "https://tass.ru/rss/v2.xml",
)


@celery_app.task(name="parse_feed")
def parse_rss_feeds():
    """Парсит RSS-ленты и отправляет каждую новость в очередь на обработку"""
    for feed_url in RSS_FEEDS:
        print(f"\n{'='*80}")
        print(f"Парсинг ленты: {feed_url}")
        print(f"{'='*80}\n")

        feed = feedparser.parse(feed_url)

        source_name = feed.feed.get("title", "Неизвестно")
        print(f"Источник: {source_name}")
        print(f"Количество новостей: {len(feed.entries)}\n")

        # Отправляем каждую новость на обработку в отдельной задаче
        for entry in feed.entries:
            news_item = {
                "title": entry.get("title", "Без заголовка"),
                "link": entry.get("link", ""),
                "published": entry.get("published", ""),
                "summary": entry.get("summary", ""),
                "source": source_name,
                "feed_url": feed_url,
            }

            # Отправляем в очередь через Celery
            # Это асинхронный вызов - задача ставится в очередь
            process_news_item.delay(news_item)
            print(f"✓ Отправлено в очередь: {news_item['title'][:60]}...")
