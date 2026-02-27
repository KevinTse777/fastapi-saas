from fastapi import FastAPI

from app.core.config import settings
from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.users import router as users_router


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)

    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(users_router)

    return app


app = create_app()
