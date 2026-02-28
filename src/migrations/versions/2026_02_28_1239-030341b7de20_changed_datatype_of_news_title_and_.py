"""changed datatype of news title and summary fields

Revision ID: 030341b7de20
Revises: 9013c445258c
Create Date: 2026-02-28 12:39:17.298647

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "030341b7de20"
down_revision: Union[str, Sequence[str], None] = "9013c445258c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "news",
        "title",
        existing_type=sa.VARCHAR(length=255),
        type_=sa.Text(),
        existing_nullable=False,
    )
    op.alter_column(
        "news_denormalized",
        "title",
        existing_type=sa.VARCHAR(length=255),
        type_=sa.Text(),
        existing_nullable=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "news_denormalized",
        "title",
        existing_type=sa.Text(),
        type_=sa.VARCHAR(length=255),
        existing_nullable=False,
    )
    op.alter_column(
        "news",
        "title",
        existing_type=sa.Text(),
        type_=sa.VARCHAR(length=255),
        existing_nullable=False,
    )
