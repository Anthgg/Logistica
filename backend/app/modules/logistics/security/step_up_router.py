"""Step-up API router — challenge creation, factor submission, completion."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.csrf import verify_csrf
from app.modules.logistics.auth_dependencies import get_logistics_principal
from app.modules.logistics.principal import LogisticsPrincipal
from app.modules.logistics.security.step_up_policy import (
    CHALLENGE_TTL_SECONDS,
    MAX_ATTEMPTS,
    POLICY_CATALOG,
    POLICY_VERSION,
    PROOF_TTL_SECONDS,
)
from app.modules.logistics.security.step_up_schemas import (
    PolicyResponse,
    StepUpChallengeCreateRequest,
    StepUpChallengeResponse,
    StepUpCompleteRequest,
    StepUpFactorSubmitRequest,
    StepUpProofResponse,
)
from app.modules.logistics.security.step_up_service import step_up_service


def create_security_router() -> APIRouter:
    router = APIRouter()

    @router.get("/policies", response_model=PolicyResponse)
    def get_policies(
        principal: LogisticsPrincipal = Depends(get_logistics_principal),
    ):
        """Return the step-up policy version and sensitive permissions list."""
        return PolicyResponse(
            policy_version=POLICY_VERSION,
            sensitive_permissions=list(POLICY_CATALOG.keys()),
            challenge_ttl_seconds=CHALLENGE_TTL_SECONDS,
            proof_ttl_seconds=PROOF_TTL_SECONDS,
            max_attempts=MAX_ATTEMPTS,
        )

    @router.post("/step-up/challenges", response_model=StepUpChallengeResponse, status_code=201)
    def create_challenge(
        data: StepUpChallengeCreateRequest,
        principal: LogisticsPrincipal = Depends(get_logistics_principal),
        db: Session = Depends(get_db),
        _csrf: None = Depends(verify_csrf),
    ):
        """Create a step-up challenge for a sensitive permission."""
        challenge = step_up_service.create_challenge(
            db, principal, data.permission_code,
            action_code=data.action_code,
            resource_type=data.resource_type,
            resource_id=data.resource_id,
            reason=data.reason,
        )
        db.commit()
        return StepUpChallengeResponse.model_validate(challenge)

    @router.get("/step-up/challenges/{challenge_id}", response_model=StepUpChallengeResponse)
    def get_challenge(
        challenge_id: UUID,
        principal: LogisticsPrincipal = Depends(get_logistics_principal),
        db: Session = Depends(get_db),
    ):
        """Get a step-up challenge by ID. Only the owner can view it."""
        challenge = step_up_service.get_challenge(db, challenge_id, principal.user_id)
        step_up_service.check_expired(challenge)
        db.commit()
        return StepUpChallengeResponse.model_validate(challenge)

    @router.post("/step-up/challenges/{challenge_id}/factors", response_model=StepUpChallengeResponse)
    def submit_factor(
        challenge_id: UUID,
        data: StepUpFactorSubmitRequest,
        principal: LogisticsPrincipal = Depends(get_logistics_principal),
        db: Session = Depends(get_db),
        _csrf: None = Depends(verify_csrf),
    ):
        """Submit a factor result to a challenge."""
        challenge = step_up_service.get_challenge(db, challenge_id, principal.user_id)
        challenge = step_up_service.submit_factor(db, challenge, data.factor, data.result, data.risk_score)
        db.commit()
        return StepUpChallengeResponse.model_validate(challenge)

    @router.post("/step-up/challenges/{challenge_id}/complete", response_model=StepUpProofResponse)
    def complete_challenge(
        challenge_id: UUID,
        data: StepUpCompleteRequest,
        principal: LogisticsPrincipal = Depends(get_logistics_principal),
        db: Session = Depends(get_db),
        _csrf: None = Depends(verify_csrf),
    ):
        """Complete a passed challenge and issue a proof."""
        challenge = step_up_service.get_challenge(db, challenge_id, principal.user_id)
        proof = step_up_service.complete_challenge(db, challenge)
        db.commit()
        return StepUpProofResponse.model_validate(proof)

    return router