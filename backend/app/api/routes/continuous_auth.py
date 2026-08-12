from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.permissions import RESEARCH_ADMIN_ROLES
from app.database.session import get_db
from app.dependencies.auth import get_current_session
from app.dependencies.csrf import verify_csrf
from app.dependencies.permissions import require_permissions
from app.models.session import UserSession
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.continuous_auth import (
    AuthenticationLevel,
    ContinuousAuthEvaluateRequest,
    ContinuousAuthEvaluateResponse,
    ContinuousAuthEvaluationRead,
    ContinuousAuthStatusResponse,
    ReverifyRequest,
    ReverifyResponse,
    RiskLevel,
)
from app.services.continuous_auth_service import ContinuousAuthService
from app.services.model_loader_service import ModelLoaderService

router = APIRouter(
    prefix="/continuous-auth",
    tags=["Continuous Authentication"],
)


def _service(request: Request) -> ContinuousAuthService:
    loader: ModelLoaderService = request.app.state.model_loader
    return ContinuousAuthService(loader)


@router.post(
    "/evaluate",
    response_model=ContinuousAuthEvaluateResponse,
    summary="Evaluar riesgo biométrico de la sesión actual",
    dependencies=[Depends(verify_csrf)],
)
async def evaluate(
    data: ContinuousAuthEvaluateRequest,
    request: Request,
    database: Session = Depends(get_db),
    user_session: UserSession = Depends(get_current_session),
) -> ContinuousAuthEvaluateResponse:
    return await _service(request).evaluate(
        database, user_session, data
    )


@router.get(
    "/status",
    response_model=ContinuousAuthStatusResponse,
    summary="Consultar estado continuo de la sesión actual",
)
def current_status(
    request: Request,
    database: Session = Depends(get_db),
    user_session: UserSession = Depends(get_current_session),
) -> ContinuousAuthStatusResponse:
    return _service(request).status(database, user_session)


@router.get(
    "/evaluations",
    response_model=PaginatedResponse[ContinuousAuthEvaluationRead],
    summary="Listar evaluaciones sin biometría cruda",
)
def list_evaluations(
    request: Request,
    user_id: UUID | None = None,
    session_id: UUID | None = None,
    participant_id: UUID | None = None,
    risk_level: RiskLevel | None = None,
    authentication_level: AuthenticationLevel | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    database: Session = Depends(get_db),
    _: User = Depends(require_permissions(*RESEARCH_ADMIN_ROLES)),
) -> PaginatedResponse[ContinuousAuthEvaluationRead]:
    return _service(request).list_evaluations(
        database,
        user_id=user_id,
        session_id=session_id,
        participant_id=participant_id,
        risk_level=risk_level,
        authentication_level=authentication_level,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/evaluations/{evaluation_id}",
    response_model=ContinuousAuthEvaluationRead,
    summary="Consultar detalle administrativo de evaluación",
)
def get_evaluation(
    evaluation_id: UUID,
    request: Request,
    database: Session = Depends(get_db),
    _: User = Depends(require_permissions(*RESEARCH_ADMIN_ROLES)),
) -> ContinuousAuthEvaluationRead:
    return _service(request).get_evaluation(database, evaluation_id)


@router.post(
    "/reverify",
    response_model=ReverifyResponse,
    summary="Reverificar la sesión mediante contraseña",
    dependencies=[Depends(verify_csrf)],
)
def reverify(
    data: ReverifyRequest,
    request: Request,
    database: Session = Depends(get_db),
    user_session: UserSession = Depends(get_current_session),
) -> ReverifyResponse:
    return _service(request).reverify(
        database, user_session, data.password
    )
