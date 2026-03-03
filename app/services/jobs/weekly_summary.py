from __future__ import annotations

from sqlalchemy.orm import Session

from app.services.tools.workspace_dashboard import get_workspace_dashboard_summary


def build_weekly_summary(db: Session, workspace_id: int) -> dict:
    dashboard = get_workspace_dashboard_summary(db, workspace_id)
    return {
        "headline": dashboard["summary"],
        "dashboard": dashboard["dashboard"],
    }
