"""removed not-null constraint from denormalized news model

Revision ID: 9013c445258c
Revises: 6004ac21cb74
Create Date: 2026-02-26 15:00:25.976566

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9013c445258c"
down_revision: Union[str, Sequence[str], None] = "6004ac21cb74"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "news_denormalized", "summary", existing_type=sa.TEXT(), nullable=True
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "news_denormalized", "summary", existing_type=sa.TEXT(), nullable=False
    )
