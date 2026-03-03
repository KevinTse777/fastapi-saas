from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.logging import new_trace_id
from app.db.session import get_db
from app.models.agent_run import AgentMessage, AgentMessageRole, AgentRun, AgentRunStatus
from app.models.user import User
from app.schemas.ai_agent import AgentRunCreateIn, AgentRunOut, AgentToolCallOut
from app.services.agents.graph import run_controlled_agent
from app.services.projects import get_project_and_require_role
from app.models.workspace import WorkspaceRole
from app.services.audit import write_audit

router = APIRouter(tags=["ai-agents"])


def _serialize_run(run: AgentRun, messages: list[AgentMessage]) -> AgentRunOut:
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


@router.post("/projects/{project_id}/agent-runs", response_model=AgentRunOut, status_code=201)
def create_agent_run(
    project_id: int,
    payload: AgentRunCreateIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = get_project_and_require_role(project_id, WorkspaceRole.MEMBER, db, user)
    trace_id = new_trace_id()
    run = AgentRun(
        workspace_id=project.workspace_id,
        project_id=project_id,
        triggered_by=user.id,
        goal=payload.goal,
        status=AgentRunStatus.RUNNING,
        trace_id=trace_id,
        started_at=datetime.now(timezone.utc),
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    db.add(
        AgentMessage(
            run_id=run.id,
            role=AgentMessageRole.USER,
            content=payload.goal,
            step_index=0,
        )
    )
    db.commit()

    try:
        tool_outputs, final_output = run_controlled_agent(
            db=db,
            workspace_id=project.workspace_id,
            project_id=project_id,
            goal=payload.goal,
        )
        for index, output in enumerate(tool_outputs, start=1):
            db.add(
                AgentMessage(
                    run_id=run.id,
                    role=AgentMessageRole.TOOL,
                    content=output["summary"],
                    tool_name=output["tool_name"],
                    step_index=index,
                    tool_input_json={"goal": payload.goal, "project_id": project_id},
                    tool_output_json=output,
                )
            )

        db.add(
            AgentMessage(
                run_id=run.id,
                role=AgentMessageRole.ASSISTANT,
                content=final_output,
                step_index=len(tool_outputs) + 1,
            )
        )
        db.commit()

        audit_log = write_audit(
            db=db,
            workspace_id=project.workspace_id,
            actor_id=user.id,
            action="AGENT_RUN_EXECUTE",
            entity_type="agent_run",
            entity_id=run.id,
            meta={"trace_id": trace_id, "project_id": project_id, "steps": len(tool_outputs)},
        )
        db.commit()
        db.refresh(audit_log)

        run.status = AgentRunStatus.SUCCESS
        run.final_output = final_output
        run.audit_log_id = audit_log.id
        run.finished_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(run)
    except Exception as exc:
        run.status = AgentRunStatus.FAILED
        run.error_message = str(exc)
        run.finished_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(run)

    messages = (
        db.query(AgentMessage)
        .filter(AgentMessage.run_id == run.id)
        .order_by(AgentMessage.step_index.asc(), AgentMessage.id.asc())
        .all()
    )
    return _serialize_run(run, messages)
