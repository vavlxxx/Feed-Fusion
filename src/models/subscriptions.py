from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base
from src.models.mixins.primary_key import PrimaryKeyMixin
from src.models.mixins.timing import TimingMixin


class Subscription(Base, PrimaryKeyMixin, TimingMixin):
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"), nullable=False)
    last_news_id: Mapped[int] = mapped_column(ForeignKey("news.id"), nullable=False)
