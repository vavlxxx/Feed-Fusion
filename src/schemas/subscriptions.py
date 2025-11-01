from datetime import datetime
from src.schemas.base import BaseDTO


class SubscriptionAddDTO(BaseDTO):
    channel_id: int
    last_news_id: int
    user_id: int


class SubscriptionDTO(SubscriptionAddDTO):
    id: int
    created_at: datetime
    updated_at: datetime
