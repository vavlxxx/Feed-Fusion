from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import mapped_column, Mapped


class TimingMixin:
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )
