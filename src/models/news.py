from datetime import datetime
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base
from src.models.mixins.primary_key import PrimaryKeyMixin
from src.models.mixins.timing import TimingMixin


class News(Base, PrimaryKeyMixin, TimingMixin):
    channel_id: Mapped[int] = mapped_column(
        ForeignKey("channels.id", ondelete="CASCADE", onupdate="CASCADE")
    )
    title: Mapped[str] = mapped_column(String(255))
    link: Mapped[str] = mapped_column(String(255))
    content_hash: Mapped[str] = mapped_column(String(255), unique=True)
    published: Mapped[datetime]
    image: Mapped[str | None]
    summary: Mapped[str] = mapped_column(Text())
    source: Mapped[str] = mapped_column(String(255))
