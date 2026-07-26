"""add password expiry policy

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-26

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add password_changed_at to users table
    op.add_column(
        "users",
        sa.Column("password_changed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Set existing users' password_changed_at to their updated_at
    op.execute(
        """
        UPDATE users
        SET password_changed_at = updated_at
        WHERE password_changed_at IS NULL
        """
    )

    # Seed password_expiry_days setting (global, firm_id=NULL)
    op.execute(
        """
        INSERT INTO system_settings (key, value, description)
        VALUES ('password_expiry_days', '90', 'Force password change after N days (0=disabled, max 90)')
        ON CONFLICT (key) DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute("DELETE FROM system_settings WHERE key = 'password_expiry_days'")
    op.drop_column("users", "password_changed_at")
