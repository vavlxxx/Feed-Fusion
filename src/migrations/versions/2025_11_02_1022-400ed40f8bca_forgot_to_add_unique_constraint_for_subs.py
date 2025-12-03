"""forgot to add unique constraint for subs

Revision ID: 400ed40f8bca
Revises: 2b1b91fb261f
Create Date: 2025-11-02 10:22:15.322716

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "400ed40f8bca"
down_revision: Union[str, Sequence[str], None] = "2b1b91fb261f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_unique_constraint(
        op.f("uq_subscriptions_user_id"),
        "subscriptions",
        ["user_id", "channel_id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        op.f("uq_subscriptions_user_id"), "subscriptions", type_="unique"
    )
