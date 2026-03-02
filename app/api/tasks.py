"""
Task API（RBAC 版）
- POST /projects/{project_id}/tasks：创建任务（MEMBER+）
- GET  /projects/{project_id}/tasks：列出任务（GUEST+，支持过滤/分页/排序）
- PATCH /tasks/{task_id}：更新任务（MEMBER+）
并且保持：dashboard 缓存失效（create/patch 后删除缓存 key）
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.task import Task, TaskStatus
from app.models.workspace import WorkspaceRole
from app.schemas.task import TaskCreateIn, TaskOut, TaskUpdateIn
from app.services.projects import get_project_and_require_role
from app.services.cache import cache_delete, dashboard_key
from app.services.audit import write_audit

router = APIRouter(tags=["tasks"])


@router.post("/projects/{project_id}/tasks", response_model=TaskOut, status_code=201)
def create_task(
    project_id: int,
    payload: TaskCreateIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # ✅ 写操作：至少 MEMBER
    project = get_project_and_require_role(project_id, WorkspaceRole.MEMBER, db, user)

    t = Task(
        project_id=project_id,
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        assignee_id=payload.assignee_id,
        due_date=payload.due_date,
        status=TaskStatus.TODO,
    )
    db.add(t)
    db.commit()
    write_audit(
        db=db,
        workspace_id=project.workspace_id,
        actor_id=user.id,
        action="TASK_CREATE",
        entity_type="task",
        entity_id=t.id,
        meta={"title": t.title, "project_id": t.project_id},
    )
    db.commit()
    db.refresh(t)

    # ✅ 缓存失效：任务变更后删 dashboard 缓存
    cache_delete(dashboard_key(project.workspace_id))

    return TaskOut(
        id=t.id,
        project_id=t.project_id,
        title=t.title,
        description=t.description,
        status=t.status.value,
        priority=t.priority,
        assignee_id=t.assignee_id,
        due_date=t.due_date,
        created_at=t.created_at,
        updated_at=t.updated_at,
    )


@router.get("/projects/{project_id}/tasks", response_model=list[TaskOut])
def list_tasks(
    project_id: int,
    status: str | None = None,
    assignee_id: int | None = None,
    limit: int = 20,
    offset: int = 0,
    order: str = "desc",
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    列出任务（读操作：GUEST+）
    Query Params:
    - status: TODO/DOING/DONE/BLOCKED
    - assignee_id: 指派人过滤
    - limit/offset: 分页
    - order: asc/desc（按 id）
    """
    # ✅ 读操作：GUEST 就能读（只要是成员）
    _project = get_project_and_require_role(project_id, WorkspaceRole.GUEST, db, user)

    # 参数保护
    limit = max(1, min(limit, 100))
    offset = max(0, offset)

    stmt = select(Task).where(Task.project_id == project_id)

    if status is not None:
        try:
            st = TaskStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status. Use TODO/DOING/DONE/BLOCKED",
            )
        stmt = stmt.where(Task.status == st)

    if assignee_id is not None:
        stmt = stmt.where(Task.assignee_id == assignee_id)

    if order.lower() == "asc":
        stmt = stmt.order_by(Task.id.asc())
    else:
        stmt = stmt.order_by(Task.id.desc())

    stmt = stmt.limit(limit).offset(offset)

    rows = db.execute(stmt).scalars().all()

    return [
        TaskOut(
            id=t.id,
            project_id=t.project_id,
            title=t.title,
            description=t.description,
            status=t.status.value,
            priority=t.priority,
            assignee_id=t.assignee_id,
            due_date=t.due_date,
            created_at=t.created_at,
            updated_at=t.updated_at,
        )
        for t in rows
    ]


def _load_task_and_require_role(task_id: int, min_role: WorkspaceRole, db: Session, user: User) -> tuple[Task, int]:
    """
    通过 task_id 加载任务，并通过 task -> project 做 RBAC 校验。
    返回：(task, workspace_id) 方便做缓存失效。
    """
    t = db.execute(select(Task).where(Task.id == task_id)).scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")

    project = get_project_and_require_role(t.project_id, min_role, db, user)
    return t, project.workspace_id


@router.patch("/tasks/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    payload: TaskUpdateIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # ✅ 写操作：至少 MEMBER
    t, workspace_id = _load_task_and_require_role(task_id, WorkspaceRole.MEMBER, db, user)

    if payload.description is not None:
        t.description = payload.description
    if payload.priority is not None:
        t.priority = payload.priority
    if payload.assignee_id is not None:
        t.assignee_id = payload.assignee_id
    if payload.due_date is not None:
        t.due_date = payload.due_date

    if payload.status is not None:
        try:
            t.status = TaskStatus(payload.status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status. Use TODO/DOING/DONE/BLOCKED",
            )
    old_status = t.status.value
    db.commit()
    db.refresh(t)
    write_audit(
        db=db,
        workspace_id=workspace_id,
        actor_id=user.id,
        action="TASK_UPDATE",
        entity_type="task",
        entity_id=t.id,
        meta={"old_status": old_status, "new_status": t.status.value},
    )
    db.commit()

    # ✅ 缓存失效：任务更新后删 dashboard 缓存
    cache_delete(dashboard_key(workspace_id))

    return TaskOut(
        id=t.id,
        project_id=t.project_id,
        title=t.title,
        description=t.description,
        status=t.status.value,
        priority=t.priority,
        assignee_id=t.assignee_id,
        due_date=t.due_date,
        created_at=t.created_at,
        updated_at=t.updated_at,
    )
