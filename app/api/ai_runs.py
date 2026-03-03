from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.agent_run import AgentMessage, AgentRun
from app.models.user import User
from app.models.workspace import WorkspaceRole
from app.schemas.ai_agent import AgentRunOut, AgentToolCallOut
from app.services.projects import get_project_and_require_role

router = APIRouter(tags=["ai-runs"])


@router.get("/agent-runs/{run_id}", response_model=AgentRunOut)
def get_agent_run(
    run_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    run = db.execute(select(AgentRun).where(AgentRun.id == run_id)).scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")

    _ = get_project_and_require_role(run.project_id, WorkspaceRole.GUEST, db, user)
    messages = (
        db.query(AgentMessage)
        .filter(AgentMessage.run_id == run.id)
        .order_by(AgentMessage.step_index.asc(), AgentMessage.id.asc())
        .all()
    )
    return AgentRunOut(
        id=run.id,
        workspace_id=run.workspace_id,
        project_id=run.project_id,
        triggered_by=run.triggered_by,
        goal=run.goal,
        status=run.status.value,
        trace_id=run.trace_id,
        final_output=run.final_output,
        error_message=run.error_message,
        audit_ref=run.audit_log_id,
        tool_calls=[
            AgentToolCallOut(
                step_index=message.step_index,
                tool_name=message.tool_name,
                content=message.content,
                tool_input=message.tool_input_json,
                tool_output=message.tool_output_json,
                created_at=message.created_at,
            )
            for message in messages
        ],
        started_at=run.started_at,
        finished_at=run.finished_at,
        created_at=run.created_at,
    )
