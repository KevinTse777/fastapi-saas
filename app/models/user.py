"""
用户表：只做最小字段，够 Day2 认证体系使用。
后续 Day3 再加 workspace 相关字段/关系。
"""

from datetime import datetime

from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    # 主键：用自增 int，简单可靠
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 邮箱：登录唯一标识，做唯一索引
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)

    # 密码哈希：绝对不要存明文
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # 显示名（可选）
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # 创建时间：由数据库生成
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
