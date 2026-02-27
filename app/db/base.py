"""
Base 用于声明 ORM 模型。
Alembic 需要通过 Base.metadata 识别所有表结构。
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
