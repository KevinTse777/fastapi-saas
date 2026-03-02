from datetime import datetime
from pydantic import BaseModel


class ProjectCreateIn(BaseModel):
    name: str
    description: str | None = None


class ProjectOut(BaseModel):
    id: int
    workspace_id: int
    name: str
    description: str | None
    created_at: datetime
