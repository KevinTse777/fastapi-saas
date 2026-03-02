"""
Workspace Dashboard API
- GET /workspaces/{workspace_id}/dashboard
返回该 workspace 的任务统计，并使用 Redis 缓存 60 秒
"""

from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, func, case

from app.db.session import get_db
from app.core.deps import get_current_user
from app.core.workspace_deps import require_workspace_member
from app.models.user import User
from app.models.project import Project
from app.models.task import Task, TaskStatus
from app.services.cache import (
    dashboard_key,
    cache_get_json,
    cache_set_json,
    DASHBOARD_TTL_SECONDS,
)

router = APIRouter(tags=["dashboard"])


@router.get("/workspaces/{workspace_id}/dashboard")
def workspace_dashboard(
    workspace_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Dashboard：
    1) 先查 Redis 缓存
    2) 缓存 miss → 查 DB 聚合 → 写缓存 → 返回
    """
    # ✅ 强制隔离：必须是成员才能看这个 workspace 的统计
    _ = require_workspace_member(workspace_id, db, user)

    key = dashboard_key(workspace_id)

    cached = cache_get_json(key)
    if cached is not None:
        # 标记命中缓存（便于你调试/演示）
        cached["_cached"] = True
        return cached

    # 找到该 workspace 下的所有 project_id
    project_ids_stmt = select(Project.id).where(Project.workspace_id == workspace_id)
    project_ids = [r[0] for r in db.execute(project_ids_stmt).all()]

    if not project_ids:
        result = {
            "workspace_id": workspace_id,
            "tasks_total": 0,
            "by_status": {"TODO": 0, "DOING": 0, "DONE": 0, "BLOCKED": 0},
            "overdue_count": 0,
        }
        cache_set_json(key, result, DASHBOARD_TTL_SECONDS)
        result["_cached"] = False
        return result

    # 总数 + 各状态计数（用 SQL 聚合）
    today = date.today()

    agg_stmt = select(
        func.count(Task.id).label("total"),
        func.sum(case((Task.status == TaskStatus.TODO, 1), else_=0)).label("todo"),
        func.sum(case((Task.status == TaskStatus.DOING, 1), else_=0)).label("doing"),
        func.sum(case((Task.status == TaskStatus.DONE, 1), else_=0)).label("done"),
        func.sum(case((Task.status == TaskStatus.BLOCKED, 1), else_=0)).label("blocked"),
        func.sum(
            case(
                (
                    (Task.due_date.is_not(None))
                    & (Task.due_date < today)
                    & (Task.status != TaskStatus.DONE),
                    1,
                ),
                else_=0,
            )
        ).label("overdue"),
    ).where(Task.project_id.in_(project_ids))

    row = db.execute(agg_stmt).one()

    result = {
        "workspace_id": workspace_id,
        "tasks_total": int(row.total or 0),
        "by_status": {
            "TODO": int(row.todo or 0),
            "DOING": int(row.doing or 0),
            "DONE": int(row.done or 0),
            "BLOCKED": int(row.blocked or 0),
        },
        "overdue_count": int(row.overdue or 0),
    }

    # 写入缓存
    cache_set_json(key, result, DASHBOARD_TTL_SECONDS)
    result["_cached"] = False
    return result
