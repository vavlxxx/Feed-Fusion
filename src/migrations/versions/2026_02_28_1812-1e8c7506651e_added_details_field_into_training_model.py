"""added details field into training model

Revision ID: 1e8c7506651e
Revises: 44901b15fde5
Create Date: 2026-02-28 18:12:10.898927

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1e8c7506651e"
down_revision: Union[str, Sequence[str], None] = "44901b15fde5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "classification_trainings",
        sa.Column("details", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("classification_trainings", "details")
