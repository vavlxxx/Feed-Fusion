from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "99d7062c1731"
down_revision: Union[str, Sequence[str], None] = "400ed40f8bca"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    userrole_enum = postgresql.ENUM("ADMIN", "CUSTOMER", name="userrole")
    userrole_enum.create(op.get_bind())

    op.add_column(
        "users",
        sa.Column("role", userrole_enum, nullable=False),
    )
    op.drop_column("users", "email")


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        "users",
        sa.Column("email", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.drop_column("users", "role")

    userrole_enum = postgresql.ENUM(name="userrole")
    userrole_enum.drop(op.get_bind())
