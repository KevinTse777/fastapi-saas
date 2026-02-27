"""
Redis 客户端（同步版）
Day2 我们主要用它来保存 refresh token 的 allowlist（按 jti）。
"""

import redis
from app.core.config import settings

# decode_responses=True：让返回值是 str 而不是 bytes，写代码更省心
redis_client = redis.Redis.from_url(settings.redis_dsn, decode_responses=True)
