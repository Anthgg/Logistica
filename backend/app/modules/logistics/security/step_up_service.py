"""Step-up service — challenge creation, factor evaluation, proof issuance and consumption."""

import hashlib
from datetime import timedelta
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ApplicationError
from app.database.base import utc_now
from app.models.session import UserSession
from app.models.user import User
from app.modules.logistics.principal import LogisticsPrincipal
from app.modules.logistics.security.models_stepup import StepUpChallenge, StepUpProof
from app.modules.logistics.security.step_up_policy import (
    CHALLENGE_TTL_SECONDS,
    MAX_ATTEMPTS,
    POLICY_VERSION,
    PROOF_TTL_SECONDS,
    ChallengeStatus,
    ProofStatus,
    RiskDecision,
    StepUpFactor,
    get_policy,
    is_sensitive_permission,
)


class StepUpService:
    """Manages step-up challenges and proofs for sensitive operations."""

    def create_challenge(
        self,
        db: Session,
        principal: LogisticsPrincipal,
        permission_code: str,
        *,
        action_code: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        reason: str | None = None,
    ) -> StepUpChallenge:
        """Create a new step-up challenge for a sensitive permission."""
        policy = get_policy(permission_code)
        if not policy:
            raise ApplicationError(
                "STEP_UP_NOT_REQUIRED",
                "Este permiso no requiere verificación reforzada.",
                422,
            )

        # Check reason if required
        if policy.requires_reason and not reason:
            raise ApplicationError(
                "SENSITIVE_ACTION_REASON_REQUIRED",
                "Esta acción requiere un motivo.",
                422,
            )

        now = utc_now()
        expires_at = now + timedelta(seconds=CHALLENGE_TTL_SECONDS)

        challenge = StepUpChallenge(
            user_id=principal.user_id,
            session_id=principal.session_id,
            device_id=principal.device_id,
            permission_code=permission_code,
            action_code=action_code,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            organization_id=UUID(principal.default_organization_id) if principal.default_organization_id else None,
            branch_id=UUID(principal.default_branch_id) if principal.default_branch_id else None,
            warehouse_id=UUID(principal.default_warehouse_id) if principal.default_warehouse_id else None,
            status=ChallengeStatus.PENDING.value,
            required_factors=[f.value for f in policy.required_factors],
            reason_codes=[policy.base_risk_level.value],
            risk_level=policy.base_risk_level.value,
            reason_text=reason,
            max_attempts=MAX_ATTEMPTS,
            correlation_id=principal.correlation_id,
            policy_version=POLICY_VERSION,
            issued_at=now,
            expires_at=expires_at,
        )
        db.add(challenge)
        db.flush()
        return challenge

    def get_challenge(self, db: Session, challenge_id: UUID, user_id: UUID) -> StepUpChallenge:
        """Get a challenge, validating ownership."""
        challenge = db.get(StepUpChallenge, challenge_id)
        if not challenge:
            raise ApplicationError("STEP_UP_CHALLENGE_NOT_FOUND", "El desafío no existe.", 404)
        if challenge.user_id != user_id:
            raise ApplicationError("STEP_UP_CHALLENGE_NOT_FOUND", "El desafío no existe.", 404)
        return challenge

    def check_expired(self, challenge: StepUpChallenge) -> bool:
        """Check if a challenge has expired and update it if so."""
        if challenge.status != ChallengeStatus.PENDING.value:
            return False
        if utc_now() > challenge.expires_at:
            challenge.status = ChallengeStatus.EXPIRED.value
            return True
        return False

    def submit_factor(
        self,
        db: Session,
        challenge: StepUpChallenge,
        factor: str,
        result: str,
        risk_score: float | None = None,
    ) -> StepUpChallenge:
        """Submit a factor result to a challenge."""
        if self.check_expired(challenge):
            db.flush()
            raise ApplicationError("STEP_UP_CHALLENGE_EXPIRED", "El desafío ha expirado.", 410)
        if challenge.status != ChallengeStatus.PENDING.value:
            raise ApplicationError(
                "STEP_UP_CHALLENGE_ALREADY_COMPLETED",
                "El desafío ya fue procesado.",
                409,
            )
        if factor not in challenge.required_factors:
            raise ApplicationError(
                "STEP_UP_FACTOR_NOT_REQUIRED",
                f"El factor {factor} no es requerido para este desafío.",
                422,
            )

        challenge.attempts += 1

        if result != "passed":
            if challenge.attempts >= challenge.max_attempts:
                challenge.status = ChallengeStatus.LOCKED.value
                challenge.failed_at = utc_now()
                db.flush()
                raise ApplicationError("STEP_UP_CHALLENGE_LOCKED", "El desafío ha sido bloqueado por exceder intentos.", 423)
            db.flush()
            return challenge

        # Check if all required factors are satisfied
        # In this simplified version, a single "passed" on the combined factor is enough
        # Real implementation would track individual factor results
        challenge.status = ChallengeStatus.PASSED.value
        challenge.completed_at = utc_now()
        db.flush()
        return challenge

    def complete_challenge(
        self,
        db: Session,
        challenge: StepUpChallenge,
    ) -> StepUpProof:
        """Complete a passed challenge and issue a proof."""
        if challenge.status != ChallengeStatus.PASSED.value:
            raise ApplicationError(
                "STEP_UP_CHALLENGE_NOT_PASSED",
                "El desafío no ha sido aprobado.",
                409,
            )

        now = utc_now()
        expires_at = now + timedelta(seconds=PROOF_TTL_SECONDS)

        # Build hash
        hash_payload = f"{challenge.id}:{challenge.user_id}:{challenge.session_id}:{challenge.permission_code}:{challenge.resource_id}"
        proof_hash = hashlib.sha256(hash_payload.encode()).hexdigest()

        proof = StepUpProof(
            challenge_id=challenge.id,
            user_id=challenge.user_id,
            session_id=challenge.session_id,
            device_id=challenge.device_id,
            permission_code=challenge.permission_code,
            action_code=challenge.action_code,
            resource_type=challenge.resource_type,
            resource_id=challenge.resource_id,
            organization_id=challenge.organization_id,
            branch_id=challenge.branch_id,
            warehouse_id=challenge.warehouse_id,
            status=ProofStatus.ACTIVE.value,
            one_time=True,
            proof_hash=proof_hash,
            policy_version=POLICY_VERSION,
            issued_at=now,
            expires_at=expires_at,
        )
        db.add(proof)
        db.flush()
        return proof

    def find_valid_proof(
        self,
        db: Session,
        user_id: UUID,
        session_id: UUID,
        permission_code: str,
        resource_type: str | None = None,
        resource_id: str | None = None,
    ) -> StepUpProof | None:
        """Find a valid (non-expired, non-consumed) proof for the given context."""
        now = utc_now()
        proofs = list(db.scalars(
            select(StepUpProof).where(
                StepUpProof.user_id == user_id,
                StepUpProof.session_id == session_id,
                StepUpProof.permission_code == permission_code,
                StepUpProof.status == ProofStatus.ACTIVE.value,
                StepUpProof.expires_at > now,
            ).order_by(StepUpProof.issued_at.desc())
        ))
        for proof in proofs:
            # Validate resource match if specified
            if resource_type and proof.resource_type and proof.resource_type != resource_type:
                continue
            if resource_id and proof.resource_id and proof.resource_id != str(resource_id):
                continue
            return proof
        return None

    def consume_proof(self, db: Session, proof: StepUpProof) -> StepUpProof:
        """Consume a one-time proof."""
        if proof.status != ProofStatus.ACTIVE.value:
            raise ApplicationError("STEP_UP_PROOF_CONSUMED", "La prueba ya fue consumida.", 409)
        if utc_now() > proof.expires_at:
            proof.status = ProofStatus.EXPIRED.value
            db.flush()
            raise ApplicationError("STEP_UP_PROOF_EXPIRED", "La prueba ha expirado.", 410)
        if proof.one_time:
            proof.status = ProofStatus.CONSUMED.value
            proof.consumed_at = utc_now()
            db.flush()
        return proof

    def revoke_session_proofs(self, db: Session, session_id: UUID) -> int:
        """Revoke all active proofs for a session (on logout/revocation)."""
        proofs = list(db.scalars(
            select(StepUpProof).where(
                StepUpProof.session_id == session_id,
                StepUpProof.status == ProofStatus.ACTIVE.value,
            )
        ))
        for proof in proofs:
            proof.status = ProofStatus.REVOKED.value
        db.flush()
        return len(proofs)

    def evaluate_risk(
        self,
        principal: LogisticsPrincipal,
        permission_code: str,
        session_risk_score: float | None = None,
    ) -> dict:
        """Evaluate risk for a sensitive action and return a decision."""
        policy = get_policy(permission_code)
        if not policy:
            return {
                "decision": RiskDecision.ALLOW.value,
                "risk_level": RiskLevel.LOW.value,
                "required_factors": [],
                "reason_codes": [],
            }

        # Check session risk
        risk_score = session_risk_score or 0.0
        base_level = policy.base_risk_level.value

        # If session risk is high, escalate
        if risk_score > 0.6:
            return {
                "decision": RiskDecision.STEP_UP_REQUIRED.value,
                "risk_level": RiskLevel.HIGH.value,
                "risk_score": risk_score,
                "required_factors": [f.value for f in policy.required_factors],
                "reason_codes": ["SESSION_RISK_HIGH"],
            }

        # If fail_closed and components unavailable, deny
        # For now, require step-up for all sensitive permissions
        return {
            "decision": RiskDecision.STEP_UP_REQUIRED.value,
            "risk_level": base_level,
            "risk_score": risk_score,
            "required_factors": [f.value for f in policy.required_factors],
            "reason_codes": ["SENSITIVE_PERMISSION"],
        }


step_up_service = StepUpService()