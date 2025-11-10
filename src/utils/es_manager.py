import sys
import logging
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from elastic_transport import ObjectApiResponse
from elasticsearch import AsyncElasticsearch

from src.config import settings


logger = logging.getLogger("src.utils.es_manager")


class ESManager:
    def __init__(self, index_name: str):
        self._dsn: str = settings.get_elasticsearch_url
        self._index: str = index_name
        self._client: AsyncElasticsearch | None = None

    async def connection_is_stable(self) -> bool:
        return await self._client.ping()

    async def __aenter__(self) -> "ESManager":
        try:
            self._client = AsyncElasticsearch(
                self._dsn,
                request_timeout=30,
                max_retries=5,
                retry_on_timeout=True,
            )
            if not await self.connection_is_stable():
                raise ConnectionError

        except Exception as e:
            logger.error("Failed to connect to Elasticsearch: %s", e)
            await self._client.close()
            raise

        logger.info("Successfully connected to Elasticsearch...")
        if await self._client.indices.exists(index=self._index):
            logger.debug("Creating new index: %s", self._index)
            await self._create_index()
        return self

    async def _delete_index(self, index_name: str) -> ObjectApiResponse:
        try:
            return await self._client.indices.delete(
                index=index_name,
                ignore_unavailable=True,
            )
        except Exception as e:
            logger.error("Failed to delete old index: %s; error: %s", self._index, e)
            raise

    async def _create_index(self):
        if settings.ES_RESET_INDEX:
            await self._delete_index(self._index)

        config = {
            "settings": {
                "index": {
                    "number_of_shards": 3,
                    "number_of_replicas": 2,
                    "refresh_interval": "1s",
                },
            },
        }

        config["mappings"] = {
            "properties": {
                "id": {"type": "keyword"},
                "channel_id": {"type": "keyword"},
                "published": {"type": "date"},
                "title": {
                    "type": "text",
                    "analyzer": "russian_analyzer",
                    "fields": {
                        "keyword": {"type": "keyword"},
                        "autocomplete": {
                            "type": "text",
                            "analyzer": "autocomplete_analyzer",
                            "search_analyzer": "search_analyzer",
                        },
                    },
                },
                "summary": {
                    "type": "text",
                    "analyzer": "russian_analyzer",
                    "fields": {
                        "autocomplete": {
                            "type": "text",
                            "analyzer": "autocomplete_analyzer",
                            "search_analyzer": "search_analyzer",
                        }
                    },
                },
                "source": {
                    "type": "text",
                    "analyzer": "russian_analyzer",
                    "fields": {"keyword": {"type": "keyword"}},
                },
                "link": {"type": "keyword"},
                "image": {"type": "keyword"},
                "content_hash": {"type": "keyword"},
            }
        }

        config["settings"]["analysis"] = {
            "analyzer": {
                "russian_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "russian_stop", "russian_stemmer"],
                },
                "autocomplete_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "autocomplete_filter"],
                },
                "search_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase"],
                },
            },
            "filter": {
                "russian_stop": {"type": "stop", "stopwords": "_russian_"},
                "russian_stemmer": {"type": "stemmer", "language": "russian"},
                "autocomplete_filter": {
                    "type": "edge_ngram",
                    "min_gram": 2,
                    "max_gram": 20,
                },
            },
        }

        try:
            return await self._client.options(ignore_status=400).indices.create(
                index=self._index,
                body=config,
            )
        except Exception as e:
            logger.error("Failed to create index: %s; error: %s", self._index, e)
            raise

    async def add(self, data: list[dict]) -> ObjectApiResponse:
        operations = []
        for item in data:
            operations.append({"index": {"_index": self._index}})
            operations.append(item)

        try:
            response = await self._client.bulk(
                index=self._index,
                operations=operations,
                refresh=True,
            )
        except Exception as e:
            logger.error("Failed to bulk index: %s; error: %s", self._index, e)
            raise

        if response.get("errors"):
            error_items = [
                item for item in response["items"] if "error" in item.get("index", {})
            ]
            logger.warning("Bulk indexing had %d errors", len(error_items))
        else:
            logger.debug("Indexed %d documents successfully", len(data))
        return response

    async def search(
        self,
        query_string: str | None = None,
        channel_id: int | None = None,
        limit: int = 15,
        offset: int = 0,
    ) -> tuple[int, list[dict]]:

        must_clauses = {"match_all": {}}
        if query_string:
            must_clauses = {
                "bool": {
                    "should": [
                        {
                            "multi_match": {
                                "query": query_string,
                                "fields": ["title^3", "summary^1.5", "source"],
                                "type": "best_fields",
                                "fuzziness": "AUTO",
                                "operator": "or",
                            }
                        },
                        {
                            "multi_match": {
                                "query": query_string,
                                "fields": ["title^5", "summary^2"],
                                "type": "phrase",
                                "boost": 2,
                            }
                        },
                        {
                            "multi_match": {
                                "query": query_string,
                                "fields": [
                                    "title.autocomplete^2",
                                    "summary.autocomplete",
                                ],
                                "type": "phrase_prefix",
                            }
                        },
                    ],
                    "minimum_should_match": 1,
                }
            }

        filter_clauses = []
        if channel_id:
            filter_clauses.append({"term": {"channel_id": f"{channel_id}"}})

        query_map = {
            "query": {"bool": {"must": must_clauses, "filter": filter_clauses}},
            "size": limit,
            "from": offset,
            "sort": [{"published": {"order": "desc"}}],
            "track_total_hits": True,
        }

        response = await self._client.search(
            index=self._index,
            body=query_map,
        )

        hits = response.get("hits", {}).get("hits", [])
        total = response.get("hits", {}).get("total", {}).get("value", 0)
        results = [hit["_source"] for hit in hits]

        return total, results

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self._client.close()
