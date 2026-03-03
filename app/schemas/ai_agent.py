from datetime import datetime, date

from pydantic import BaseModel, Field


class AITaskDraftItem(BaseModel):
    title: str
    description: str
    priority: int = 0
    due_date: date | None = None
    rationale: str


class AITaskDraftRequestIn(BaseModel):
    requirement: str = Field(min_length=5, max_length=5000)
    document_ids: list[int] = Field(default_factory=list)


class AITaskDraftResponseOut(BaseModel):
    project_id: int
    trace_id: str
    drafts: list[AITaskDraftItem]


class CreateTasksFromDraftIn(BaseModel):
    drafts: list[AITaskDraftItem]


class AgentRunCreateIn(BaseModel):
    goal: str = Field(min_length=5, max_length=3000)


class AgentToolCallOut(BaseModel):
    step_index: int
    tool_name: str | None
    content: str
    tool_input: dict | None
    tool_output: dict | None
    created_at: datetime


class AgentRunOut(BaseModel):
    id: int
    workspace_id: int
    project_id: int
    triggered_by: int
    goal: str
    status: str
    trace_id: str
    final_output: str | None
    error_message: str | None
    audit_ref: int | None
    tool_calls: list[AgentToolCallOut]
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
