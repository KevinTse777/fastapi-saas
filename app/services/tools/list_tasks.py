from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.task import Task


def list_project_tasks(db: Session, project_id: int) -> dict:
    tasks = db.execute(
        select(Task).where(Task.project_id == project_id).order_by(Task.id.desc()).limit(20)
    ).scalars().all()
    items = [
        {
            "id": task.id,
            "title": task.title,
            "status": task.status.value,
            "priority": task.priority,
            "due_date": task.due_date.isoformat() if task.due_date else None,
        }
        for task in tasks
    ]
    return {
        "tool_name": "list_project_tasks",
        "summary": f"Loaded {len(items)} tasks from the project.",
        "tasks": items,
    }
