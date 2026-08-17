import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

import app.db.base  # noqa: F401
from app.api.routes.ai import router as ai_router
from app.api.routes.auth import router as auth_router
from app.api.routes.images import router as images_router
from app.api.routes.inspections import router as inspections_router
from app.api.routes.reviews import router as reviews_router
from app.api.routes.reports import router as reports_router
from app.api.routes.vehicles import router as vehicles_router
from app.core.config import get_settings
from app.core.logging_config import setup_logging
from app.db.database import check_database_connection

setup_logging()

settings = get_settings()
logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    logger.info(
        "Starting %s version %s in %s mode",
        settings.app_name,
        settings.app_version,
        settings.app_env,
    )
    yield
    logger.info("Stopping %s", application.title)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")
app.include_router(vehicles_router, prefix="/api")
app.include_router(inspections_router, prefix="/api")
app.include_router(images_router, prefix="/api")
app.include_router(ai_router, prefix="/api")
app.include_router(reviews_router, prefix="/api")
app.include_router(reports_router, prefix="/api")


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    if isinstance(exc.detail, dict) and "success" in exc.detail:
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail,
            headers=exc.headers,
        )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": "Request failed.",
            "error": str(exc.detail),
        },
        headers=exc.headers,
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(
    request: Request,
    exc: SQLAlchemyError,
) -> JSONResponse:
    logger.exception("Database operation failed")
    return JSONResponse(
        status_code=503,
        content={
            "success": False,
            "message": "Database operation failed.",
            "error": exc.__class__.__name__,
        },
    )


@app.get("/", tags=["System"])
def root() -> dict[str, object]:
    return {
        "success": True,
        "message": "AI Vehicle Damage Inspection API is running.",
        "data": {
            "app_name": settings.app_name,
            "version": settings.app_version,
            "docs_url": "/docs",
            "health_url": "/health",
            "database_health_url": "/health/database",
        },
    }


@app.get("/health", tags=["System"])
def health_check() -> dict[str, object]:
    return {
        "success": True,
        "message": "Application is healthy.",
        "data": {
            "status": "ok",
            "environment": settings.app_env,
            "debug": settings.debug,
        },
    }


@app.get("/health/database", tags=["System"], response_model=None)
def database_health_check() -> dict[str, object] | JSONResponse:
    try:
        check_database_connection()
    except SQLAlchemyError as exc:
        logger.exception("Database health check failed")
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "message": "Database connection failed.",
                "error": exc.__class__.__name__,
            },
        )

    return {
        "success": True,
        "message": "Database connection is healthy.",
        "data": {
            "status": "ok",
            "database": "connected",
        },
    }
