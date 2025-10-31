"""created model for news

Revision ID: a7be86e6ce36
Revises: 18c93b7b5930
Create Date: 2025-10-31 17:53:22.692994

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a7be86e6ce36"
down_revision: Union[str, Sequence[str], None] = "18c93b7b5930"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "news",
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("link", sa.String(length=255), nullable=False),
        sa.Column("content_hash", sa.String(length=255), nullable=False),
        sa.Column("published", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=255), nullable=False),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_news")),
        sa.UniqueConstraint("content_hash", name=op.f("uq_news_content_hash")),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("news")
