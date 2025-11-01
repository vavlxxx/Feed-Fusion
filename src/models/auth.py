from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column

from src.models.mixins.primary_key import PrimaryKeyMixin
from src.models.mixins.timing import TimingMixin
from src.models.base import Base
from src.schemas.auth import TokenType


class User(Base, PrimaryKeyMixin, TimingMixin):
    username: Mapped[str] = mapped_column(unique=True)
    first_name: Mapped[str | None]
    last_name: Mapped[str | None]
    hashed_password: Mapped[str]
    email: Mapped[str | None]
    telegram_id: Mapped[str | None]


class Token(Base, PrimaryKeyMixin, TimingMixin):
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    type: Mapped[TokenType] = mapped_column(ENUM(TokenType))
    hashed_data: Mapped[str]
    expires_at: Mapped[datetime]
