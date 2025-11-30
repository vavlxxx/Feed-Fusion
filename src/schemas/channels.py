from datetime import datetime

from pydantic import model_validator

from src.schemas.base import BaseDTO


class ChannelAddDTO(BaseDTO):
    title: str
    link: str
    description: str | None = None


class ChannelUpdateDTO(BaseDTO):
    title: str | None = None
    link: str | None = None
    description: str | None = None

    @model_validator(mode="after")
    def validate_all_fields_are_providen(self):
        values = tuple(self.model_dump().values())
        if all(map(lambda val: val is None, values)):
            raise ValueError("provide at least one non-empty field")
        return self


class ChannelDTO(ChannelAddDTO):
    id: int
    created_at: datetime
    updated_at: datetime
