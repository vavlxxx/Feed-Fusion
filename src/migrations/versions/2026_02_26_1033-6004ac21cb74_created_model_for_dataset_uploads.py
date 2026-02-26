"""created model for dataset uploads

Revision ID: 6004ac21cb74
Revises: 1bc71611db4c
Create Date: 2026-02-26 10:33:46.009605

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "6004ac21cb74"
down_revision: Union[str, Sequence[str], None] = "1bc71611db4c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "dataset_uploads",
        sa.Column(
            "uploads",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column("errors", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "is_completed",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "details",
            postgresql.ARRAY(sa.String()),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
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
        sa.CheckConstraint(
            "errors >= 0",
            name=op.f("ck_dataset_uploads_chk_dataset_uploads_positive_errors"),
        ),
        sa.CheckConstraint(
            "uploads >= 0",
            name=op.f("ck_dataset_uploads_chk_dataset_uploads_positive_uploads"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_dataset_uploads")),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("dataset_uploads")
