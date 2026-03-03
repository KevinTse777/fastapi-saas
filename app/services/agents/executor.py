from __future__ import annotations

from app.services.tools.create_task_draft import create_task_draft
from app.services.tools.list_tasks import list_project_tasks
from app.services.tools.search_knowledge import search_knowledge
from app.services.tools.workspace_dashboard import get_workspace_dashboard_summary


def execute_tool(
    tool_name: str,
    *,
    db,
    workspace_id: int,
    project_id: int,
    goal: str,
) -> dict:
    if tool_name == "search_knowledge":
        return search_knowledge(db, workspace_id=workspace_id, query=goal, top_k=3)
    if tool_name == "list_project_tasks":
        return list_project_tasks(db, project_id=project_id)
    if tool_name == "summarize_workspace_dashboard":
        return get_workspace_dashboard_summary(db, workspace_id=workspace_id)
    if tool_name == "create_task_draft":
        return create_task_draft(
            db,
            workspace_id=workspace_id,
            project_id=project_id,
            requirement=goal,
        )
    raise ValueError(f"Unsupported tool: {tool_name}")
