"""
Task API（Day4 Step2）
- POST /projects/{project_id}/tasks：创建任务（必须是该 project 所属 workspace 的成员）
- GET  /projects/{project_id}/tasks：列出任务（同上）
- PATCH /tasks/{task_id}：更新任务（通过 task -> project -> workspace 做隔离校验）
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.task import Task, TaskStatus
from app.schemas.task import TaskCreateIn, TaskOut, TaskUpdateIn
from app.services.projects import get_project_and_require_member
from app.services.cache import cache_delete, dashboard_key
from app.models.project import Project  # 为了拿 workspace_id（也可通过查询 project）
router = APIRouter(tags=["tasks"])


@router.post("/projects/{project_id}/tasks", response_model=TaskOut, status_code=201)
def create_task(
    project_id: int,
    payload: TaskCreateIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # 1) project 必须存在 + 当前用户必须是 project 所属 workspace 成员
    _project = get_project_and_require_member(project_id, db, user)

    # 2) 创建任务
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
    db.refresh(t)

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
    列出任务（支持过滤/分页/排序）
    Query Params:
    - status: TODO/DOING/DONE/BLOCKED
    - assignee_id: 指派人过滤
    - limit/offset: 分页
    - order: asc/desc（按 id）
    """

    # project 存在 + 成员校验（强制隔离）
    _project = get_project_and_require_member(project_id, db, user)

    # 参数保护：避免用户传很大的 limit 把库打爆
    limit = max(1, min(limit, 100))
    offset = max(0, offset)

    stmt = select(Task).where(Task.project_id == project_id)

    # status 过滤
    if status is not None:
        try:
            st = TaskStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status. Use TODO/DOING/DONE/BLOCKED",
            )
        stmt = stmt.where(Task.status == st)

    # assignee 过滤
    if assignee_id is not None:
        stmt = stmt.where(Task.assignee_id == assignee_id)

    # 排序
    if order.lower() == "asc":
        stmt = stmt.order_by(Task.id.asc())
    else:
        stmt = stmt.order_by(Task.id.desc())

    # 分页
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


def _load_task_and_require_member(task_id: int, db: Session, user: User) -> Task:
    """
    通过 task_id 加载任务，并通过 task -> project 做 workspace 隔离校验。
    """
    t = db.execute(select(Task).where(Task.id == task_id)).scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")

    # 关键：通过 project_id 验证成员身份
    _project = get_project_and_require_member(t.project_id, db, user)

    return t


@router.patch("/tasks/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    payload: TaskUpdateIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    t = _load_task_and_require_member(task_id, db, user)

    # 更新字段（只更新用户提供的字段）
    if payload.description is not None:
        t.description = payload.description
    if payload.priority is not None:
        t.priority = payload.priority
    if payload.assignee_id is not None:
        t.assignee_id = payload.assignee_id
    if payload.due_date is not None:
        t.due_date = payload.due_date

    # 状态更新：做简单校验
    if payload.status is not None:
        try:
            t.status = TaskStatus(payload.status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status. Use TODO/DOING/DONE/BLOCKED",
            )

    db.commit()
    db.refresh(t)

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
