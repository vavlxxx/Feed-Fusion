from datetime import datetime

from bs4 import BeautifulSoup
from pydantic import field_validator

from src.schemas.base import BaseDTO


class ParsedNewsDTO(BaseDTO):
    image: str | None
    title: str
    link: str
    summary: str
    source: str
    channel_id: int
    published: datetime

    @field_validator("summary")
    @classmethod
    def clean_summary(cls, v):
        return BeautifulSoup(v, "html.parser").get_text(strip=True)


class AddNewsDTO(ParsedNewsDTO):
    content_hash: str


class NewsDTO(AddNewsDTO):
    id: int
    created_at: datetime
    updated_at: datetime
