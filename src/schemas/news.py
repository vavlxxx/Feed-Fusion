from datetime import datetime

from src.schemas.base import BaseDTO


class ParsedNewsDTO(BaseDTO):
    image: str | None
    title: str
    link: str
    summary: str
    source: str
    published: str


class AddNewsDTO(ParsedNewsDTO):
    content_hash: str


class NewsDTO(AddNewsDTO):
    id: int
    created_at: datetime
    updated_at: datetime
