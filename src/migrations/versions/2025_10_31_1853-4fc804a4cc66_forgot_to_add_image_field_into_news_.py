"""forgot to add image field into news model

Revision ID: 4fc804a4cc66
Revises: a7be86e6ce36
Create Date: 2025-10-31 18:53:41.740536

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4fc804a4cc66"
down_revision: Union[str, Sequence[str], None] = "a7be86e6ce36"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("news", sa.Column("image", sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("news", "image")
