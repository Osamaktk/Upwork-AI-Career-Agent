from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    auth,
    claims,
    clients,
    dashboard,
    development,
    evaluations,
    health,
    jobs,
    portfolio,
    profile,
)
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Sample-data-first, human-controlled freelancing workflow API",
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(health.router)
    application.include_router(auth.router, prefix=settings.api_v1_prefix)
    application.include_router(profile.router, prefix=settings.api_v1_prefix)
    application.include_router(claims.router, prefix=settings.api_v1_prefix)
    application.include_router(portfolio.router, prefix=settings.api_v1_prefix)
    application.include_router(jobs.router, prefix=settings.api_v1_prefix)
    application.include_router(clients.router, prefix=settings.api_v1_prefix)
    application.include_router(evaluations.router, prefix=settings.api_v1_prefix)
    application.include_router(dashboard.router, prefix=settings.api_v1_prefix)
    application.include_router(development.router, prefix=settings.api_v1_prefix)
    return application


app = create_app()
