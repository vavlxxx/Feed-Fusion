from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base
from src.models.mixins.primary_key import PrimaryKeyMixin
from src.models.mixins.timing import TimingMixin
from src.schemas.news import NewsCategory


class News(Base, PrimaryKeyMixin, TimingMixin):
    __tablename__ = "news"

    link: Mapped[str] = mapped_column(String(255))
    published: Mapped[datetime]
    image: Mapped[str | None]
    title: Mapped[str] = mapped_column(String(255))
    summary: Mapped[str] = mapped_column(Text())
    source: Mapped[str] = mapped_column(String(255))
    content_hash: Mapped[str] = mapped_column(
        String(255),
        unique=True,
    )
    channel_id: Mapped[int] = mapped_column(
        ForeignKey("channels.id", ondelete="CASCADE", onupdate="CASCADE")
    )
    category: Mapped[NewsCategory | None ]= mapped_column(
        ENUM(NewsCategory, name="newscategory_enum",),
        default=None
    )


class DenormalizedNews(Base, PrimaryKeyMixin, TimingMixin):
    __tablename__ = "news_denormalized"
    title: Mapped[str] = mapped_column(String(255))
    summary: Mapped[str] = mapped_column(Text())
    category: Mapped[NewsCategory] = mapped_column(
        ENUM(NewsCategory, name="newscategory_enum")
    )
