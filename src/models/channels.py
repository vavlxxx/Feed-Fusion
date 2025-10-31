from sqlalchemy.orm import Mapped

from src.models.base import Base
from src.models.mixins.primary_key import PrimaryKeyMixin
from src.models.mixins.timing import TimingMixin


class Channel(Base, PrimaryKeyMixin, TimingMixin):
    title: Mapped[str]
    link: Mapped[str]
    description: Mapped[str | None]
