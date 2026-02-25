from datetime import datetime

from bs4 import BeautifulSoup
from pydantic import field_validator
from enum import Enum

from src.schemas.base import BaseDTO


class NewsCategory(str, Enum):
    INTERNATIONAL = "Международные отношения"
    CULTURE = "Культура"
    SCIENCETECH = "Наука и технологии"
    SOCIETY = "Общество"
    ECONOMICS = "Экономика"
    INCIDENTS = "Происшествия"
    SPORT = "Спорт"
    MEDICINE = "Здоровье"


class DenormalizedNewsAddDTO(BaseDTO):
    title: str
    summary: str | None = None
    category: NewsCategory

    @field_validator("category", mode="before")
    @classmethod
    def parse_category(cls, value: str | NewsCategory) -> NewsCategory:
        if isinstance(value, str):
            try:
                return NewsCategory(value)
            except ValueError:
                raise ValueError(f"Неизвестная категория: {value}")
        return value


class DenormalizedNewsDTO(DenormalizedNewsAddDTO):
    id: int
    created_at: datetime
    updated_at: datetime


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
    channel_id: int
    published: str
    created_at: str
    updated_at: str


class NewsResponse(BaseDTO):
    meta: PagingInfo
    news: list[NewsResponseDTO]
