"""
安全相关工具：
- 密码哈希/校验（bcrypt）
- JWT 生成/解析
- refresh rotation：refresh token 使用一次就作废（靠 Redis allowlist）
"""

from datetime import datetime, timedelta, timezone
import uuid

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.redis_client import redis_client

# bcrypt 密码哈希
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 你现在先用一个开发用 secret（建议 Day7 再改成从 env 读取，并且更复杂）
# 为了简化 Day2：直接写死。你也可以放进 .env 再读取。
JWT_SECRET = "dev_secret_change_me"
JWT_ALG = "HS256"

ACCESS_TTL_MIN = 15
REFRESH_TTL_DAYS = 7

# Redis key 前缀：refresh allowlist
REFRESH_KEY_PREFIX = "auth:refresh:"


def hash_password(password: str) -> str:
    """将明文密码哈希后存储。"""
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """校验明文密码是否匹配哈希。"""
    return pwd_context.verify(password, password_hash)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(user_id: int) -> str:
    """
    access token：短期有效，用于携带 user_id。
    """
    jti = str(uuid.uuid4())  # token 唯一 ID（可用于黑名单/追踪）
    exp = _now() + timedelta(minutes=ACCESS_TTL_MIN)
    payload = {"sub": str(user_id), "jti": jti, "type": "access", "exp": exp}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def create_refresh_token(user_id: int) -> str:
    """
    refresh token：长期有效，用于换取新的 access token。
    关键点：refresh rotation
    - 每次登录/刷新都生成新的 refresh token
    - 新 refresh 的 jti 写入 Redis allowlist
    - 旧 refresh 的 jti 删除/失效
    """
    jti = str(uuid.uuid4())
    exp = _now() + timedelta(days=REFRESH_TTL_DAYS)
    payload = {"sub": str(user_id), "jti": jti, "type": "refresh", "exp": exp}
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

    # 写入 allowlist：key = auth:refresh:{jti} -> user_id，设置 TTL
    key = f"{REFRESH_KEY_PREFIX}{jti}"
    ttl_seconds = int((exp - _now()).total_seconds())
    redis_client.setex(key, ttl_seconds, str(user_id))

    return token


def decode_token(token: str) -> dict:
    """解析 token，失败会抛 JWTError。"""
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])


def refresh_is_allowed(jti: str, user_id: int) -> bool:
    """
    检查 refresh token 是否在 allowlist 中。
    rotation 后，旧 token 的 jti 不在 allowlist，直接拒绝。
    """
    key = f"{REFRESH_KEY_PREFIX}{jti}"
    val = redis_client.get(key)
    return val == str(user_id)


def revoke_refresh(jti: str) -> None:
    """作废 refresh token：从 allowlist 删除。"""
    key = f"{REFRESH_KEY_PREFIX}{jti}"
    redis_client.delete(key)


def rotate_refresh(old_refresh_payload: dict) -> str:
    """
    refresh rotation：
    - 校验 old refresh 是否允许
    - 删除 old refresh jti
    - 生成新 refresh 并写入 allowlist
    """
    user_id = int(old_refresh_payload["sub"])
    old_jti = old_refresh_payload["jti"]

    if not refresh_is_allowed(old_jti, user_id):
        raise PermissionError("Refresh token is not allowed (maybe reused or revoked).")

    # 作废旧 refresh
    revoke_refresh(old_jti)

    # 生成新 refresh（自动写入 allowlist）
    return create_refresh_token(user_id)
