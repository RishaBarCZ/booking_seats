"""Add cafe_id to users.

Revision ID: a3f8c1d2e4b5
Revises: 619fccd2d803
Create Date: 2026-06-09 06:20:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = 'a3f8c1d2e4b5'
down_revision: Union[str, Sequence[str], None] = '619fccd2d803'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = inspect(bind)

    columns = {column['name'] for column in inspector.get_columns('users')}
    if 'cafe_id' not in columns:
        op.add_column('users', sa.Column('cafe_id', sa.Integer(), nullable=True))

    foreign_keys = {foreign_key['name'] for foreign_key in inspect(bind).get_foreign_keys('users')}
    if 'fk_users_cafe_id_cafes' not in foreign_keys:
        op.create_foreign_key(
            'fk_users_cafe_id_cafes',
            'users',
            'cafes',
            ['cafe_id'],
            ['id'],
            ondelete='SET NULL',
        )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_users_cafe_id_cafes', 'users', type_='foreignkey')
    op.drop_column('users', 'cafe_id')
