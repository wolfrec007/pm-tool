"""add sa totp and license inventory

Revision ID: d3e4f5a6b7c8
Revises: b2c3d4e5f6a7
Create Date: 2026-07-27 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd3e4f5a6b7c8'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # SuperAdmin TOTP fields
    op.add_column('super_admins', sa.Column('totp_secret', sa.String(length=255), nullable=True))
    op.add_column('super_admins', sa.Column('totp_enabled', sa.Boolean(), nullable=False, server_default='false'))

    # License inventory table
    op.create_table(
        'license_inventory',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('license_key', sa.String(length=255), nullable=False),
        sa.Column('license_key_hash', sa.String(length=255), nullable=False),
        sa.Column('tier', sa.String(length=50), nullable=False),
        sa.Column('duration_days', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='available'),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('assigned_firm_id', sa.Integer(), sa.ForeignKey('firms.id'), nullable=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('generated_by_id', sa.Integer(), sa.ForeignKey('super_admins.id'), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_license_inventory_license_key', 'license_inventory', ['license_key'], unique=True)
    op.create_index('ix_license_inventory_license_key_hash', 'license_inventory', ['license_key_hash'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_license_inventory_license_key_hash', table_name='license_inventory')
    op.drop_index('ix_license_inventory_license_key', table_name='license_inventory')
    op.drop_table('license_inventory')
    op.drop_column('super_admins', 'totp_enabled')
    op.drop_column('super_admins', 'totp_secret')
