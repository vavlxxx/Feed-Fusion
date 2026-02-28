from sqlalchemy import text, String, CheckConstraint, Index, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSON
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base
from src.models.mixins.primary_key import PrimaryKeyMixin
from src.models.mixins.timing import TimingMixin


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


class ClassificatorTraining(Base, PrimaryKeyMixin, TimingMixin):
    __tablename__ = "classification_trainings"  # pyright: ignore

    config: Mapped[dict] = mapped_column(
        JSON,
        default={},
        server_default=text("'{}'"),
    )
    metrics: Mapped[dict | None] = mapped_column(
        JSON,
        default={},
        nullable=True,
        server_default=text("'{}'"),
    )
    model_dir: Mapped[str]
    device: Mapped[str]
    in_progress: Mapped[bool] = mapped_column(
        default=True, server_default=text("True")
    )
    details: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    __table_args__ = (
        Index(
            "uq_model_dir_in_progress",
            "model_dir",
            unique=True,
            postgresql_where=text("in_progress = true"),
        ),
    )
