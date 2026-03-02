from datetime import datetime
from pydantic import BaseModel, EmailStr


class WorkspaceCreateIn(BaseModel):
    # 创建 workspace 的输入
    name: str


class WorkspaceOut(BaseModel):
    id: int
    name: str
    owner_id: int
    created_at: datetime


class MemberOut(BaseModel):
    user_id: int
    role: str
    created_at: datetime


class InviteCreateIn(BaseModel):
    # 邀请某个邮箱加入 workspace
    email: EmailStr
    # 先默认 MEMBER；Day5 再做更细权限
    role: str = "MEMBER"


class InviteOut(BaseModel):
    id: int
    workspace_id: int
    email: EmailStr
    token: str
    status: str
    expires_at: datetime
    created_at: datetime
    role: str


class InviteAcceptIn(BaseModel):
    token: str


class WorkspaceMeOut(BaseModel):
    workspace_id: int
    user_id: int
    role: str
    created_at: datetime