"""created training model + added used_in_training field into samples

Revision ID: 44901b15fde5
Revises: 030341b7de20
Create Date: 2026-02-28 17:25:54.698837

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "44901b15fde5"
down_revision: Union[str, Sequence[str], None] = "030341b7de20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "classification_trainings",
        sa.Column(
            "id", sa.Integer(), autoincrement=True, nullable=False
        ),
        sa.Column(
            "config",
            postgresql.JSON(astext_type=sa.Text()),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
        sa.Column(
            "metrics",
            postgresql.JSON(astext_type=sa.Text()),
            server_default=sa.text("'{}'"),
            nullable=True,
        ),
        sa.Column("model_dir", sa.String(), nullable=False),
        sa.Column("device", sa.String(), nullable=False),
        sa.Column(
            "in_progress",
            sa.Boolean(),
            server_default=sa.text("True"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint(
            "id", name=op.f("pk_classification_trainings")
        ),
    )
    op.create_index(
        "uq_model_dir_in_progress",
        "classification_trainings",
        ["model_dir"],
        unique=True,
        postgresql_where=sa.text("in_progress = true"),
    )
    op.add_column(
        "news_denormalized",
        sa.Column(
            "used_in_training",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("news_denormalized", "used_in_training")
    op.drop_index(
        "uq_model_dir_in_progress",
        table_name="classification_trainings",
        postgresql_where=sa.text("in_progress = true"),
    )
    op.drop_table("classification_trainings")
