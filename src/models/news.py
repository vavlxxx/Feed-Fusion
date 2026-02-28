from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, ENUM
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


class DatasetUploads(Base, PrimaryKeyMixin, TimingMixin):
    __tablename__ = "dataset_uploads"  # type: ignore
    uploads: Mapped[int] = mapped_column(
        default=0, server_default=text("0")
    )
    errors: Mapped[int] = mapped_column(
        default=0, server_default=text("0")
    )
    is_completed: Mapped[bool] = mapped_column(
        default=False, server_default=text("false")
    )

    details: Mapped[list[str]] = mapped_column(
        ARRAY(String), default=list, server_default=text("'{}'")
    )

    __table_args__ = (
        CheckConstraint(
            "uploads >= 0",
            name="chk_dataset_uploads_positive_uploads",
        ),
        CheckConstraint(
            "errors >= 0",
            name="chk_dataset_uploads_positive_errors",
        ),
    )
