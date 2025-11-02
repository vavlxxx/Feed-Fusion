from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base
from src.models.mixins.primary_key import PrimaryKeyMixin
from src.models.mixins.timing import TimingMixin


if TYPE_CHECKING:
    from src.models.auth import User


class Subscription(Base, PrimaryKeyMixin, TimingMixin):
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"), nullable=False)
    last_news_id: Mapped[int] = mapped_column(ForeignKey("news.id"), nullable=False)

    user: Mapped["User"] = relationship(
        "User",
        back_populates="subscriptions",
        uselist=False,
    )

    __table_args__ = __table_args__ = __table_args__ = (
        UniqueConstraint(
            "user_id",
            "channel_id",
        ),
    )
