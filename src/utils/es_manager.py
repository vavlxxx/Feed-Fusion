import logging
import sys
from pathlib import Path

from src.schemas.enums import NewsCategory

sys.path.append(str(Path(__file__).parent.parent.parent))

from elastic_transport import ObjectApiResponse
from elasticsearch import AsyncElasticsearch

from src.config import settings

logger = logging.getLogger("src.utils.es_manager")


class ESManager:
    def __init__(self, index_name: str):
        self._dsn: str = settings.get_elasticsearch_url
        self._index: str = index_name

    async def connection_is_stable(self) -> bool:
        if getattr(self, "_client", None) is None:
            return False
        return await self._client.ping()

    async def __aenter__(self) -> "ESManager":
        try:
            self._client: AsyncElasticsearch = AsyncElasticsearch(
                self._dsn,
                request_timeout=30,
                max_retries=5,
                retry_on_timeout=True,
            )
            if not await self.connection_is_stable():
                raise ConnectionError

        except Exception as e:
            logger.error(
                "Failed to connect to Elasticsearch: %s", e
            )
            await self._client.close()
            raise

        logger.info("Successfully connected to Elasticsearch...")
        await self._create_index()
        return self

    async def delete_index(
        self, index_name: str
    ) -> ObjectApiResponse:
        try:
            return await self._client.indices.delete(
                index=index_name,
                ignore_unavailable=True,
            )
        except Exception as e:
            logger.error(
                "Failed to delete old index: %s; error: %s",
                self._index,
                e,
            )
            raise

    async def _create_index(self):
        if await self._client.indices.exists(index=self._index):
            return

        config = {
            "settings": {
                "index": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                    "refresh_interval": "30s",
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
                "category": {
                    "type": "keyword",
                    "analyzer": "russian_analyzer",
                    "fields": {"keyword": {"type": "keyword"}},
                },
                "source": {
                    "type": "keyword",
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
                    "filter": [
                        "lowercase",
                        "russian_stop",
                        "russian_stemmer",
                    ],
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
                "russian_stop": {
                    "type": "stop",
                    "stopwords": "_russian_",
                },
                "russian_stemmer": {
                    "type": "stemmer",
                    "language": "russian",
                },
                "autocomplete_filter": {
                    "type": "edge_ngram",
                    "min_gram": 2,
                    "max_gram": 20,
                },
            },
        }

        try:
            return await self._client.options(
                ignore_status=400
            ).indices.create(
                index=self._index,
                mappings=config["mappings"],
                settings=config["settings"],
            )
        except Exception as e:
            logger.error(
                "Failed to create index: %s; error: %s",
                self._index,
                e,
            )
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
                refresh=False,
            )
        except Exception as e:
            logger.error(
                "Failed to bulk index: %s; error: %s",
                self._index,
                e,
            )
            raise

        if response.get("errors"):
            error_items = [
                item
                for item in response["items"]
                if "error" in item.get("index", {})
            ]
            logger.warning(
                "Bulk indexing had %d errors", len(error_items)
            )
        else:
            logger.debug(
                "Indexed %d documents successfully", len(data)
            )
        return response

    async def search(
        self,
        limit: int,
        query_string: str | None = None,
        categories: list[NewsCategory] | None = None,
        channel_ids: list[int] | None = None,
        search_after: list | None = None,
        recent_first: bool = True,
        # offset: int = 0,
    ) -> tuple[int, list[dict], list | None]:
        must_clauses = {"match_all": {}}
        if query_string:
            must_clauses = {
                "bool": {
                    "should": [
                        {
                            "multi_match": {
                                "query": query_string,
                                "fields": [
                                    "title^3",
                                    "summary^1.5",
                                    "source",
                                ],
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
        if channel_ids:
            filter_clauses.append(
                {
                    "terms": {
                        "channel_id": [
                            str(cid) for cid in channel_ids
                        ]
                    }
                }
            )

        if categories:
            filter_clauses.append(
                {
                    "terms": {
                        "category": [
                            str(category.value)
                            for category in categories
                        ]
                    }
                }
            )

        query_map = {
            "query": {
                "bool": {
                    "must": must_clauses,
                    "filter": filter_clauses,
                }
            },
            "size": limit,
            "search_after": search_after,
            # "from": offset,
            "sort": [
                {
                    "published": {
                        "order": "desc" if recent_first else "asc"
                    }
                }
            ],
            "track_total_hits": True,
        }

        response = await self._client.search(
            index=self._index,
            **query_map,
            # body=query_map,
        )

        hits = response.get("hits", {}).get("hits", [])
        total = (
            response.get("hits", {})
            .get("total", {})
            .get("value", 0)
        )
        results = [hit["_source"] for hit in hits]

        last_hit = None
        if hits:
            last_hit = hits[-1]["sort"]

        return total, results, last_hit

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self._client.close()
