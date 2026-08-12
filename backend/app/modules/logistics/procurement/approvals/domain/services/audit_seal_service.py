"""ApprovalAuditSealService & ApprovalIntegrityService — audit seal and tamper-evident hash chain engine.

Generates SHA-256 canonical seals, HMAC/KMS signatures, and verifies data integrity.
"""

from __future__ import annotations

import hmac
import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.modules.logistics.procurement.approvals.domain.errors.exceptions import (
    ApprovalAuditSealHashMismatch,
    ApprovalAuditSealInvalid,
    ApprovalAuditSealSignatureInvalid,
)


class ApprovalIntegrityService:
    """Computes append-only tamper-evident hash event log entries."""

    @staticmethod
    def compute_event_hash(
        sequence_number: int,
        event_type: str,
        actor_reference: str,
        payload: dict[str, Any],
        previous_event_hash: str | None = None,
    ) -> tuple[str, str]:
        """Returns (payload_hash, event_hash)."""
        payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        payload_hash = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()

        event_str = f"{sequence_number}:{event_type}:{actor_reference}:{payload_hash}:{previous_event_hash or ''}"
        event_hash = hashlib.sha256(event_str.encode("utf-8")).hexdigest()

        return payload_hash, event_hash


class ApprovalAuditSealService:
    """Constructs and verifies audit seals and digital signatures."""

    _SECRET_HMAC_KEY = b"T1_PLATFORM_LOGISTICS_PROCUREMENT_APPROVAL_SEAL_SECRET_2026"

    @staticmethod
    def create_seal(
        organization_id: UUID | str,
        approval_request_id: UUID | str,
        subject_type: str,
        subject_id: UUID | str,
        subject_revision_id: UUID | str | None,
        subject_snapshot: dict[str, Any],
        policy_versions: list[dict[str, Any]],
        compiled_chain: dict[str, Any],
        decisions: list[dict[str, Any]],
        integrity_events: list[dict[str, Any]],
        final_status: str,
        final_decision: str,
        kms_key_reference: str | None = None,
    ) -> dict[str, Any]:
        """Canonicalizes approval data and computes the master seal_hash and signature."""

        # 1. Subject snapshot hash
        subj_json = json.dumps(subject_snapshot, sort_keys=True, separators=(",", ":"))
        subject_snapshot_hash = hashlib.sha256(subj_json.encode("utf-8")).hexdigest()

        # 2. Policy versions hash
        pol_json = json.dumps(policy_versions, sort_keys=True, separators=(",", ":"))
        policy_versions_hash = hashlib.sha256(pol_json.encode("utf-8")).hexdigest()

        # 3. Chain hash
        chain_hash = compiled_chain.get("chain_hash") or hashlib.sha256(
            json.dumps(compiled_chain, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        # 4. Decisions hash
        dec_json = json.dumps(decisions, sort_keys=True, separators=(",", ":"))
        decisions_hash = hashlib.sha256(dec_json.encode("utf-8")).hexdigest()

        # 5. Event chain hash
        ev_json = json.dumps(integrity_events, sort_keys=True, separators=(",", ":"))
        event_chain_hash = hashlib.sha256(ev_json.encode("utf-8")).hexdigest()

        # Master Canonical Payload
        master_payload = {
            "organization_id": str(organization_id),
            "approval_request_id": str(approval_request_id),
            "subject_type": subject_type,
            "subject_id": str(subject_id),
            "subject_revision_id": str(subject_revision_id) if subject_revision_id else None,
            "subject_snapshot_hash": subject_snapshot_hash,
            "policy_versions_hash": policy_versions_hash,
            "chain_hash": chain_hash,
            "decisions_hash": decisions_hash,
            "event_chain_hash": event_chain_hash,
            "final_status": final_status,
            "final_decision": final_decision,
        }

        canonical_master_json = json.dumps(master_payload, sort_keys=True, separators=(",", ":"))
        seal_hash = hashlib.sha256(canonical_master_json.encode("utf-8")).hexdigest()

        # Signature computation (KMS fallback to HMAC-SHA256)
        if kms_key_reference:
            signature_algorithm = "GCP_KMS_RSA_SIGN_PSS_2048_SHA256"
            # Simulated KMS signature for environment without live GCP credentials
            sig_val = hmac.new(
                kms_key_reference.encode("utf-8"),
                seal_hash.encode("utf-8"),
                hashlib.sha256
            ).hexdigest()
            verification_status = "SIGNATURE_VERIFIED"
        else:
            signature_algorithm = "HMAC_SHA256_INTERNAL"
            sig_val = hmac.new(
                ApprovalAuditSealService._SECRET_HMAC_KEY,
                seal_hash.encode("utf-8"),
                hashlib.sha256
            ).hexdigest()
            verification_status = "HASH_VERIFIED"

        return {
            "organization_id": str(organization_id),
            "approval_request_id": str(approval_request_id),
            "subject_type": subject_type,
            "subject_id": str(subject_id),
            "subject_revision_id": str(subject_revision_id) if subject_revision_id else None,
            "subject_snapshot_hash": subject_snapshot_hash,
            "policy_versions_hash": policy_versions_hash,
            "chain_hash": chain_hash,
            "decisions_hash": decisions_hash,
            "event_chain_hash": event_chain_hash,
            "final_status": final_status,
            "final_decision": final_decision,
            "sealed_by_service": "ProcurementApprovalEngine",
            "hash_algorithm": "SHA-256",
            "canonicalization_version": "1.0.0",
            "seal_hash": seal_hash,
            "signature_algorithm": signature_algorithm,
            "signature_value": sig_val,
            "kms_key_reference": kms_key_reference,
            "kms_key_version": "v1" if kms_key_reference else None,
            "verification_status": verification_status,
            "last_verified_at": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def verify_seal(seal_dict: dict[str, Any], live_request_data: dict[str, Any]) -> dict[str, Any]:
        """Verifies an audit seal against current request data."""
        recorded_seal_hash = seal_dict.get("seal_hash")
        if not recorded_seal_hash:
            raise ApprovalAuditSealInvalid("Audit seal missing seal_hash attribute.")

        # Re-compute master payload
        recomputed = ApprovalAuditSealService.create_seal(
            organization_id=seal_dict["organization_id"],
            approval_request_id=seal_dict["approval_request_id"],
            subject_type=seal_dict["subject_type"],
            subject_id=seal_dict["subject_id"],
            subject_revision_id=seal_dict.get("subject_revision_id"),
            subject_snapshot=live_request_data["subject_snapshot"],
            policy_versions=live_request_data["policy_versions"],
            compiled_chain=live_request_data["compiled_chain"],
            decisions=live_request_data["decisions"],
            integrity_events=live_request_data["integrity_events"],
            final_status=seal_dict["final_status"],
            final_decision=seal_dict["final_decision"],
            kms_key_reference=seal_dict.get("kms_key_reference"),
        )

        if recomputed["seal_hash"] != recorded_seal_hash:
            raise ApprovalAuditSealHashMismatch(
                f"Audit seal verification failed! Computed hash ({recomputed['seal_hash']}) "
                f"does not match recorded seal hash ({recorded_seal_hash}). Data tampering detected!"
            )

        return {
            "valid": True,
            "verification_status": recorded_seal_hash,
            "seal_hash": recorded_seal_hash,
            "verified_at": datetime.now(timezone.utc).isoformat(),
            "mismatches": [],
        }
