from sqlalchemy import Column, ForeignKey, Integer, Table

from core.base_model import Base

cafe_dishes = Table(
    'cafe_dishes',
    Base.metadata,
    Column('cafe_id', Integer, ForeignKey('cafes.id', ondelete='RESTRICT'), primary_key=True),
    Column('dish_id', Integer, ForeignKey('dishes.id', ondelete='RESTRICT'), primary_key=True),
)

cafe_actions = Table(
    'cafe_actions',
    Base.metadata,
    Column('cafe_id', Integer, ForeignKey('cafes.id', ondelete='RESTRICT'), primary_key=True),
    Column('action_id', Integer, ForeignKey('actions.id', ondelete='RESTRICT'), primary_key=True),
)

cafe_managers = Table(
    'cafe_managers',
    Base.metadata,
    Column('cafe_id', Integer, ForeignKey('cafes.id', ondelete='RESTRICT'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id', ondelete='RESTRICT'), primary_key=True),
)
