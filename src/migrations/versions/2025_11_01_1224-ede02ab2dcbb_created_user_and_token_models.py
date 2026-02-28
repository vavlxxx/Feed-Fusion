"""created User and Token models

Revision ID: ede02ab2dcbb
Revises: a7be86e6ce36
Create Date: 2025-11-01 12:24:44.309359

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "ede02ab2dcbb"
down_revision: Union[str, Sequence[str], None] = "a7be86e6ce36"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("DROP TYPE IF EXISTS tokentype CASCADE")
    tokentype_enum = postgresql.ENUM(
        "ACCESS", "REFRESH", name="tokentype"
    )
    tokentype_enum.create(op.get_bind())

    op.create_table(
        "users",
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("first_name", sa.String(), nullable=True),
        sa.Column("last_name", sa.String(), nullable=True),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=True),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint(
            "username", name=op.f("uq_users_username")
        ),
    )
    op.create_table(
        "tokens",
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column(
            "type",
            postgresql.ENUM(name="tokentype", create_type=False),
            nullable=False,
        ),
        sa.Column("hashed_data", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            name=op.f("fk_tokens_owner_id_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tokens")),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("tokens")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS tokentype CASCADE")
