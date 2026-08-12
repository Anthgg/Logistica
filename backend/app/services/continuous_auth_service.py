import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from time import perf_counter
from typing import Callable
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings, settings
from app.core.exceptions import ApplicationError
from app.core.security import verify_password
from app.database.base import utc_now
from app.ml.model_bundle import ComponentInference
from app.models.continuous_auth_evaluation import (
    ContinuousAuthEvaluation,
)
from app.models.research_participant import ResearchParticipant
from app.models.risk_event import RiskEvent
from app.models.session import UserSession
from app.repositories.continuous_auth_repository import (
    ContinuousAuthRepository,
)
from app.repositories.research_repository import ResearchRepository
from app.repositories.risk_event_repository import RiskEventRepository
from app.schemas.common import PaginatedResponse
from app.schemas.continuous_auth import (
    AuthenticationLevel,
    ContinuousAuthEvaluateRequest,
    ContinuousAuthEvaluateResponse,
    ContinuousAuthEvaluationRead,
    ContinuousAuthPublicEvaluation,
    ContinuousAuthStatusResponse,
    ReverifyResponse,
    RiskLevel,
)
from app.schemas.inference import (
    PublicComponents,
    PublicComponentStatus,
)
from app.services.audit_service import AuditService
from app.services.behavioral_inference_service import (
    BehavioralInferenceService,
)
from app.services.capture_storage_service import LocalCaptureStorageService
from app.services.facial_inference_service import FacialInferenceService
from app.services.model_loader_service import ModelLoaderService
from app.services.pad_inference_service import PadInferenceService
from app.services.risk_decision_service import (
    RiskDecision,
    RiskDecisionService,
)

DEGRADABLE_COMPONENT_ERRORS = {
    "MODEL_REGISTRY_UNAVAILABLE",
    "MODEL_ARTIFACT_INVALID",
    "FACIAL_MODEL_UNAVAILABLE",
    "PAD_MODEL_UNAVAILABLE",
    "BEHAVIORAL_MODEL_UNAVAILABLE",
    "FACIAL_TEMPLATE_NOT_FOUND",
    "FUSION_CONFIG_UNAVAILABLE",
    "INTERNAL_INFERENCE_ERROR",
}


@dataclass(frozen=True, slots=True)
class InferenceContext:
    participant: ResearchParticipant
    image_content: bytes | None
    experimental_session_id: UUID
    behavioral_window_id: str | None


class ContinuousAuthService:
    def __init__(
        self,
        loader: ModelLoaderService,
        source_settings: Settings = settings,
    ) -> None:
        self.loader = loader
        self.settings = source_settings
        self.repository = ContinuousAuthRepository()
        self.risk_events = RiskEventRepository()
        self.research = ResearchRepository()
        self.audit = AuditService()
        self.storage = LocalCaptureStorageService()
        self.facial = FacialInferenceService(loader)
        self.pad = PadInferenceService(loader)
        self.behavioral = BehavioralInferenceService(loader)

    async def evaluate(
        self,
        database: Session,
        user_session: UserSession,
        data: ContinuousAuthEvaluateRequest,
    ) -> ContinuousAuthEvaluateResponse:
        total_started = perf_counter()
        self._assert_enabled(user_session)
        context = self._prepare_context(
            database, user_session, data
        )
        components = await self._infer_components(context, data)
        fusion = self.loader.fusion
        if fusion is None:
            self._mark_degraded(
                database,
                user_session,
                reason_code="FUSION_CONFIG_UNAVAILABLE",
                components=components,
            )
            raise ApplicationError(
                "FUSION_CONFIG_UNAVAILABLE",
                "La configuración de fusión no está disponible.",
                503,
            )
        try:
            fused = fusion.fuse(
                {
                    name: component.risk
                    if component.available and component.valid
                    else None
                    for name, component in components.items()
                }
            )
        except ApplicationError as exc:
            if exc.code == "INSUFFICIENT_COMPONENTS":
                self._mark_degraded(
                    database,
                    user_session,
                    reason_code=exc.code,
                    components=components,
                )
            raise
        config = fusion.config
        decision_service = RiskDecisionService(
            config.risk_thresholds,
            self.settings,
        )
        previous = self.repository.last_for_session(
            database, user_session.id
        )
        recent_risks = self.repository.recent_risks(
            database,
            session_id=user_session.id,
            since=utc_now()
            - timedelta(
                seconds=self.settings.RISK_EVALUATION_WINDOW_SECONDS
            ),
            reset_after=user_session.last_continuous_verification_at,
            limit=max(
                self.settings.RISK_RECOVERY_CONFIRMATION_COUNT,
                self.settings.RISK_HIGH_CONFIRMATION_COUNT,
                self.settings.RISK_CRITICAL_CONFIRMATION_COUNT,
            ),
        )
        decision = decision_service.decide(
            combined_risk=fused.risk,
            previous_level=previous.risk_level if previous else None,
            recent_risks=recent_risks,
        )
        evaluation = self._persist(
            database=database,
            user_session=user_session,
            data=data,
            context=context,
            components=components,
            decision=decision,
            combined_risk=fused.risk,
            fusion_ms=fused.latency_ms,
            previous_level=previous.risk_level if previous else None,
            total_started=total_started,
        )
        return ContinuousAuthEvaluateResponse(
            evaluation=self._public_evaluation(evaluation, components)
        )

    def _assert_enabled(self, user_session: UserSession) -> None:
        if not self.settings.CONTINUOUS_AUTH_ENABLED:
            raise ApplicationError(
                "CONTINUOUS_AUTH_DISABLED",
                "La autenticación continua está deshabilitada.",
                503,
            )
        if user_session.revoked_at:
            raise ApplicationError(
                "SESSION_TERMINATED", "La sesión está revocada.", 401
            )
        if user_session.device and user_session.device.is_blocked:
            raise ApplicationError(
                "DEVICE_BLOCKED", "El dispositivo está bloqueado.", 403
            )

    def _prepare_context(
        self,
        database: Session,
        user_session: UserSession,
        data: ContinuousAuthEvaluateRequest,
    ) -> InferenceContext:
        now = utc_now()
        timestamp = data.evaluation_timestamp.astimezone(timezone.utc)
        if timestamp > now + timedelta(minutes=5):
            raise ApplicationError(
                "INVALID_EVALUATION_TIMESTAMP",
                "La fecha de evaluación está en el futuro.",
                422,
            )
        last = self.repository.last_for_session(database, user_session.id)
        if last and last.evaluated_at + timedelta(
            seconds=self.settings.CONTINUOUS_AUTH_MIN_INTERVAL_SECONDS
        ) > now:
            raise ApplicationError(
                "CONTINUOUS_AUTH_INTERVAL_NOT_ELAPSED",
                "La sesión todavía no requiere otra evaluación.",
                429,
            )
        participant = self.research.participant_for_user(
            database, user_session.user_id
        )
        if not participant or not participant.is_active:
            raise ApplicationError(
                "PARTICIPANT_NOT_FOUND",
                "El usuario no tiene un participante activo.",
                409,
            )
        experimental = self.repository.experimental_session(
            database, data.experimental_session_id
        )
        if not experimental:
            raise ApplicationError(
                "EXPERIMENTAL_SESSION_NOT_FOUND",
                "La sesión experimental no existe.",
                404,
            )
        if (
            experimental.user_id != user_session.user_id
            or experimental.participant_id != participant.id
        ):
            raise ApplicationError(
                "RESEARCH_RESOURCE_FORBIDDEN",
                "La sesión experimental no corresponde al usuario.",
                403,
            )
        image_content = None
        if data.facial_capture_id:
            capture = self.repository.capture(
                database, data.facial_capture_id
            )
            if (
                not capture
                or capture.experimental_session_id != experimental.id
            ):
                raise ApplicationError(
                    "INVALID_CAPTURE",
                    "La captura no corresponde a la sesión experimental.",
                    422,
                )
            image_content = self.storage.read_capture(
                capture.storage_path
            )
            if (
                self.storage.calculate_checksum(image_content)
                != capture.checksum
            ):
                raise ApplicationError(
                    "INVALID_CAPTURE",
                    "La integridad de la captura no es válida.",
                    422,
                )
        return InferenceContext(
            participant=participant,
            image_content=image_content,
            experimental_session_id=experimental.id,
            behavioral_window_id=data.behavioral_window_id,
        )

    async def _infer_components(
        self,
        context: InferenceContext,
        data: ContinuousAuthEvaluateRequest,
    ) -> dict[str, ComponentInference]:
        tasks: dict[str, asyncio.Task[ComponentInference]] = {}
        if context.image_content is not None:
            tasks["facial"] = asyncio.create_task(
                self._safe_component(
                    "facial",
                    lambda: self.facial.infer(
                        context.participant.participant_code,
                        context.image_content or b"",
                    ),
                )
            )
            tasks["pad"] = asyncio.create_task(
                self._safe_component(
                    "pad",
                    lambda: self.pad.infer(context.image_content or b""),
                )
            )
        if data.behavioral_window_id:
            tasks["behavioral"] = asyncio.create_task(
                self._safe_component(
                    "behavioral",
                    lambda: self.behavioral.infer(
                        participant_code=(
                            context.participant.participant_code
                        ),
                        window_id=data.behavioral_window_id or "",
                        experimental_session_id=(
                            context.experimental_session_id
                        ),
                    ),
                )
            )
        results = {
            name: await task for name, task in tasks.items()
        }
        for name in ("facial", "pad", "behavioral"):
            results.setdefault(
                name,
                ComponentInference(
                    available=False,
                    valid=False,
                    score=None,
                    risk=None,
                    decision="not_requested",
                    latency_ms=0,
                    model_version=None,
                    reason_code="NOT_REQUESTED",
                ),
            )
        return results

    async def _safe_component(
        self,
        name: str,
        operation: Callable[[], ComponentInference],
    ) -> ComponentInference:
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(operation),
                timeout=self.settings.INFERENCE_TIMEOUT_SECONDS,
            )
        except TimeoutError:
            return ComponentInference(
                available=False,
                valid=False,
                score=None,
                risk=None,
                decision="unavailable",
                latency_ms=(
                    float(self.settings.INFERENCE_TIMEOUT_SECONDS) * 1000
                ),
                model_version=None,
                reason_code="INFERENCE_TIMEOUT",
                latency_breakdown={
                    f"{name}_ms": (
                        float(self.settings.INFERENCE_TIMEOUT_SECONDS)
                        * 1000
                    )
                },
            )
        except ApplicationError as exc:
            if exc.code not in DEGRADABLE_COMPONENT_ERRORS:
                raise
            return ComponentInference(
                available=False,
                valid=False,
                score=None,
                risk=None,
                decision="unavailable",
                latency_ms=0,
                model_version=None,
                reason_code=exc.code,
            )
        except Exception as exc:
            del exc
            return ComponentInference(
                available=False,
                valid=False,
                score=None,
                risk=None,
                decision="unavailable",
                latency_ms=0,
                model_version=None,
                reason_code="INTERNAL_INFERENCE_ERROR",
            )

    def _persist(
        self,
        *,
        database: Session,
        user_session: UserSession,
        data: ContinuousAuthEvaluateRequest,
        context: InferenceContext,
        components: dict[str, ComponentInference],
        decision: RiskDecision,
        combined_risk: float,
        fusion_ms: float,
        previous_level: str | None,
        total_started: float,
    ) -> ContinuousAuthEvaluation:
        database_started = perf_counter()
        locked = self.repository.lock_session(
            database, user_session.id
        )
        if not locked or locked.revoked_at:
            raise ApplicationError(
                "SESSION_TERMINATED", "La sesión ya no está activa.", 401
            )
        now = utc_now()
        latest = self.repository.last_for_session(database, locked.id)
        if latest and latest.evaluated_at + timedelta(
            seconds=self.settings.CONTINUOUS_AUTH_MIN_INTERVAL_SECONDS
        ) > now:
            raise ApplicationError(
                "CONTINUOUS_AUTH_INTERVAL_NOT_ELAPSED",
                "Otra evaluación de la sesión acaba de completarse.",
                429,
            )
        latency = self._latency_breakdown(components, fusion_ms)
        evaluation = ContinuousAuthEvaluation(
            user_id=locked.user_id,
            session_id=locked.id,
            experimental_session_id=context.experimental_session_id,
            participant_id=context.participant.id,
            facial_capture_id=data.facial_capture_id,
            behavioral_window_id=data.behavioral_window_id,
            facial_available=components["facial"].available,
            pad_available=components["pad"].available,
            behavioral_available=components["behavioral"].available,
            facial_score=self._decimal(components["facial"].score),
            pad_score=self._decimal(components["pad"].score),
            behavioral_score=self._decimal(
                components["behavioral"].score
            ),
            facial_risk=self._decimal(components["facial"].risk),
            pad_risk=self._decimal(components["pad"].risk),
            behavioral_risk=self._decimal(
                components["behavioral"].risk
            ),
            combined_risk=self._decimal(combined_risk)
            or Decimal("0"),
            risk_level=decision.applied_level,
            authentication_level=decision.authentication_level,
            recommended_action=decision.recommended_action,
            applied_action=decision.applied_action,
            model_versions={
                name: component.model_version
                for name, component in components.items()
                if component.model_version
            },
            latency_ms=Decimal("0"),
            latency_breakdown=latency,
            evaluated_at=now,
        )
        self.repository.create(database, evaluation)
        locked.risk_score = self._decimal(combined_risk) or Decimal("0")
        locked.authentication_level = decision.authentication_level
        locked.last_risk_action = decision.applied_action
        locked.continuous_auth_status = decision.continuous_auth_status
        if decision.authentication_level == "continuously_verified":
            locked.last_continuous_verification_at = now
        if decision.applied_action == "terminate_session":
            locked.revoked_at = now
        if previous_level != decision.applied_level:
            self.risk_events.create(
                database,
                RiskEvent(
                    continuous_auth_evaluation_id=evaluation.id,
                    user_id=locked.user_id,
                    session_id=locked.id,
                    previous_risk_level=previous_level,
                    new_risk_level=decision.applied_level,
                    recommended_action=decision.recommended_action,
                    applied_action=decision.applied_action,
                    reason_code=decision.reason_code,
                ),
            )
            self.audit.record(
                database,
                "RISK_LEVEL_CHANGED",
                user_id=locked.user_id,
                session_id=locked.id,
                resource_type="continuous_auth_evaluation",
                resource_id=str(evaluation.id),
                event_metadata={
                    "previous_level": previous_level,
                    "new_level": decision.applied_level,
                    "reason_code": decision.reason_code,
                },
            )
        self.audit.record(
            database,
            "CONTINUOUS_AUTH_EVALUATED",
            user_id=locked.user_id,
            session_id=locked.id,
            resource_type="continuous_auth_evaluation",
            resource_id=str(evaluation.id),
            event_metadata={
                "risk_level": decision.applied_level,
                "components_available": [
                    name
                    for name, component in components.items()
                    if component.available
                ],
            },
        )
        self._audit_component_failures(
            database,
            locked,
            components,
            evaluation_id=evaluation.id,
        )
        if decision.recommended_action == "request_reverification":
            self.audit.record(
                database,
                "REVERIFICATION_REQUIRED",
                user_id=locked.user_id,
                session_id=locked.id,
                resource_type="continuous_auth_evaluation",
                resource_id=str(evaluation.id),
            )
        session_event = {
            "mark_restricted": "SESSION_RESTRICTED",
            "terminate_session": "SESSION_TERMINATED",
        }.get(decision.applied_action)
        if session_event:
            self.audit.record(
                database,
                session_event,
                user_id=locked.user_id,
                session_id=locked.id,
                resource_type="continuous_auth_evaluation",
                resource_id=str(evaluation.id),
                event_metadata={"reason_code": decision.reason_code},
            )
        database.flush()
        database_ms = (perf_counter() - database_started) * 1000
        latency["database_ms"] = database_ms
        latency["total_ms"] = (perf_counter() - total_started) * 1000
        evaluation.latency_breakdown = latency
        evaluation.latency_ms = Decimal(str(latency["total_ms"]))
        database.commit()
        database.refresh(evaluation)
        return evaluation

    @staticmethod
    def _decimal(value: float | None) -> Decimal | None:
        return Decimal(str(value)) if value is not None else None

    @staticmethod
    def _latency_breakdown(
        components: dict[str, ComponentInference],
        fusion_ms: float,
    ) -> dict[str, float]:
        breakdown: dict[str, float] = {
            "fusion_ms": fusion_ms,
            "normalization_ms": 0.0,
        }
        decode_times: list[float] = []
        for component in components.values():
            for key, value in component.latency_breakdown.items():
                if key == "image_decode_ms":
                    decode_times.append(value)
                elif key == "normalization_ms":
                    breakdown[key] += value
                else:
                    breakdown[key] = breakdown.get(key, 0.0) + value
        if decode_times:
            breakdown["image_decode_ms"] = max(decode_times)
        return breakdown

    def _mark_degraded(
        self,
        database: Session,
        user_session: UserSession,
        *,
        reason_code: str,
        components: dict[str, ComponentInference] | None = None,
    ) -> None:
        locked = self.repository.lock_session(
            database, user_session.id
        )
        if locked and not locked.revoked_at:
            latest = self.repository.last_for_session(database, locked.id)
            now = utc_now()
            concurrent_success = bool(
                latest
                and latest.evaluated_at
                + timedelta(
                    seconds=(
                        self.settings.CONTINUOUS_AUTH_MIN_INTERVAL_SECONDS
                    )
                )
                > now
            )
            if not concurrent_success:
                locked.continuous_auth_status = "degraded"
                locked.last_risk_action = "insufficient_components"
            if components is not None:
                self._audit_component_failures(
                    database,
                    locked,
                    components,
                )
            self.audit.record(
                database,
                "INFERENCE_COMPONENT_FAILED",
                user_id=locked.user_id,
                session_id=locked.id,
                event_metadata={
                    "reason_code": reason_code,
                    "session_state_updated": not concurrent_success,
                },
            )
            database.commit()

    def _audit_component_failures(
        self,
        database: Session,
        user_session: UserSession,
        components: dict[str, ComponentInference],
        *,
        evaluation_id: UUID | None = None,
    ) -> None:
        for name, component in components.items():
            if component.reason_code in {None, "NOT_REQUESTED"}:
                continue
            event_type = (
                "INFERENCE_TIMEOUT"
                if component.reason_code == "INFERENCE_TIMEOUT"
                else "INFERENCE_COMPONENT_FAILED"
            )
            self.audit.record(
                database,
                event_type,
                user_id=user_session.user_id,
                session_id=user_session.id,
                resource_type=(
                    "continuous_auth_evaluation"
                    if evaluation_id
                    else None
                ),
                resource_id=(
                    str(evaluation_id) if evaluation_id else None
                ),
                event_metadata={
                    "component": name,
                    "reason_code": component.reason_code,
                },
            )

    @staticmethod
    def _public_evaluation(
        evaluation: ContinuousAuthEvaluation,
        components: dict[str, ComponentInference],
    ) -> ContinuousAuthPublicEvaluation:
        def public(name: str) -> PublicComponentStatus:
            component = components[name]
            return PublicComponentStatus(
                available=component.available,
                status=component.decision,
            )

        return ContinuousAuthPublicEvaluation(
            id=evaluation.id,
            risk_score=float(evaluation.combined_risk),
            risk_level=evaluation.risk_level,
            authentication_level=evaluation.authentication_level,
            recommended_action=evaluation.recommended_action,
            applied_action=evaluation.applied_action,
            evaluated_at=evaluation.evaluated_at,
            components=PublicComponents(
                facial=public("facial"),
                pad=public("pad"),
                behavioral=public("behavioral"),
            ),
        )

    def status(
        self, database: Session, user_session: UserSession
    ) -> ContinuousAuthStatusResponse:
        last = self.repository.last_for_session(
            database, user_session.id
        )
        participant = self.research.participant_for_user(
            database, user_session.user_id
        )
        behavioral_available = bool(
            participant
            and self.loader.has_behavioral_model(
                participant.participant_code
            )
        )
        next_after = (
            last.evaluated_at
            + timedelta(
                seconds=self.settings.CONTINUOUS_AUTH_MIN_INTERVAL_SECONDS
            )
            if last
            else None
        )
        return ContinuousAuthStatusResponse(
            enabled=self.settings.CONTINUOUS_AUTH_ENABLED,
            continuous_auth_status=user_session.continuous_auth_status,
            risk_level=last.risk_level if last else None,
            authentication_level=user_session.authentication_level,
            last_evaluation_at=last.evaluated_at if last else None,
            recommended_action=(
                last.recommended_action if last else None
            ),
            applied_action=last.applied_action if last else None,
            components_available={
                "facial": self.loader.facial_runtime is not None,
                "pad": self.loader.pad_runtime is not None,
                "behavioral": behavioral_available,
            },
            next_evaluation_after=next_after,
        )

    def list_evaluations(
        self,
        database: Session,
        *,
        user_id: UUID | None,
        session_id: UUID | None,
        participant_id: UUID | None,
        risk_level: RiskLevel | None,
        authentication_level: AuthenticationLevel | None,
        date_from: datetime | None,
        date_to: datetime | None,
        page: int,
        page_size: int,
    ) -> PaginatedResponse[ContinuousAuthEvaluationRead]:
        items, total = self.repository.list(
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
        total_pages = (total + page_size - 1) // page_size
        return PaginatedResponse(
            items=[
                ContinuousAuthEvaluationRead.model_validate(item)
                for item in items
            ],
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        )

    def get_evaluation(
        self, database: Session, evaluation_id: UUID
    ) -> ContinuousAuthEvaluationRead:
        evaluation = self.repository.get(database, evaluation_id)
        if not evaluation:
            raise ApplicationError(
                "CONTINUOUS_AUTH_EVALUATION_NOT_FOUND",
                "La evaluación no existe.",
                404,
            )
        return ContinuousAuthEvaluationRead.model_validate(evaluation)

    def reverify(
        self,
        database: Session,
        user_session: UserSession,
        password: str,
    ) -> ReverifyResponse:
        if user_session.revoked_at:
            raise ApplicationError(
                "SESSION_TERMINATED", "La sesión está revocada.", 401
            )
        if not verify_password(password, user_session.user.password_hash):
            self.audit.record(
                database,
                "REVERIFICATION_FAILED",
                user_id=user_session.user_id,
                session_id=user_session.id,
            )
            database.commit()
            raise ApplicationError(
                "REVERIFICATION_REQUIRED",
                "La credencial de reverificación no es válida.",
                401,
            )
        now = utc_now()
        locked = self.repository.lock_session(
            database, user_session.id
        )
        if not locked or locked.revoked_at:
            raise ApplicationError(
                "SESSION_TERMINATED", "La sesión está revocada.", 401
            )
        locked.authentication_level = "traditional"
        locked.continuous_auth_status = "active"
        locked.last_risk_action = "password_reverified"
        locked.last_continuous_verification_at = now
        self.audit.record(
            database,
            "REVERIFICATION_SUCCESS",
            user_id=locked.user_id,
            session_id=locked.id,
        )
        database.commit()
        return ReverifyResponse(
            authentication_level="traditional",
            continuous_auth_status="active",
            reverified_at=now,
        )
