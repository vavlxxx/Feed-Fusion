from datetime import datetime

from src.schemas.base import BaseDTO


class ChannelDTO(BaseDTO):
    id: int
    title: str
    link: str
    description: str | None
    created_at: datetime
    updated_at: datetime
