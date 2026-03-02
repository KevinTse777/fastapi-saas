from datetime import datetime, date
from pydantic import BaseModel


class TaskCreateIn(BaseModel):
    title: str
    description: str | None = None
    priority: int = 0
    assignee_id: int | None = None
    due_date: date | None = None


class TaskOut(BaseModel):
    id: int
    project_id: int
    title: str
    description: str | None
    status: str
    priority: int
    assignee_id: int | None
    due_date: date | None
    created_at: datetime
    updated_at: datetime


class TaskUpdateIn(BaseModel):
    """
    更新任务（Day4 先支持几个常见字段）
    - status：状态流转
    - assignee_id：重新指派
    - priority/due_date/description：基本编辑
    """
    status: str | None = None
    assignee_id: int | None = None
    priority: int | None = None
    due_date: date | None = None
    description: str | None = None
