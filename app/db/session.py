"""
数据库会话管理（SQLAlchemy 2.0）
- engine：数据库连接池
- SessionLocal：会话工厂
- get_db：FastAPI 依赖注入，用于自动关闭 session
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings

# 创建数据库引擎（连接 MySQL）
# pool_pre_ping=True：避免 MySQL 连接被服务器断开后出现“失效连接”
engine = create_engine(
    settings.mysql_dsn,
    pool_pre_ping=True,
)

# 创建会话工厂：每个请求拿一个 Session，用完关闭
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    """
    FastAPI 依赖：在路由函数里用 `db: Session = Depends(get_db)`
    这样每次请求都会获得一个 Session，并在请求结束后自动关闭。
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
