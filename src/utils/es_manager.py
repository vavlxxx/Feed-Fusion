import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from elastic_transport import ObjectApiResponse
from elasticsearch import AsyncElasticsearch

from src.config import settings


class ESManager:
    def __init__(self, index_name: str):
        self._dsn: str = settings.get_elasticsearch_url
        self._index: str = index_name
        self._client: AsyncElasticsearch | None = None

    async def __aenter__(self) -> "ESManager":
        self._client = AsyncElasticsearch(self._dsn)

        if not await self.connection_is_stable():
            raise ConnectionError("Failed to connect to Elasticsearch")

        await self._create_index()
        return self

    async def _create_index(self) -> ObjectApiResponse | None:
        if await self._client.indices.exists(index=self._index):
            return

        config = {
            "settings": {
                "index": {
                    "number_of_shards": 3,
                    "number_of_replicas": 2,
                    "refresh_interval": "1s",
                },
            },
        }

        config["settings"]["mappings"] = {
            "properties": {
                "published": {"type": "date"},
                "title": {"type": "text"},
                "summary": {"type": "text"},
                "source": {"type": "text"},
                "id": {"type": "keyword"},
            }
        }

        config["settings"]["analysis"] = {
            "analyzer": {
                "default": {"type": "custom", "tokenizer": "n_gram_tokenizer"},
            },
            "tokenizer": {
                "n_gram_tokenizer": {
                    "type": "edge_ngram",
                    "min_gram": 1,
                    "max_gram": 30,
                    "token_chars": ["letter", "digit"],
                },
            },
        }

        response = await self._client.indices.create(
            index=self._index,
            ignore=400,
            body=config,
        )
        return response

    async def connection_is_stable(self) -> bool:
        return await self._client.ping()

    async def add(self, data: list[dict]) -> ObjectApiResponse:
        operations = []
        for item in data:
            operations.append({"index": {"_index": self._index}})
            operations.append(item)

        return await self._client.bulk(index=self._index, body=operations)

    async def search(self, query_string: str) -> list[dict]:
        config = {
            "should": [
                {"match": {"title": query_string}},
                {"match": {"summary": query_string}},
                {"match": {"source": query_string}},
            ],
            "minimum_should_match": 1,
        }
        return await self._client.search(index=self._index, body={"query": config})

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self._client.close()


elasticsearch_mgr = ESManager(index_name=settings.ES_INDEX_NAME)


async def main():
    async with elasticsearch_mgr as es:
        await es.connection_is_stable()


if __name__ == "__main__":
    asyncio.run(main())
