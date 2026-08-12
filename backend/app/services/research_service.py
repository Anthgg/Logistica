import json
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from io import BytesIO
from math import ceil
from uuid import UUID, uuid4

from PIL import Image, UnidentifiedImageError
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ApplicationError
from app.core.permissions import Role
from app.database.base import utc_now
from app.models.behavioral_batch import BehavioralBatch
from app.models.consent_record import ConsentRecord
from app.models.experimental_session import ExperimentalSession
from app.models.facial_capture import FacialCapture
from app.models.research_participant import ResearchParticipant
from app.models.user import User
from app.repositories.research_repository import ResearchRepository
from app.schemas.common import PaginatedResponse
from app.schemas.research import (
    BehavioralBatchCreate,
    BehavioralBatchResponse,
    CollectorConfiguration,
    ConsentCreate,
    ConsentRead,
    ExperimentalSessionCancel,
    ExperimentalSessionFinish,
    ExperimentalSessionAnnotationUpdate,
    ExperimentalSessionRead,
    ExperimentalSessionStart,
    FacialCaptureResponse,
    ParticipantCreate,
    ParticipantRead,
    ParticipantUpdate,
    SelfEnrollmentResponse,
    SessionStartResponse,
)
from app.services.audit_service import AuditService
from app.services.capture_storage_service import LocalCaptureStorageService

FORBIDDEN_BEHAVIOR_KEYS = {
    "key",
    "key_value",
    "code",
    "text",
    "typed_text",
    "input_value",
    "password",
    "email_value",
    "clipboard",
    "clipboard_text",
    "inner_html",
    "html",
    "target_value",
}
COMMON_EVENT_KEYS = {"type", "event", "timestamp", "sequence_index"}
KEYBOARD_KEYS = COMMON_EVENT_KEYS | {
    "category",
    "dwell_time_ms",
    "flight_time_ms",
    "interval_from_previous_ms",
    "is_backspace",
    "is_modifier",
}
MOUSE_KEYS = COMMON_EVENT_KEYS | {
    "normalized_x",
    "normalized_y",
    "delta_x",
    "delta_y",
    "distance",
    "velocity",
    "button_category",
    "scroll_delta",
}
KEYBOARD_CATEGORIES = {
    "alphanumeric",
    "navigation",
    "modifier",
    "correction",
    "function",
    "other",
}
MOUSE_EVENTS = {"move", "click", "scroll", "pointerdown", "pointerup"}


def _masked_ip(ip_address: str | None) -> str | None:
    if not ip_address:
        return None
    if "." in ip_address:
        parts = ip_address.split(".")
        return ".".join(parts[:2] + ["0", "0"]) if len(parts) == 4 else None
    return f"{ip_address.split(':', 1)[0]}::"


def _duration_seconds(session: ExperimentalSession) -> int:
    end = session.ended_at or utc_now()
    return max(0, int((end - session.started_at).total_seconds()))


def _session_read(session: ExperimentalSession) -> ExperimentalSessionRead:
    return ExperimentalSessionRead(
        id=session.id,
        participant_id=session.participant_id,
        scenario=session.scenario,
        status=session.status,
        started_at=session.started_at,
        ended_at=session.ended_at,
        duration_seconds=_duration_seconds(session),
        facial_capture_count=session.facial_capture_count,
        keyboard_event_count=session.keyboard_event_count,
        mouse_event_count=session.mouse_event_count,
        batch_count=session.batch_count,
        error_count=session.error_count,
        protocol_version=session.protocol_version,
        collector_version=session.collector_version,
        identity_label=session.identity_label,
        sample_role=session.sample_role,
        operator_change_at=session.operator_change_at,
        presentation_label=session.presentation_label,
        attack_type=session.attack_type,
        source_device=session.source_device,
        pad_source_id=session.pad_source_id,
        annotation_status=session.annotation_status,
    )


def _contains_forbidden_key(value: object) -> bool:
    if isinstance(value, dict):
        for key, nested in value.items():
            if str(key).casefold() in FORBIDDEN_BEHAVIOR_KEYS:
                return True
            if _contains_forbidden_key(nested):
                return True
    elif isinstance(value, list):
        return any(_contains_forbidden_key(item) for item in value)
    return False


def _number_in_range(
    event: dict[str, object], field: str, minimum: float, maximum: float
) -> None:
    value = event.get(field)
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ApplicationError(
            "INVALID_BEHAVIOR_EVENT", f"{field} debe ser numérico.", 422
        )
    if float(value) < minimum or float(value) > maximum:
        raise ApplicationError(
            "INVALID_BEHAVIOR_EVENT", f"{field} está fuera del rango permitido.", 422
        )


def _validate_event(event: dict[str, object]) -> str:
    event_type = event.get("type")
    event_name = event.get("event")
    sequence_index = event.get("sequence_index")
    timestamp = event.get("timestamp")
    if isinstance(sequence_index, bool) or not isinstance(sequence_index, int) or sequence_index <= 0:
        raise ApplicationError(
            "INVALID_BEHAVIOR_EVENT", "sequence_index debe ser positivo.", 422
        )
    if not isinstance(timestamp, str):
        raise ApplicationError(
            "INVALID_BEHAVIOR_EVENT", "timestamp es obligatorio.", 422
        )
    try:
        parsed_timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ApplicationError(
            "INVALID_BEHAVIOR_EVENT", "timestamp no es válido.", 422
        ) from exc
    if parsed_timestamp.tzinfo is None:
        raise ApplicationError(
            "INVALID_BEHAVIOR_EVENT", "timestamp debe incluir zona horaria.", 422
        )
    if event_type == "keyboard":
        if event_name != "timing":
            raise ApplicationError(
                "INVALID_BEHAVIOR_EVENT", "Evento de teclado no permitido.", 422
            )
        if set(event) - KEYBOARD_KEYS:
            raise ApplicationError(
                "INVALID_BEHAVIOR_EVENT", "El evento de teclado contiene campos no permitidos.", 422
            )
        if event.get("category") not in KEYBOARD_CATEGORIES:
            raise ApplicationError(
                "INVALID_BEHAVIOR_EVENT", "Categoría de teclado no permitida.", 422
            )
        _number_in_range(event, "dwell_time_ms", 0, 5000)
        _number_in_range(event, "flight_time_ms", -5000, 10000)
        _number_in_range(event, "interval_from_previous_ms", 0, 60000)
        return "keyboard"
    if event_type == "mouse":
        if event_name not in MOUSE_EVENTS:
            raise ApplicationError(
                "INVALID_BEHAVIOR_EVENT", "Evento de mouse no permitido.", 422
            )
        if set(event) - MOUSE_KEYS:
            raise ApplicationError(
                "INVALID_BEHAVIOR_EVENT", "El evento de mouse contiene campos no permitidos.", 422
            )
        _number_in_range(event, "normalized_x", 0, 1)
        _number_in_range(event, "normalized_y", 0, 1)
        _number_in_range(event, "velocity", 0, 1_000_000)
        _number_in_range(event, "distance", 0, 1_000_000)
        return "mouse"
    raise ApplicationError(
        "INVALID_BEHAVIOR_EVENT", "Tipo de evento conductual no permitido.", 422
    )


class ResearchService:
    def __init__(self) -> None:
        self.repository = ResearchRepository()
        self.audit = AuditService()

    def record_rejection(
        self,
        database: Session,
        *,
        event_type: str,
        user: User,
        session_id: UUID,
        error_code: str,
    ) -> None:
        self.audit.record(
            database,
            event_type,
            user_id=user.id,
            resource_type="experimental_session",
            resource_id=str(session_id),
            event_metadata={"error_code": error_code},
        )
        database.commit()

    def list_participants(
        self, database: Session, page: int, page_size: int, is_active: bool | None
    ) -> PaginatedResponse[ParticipantRead]:
        items, total = self.repository.list_participants(
            database, page=page, page_size=page_size, is_active=is_active
        )
        return PaginatedResponse(
            items=[ParticipantRead.model_validate(item) for item in items],
            page=page,
            page_size=page_size,
            total=total,
            total_pages=ceil(total / page_size),
        )

    def get_participant(
        self, database: Session, participant_id: UUID
    ) -> ResearchParticipant:
        participant = self.repository.get_participant(database, participant_id)
        if not participant:
            raise ApplicationError(
                "PARTICIPANT_NOT_FOUND", "El participante no existe.", 404
            )
        return participant

    def create_participant(
        self, database: Session, data: ParticipantCreate, user: User
    ) -> ResearchParticipant:
        if data.linked_user_id:
            linked_user = database.get(User, data.linked_user_id)
            if not linked_user:
                raise ApplicationError("USER_NOT_FOUND", "El usuario vinculado no existe.", 422)
            existing = self.repository.participant_for_user(database, data.linked_user_id)
            if existing and existing.is_active:
                raise ApplicationError(
                    "USER_ALREADY_ENROLLED",
                    "El usuario ya tiene un participante activo.",
                    409,
                )
        sequence = database.execute(
            text("SELECT nextval('research_participant_code_seq')")
        ).scalar_one()
        participant = ResearchParticipant(
            linked_user_id=data.linked_user_id,
            participant_code=f"P-{int(sequence):04d}",
        )
        database.add(participant)
        database.flush()
        self.audit.record(
            database,
            "RESEARCH_PARTICIPANT_ENROLLED",
            user_id=user.id,
            resource_type="research_participant",
            resource_id=str(participant.id),
        )
        database.commit()
        database.refresh(participant)
        return participant

    def current_participant(
        self, database: Session, user: User
    ) -> ResearchParticipant:
        participant = self.repository.participant_for_user(database, user.id)
        if not participant:
            raise ApplicationError(
                "PARTICIPANT_NOT_FOUND",
                "No existe un participante vinculado a este usuario.",
                404,
            )
        return participant

    def self_enroll(
        self, database: Session, user: User
    ) -> SelfEnrollmentResponse:
        existing = self.repository.participant_for_user(database, user.id)
        if existing:
            if not existing.is_active:
                raise ApplicationError(
                    "PARTICIPANT_INACTIVE",
                    "El participante vinculado está retirado y requiere revisión administrativa.",
                    409,
                )
            return SelfEnrollmentResponse(
                participant=ParticipantRead.model_validate(existing),
                created=False,
            )

        try:
            sequence = database.execute(
                text("SELECT nextval('research_participant_code_seq')")
            ).scalar_one()
            participant = ResearchParticipant(
                linked_user_id=user.id,
                participant_code=f"P-{int(sequence):04d}",
            )
            database.add(participant)
            database.flush()
            self.audit.record(
                database,
                "RESEARCH_PARTICIPANT_SELF_ENROLLED",
                user_id=user.id,
                resource_type="research_participant",
                resource_id=str(participant.id),
            )
            database.commit()
            database.refresh(participant)
        except IntegrityError:
            database.rollback()
            concurrent = self.repository.participant_for_user(database, user.id)
            if concurrent and concurrent.is_active:
                return SelfEnrollmentResponse(
                    participant=ParticipantRead.model_validate(concurrent),
                    created=False,
                )
            raise

        return SelfEnrollmentResponse(
            participant=ParticipantRead.model_validate(participant),
            created=True,
        )

    def update_participant(
        self, database: Session, participant_id: UUID, data: ParticipantUpdate
    ) -> ResearchParticipant:
        participant = self.get_participant(database, participant_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(participant, field, value)
        database.commit()
        database.refresh(participant)
        return participant

    def withdraw_participant(
        self, database: Session, participant_id: UUID
    ) -> ResearchParticipant:
        participant = self.get_participant(database, participant_id)
        participant.is_active = False
        participant.withdrawal_date = utc_now()
        active = self.repository.active_session(database, participant.id)
        if active:
            active.status = "cancelled"
            active.ended_at = utc_now()
            active.invalid_reason = "participant_withdrawn"
        database.commit()
        database.refresh(participant)
        return participant

    def _assert_participant_access(
        self, participant: ResearchParticipant, user: User, *, admin_override: bool = True
    ) -> None:
        if participant.linked_user_id == user.id:
            return
        if admin_override and user.role == Role.ADMIN:
            return
        raise ApplicationError(
            "RESEARCH_RESOURCE_FORBIDDEN",
            "El participante no corresponde al usuario autenticado.",
            403,
        )

    def current_consent(self, database: Session, user: User) -> ConsentRecord:
        participant = self.repository.participant_for_user(database, user.id)
        if not participant:
            raise ApplicationError(
                "PARTICIPANT_NOT_FOUND",
                "No existe un participante vinculado a este usuario.",
                404,
            )
        consent = self.repository.current_consent(database, participant.id)
        if not consent:
            raise ApplicationError(
                "CONSENT_NOT_FOUND", "No existe consentimiento vigente.", 404
            )
        return consent

    def accept_consent(
        self,
        database: Session,
        data: ConsentCreate,
        user: User,
        ip_address: str | None,
    ) -> ConsentRecord:
        participant = self.get_participant(database, data.participant_id)
        self._assert_participant_access(participant, user)
        if not participant.is_active:
            raise ApplicationError(
                "PARTICIPANT_INACTIVE", "El participante está retirado.", 409
            )
        if not data.accepted:
            raise ApplicationError(
                "CONSENT_MUST_BE_ACCEPTED",
                "Use el endpoint de retiro para rechazar el consentimiento.",
                422,
            )
        current = self.repository.current_consent(database, participant.id)
        if current:
            current.withdrawn_at = utc_now()
        consent = ConsentRecord(
            participant_id=participant.id,
            consent_version=data.consent_version,
            accepted=True,
            ip_address=_masked_ip(ip_address),
        )
        database.add(consent)
        database.flush()
        self.audit.record(
            database,
            "CONSENT_ACCEPTED",
            user_id=user.id,
            resource_type="research_participant",
            resource_id=str(participant.id),
            event_metadata={"consent_version": data.consent_version},
        )
        database.commit()
        database.refresh(consent)
        return consent

    def withdraw_consent(
        self, database: Session, participant_id: UUID, user: User
    ) -> ConsentRecord:
        participant = self.get_participant(database, participant_id)
        self._assert_participant_access(participant, user)
        consent = self.repository.current_consent(database, participant.id)
        if not consent:
            raise ApplicationError(
                "CONSENT_NOT_FOUND", "No existe consentimiento vigente.", 404
            )
        consent.withdrawn_at = utc_now()
        active = self.repository.active_session(database, participant.id)
        if active:
            active.status = "cancelled"
            active.ended_at = utc_now()
            active.invalid_reason = "consent_withdrawn"
        self.audit.record(
            database,
            "CONSENT_WITHDRAWN",
            user_id=user.id,
            resource_type="research_participant",
            resource_id=str(participant.id),
        )
        database.commit()
        database.refresh(consent)
        return consent

    def start_session(
        self,
        database: Session,
        data: ExperimentalSessionStart,
        user: User,
    ) -> SessionStartResponse:
        participant = self.get_participant(database, data.participant_id)
        self._assert_participant_access(participant, user)
        if not participant.is_active:
            raise ApplicationError(
                "PARTICIPANT_INACTIVE", "El participante está retirado.", 409
            )
        if not self.repository.current_consent(database, participant.id):
            raise ApplicationError(
                "CONSENT_REQUIRED",
                "Se requiere consentimiento vigente antes de iniciar.",
                409,
            )
        if self.repository.active_session(database, participant.id):
            raise ApplicationError(
                "ACTIVE_RESEARCH_SESSION_EXISTS",
                "El participante ya tiene una sesión activa.",
                409,
            )
        if (
            self.repository.active_session_count_for_user(database, user.id)
            >= settings.RESEARCH_MAX_ACTIVE_SESSIONS_PER_USER
        ):
            raise ApplicationError(
                "ACTIVE_RESEARCH_SESSION_LIMIT",
                "El usuario alcanzó el máximo de sesiones activas.",
                409,
            )
        now = utc_now()
        session = ExperimentalSession(
            participant_id=participant.id,
            user_id=user.id,
            scenario=data.scenario,
            status="active",
            started_at=now,
            last_activity_at=now,
            expected_duration_minutes=data.expected_duration_minutes,
            protocol_version=settings.RESEARCH_PROTOCOL_VERSION,
            collector_version=(
                data.collector_version or settings.RESEARCH_COLLECTOR_VERSION
            ),
            capture_interval_seconds=settings.FACIAL_CAPTURE_INTERVAL_SECONDS,
            batch_interval_seconds=settings.BEHAVIOR_BATCH_INTERVAL_SECONDS,
            max_batch_events=settings.BEHAVIOR_BATCH_MAX_EVENTS,
            max_image_size_bytes=settings.CAPTURE_MAX_FILE_SIZE,
            client_timezone=data.client_timezone,
            client_timezone_offset_minutes=data.client_timezone_offset_minutes,
            client_language=data.client_language,
            screen_width=data.screen_width,
            screen_height=data.screen_height,
            screen_pixel_ratio=data.screen_pixel_ratio,
            browser=data.browser,
            operating_system=data.operating_system,
            device_type=data.device_type,
        )
        database.add(session)
        database.flush()
        self.audit.record(
            database,
            "EXPERIMENTAL_SESSION_STARTED",
            user_id=user.id,
            resource_type="experimental_session",
            resource_id=str(session.id),
            event_metadata={"scenario": data.scenario},
        )
        database.commit()
        return SessionStartResponse(
            session=CollectorConfiguration(
                id=session.id,
                scenario=session.scenario,
                status=session.status,
                started_at=session.started_at,
                capture_interval_seconds=session.capture_interval_seconds,
                batch_interval_seconds=session.batch_interval_seconds,
                max_batch_events=session.max_batch_events,
                max_image_size_bytes=session.max_image_size_bytes,
            )
        )

    def _owned_active_session(
        self, database: Session, session_id: UUID, user: User
    ) -> ExperimentalSession:
        session = self.repository.get_session(database, session_id, lock=True)
        if not session:
            raise ApplicationError(
                "EXPERIMENTAL_SESSION_NOT_FOUND", "La sesión experimental no existe.", 404
            )
        if session.user_id != user.id and user.role != Role.ADMIN:
            raise ApplicationError(
                "RESEARCH_RESOURCE_FORBIDDEN",
                "La sesión no corresponde al usuario autenticado.",
                403,
            )
        if session.status != "active":
            raise ApplicationError(
                "EXPERIMENTAL_SESSION_NOT_ACTIVE",
                "La sesión experimental ya no está activa.",
                409,
            )
        if not self.repository.current_consent(database, session.participant_id):
            raise ApplicationError(
                "CONSENT_REQUIRED", "El consentimiento ya no está vigente.", 409
            )
        return session

    def receive_capture(
        self,
        database: Session,
        *,
        session_id: UUID,
        user: User,
        content: bytes,
        declared_content_type: str,
        sequence_number: int,
        captured_at: datetime,
        declared_width: int,
        declared_height: int,
        visibility_state: str | None,
        client_timezone_offset_minutes: int | None,
        capture_source: str,
        camera_facing_mode: str | None,
    ) -> FacialCaptureResponse:
        session = self._owned_active_session(database, session_id, user)
        duplicate = self.repository.capture_by_sequence(
            database, session.id, sequence_number
        )
        if duplicate:
            return FacialCaptureResponse(
                id=duplicate.id,
                sequence_number=duplicate.sequence_number,
                file_size=duplicate.file_size,
                width=duplicate.width,
                height=duplicate.height,
                captured_at=duplicate.captured_at,
                processing_status=duplicate.processing_status,
                idempotent_replay=True,
            )
        if sequence_number <= 0:
            raise ApplicationError(
                "INVALID_CAPTURE_SEQUENCE", "La secuencia debe ser positiva.", 422
            )
        if declared_content_type not in {"image/jpeg", "image/webp"}:
            raise ApplicationError(
                "CAPTURE_CONTENT_TYPE_NOT_ALLOWED",
                "Solo se aceptan imágenes JPEG o WebP.",
                415,
            )
        if capture_source not in {"webcam", "controlled_upload"}:
            raise ApplicationError(
                "INVALID_CAPTURE_SOURCE",
                "La fuente de captura no está permitida.",
                422,
            )
        if not content or len(content) > settings.CAPTURE_MAX_FILE_SIZE:
            raise ApplicationError(
                "CAPTURE_SIZE_EXCEEDED",
                "La captura supera el tamaño máximo permitido.",
                413,
            )
        if captured_at.tzinfo is None:
            raise ApplicationError(
                "INVALID_CAPTURE_TIMESTAMP",
                "captured_at debe incluir zona horaria.",
                422,
            )
        now = datetime.now(timezone.utc)
        captured_utc = captured_at.astimezone(timezone.utc)
        if captured_utc > now + timedelta(minutes=5) or captured_utc < session.started_at - timedelta(minutes=5):
            raise ApplicationError(
                "INVALID_CAPTURE_TIMESTAMP",
                "captured_at está fuera del intervalo permitido.",
                422,
            )
        try:
            with Image.open(BytesIO(content)) as image:
                image.load()
                actual_format = image.format
                actual_width, actual_height = image.size
        except (UnidentifiedImageError, OSError) as exc:
            raise ApplicationError(
                "INVALID_CAPTURE_FILE", "El archivo no contiene una imagen válida.", 422
            ) from exc
        expected_format = "JPEG" if declared_content_type == "image/jpeg" else "WEBP"
        if actual_format != expected_format:
            raise ApplicationError(
                "CAPTURE_SIGNATURE_MISMATCH",
                "La firma del archivo no coincide con el tipo MIME declarado.",
                422,
            )
        if not (64 <= actual_width <= 8192 and 64 <= actual_height <= 8192):
            raise ApplicationError(
                "INVALID_CAPTURE_DIMENSIONS",
                "Las dimensiones de la captura no son razonables.",
                422,
            )
        if actual_width != declared_width or actual_height != declared_height:
            raise ApplicationError(
                "CAPTURE_DIMENSIONS_MISMATCH",
                "Las dimensiones declaradas no coinciden con el archivo.",
                422,
            )
        capture_id = uuid4()
        extension = "jpg" if actual_format == "JPEG" else "webp"
        storage = LocalCaptureStorageService()
        try:
            storage_path = storage.save_capture(
                session.id, capture_id, extension, content
            )
        except OSError as exc:
            self.audit.record(
                database,
                "CAPTURE_STORAGE_ERROR",
                user_id=user.id,
                resource_type="experimental_session",
                resource_id=str(session.id),
            )
            database.commit()
            raise ApplicationError(
                "CAPTURE_STORAGE_ERROR", "No fue posible almacenar la captura.", 503
            ) from exc
        capture = FacialCapture(
            id=capture_id,
            experimental_session_id=session.id,
            sequence_number=sequence_number,
            storage_path=storage_path,
            content_type=declared_content_type,
            file_size=len(content),
            width=actual_width,
            height=actual_height,
            captured_at=captured_utc,
            visibility_state=visibility_state,
            client_timezone_offset_minutes=client_timezone_offset_minutes,
            capture_source=capture_source,
            camera_facing_mode=camera_facing_mode,
            checksum=storage.calculate_checksum(content),
        )
        database.add(capture)
        session.last_activity_at = utc_now()
        session.facial_capture_count += 1
        try:
            database.flush()
        except IntegrityError as exc:
            database.rollback()
            storage.delete_capture(storage_path)
            replay = self.repository.capture_by_sequence(
                database, session.id, sequence_number
            )
            if replay:
                return FacialCaptureResponse(
                    id=replay.id,
                    sequence_number=replay.sequence_number,
                    file_size=replay.file_size,
                    width=replay.width,
                    height=replay.height,
                    captured_at=replay.captured_at,
                    processing_status=replay.processing_status,
                    idempotent_replay=True,
                )
            raise ApplicationError(
                "CAPTURE_SEQUENCE_DUPLICATE", "La secuencia ya fue recibida.", 409
            ) from exc
        self.audit.record(
            database,
            "FACIAL_CAPTURE_RECEIVED",
            user_id=user.id,
            resource_type="experimental_session",
            resource_id=str(session.id),
            event_metadata={
                "sequence_number": sequence_number,
                "file_size": len(content),
            },
        )
        database.commit()
        return FacialCaptureResponse(
            id=capture.id,
            sequence_number=capture.sequence_number,
            file_size=capture.file_size,
            width=capture.width,
            height=capture.height,
            captured_at=capture.captured_at,
            processing_status=capture.processing_status,
            idempotent_replay=False,
        )

    def receive_behavior_batch(
        self,
        database: Session,
        session_id: UUID,
        data: BehavioralBatchCreate,
        user: User,
    ) -> BehavioralBatchResponse:
        session = self._owned_active_session(database, session_id, user)
        replay = self.repository.batch_by_id(database, data.batch_id)
        if replay:
            if replay.experimental_session_id != session.id:
                raise ApplicationError(
                    "BEHAVIOR_BATCH_ID_CONFLICT",
                    "El identificador del lote pertenece a otra sesión.",
                    409,
                )
            return BehavioralBatchResponse(
                id=replay.id,
                batch_id=replay.batch_id,
                sequence_number=replay.sequence_number,
                event_count=replay.event_count,
                keyboard_event_count=replay.keyboard_event_count,
                mouse_event_count=replay.mouse_event_count,
                idempotent_replay=True,
            )
        if self.repository.batch_by_sequence(database, session.id, data.sequence_number):
            raise ApplicationError(
                "BEHAVIOR_SEQUENCE_DUPLICATE",
                "La secuencia del lote ya fue utilizada.",
                409,
            )
        if not data.events or len(data.events) > settings.BEHAVIOR_BATCH_MAX_EVENTS:
            raise ApplicationError(
                "BEHAVIOR_EVENT_LIMIT_EXCEEDED",
                "El lote no contiene una cantidad permitida de eventos.",
                413,
            )
        if _contains_forbidden_key(data.events):
            raise ApplicationError(
                "BEHAVIOR_PAYLOAD_CONTAINS_FORBIDDEN_DATA",
                "El lote contiene propiedades que podrían revelar texto escrito.",
                422,
            )
        serialized = json.dumps(
            data.events, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
        if len(serialized) > settings.BEHAVIOR_BATCH_MAX_PAYLOAD_BYTES:
            raise ApplicationError(
                "BEHAVIOR_PAYLOAD_SIZE_EXCEEDED",
                "El lote conductual supera el tamaño máximo.",
                413,
            )
        keyboard_count = 0
        mouse_count = 0
        indexes: set[int] = set()
        for event in data.events:
            event_type = _validate_event(event)
            event_index = int(event["sequence_index"])
            if event_index in indexes:
                raise ApplicationError(
                    "DUPLICATE_BEHAVIOR_SEQUENCE_INDEX",
                    "sequence_index debe ser único dentro del lote.",
                    422,
                )
            indexes.add(event_index)
            keyboard_count += event_type == "keyboard"
            mouse_count += event_type == "mouse"
        batch = BehavioralBatch(
            experimental_session_id=session.id,
            batch_id=data.batch_id,
            sequence_number=data.sequence_number,
            event_count=len(data.events),
            keyboard_event_count=keyboard_count,
            mouse_event_count=mouse_count,
            started_at=data.started_at,
            ended_at=data.ended_at,
            visibility_state=data.visibility_state,
            client_timezone_offset_minutes=data.client_timezone_offset_minutes,
            dropped_event_count=data.dropped_event_count,
            collector_error_count=data.collector_error_count,
            payload=data.events,
            checksum=sha256(serialized).hexdigest(),
        )
        database.add(batch)
        session.last_activity_at = utc_now()
        session.batch_count += 1
        session.keyboard_event_count += keyboard_count
        session.mouse_event_count += mouse_count
        try:
            database.flush()
        except IntegrityError as exc:
            database.rollback()
            replay = self.repository.batch_by_id(database, data.batch_id)
            if replay and replay.experimental_session_id == session.id:
                return BehavioralBatchResponse(
                    id=replay.id,
                    batch_id=replay.batch_id,
                    sequence_number=replay.sequence_number,
                    event_count=replay.event_count,
                    keyboard_event_count=replay.keyboard_event_count,
                    mouse_event_count=replay.mouse_event_count,
                    idempotent_replay=True,
                )
            raise ApplicationError(
                "BEHAVIOR_BATCH_CONFLICT", "El lote o su secuencia ya existen.", 409
            ) from exc
        self.audit.record(
            database,
            "BEHAVIOR_BATCH_RECEIVED",
            user_id=user.id,
            resource_type="experimental_session",
            resource_id=str(session.id),
            event_metadata={
                "batch_id": str(batch.batch_id),
                "event_count": batch.event_count,
            },
        )
        database.commit()
        return BehavioralBatchResponse(
            id=batch.id,
            batch_id=batch.batch_id,
            sequence_number=batch.sequence_number,
            event_count=batch.event_count,
            keyboard_event_count=batch.keyboard_event_count,
            mouse_event_count=batch.mouse_event_count,
            idempotent_replay=False,
        )

    def annotate_session(
        self,
        database: Session,
        session_id: UUID,
        data: ExperimentalSessionAnnotationUpdate,
        user: User,
    ) -> ExperimentalSessionRead:
        session = self.repository.get_session(database, session_id, lock=True)
        if not session:
            raise ApplicationError(
                "EXPERIMENTAL_SESSION_NOT_FOUND",
                "La sesión experimental no existe.",
                404,
            )
        if data.operator_change_at is not None:
            change = data.operator_change_at.astimezone(timezone.utc)
            end = session.ended_at or utc_now()
            if not session.started_at < change < end:
                raise ApplicationError(
                    "INVALID_OPERATOR_CHANGE_TIME",
                    "operator_change_at debe estar dentro de la sesión.",
                    422,
                )
            session.operator_change_at = change
        else:
            session.operator_change_at = None
        session.identity_label = data.identity_label
        session.sample_role = data.sample_role
        session.presentation_label = data.presentation_label
        session.attack_type = data.attack_type
        session.source_device = data.source_device
        session.pad_source_id = data.pad_source_id
        session.annotation_notes = data.annotation_notes
        session.annotation_status = "confirmed" if data.confirmed else "pending"
        session.annotated_by = user.id
        session.annotated_at = utc_now()
        self.audit.record(
            database,
            "EXPERIMENTAL_SESSION_ANNOTATED",
            user_id=user.id,
            resource_type="experimental_session",
            resource_id=str(session.id),
            event_metadata={
                "annotation_status": session.annotation_status,
                "identity_label": session.identity_label,
                "sample_role": session.sample_role,
                "presentation_label": session.presentation_label,
                "attack_type": session.attack_type,
            },
        )
        database.commit()
        database.refresh(session)
        return _session_read(session)

    def _refresh_counts(
        self, database: Session, session: ExperimentalSession
    ) -> None:
        capture_count, batch_count, keyboard_count, mouse_count = (
            self.repository.session_counts(database, session.id)
        )
        session.facial_capture_count = capture_count
        session.batch_count = batch_count
        session.keyboard_event_count = keyboard_count
        session.mouse_event_count = mouse_count

    def finish_session(
        self,
        database: Session,
        session_id: UUID,
        data: ExperimentalSessionFinish,
        user: User,
    ) -> ExperimentalSessionRead:
        session = self._owned_active_session(database, session_id, user)
        self._refresh_counts(database, session)
        now = utc_now()
        client_end = data.client_ended_at.astimezone(timezone.utc)
        session.ended_at = min(now, client_end + timedelta(minutes=5))
        session.error_count = data.client_error_count
        complete = (
            session.facial_capture_count >= 1
            and session.batch_count >= 1
            and _duration_seconds(session)
            >= settings.RESEARCH_MIN_SESSION_DURATION_SECONDS
        )
        session.status = "completed" if complete else "invalid"
        if not complete:
            session.invalid_reason = "minimum_collection_requirements_not_met"
        self.audit.record(
            database,
            "EXPERIMENTAL_SESSION_COMPLETED"
            if complete
            else "EXPERIMENTAL_SESSION_INVALID",
            user_id=user.id,
            resource_type="experimental_session",
            resource_id=str(session.id),
        )
        database.commit()
        database.refresh(session)
        return _session_read(session)

    def cancel_session(
        self,
        database: Session,
        session_id: UUID,
        data: ExperimentalSessionCancel,
        user: User,
    ) -> ExperimentalSessionRead:
        session = self._owned_active_session(database, session_id, user)
        self._refresh_counts(database, session)
        session.status = "cancelled"
        session.ended_at = utc_now()
        session.invalid_reason = data.reason
        self.audit.record(
            database,
            "EXPERIMENTAL_SESSION_CANCELLED",
            user_id=user.id,
            resource_type="experimental_session",
            resource_id=str(session.id),
            event_metadata={"reason": data.reason},
        )
        database.commit()
        database.refresh(session)
        return _session_read(session)

    def get_session(
        self, database: Session, session_id: UUID, user: User
    ) -> ExperimentalSessionRead:
        session = self.repository.get_session(database, session_id)
        if not session:
            raise ApplicationError(
                "EXPERIMENTAL_SESSION_NOT_FOUND", "La sesión experimental no existe.", 404
            )
        if session.user_id != user.id and user.role not in {
            Role.ADMIN,
            Role.SUPERVISOR,
        }:
            raise ApplicationError(
                "RESEARCH_RESOURCE_FORBIDDEN",
                "La sesión no corresponde al usuario autenticado.",
                403,
            )
        return _session_read(session)

    def list_sessions(
        self, database: Session, **filters: object
    ) -> PaginatedResponse[ExperimentalSessionRead]:
        sessions, total = self.repository.list_sessions(database, **filters)
        page = int(filters["page"])
        page_size = int(filters["page_size"])
        return PaginatedResponse(
            items=[_session_read(item) for item in sessions],
            page=page,
            page_size=page_size,
            total=total,
            total_pages=ceil(total / page_size),
        )

    def invalidate_stale_sessions(self, database: Session) -> int:
        cutoff = utc_now() - timedelta(
            minutes=settings.EXPERIMENTAL_SESSION_STALE_MINUTES
        )
        sessions = list(
            database.scalars(
                select(ExperimentalSession)
                .where(
                    ExperimentalSession.status == "active",
                    ExperimentalSession.last_activity_at < cutoff,
                )
                .with_for_update(skip_locked=True)
            )
        )
        for session in sessions:
            self._refresh_counts(database, session)
            session.status = "invalid"
            session.ended_at = utc_now()
            session.invalid_reason = "stale_session_timeout"
            self.audit.record(
                database,
                "EXPERIMENTAL_SESSION_INVALID",
                user_id=session.user_id,
                resource_type="experimental_session",
                resource_id=str(session.id),
                event_metadata={"reason": "stale_session_timeout"},
            )
        database.commit()
        return len(sessions)
