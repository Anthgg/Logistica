from datetime import datetime, timezone

from fastapi import APIRouter, Response, status

from app.core.config import settings
from app.database.health import is_database_connected
from app.schemas.health import DatabaseHealth, HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar el estado del servicio",
    description="Confirma que la API está disponible sin consultar servicios externos.",
)
def health_check(response: Response) -> HealthResponse:
    database_connected = is_database_connected()
    if not database_connected:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return HealthResponse(
        status="ok" if database_connected else "degraded",
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
        database=DatabaseHealth(
            status="connected" if database_connected else "disconnected"
        ),
        timestamp=datetime.now(timezone.utc),
    )
