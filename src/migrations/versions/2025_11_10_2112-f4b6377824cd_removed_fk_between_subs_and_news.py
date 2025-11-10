"""removed FK between subs and news

Revision ID: f4b6377824cd
Revises: 99d7062c1731
Create Date: 2025-11-10 21:12:06.271715

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f4b6377824cd"
down_revision: Union[str, Sequence[str], None] = "99d7062c1731"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint(
        op.f("fk_subscriptions_last_news_id_news"),
        "subscriptions",
        type_="foreignkey",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.create_foreign_key(
        op.f("fk_subscriptions_last_news_id_news"),
        "subscriptions",
        "news",
        ["last_news_id"],
        ["id"],
    )
