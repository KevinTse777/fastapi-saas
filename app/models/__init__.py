# 统一导入所有模型，确保 Alembic autogenerate 能发现表结构

from app.models.user import User  # noqa: F401
from app.models.workspace import Workspace, WorkspaceMember, Invite  # noqa: F401
