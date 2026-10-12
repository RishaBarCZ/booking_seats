"""Sync database schema with models.

Revision ID: 65b7f839aafa
Revises: a3f8c1d2e4b5
Create Date: 2026-06-09 09:22:58.269771

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = '65b7f839aafa'
down_revision: Union[str, Sequence[str], None] = 'a3f8c1d2e4b5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table_name: str, column_name: str) -> bool:
    return column_name in {column['name'] for column in inspect(op.get_bind()).get_columns(table_name)}


def _constraint_exists(table_name: str, constraint_name: str) -> bool:
    inspector = inspect(op.get_bind())
    constraints = [
        *inspector.get_unique_constraints(table_name),
        *inspector.get_check_constraints(table_name),
        *inspector.get_foreign_keys(table_name),
    ]
    return constraint_name in {constraint['name'] for constraint in constraints}


def _index_exists(table_name: str, index_name: str) -> bool:
    return index_name in {index['name'] for index in inspect(op.get_bind()).get_indexes(table_name)}


def _replace_foreign_key(
    table_name: str,
    constraint_name: str,
    referred_table: str,
    local_columns: list[str],
    remote_columns: list[str],
    *,
    ondelete: str,
) -> None:
    if _constraint_exists(table_name, constraint_name):
        op.drop_constraint(constraint_name, table_name, type_='foreignkey')
    op.create_foreign_key(
        constraint_name,
        table_name,
        referred_table,
        local_columns,
        remote_columns,
        ondelete=ondelete,
    )


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        'actions',
        'description',
        existing_type=sa.TEXT(),
        type_=sa.String(length=500),
        existing_nullable=False,
    )
    if not _constraint_exists('actions', op.f('uq_actions_description')):
        op.create_unique_constraint(op.f('uq_actions_description'), 'actions', ['description'])

    if not _column_exists('booking_table_slots', 'booking_date'):
        op.add_column('booking_table_slots', sa.Column('booking_date', sa.Date(), nullable=True))
        op.execute(
            sa.text(
                'UPDATE booking_table_slots AS slots '
                'SET booking_date = bookings.booking_date '
                'FROM bookings WHERE bookings.id = slots.booking_id',
            ),
        )
        op.alter_column('booking_table_slots', 'booking_date', nullable=False)

    if _constraint_exists('booking_table_slots', op.f('uq_booking_table_slot')):
        op.drop_constraint(op.f('uq_booking_table_slot'), 'booking_table_slots', type_='unique')
    if not _index_exists('booking_table_slots', 'ix_unique_booking_table_slot_date'):
        op.create_index(
            'ix_unique_booking_table_slot_date',
            'booking_table_slots',
            ['table_id', 'slot_id', 'booking_date'],
            unique=True,
            postgresql_where=sa.text('is_active'),
        )
    op.alter_column(
        'bookings',
        'note',
        existing_type=sa.TEXT(),
        type_=sa.String(length=255),
        nullable=False,
        server_default='',
    )
    op.alter_column(
        'bookings',
        'status',
        existing_type=sa.Enum('BOOKING', 'CANCELED', 'ACTIVE', 'COMPLETED', name='bookingstatus'),
        existing_nullable=False,
        server_default='BOOKING',
    )
    _replace_foreign_key(
        'cafe_actions',
        op.f('fk_cafe_actions_action_id_actions'),
        'actions',
        ['action_id'],
        ['id'],
        ondelete='RESTRICT',
    )
    _replace_foreign_key(
        'cafe_actions',
        op.f('fk_cafe_actions_cafe_id_cafes'),
        'cafes',
        ['cafe_id'],
        ['id'],
        ondelete='RESTRICT',
    )
    _replace_foreign_key(
        'cafe_dishes',
        op.f('fk_cafe_dishes_dish_id_dishes'),
        'dishes',
        ['dish_id'],
        ['id'],
        ondelete='RESTRICT',
    )
    _replace_foreign_key(
        'cafe_dishes',
        op.f('fk_cafe_dishes_cafe_id_cafes'),
        'cafes',
        ['cafe_id'],
        ['id'],
        ondelete='RESTRICT',
    )
    _replace_foreign_key(
        'cafe_managers',
        op.f('fk_cafe_managers_user_id_users'),
        'users',
        ['user_id'],
        ['id'],
        ondelete='RESTRICT',
    )
    _replace_foreign_key(
        'cafe_managers',
        op.f('fk_cafe_managers_cafe_id_cafes'),
        'cafes',
        ['cafe_id'],
        ['id'],
        ondelete='RESTRICT',
    )
    op.alter_column(
        'cafes',
        'description',
        existing_type=sa.TEXT(),
        type_=sa.String(length=2000),
        existing_nullable=True,
    )
    if not _constraint_exists('cafes', 'uq_cafe_name_address'):
        op.create_unique_constraint('uq_cafe_name_address', 'cafes', ['name', 'address'])
    op.alter_column(
        'dishes',
        'description',
        existing_type=sa.TEXT(),
        type_=sa.String(length=1000),
        existing_nullable=True,
    )
    if not _constraint_exists('dishes', op.f('uq_dishes_name')):
        op.create_unique_constraint(op.f('uq_dishes_name'), 'dishes', ['name'])
    if _column_exists('media', 'content_type'):
        op.drop_column('media', 'content_type')
    op.alter_column(
        'tables',
        'description',
        existing_type=sa.TEXT(),
        type_=sa.String(length=500),
        existing_nullable=True,
    )
    _replace_foreign_key(
        'tables',
        op.f('fk_tables_cafe_id_cafes'),
        'cafes',
        ['cafe_id'],
        ['id'],
        ondelete='RESTRICT',
    )
    op.alter_column(
        'time_slots',
        'description',
        existing_type=sa.TEXT(),
        type_=sa.String(length=500),
        existing_nullable=True,
    )
    _replace_foreign_key(
        'time_slots',
        op.f('fk_time_slots_cafe_id_cafes'),
        'cafes',
        ['cafe_id'],
        ['id'],
        ondelete='RESTRICT',
    )

    check_constraints = (
        ('bookings', op.f('ck_bookings_ck_bookings_guest_number_positive'), 'guest_number > 0'),
        ('cafes', op.f('ck_cafes_ck_cafe_phone_format'), r"phone ~ '^\+?[0-9][0-9 \-\(\)]{5,}$'"),
        ('dishes', op.f('ck_dishes_ck_dish_price_non_negative'), 'price >= 0'),
        ('tables', op.f('ck_tables_ck_table_seat_number_positive'), 'seat_number > 0'),
        ('time_slots', op.f('ck_time_slots_ck_time_slot_start_before_end'), 'start_time < end_time'),
        ('users', op.f('ck_users_ck_user_email_or_phone'), 'email IS NOT NULL OR phone IS NOT NULL'),
        ('users', op.f('ck_users_ck_user_email_format'), r"email IS NULL OR email ~ '^[^@]+@[^@]+\.[^@]+$'"),
        (
            'users',
            op.f('ck_users_ck_user_phone_format'),
            r"phone IS NULL OR phone ~ '^\+?[0-9][0-9 \-\(\)]{5,}$'",
        ),
    )
    for table_name, constraint_name, condition in check_constraints:
        if not _constraint_exists(table_name, constraint_name):
            op.create_check_constraint(constraint_name, table_name, condition)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(op.f('ck_users_ck_user_phone_format'), 'users', type_='check')
    op.drop_constraint(op.f('ck_users_ck_user_email_format'), 'users', type_='check')
    op.drop_constraint(op.f('ck_users_ck_user_email_or_phone'), 'users', type_='check')
    op.drop_constraint(op.f('ck_time_slots_ck_time_slot_start_before_end'), 'time_slots', type_='check')
    op.drop_constraint(op.f('ck_tables_ck_table_seat_number_positive'), 'tables', type_='check')
    op.drop_constraint(op.f('ck_dishes_ck_dish_price_non_negative'), 'dishes', type_='check')
    op.drop_constraint(op.f('ck_cafes_ck_cafe_phone_format'), 'cafes', type_='check')
    op.drop_constraint(op.f('ck_bookings_ck_bookings_guest_number_positive'), 'bookings', type_='check')

    op.drop_constraint(op.f('fk_time_slots_cafe_id_cafes'), 'time_slots', type_='foreignkey')
    op.create_foreign_key(
        op.f('fk_time_slots_cafe_id_cafes'),
        'time_slots',
        'cafes',
        ['cafe_id'],
        ['id'],
        ondelete='CASCADE',
    )
    op.alter_column(
        'time_slots',
        'description',
        existing_type=sa.String(length=500),
        type_=sa.TEXT(),
        existing_nullable=True,
    )
    op.drop_constraint(op.f('fk_tables_cafe_id_cafes'), 'tables', type_='foreignkey')
    op.create_foreign_key(
        op.f('fk_tables_cafe_id_cafes'),
        'tables',
        'cafes',
        ['cafe_id'],
        ['id'],
        ondelete='CASCADE',
    )
    op.alter_column(
        'tables',
        'description',
        existing_type=sa.String(length=500),
        type_=sa.TEXT(),
        existing_nullable=True,
    )
    op.add_column(
        'media',
        sa.Column(
            'content_type',
            sa.VARCHAR(length=100),
            autoincrement=False,
            nullable=False,
            server_default='application/octet-stream',
        ),
    )
    op.alter_column('media', 'content_type', server_default=None)
    op.drop_constraint(op.f('uq_dishes_name'), 'dishes', type_='unique')
    op.alter_column(
        'dishes',
        'description',
        existing_type=sa.String(length=1000),
        type_=sa.TEXT(),
        existing_nullable=True,
    )
    op.drop_constraint('uq_cafe_name_address', 'cafes', type_='unique')
    op.alter_column(
        'cafes',
        'description',
        existing_type=sa.String(length=2000),
        type_=sa.TEXT(),
        existing_nullable=True,
    )
    op.drop_constraint(op.f('fk_cafe_managers_cafe_id_cafes'), 'cafe_managers', type_='foreignkey')
    op.drop_constraint(op.f('fk_cafe_managers_user_id_users'), 'cafe_managers', type_='foreignkey')
    op.create_foreign_key(
        op.f('fk_cafe_managers_user_id_users'),
        'cafe_managers',
        'users',
        ['user_id'],
        ['id'],
        ondelete='CASCADE',
    )
    op.create_foreign_key(
        op.f('fk_cafe_managers_cafe_id_cafes'),
        'cafe_managers',
        'cafes',
        ['cafe_id'],
        ['id'],
        ondelete='CASCADE',
    )
    op.drop_constraint(op.f('fk_cafe_dishes_cafe_id_cafes'), 'cafe_dishes', type_='foreignkey')
    op.drop_constraint(op.f('fk_cafe_dishes_dish_id_dishes'), 'cafe_dishes', type_='foreignkey')
    op.create_foreign_key(
        op.f('fk_cafe_dishes_cafe_id_cafes'),
        'cafe_dishes',
        'cafes',
        ['cafe_id'],
        ['id'],
        ondelete='CASCADE',
    )
    op.create_foreign_key(
        op.f('fk_cafe_dishes_dish_id_dishes'),
        'cafe_dishes',
        'dishes',
        ['dish_id'],
        ['id'],
        ondelete='CASCADE',
    )
    op.drop_constraint(op.f('fk_cafe_actions_cafe_id_cafes'), 'cafe_actions', type_='foreignkey')
    op.drop_constraint(op.f('fk_cafe_actions_action_id_actions'), 'cafe_actions', type_='foreignkey')
    op.create_foreign_key(
        op.f('fk_cafe_actions_cafe_id_cafes'),
        'cafe_actions',
        'cafes',
        ['cafe_id'],
        ['id'],
        ondelete='CASCADE',
    )
    op.create_foreign_key(
        op.f('fk_cafe_actions_action_id_actions'),
        'cafe_actions',
        'actions',
        ['action_id'],
        ['id'],
        ondelete='CASCADE',
    )
    op.alter_column(
        'bookings',
        'note',
        existing_type=sa.String(length=255),
        type_=sa.TEXT(),
        nullable=True,
        server_default=None,
    )
    op.alter_column(
        'bookings',
        'status',
        existing_type=sa.Enum('BOOKING', 'CANCELED', 'ACTIVE', 'COMPLETED', name='bookingstatus'),
        existing_nullable=False,
        server_default=None,
    )
    op.drop_index(
        'ix_unique_booking_table_slot_date',
        table_name='booking_table_slots',
        postgresql_where=sa.text('is_active'),
    )
    op.create_unique_constraint(
        op.f('uq_booking_table_slot'),
        'booking_table_slots',
        ['table_id', 'slot_id', 'booking_id'],
        postgresql_nulls_not_distinct=False,
    )
    op.drop_column('booking_table_slots', 'booking_date')
    op.drop_constraint(op.f('uq_actions_description'), 'actions', type_='unique')
    op.alter_column(
        'actions',
        'description',
        existing_type=sa.String(length=500),
        type_=sa.TEXT(),
        existing_nullable=False,
    )
