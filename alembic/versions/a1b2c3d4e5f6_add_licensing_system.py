"""add licensing system

Revision ID: a1b2c3d4e5f6
Revises: 968d26aaac9ca
Create Date: 2026-07-22

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "968d26aaac9c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create super_admins table
    op.create_table(
        "super_admins",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_super_admins_id", "super_admins", ["id"])
    op.create_index("ix_super_admins_email", "super_admins", ["email"])

    # Add license columns to firms table
    op.add_column(
        "firms",
        sa.Column("license_key_hash", sa.String(64), nullable=True),
    )
    op.create_index("ix_firms_license_key_hash", "firms", ["license_key_hash"])
    op.add_column(
        "firms",
        sa.Column("license_tier", sa.String(50), nullable=True),
    )
    op.add_column(
        "firms",
        sa.Column("license_expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "firms",
        sa.Column("license_activated_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Auto-generate perpetual "legacy" license for existing firms
    op.execute(
        """
        UPDATE firms
        SET
            license_key_hash = encode(sha256('LEGACY-PERPETUAL'::bytea), 'hex'),
            license_tier = 'enterprise',
            license_activated_at = now()
        WHERE license_key_hash IS NULL
        """
    )


def downgrade() -> None:
    # Remove license columns from firms
    op.drop_column("firms", "license_activated_at")
    op.drop_column("firms", "license_expires_at")
    op.drop_column("firms", "license_tier")
    op.drop_index("ix_firms_license_key_hash", table_name="firms")
    op.drop_column("firms", "license_key_hash")

    # Drop super_admins table
    op.drop_index("ix_super_admins_email", table_name="super_admins")
    op.drop_index("ix_super_admins_id", table_name="super_admins")
    op.drop_table("super_admins")
