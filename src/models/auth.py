from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.mixins.primary_key import PrimaryKeyMixin
from src.models.mixins.timing import TimingMixin
from src.models.base import Base
from src.schemas.auth import TokenType, UserRole

if TYPE_CHECKING:
    from src.models.subscriptions import Subscription


class User(Base, PrimaryKeyMixin, TimingMixin):
    username: Mapped[str] = mapped_column(unique=True)
    first_name: Mapped[str | None]
    last_name: Mapped[str | None]
    hashed_password: Mapped[str]
    role: Mapped[UserRole] = mapped_column(ENUM(UserRole), default=UserRole.CUSTOMER)
    telegram_id: Mapped[str | None]

    subscriptions: Mapped[list["Subscription"]] = relationship(
        "Subscription",
        back_populates="user",
    )


class Token(Base, PrimaryKeyMixin, TimingMixin):
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    type: Mapped[TokenType] = mapped_column(ENUM(TokenType))
    hashed_data: Mapped[str]
    expires_at: Mapped[datetime]
