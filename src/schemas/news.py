from datetime import datetime

from bs4 import BeautifulSoup
from pydantic import field_validator

from src.schemas.enums import NewsCategory
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
    category: NewsCategory | None = None
    created_at: datetime
    updated_at: datetime

    @field_validator("category", mode="before")
    @classmethod
    def parse_category(
        cls, value: str | NewsCategory
    ) -> NewsCategory:
        if isinstance(value, str):
            try:
                return NewsCategory(value)
            except ValueError:
                raise ValueError("unknown category: %s" % value)
        return value


class NewsUpdateDTO(BaseDTO):
    category: NewsCategory | None = None


class PagingInfo(BaseDTO):
    page: int
    per_page: int
    has_next: bool
    total_count: int
    cursor: str | None = None
    recent_first: bool
    total_pages: int
    offset: int


class NewsResponseDTO(BaseDTO):
    id: int
    image: str | None
    title: str
    link: str
    summary: str
    source: str
    category: NewsCategory | None = None
    channel_id: int
    published: str
    created_at: str
    updated_at: str

    @field_validator("category", mode="before")
    @classmethod
    def parse_category(
        cls, value: str | NewsCategory
    ) -> NewsCategory:
        if isinstance(value, str):
            try:
                return NewsCategory(value)
            except ValueError:
                raise ValueError("unknown category: %s" % value)
        return value


class NewsResponse(BaseDTO):
    meta: PagingInfo
    news: list[NewsResponseDTO]
