from datetime import datetime
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Query,
    Request,
    Response,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ApplicationError
from app.core.permissions import RESEARCH_ADMIN_ROLES, Role
from app.core.rate_limit import (
    enforce_behavior_rate_limit,
    enforce_capture_rate_limit,
    enforce_research_finish_rate_limit,
    enforce_research_start_rate_limit,
)
from app.database.session import get_db
from app.dependencies.auth import require_active_user
from app.dependencies.csrf import verify_csrf
from app.dependencies.permissions import require_permissions
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.research import (
    BehavioralBatchCreate,
    BehavioralBatchResponse,
    ConsentCreate,
    ConsentRead,
    ConsentWithdraw,
    ExperimentalSessionCancel,
    ExperimentalSessionFinish,
    ExperimentalSessionAnnotationUpdate,
    ExperimentalSessionRead,
    ExperimentalSessionStart,
    FacialCaptureResponse,
    ParticipantCreate,
    ParticipantRead,
    ParticipantUpdate,
    ResearchScenario,
    ResearchSessionStatus,
    SelfEnrollmentResponse,
    SessionMutationResponse,
    SessionStartResponse,
)
from app.services.research_service import ResearchService

router = APIRouter(prefix="/research", tags=["Research"])
service = ResearchService()


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",", 1)[0].strip()
    return request.client.host if request.client else None


@router.get(
    "/participants",
    response_model=PaginatedResponse[ParticipantRead],
    summary="Listar participantes",
)
def list_participants(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_active: bool | None = None,
    database: Session = Depends(get_db),
    _: User = Depends(require_permissions(Role.ADMIN)),
) -> PaginatedResponse[ParticipantRead]:
    return service.list_participants(database, page, page_size, is_active)


@router.post(
    "/participants",
    response_model=ParticipantRead,
    status_code=status.HTTP_201_CREATED,
    summary="Inscribir participante",
    dependencies=[Depends(verify_csrf)],
)
def create_participant(
    data: ParticipantCreate,
    database: Session = Depends(get_db),
    user: User = Depends(require_permissions(Role.ADMIN)),
) -> ParticipantRead:
    return ParticipantRead.model_validate(
        service.create_participant(database, data, user)
    )


@router.get(
    "/participants/me",
    response_model=ParticipantRead,
    summary="Consultar mi perfil experimental seudonimizado",
)
def current_participant(
    database: Session = Depends(get_db),
    user: User = Depends(require_active_user),
) -> ParticipantRead:
    return ParticipantRead.model_validate(
        service.current_participant(database, user)
    )


@router.post(
    "/participants/self-enroll",
    response_model=SelfEnrollmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Autoinscribirme como participante seudonimizado",
    dependencies=[Depends(verify_csrf)],
)
def self_enroll(
    response: Response,
    database: Session = Depends(get_db),
    user: User = Depends(require_active_user),
) -> SelfEnrollmentResponse:
    result = service.self_enroll(database, user)
    if not result.created:
        response.status_code = status.HTTP_200_OK
    return result


@router.get(
    "/participants/{participant_id}",
    response_model=ParticipantRead,
    summary="Consultar participante",
)
def get_participant(
    participant_id: UUID,
    database: Session = Depends(get_db),
    _: User = Depends(require_permissions(Role.ADMIN)),
) -> ParticipantRead:
    return ParticipantRead.model_validate(
        service.get_participant(database, participant_id)
    )


@router.patch(
    "/participants/{participant_id}",
    response_model=ParticipantRead,
    summary="Actualizar participante",
    dependencies=[Depends(verify_csrf)],
)
def update_participant(
    participant_id: UUID,
    data: ParticipantUpdate,
    database: Session = Depends(get_db),
    _: User = Depends(require_permissions(Role.ADMIN)),
) -> ParticipantRead:
    return ParticipantRead.model_validate(
        service.update_participant(database, participant_id, data)
    )


@router.post(
    "/participants/{participant_id}/withdraw",
    response_model=ParticipantRead,
    summary="Retirar participante",
    dependencies=[Depends(verify_csrf)],
)
def withdraw_participant(
    participant_id: UUID,
    database: Session = Depends(get_db),
    _: User = Depends(require_permissions(Role.ADMIN)),
) -> ParticipantRead:
    return ParticipantRead.model_validate(
        service.withdraw_participant(database, participant_id)
    )


@router.get(
    "/consent/current",
    response_model=ConsentRead,
    summary="Consultar consentimiento vigente propio",
)
def current_consent(
    database: Session = Depends(get_db),
    user: User = Depends(require_active_user),
) -> ConsentRead:
    return ConsentRead.model_validate(service.current_consent(database, user))


@router.post(
    "/consent",
    response_model=ConsentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Aceptar consentimiento informado",
    dependencies=[Depends(verify_csrf)],
)
def accept_consent(
    data: ConsentCreate,
    request: Request,
    database: Session = Depends(get_db),
    user: User = Depends(require_active_user),
) -> ConsentRead:
    return ConsentRead.model_validate(
        service.accept_consent(database, data, user, _client_ip(request))
    )


@router.post(
    "/consent/withdraw",
    response_model=ConsentRead,
    summary="Retirar consentimiento informado",
    dependencies=[Depends(verify_csrf)],
)
def withdraw_consent(
    data: ConsentWithdraw,
    database: Session = Depends(get_db),
    user: User = Depends(require_active_user),
) -> ConsentRead:
    return ConsentRead.model_validate(
        service.withdraw_consent(database, data.participant_id, user)
    )


@router.post(
    "/sessions/start",
    response_model=SessionStartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Iniciar sesión experimental",
    dependencies=[
        Depends(verify_csrf),
        Depends(enforce_research_start_rate_limit),
    ],
)
def start_session(
    data: ExperimentalSessionStart,
    database: Session = Depends(get_db),
    user: User = Depends(require_active_user),
) -> SessionStartResponse:
    return service.start_session(database, data, user)


@router.post(
    "/sessions/{session_id}/face-captures",
    response_model=FacialCaptureResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Recibir captura facial validada",
    description=(
        "Acepta exclusivamente JPEG o WebP, valida firma y dimensiones, "
        "y nunca expone la ruta interna de almacenamiento."
    ),
    dependencies=[
        Depends(verify_csrf),
        Depends(enforce_capture_rate_limit),
    ],
)
async def receive_face_capture(
    session_id: UUID,
    response: Response,
    image: UploadFile = File(...),
    captured_at: datetime = Form(...),
    sequence_number: int = Form(..., gt=0),
    width: int = Form(..., ge=64, le=8192),
    height: int = Form(..., ge=64, le=8192),
    visibility_state: str | None = Form(None, max_length=30),
    client_timezone_offset: int | None = Form(None, ge=-840, le=840),
    capture_source: str = Form("webcam", max_length=30),
    camera_facing_mode: str | None = Form(None, max_length=20),
    database: Session = Depends(get_db),
    user: User = Depends(require_active_user),
) -> FacialCaptureResponse:
    content = await image.read(settings.CAPTURE_MAX_FILE_SIZE + 1)
    await image.close()
    try:
        result = service.receive_capture(
            database,
            session_id=session_id,
            user=user,
            content=content,
            declared_content_type=image.content_type or "",
            sequence_number=sequence_number,
            captured_at=captured_at,
            declared_width=width,
            declared_height=height,
            visibility_state=visibility_state,
            client_timezone_offset_minutes=client_timezone_offset,
            capture_source=capture_source,
            camera_facing_mode=camera_facing_mode,
        )
    except ApplicationError as exc:
        service.record_rejection(
            database,
            event_type="CAPTURE_REJECTED",
            user=user,
            session_id=session_id,
            error_code=exc.code,
        )
        raise
    if result.idempotent_replay:
        response.status_code = status.HTTP_200_OK
    return result


@router.post(
    "/sessions/{session_id}/behavior-batches",
    response_model=BehavioralBatchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Recibir lote conductual privado e idempotente",
    dependencies=[
        Depends(verify_csrf),
        Depends(enforce_behavior_rate_limit),
    ],
)
def receive_behavior_batch(
    session_id: UUID,
    data: BehavioralBatchCreate,
    response: Response,
    database: Session = Depends(get_db),
    user: User = Depends(require_active_user),
) -> BehavioralBatchResponse:
    try:
        result = service.receive_behavior_batch(database, session_id, data, user)
    except ApplicationError as exc:
        service.record_rejection(
            database,
            event_type="BEHAVIOR_BATCH_REJECTED",
            user=user,
            session_id=session_id,
            error_code=exc.code,
        )
        raise
    if result.idempotent_replay:
        response.status_code = status.HTTP_200_OK
    return result


@router.post(
    "/sessions/{session_id}/finish",
    response_model=SessionMutationResponse,
    summary="Finalizar sesión y recalcular contadores",
    dependencies=[
        Depends(verify_csrf),
        Depends(enforce_research_finish_rate_limit),
    ],
)
def finish_session(
    session_id: UUID,
    data: ExperimentalSessionFinish,
    database: Session = Depends(get_db),
    user: User = Depends(require_active_user),
) -> SessionMutationResponse:
    return SessionMutationResponse(
        session=service.finish_session(database, session_id, data, user)
    )


@router.post(
    "/sessions/{session_id}/cancel",
    response_model=SessionMutationResponse,
    summary="Cancelar sesión experimental",
    dependencies=[Depends(verify_csrf)],
)
def cancel_session(
    session_id: UUID,
    data: ExperimentalSessionCancel,
    database: Session = Depends(get_db),
    user: User = Depends(require_active_user),
) -> SessionMutationResponse:
    return SessionMutationResponse(
        session=service.cancel_session(database, session_id, data, user)
    )


@router.patch(
    "/sessions/{session_id}/annotation",
    response_model=ExperimentalSessionRead,
    summary="Registrar etiqueta experimental controlada",
    dependencies=[Depends(verify_csrf)],
)
def annotate_session(
    session_id: UUID,
    data: ExperimentalSessionAnnotationUpdate,
    database: Session = Depends(get_db),
    user: User = Depends(require_permissions(*RESEARCH_ADMIN_ROLES)),
) -> ExperimentalSessionRead:
    return service.annotate_session(database, session_id, data, user)


@router.get(
    "/sessions/{session_id}",
    response_model=ExperimentalSessionRead,
    summary="Consultar resumen seguro de sesión",
)
def get_session(
    session_id: UUID,
    database: Session = Depends(get_db),
    user: User = Depends(require_active_user),
) -> ExperimentalSessionRead:
    return service.get_session(database, session_id, user)


@router.get(
    "/sessions",
    response_model=PaginatedResponse[ExperimentalSessionRead],
    summary="Listar sesiones experimentales",
)
def list_sessions(
    participant_id: UUID | None = None,
    session_status: ResearchSessionStatus | None = Query(None, alias="status"),
    scenario: ResearchScenario | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    database: Session = Depends(get_db),
    _: User = Depends(require_permissions(*RESEARCH_ADMIN_ROLES)),
) -> PaginatedResponse[ExperimentalSessionRead]:
    return service.list_sessions(
        database,
        participant_id=participant_id,
        status=session_status,
        scenario=scenario,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )
