from datetime import datetime

from sqlalchemy import (
    ForeignKey,
    String,
    Text, text, Boolean,
)
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base
from src.models.mixins.primary_key import PrimaryKeyMixin
from src.models.mixins.timing import TimingMixin
from src.schemas.enums import NewsCategory


class News(Base, PrimaryKeyMixin, TimingMixin):
    __tablename__ = "news"  # type: ignore

    link: Mapped[str] = mapped_column(String(255))
    published: Mapped[datetime]
    image: Mapped[str | None]
    title: Mapped[str] = mapped_column(Text())
    summary: Mapped[str] = mapped_column(Text())
    source: Mapped[str] = mapped_column(String(255))
    content_hash: Mapped[str] = mapped_column(
        String(255),
        unique=True,
    )
    channel_id: Mapped[int] = mapped_column(
        ForeignKey(
            "channels.id", ondelete="CASCADE", onupdate="CASCADE"
        )
    )
    category: Mapped[NewsCategory | None] = mapped_column(
        ENUM(
            NewsCategory,
            name="newscategory_enum",
        ),
        default=None,
    )


class DenormalizedNews(Base, PrimaryKeyMixin, TimingMixin):
    __tablename__ = "news_denormalized"  # type: ignore
    title: Mapped[str] = mapped_column(Text())
    summary: Mapped[str | None] = mapped_column(
        Text(), default=None
    )
    category: Mapped[NewsCategory] = mapped_column(
        ENUM(NewsCategory, name="newscategory_enum")
    )
    used_in_training: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))