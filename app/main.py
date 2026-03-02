from fastapi import FastAPI

from app.core.config import settings
from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.workspaces import router as workspaces_router
from app.api.invites import router as invites_router
from app.api.projects import router as projects_router
from app.api.tasks import router as tasks_router
from app.api.dashboard import router as dashboard_router


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)

    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(users_router)
    app.include_router(workspaces_router)
    app.include_router(invites_router)
    app.include_router(projects_router)
    app.include_router(tasks_router)
    app.include_router(dashboard_router)

    return app


app = create_app()
