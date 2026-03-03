from __future__ import annotations

from datetime import date

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.task import Task, TaskStatus


def get_workspace_dashboard_summary(db: Session, workspace_id: int) -> dict:
    project_ids = [
        row[0]
        for row in db.execute(select(Project.id).where(Project.workspace_id == workspace_id)).all()
    ]
    if not project_ids:
        return {
            "tool_name": "summarize_workspace_dashboard",
            "summary": "Workspace has no projects yet.",
            "dashboard": {
                "tasks_total": 0,
                "overdue_count": 0,
                "by_status": {"TODO": 0, "DOING": 0, "DONE": 0, "BLOCKED": 0},
            },
        }

    today = date.today()
    row = db.execute(
        select(
            func.count(Task.id).label("total"),
            func.sum(case((Task.status == TaskStatus.TODO, 1), else_=0)).label("todo"),
            func.sum(case((Task.status == TaskStatus.DOING, 1), else_=0)).label("doing"),
            func.sum(case((Task.status == TaskStatus.DONE, 1), else_=0)).label("done"),
            func.sum(case((Task.status == TaskStatus.BLOCKED, 1), else_=0)).label("blocked"),
            func.sum(
                case(
                    ((Task.due_date.is_not(None)) & (Task.due_date < today) & (Task.status != TaskStatus.DONE), 1),
                    else_=0,
                )
            ).label("overdue"),
        ).where(Task.project_id.in_(project_ids))
    ).one()

    dashboard = {
        "tasks_total": int(row.total or 0),
        "overdue_count": int(row.overdue or 0),
        "by_status": {
            "TODO": int(row.todo or 0),
            "DOING": int(row.doing or 0),
            "DONE": int(row.done or 0),
            "BLOCKED": int(row.blocked or 0),
        },
    }
    return {
        "tool_name": "summarize_workspace_dashboard",
        "summary": f"Workspace has {dashboard['tasks_total']} tasks and {dashboard['overdue_count']} overdue items.",
        "dashboard": dashboard,
    }
