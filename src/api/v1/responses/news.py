from typing import Any, Dict

from fastapi import status

from src.schemas.news import NewsResponse
from src.utils.exceptions import (
    ChannelNotFoundHTTPError,
    ValueOutOfRangeHTTPError,
)

NEWS_RESPONSES: Dict[int | str, Dict[str, Any]] | None = {
    status.HTTP_200_OK: {
        "description": "Новости успешно получены",
        "model": NewsResponse,
        "content": {
            "application/json": {
                "example": {
                    "meta": {
                        "page": 1,
                        "per_page": 10,
                        "has_next": False,
                        "total_count": 10,
                        "cursor": None,
                        "recent_first": True,
                        "total_pages": 1,
                        "offset": 0,
                    },
                    "data": [
                        {
                            "id": 1,
                            "title": "Новости Москвы",
                            "link": "https://example.com/moscow-news",
                            "summary": "",
                            "source": "Москва Times",
                            "channel_id": 1,
                            "image": "https://example.com/img.png",
                            "published": "2025-12-03T07:20:28",
                            "content_hash": "some-hash-value",
                            "created_at": "2025-12-03T07:35:04.005600",
                            "updated_at": "2025-12-03T07:35:04.005600",
                        }
                    ],
                }
            }
        },
    },
    status.HTTP_404_NOT_FOUND: {
        "description": "Канал не найден",
        "content": {
            "application/json": {
                "example": {
                    "detail": ChannelNotFoundHTTPError.detail
                }
            }
        },
    },
    status.HTTP_422_UNPROCESSABLE_ENTITY: {
        "description": "Ошибка валидации",
        "content": {
            "application/json": {
                "example": {
                    "detail": ValueOutOfRangeHTTPError.detail
                }
            }
        },
    },
}
