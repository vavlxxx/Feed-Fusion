from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base
from src.models.mixins.primary_key import PrimaryKeyMixin
from src.models.mixins.timing import TimingMixin


class Channel(Base, PrimaryKeyMixin, TimingMixin):
    title: Mapped[str]
    link: Mapped[str] = mapped_column(unique=True)
    description: Mapped[str | None]
