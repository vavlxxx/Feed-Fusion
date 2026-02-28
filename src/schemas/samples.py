from datetime import datetime

from pydantic import field_validator, Field

from src.schemas.enums import NewsCategory
from src.schemas.base import BaseDTO


class DenormalizedNewsAddDTO(BaseDTO):
    title: str
    summary: str | None = None
    category: NewsCategory

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


class DenormalizedNewsUpdateDTO(BaseDTO):
    used_in_training: bool | None = None


class DenormalizedNewsDTO(DenormalizedNewsAddDTO):
    id: int
    used_in_training: bool
    created_at: datetime
    updated_at: datetime


class DatasetUploadAddDTO(BaseDTO):
    uploads: int = Field(default=0, ge=0)
    errors: int = Field(default=0, ge=0)
    details: list[str] = Field(default_factory=list)


class DatasetUploadUpdateDTO(BaseDTO):
    uploads: int | None = Field(default=None, ge=0)
    errors: int | None = Field(default=None, ge=0)
    details: list[str] | None = None
    is_completed: bool | None = None


class DatasetUploadDTO(DatasetUploadAddDTO):
    id: int
    is_completed: bool
    created_at: datetime
    updated_at: datetime
