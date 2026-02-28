"""created denomalized model + enum for categories

Revision ID: 1bc71611db4c
Revises: f4b6377824cd
Create Date: 2026-02-25 19:39:19.216938

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "1bc71611db4c"
down_revision: Union[str, Sequence[str], None] = "f4b6377824cd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("DROP TYPE IF EXISTS newscategory_enum CASCADE")
    newscategory_enum = postgresql.ENUM(
        "INTERNATIONAL",
        "CULTURE",
        "SCIENCETECH",
        "SOCIETY",
        "ECONOMICS",
        "INCIDENTS",
        "SPORT",
        "MEDICINE",
        name="newscategory_enum",
    )
    newscategory_enum.create(op.get_bind())
    op.create_table(
        "news_denormalized",
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column(
            "category",
            postgresql.ENUM(
                name="newscategory_enum",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "id", sa.Integer(), autoincrement=True, nullable=False
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
            "id", name=op.f("pk_news_denormalized")
        ),
    )
    op.add_column(
        "news",
        sa.Column(
            "category",
            postgresql.ENUM(
                name="newscategory_enum",
                create_type=False,
            ),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("news", "category")
    op.drop_table("news_denormalized")
    op.execute("DROP TYPE IF EXISTS newscategory_enum CASCADE")
