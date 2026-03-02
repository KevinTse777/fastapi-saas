"""
缓存相关工具：
- 统一管理 Redis key
- 缓存读取/写入/失效
"""

import json
from typing import Any

from app.core.redis_client import redis_client

DASHBOARD_TTL_SECONDS = 60


def dashboard_key(workspace_id: int) -> str:
    """workspace dashboard 缓存 key"""
    return f"cache:ws:{workspace_id}:dashboard"


def cache_get_json(key: str) -> Any | None:
    """从 Redis 读取 JSON（取不到返回 None）"""
    val = redis_client.get(key)
    if not val:
        return None
    try:
        return json.loads(val)
    except json.JSONDecodeError:
        return None


def cache_set_json(key: str, obj: Any, ttl: int) -> None:
    """写入 JSON 到 Redis，并设置 TTL"""
    redis_client.setex(key, ttl, json.dumps(obj, default=str))


def cache_delete(key: str) -> None:
    """删除缓存 key"""
    redis_client.delete(key)
