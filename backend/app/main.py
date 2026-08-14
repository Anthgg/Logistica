import logging
import os
from asyncio import to_thread
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.models.registry  # noqa: F401
from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.middleware.locale import LocaleMiddleware
from app.middleware.request_logging import RequestLoggingMiddleware
from app.services.audit_service import AuditService
from app.services.model_loader_service import ModelLoaderService
from app.database.session import SessionLocal

configure_logging(settings.LOG_LEVEL)
logger = logging.getLogger("app.lifecycle")


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    logger.info(
        "Service started | name=%s | version=%s | environment=%s",
        settings.APP_NAME,
        settings.APP_VERSION,
        settings.APP_ENV,
    )
    loader = ModelLoaderService(settings)
    application.state.model_loader = loader
    event_type = "MODEL_REGISTRY_LOADED"
    try:
        await to_thread(loader.startup)
        if loader.status.global_status in {"unavailable", "degraded"}:
            event_type = "MODEL_REGISTRY_FAILED"
        _audit_model_lifecycle(event_type, loader.status.global_status)
        if loader.snapshot is not None:
            _audit_model_lifecycle(
                "MODEL_ARTIFACT_VALIDATED",
                f"{len(loader.snapshot.models)}_registered_models",
            )
        if "MODEL_ARTIFACT_INVALID" in loader.status.errors:
            _audit_model_lifecycle(
                "MODEL_ARTIFACT_REJECTED",
                "artifact_validation_failed",
            )
        yield
    except Exception:
        _audit_model_lifecycle("MODEL_REGISTRY_FAILED", "startup_failed")
        raise
    finally:
        loader.shutdown()
        logger.info("Service stopped | name=%s", settings.APP_NAME)


def _audit_model_lifecycle(event_type: str, status: str) -> None:
    if (
        settings.APP_ENV != "production"
        or os.getenv("PYTEST_CURRENT_TEST")
    ):
        logger.info("Model lifecycle | event=%s | status=%s", event_type, status)
        return
    database = SessionLocal()
    try:
        AuditService().record(
            database,
            event_type,
            resource_type="model_registry",
            event_metadata={"status": status},
        )
        database.commit()
    except Exception:
        database.rollback()
        logger.warning("Model lifecycle audit could not be persisted.")
    finally:
        database.close()


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "API segura de autenticación continua, operación logística y "
        "recolección experimental de AndesLog Operaciones S.A.C."
    ),
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(LocaleMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Accept-Language",
        "Content-Type",
        "Idempotency-Key",
        "If-Match",
        "X-CSRF-Token",
        "X-Correlation-ID",
        "X-Request-ID",
        "X-Step-Up-Proof-ID",
    ],
    expose_headers=[
        # Lets the browser read the download filename instead of guessing one.
        "Content-Disposition",
        "Content-Language",
        "ETag",
        "X-Content-SHA256",
        "X-Request-ID",
    ],
)
register_exception_handlers(app)
app.include_router(api_router, prefix=settings.API_PREFIX)


@app.get("/health", tags=["Health Probes"])
@app.get("/live", tags=["Health Probes"])
def liveness_probe():
    return {"status": "ok", "environment": settings.APP_ENV, "version": settings.APP_VERSION}


@app.get("/ready", tags=["Health Probes"])
def readiness_probe():
    return {"status": "ready", "environment": settings.APP_ENV, "version": settings.APP_VERSION}
