"""SQLAlchemy 2 models for Phase 035 — Procurement Approvals Engine.

Defines 17 persistent ORM models supporting policies, versions, conditions,
step definitions, approval requests, step instances, assignments, decisions,
delegations, escalations, audit seals, and hash integrity event chains.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.database.base import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# 1. Policy & Version Models
# ---------------------------------------------------------------------------
class ProcurementApprovalPolicyModel(Base):
    """Aggregate root for a procurement approval policy."""
    __tablename__ = "procurement_approval_policies"
    __allow_unmapped__ = True

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    code = Column(String(50), nullable=False)
    normalized_code = Column(String(50), nullable=False)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    subject_type = Column(String(50), nullable=False, index=True)  # PURCHASE_ORDER, REVISION, etc.
    priority = Column(Integer, nullable=False, default=100)
    status = Column(String(20), nullable=False, default="DRAFT", index=True)  # DRAFT, ACTIVE, INACTIVE, ARCHIVED
    active_version_id = Column(UUID(as_uuid=True), nullable=True)
    effective_scope = Column(String(50), nullable=False, default="ORGANIZATION")  # ORGANIZATION, BRANCH, COST_CENTER
    is_fallback = Column(Boolean, nullable=False, default=False)
    created_by = Column(UUID(as_uuid=True), nullable=False)
    updated_by = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now, onupdate=_utc_now)
    row_version = Column(Integer, nullable=False, default=1)

    versions = relationship("ProcurementApprovalPolicyVersionModel", back_populates="policy", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("organization_id", "normalized_code", name="uq_proc_appr_policy_org_code"),
        CheckConstraint("status IN ('DRAFT', 'ACTIVE', 'INACTIVE', 'ARCHIVED')", name="ck_proc_appr_policy_status"),
        CheckConstraint("priority >= 1 AND priority <= 9999", name="ck_proc_appr_policy_priority"),
    )


class ProcurementApprovalPolicyVersionModel(Base):
    """Immutable version of a policy."""
    __tablename__ = "procurement_approval_policy_versions"
    __allow_unmapped__ = True

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_id = Column(UUID(as_uuid=True), ForeignKey("procurement_approval_policies.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="DRAFT", index=True)  # DRAFT, VALIDATED, ACTIVE, RETIRED, ARCHIVED
    effective_from = Column(DateTime(timezone=True), nullable=False, default=_utc_now)
    effective_to = Column(DateTime(timezone=True), nullable=True)
    matching_mode = Column(String(30), nullable=False, default="ALL_GROUPS")  # ALL_GROUPS, ANY_GROUP
    mixed_category_strategy = Column(String(40), nullable=False, default="MOST_RESTRICTIVE_UNION")
    amount_currency_policy = Column(String(40), nullable=False, default="SUBJECT_CURRENCY")
    separation_of_duties_policy = Column(String(50), nullable=False, default="CREATOR_CANNOT_BE_SOLE_APPROVER")
    default_step_deadline_hours = Column(Integer, nullable=True)
    escalation_enabled = Column(Boolean, nullable=False, default=True)
    delegation_enabled = Column(Boolean, nullable=False, default=True)
    content_hash = Column(String(64), nullable=True)
    compiler_version = Column(String(20), nullable=False, default="1.0.0")
    created_by = Column(UUID(as_uuid=True), nullable=False)
    validated_by = Column(UUID(as_uuid=True), nullable=True)
    validated_at = Column(DateTime(timezone=True), nullable=True)
    activated_by = Column(UUID(as_uuid=True), nullable=True)
    activated_at = Column(DateTime(timezone=True), nullable=True)
    retired_by = Column(UUID(as_uuid=True), nullable=True)
    retired_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)

    policy = relationship("ProcurementApprovalPolicyModel", back_populates="versions")
    conditions = relationship("ApprovalPolicyConditionModel", back_populates="version", cascade="all, delete-orphan")
    steps = relationship("ApprovalPolicyStepDefinitionModel", back_populates="version", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("policy_id", "version_number", name="uq_proc_appr_version_policy_num"),
        CheckConstraint("status IN ('DRAFT', 'VALIDATED', 'ACTIVE', 'RETIRED', 'ARCHIVED')", name="ck_proc_appr_version_status"),
    )


# ---------------------------------------------------------------------------
# 2. Conditions & Step Definitions
# ---------------------------------------------------------------------------
class ApprovalPolicyConditionModel(Base):
    """Typed condition parameter within a policy version."""
    __tablename__ = "approval_policy_conditions"
    __allow_unmapped__ = True

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_version_id = Column(UUID(as_uuid=True), ForeignKey("procurement_approval_policy_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    condition_group = Column(String(20), nullable=False, default="ALL")  # ALL, ANY
    field_code = Column(String(50), nullable=False)  # TOTAL_AMOUNT, CURRENCY_CODE, COST_CENTER_ID, PRODUCT_CATEGORY_ID, etc.
    operator = Column(String(30), nullable=False)    # EQUALS, IN, GREATER_THAN_OR_EQUAL, BETWEEN, CONTAINS_ANY
    value_type = Column(String(20), nullable=False, default="STRING")  # STRING, DECIMAL, UUID, LIST, JSON
    value_data = Column(JSONB, nullable=False)        # Structured JSON value
    order_index = Column(Integer, nullable=False, default=1)
    is_required = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)

    version = relationship("ProcurementApprovalPolicyVersionModel", back_populates="conditions")


class ApprovalPolicyStepDefinitionModel(Base):
    """Step definition within a policy version."""
    __tablename__ = "approval_policy_step_definitions"
    __allow_unmapped__ = True

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_version_id = Column(UUID(as_uuid=True), ForeignKey("procurement_approval_policy_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    step_code = Column(String(50), nullable=False)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    order_index = Column(Integer, nullable=False, default=1)
    execution_mode = Column(String(20), nullable=False, default="SEQUENTIAL")  # SEQUENTIAL, PARALLEL_GROUP
    completion_mode = Column(String(30), nullable=False, default="ALL")       # ALL, ANY_ONE, QUORUM, UNANIMOUS
    minimum_approvals = Column(Integer, nullable=False, default=1)
    required_approvals = Column(Integer, nullable=False, default=1)
    approver_source_type = Column(String(50), nullable=False)  # FIXED_USER, ROLE_SCOPE, COST_CENTER_RESPONSIBLE, PRODUCT_CATEGORY_OWNER, etc.
    approver_source_config = Column(JSONB, nullable=False)
    permission_required = Column(String(100), nullable=False, default="logistics.purchase_orders.approve")
    step_up_level = Column(String(20), nullable=False, default="HIGH")        # NONE, LOW, MEDIUM, HIGH, CRITICAL
    deadline_hours = Column(Integer, nullable=True)
    allow_delegation = Column(Boolean, nullable=False, default=True)
    allow_abstention = Column(Boolean, nullable=False, default=False)
    allow_return = Column(Boolean, nullable=False, default=True)
    allow_request_information = Column(Boolean, nullable=False, default=True)
    distinct_from_creator = Column(Boolean, nullable=False, default=True)
    distinct_from_requester = Column(Boolean, nullable=False, default=True)
    distinct_from_previous_steps = Column(Boolean, nullable=False, default=False)
    is_mandatory = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)

    version = relationship("ProcurementApprovalPolicyVersionModel", back_populates="steps")
    escalation_rules = relationship("ApprovalEscalationRuleModel", back_populates="step_definition", cascade="all, delete-orphan")


class ApprovalEscalationRuleModel(Base):
    """Escalation rule for a step definition."""
    __tablename__ = "approval_escalation_rules"
    __allow_unmapped__ = True

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    step_definition_id = Column(UUID(as_uuid=True), ForeignKey("approval_policy_step_definitions.id", ondelete="CASCADE"), nullable=False, index=True)
    trigger_after_hours = Column(Integer, nullable=False)
    repeat_every_hours = Column(Integer, nullable=True)
    maximum_repeats = Column(Integer, nullable=False, default=1)
    action_type = Column(String(30), nullable=False)  # REMIND, NOTIFY_MANAGER, ADD_APPROVER, REASSIGN, ESCALATE_TO_ROLE
    target_source_type = Column(String(50), nullable=False)
    target_source_config = Column(JSONB, nullable=False)
    preserve_original_assignment = Column(Boolean, nullable=False, default=True)
    status = Column(String(20), nullable=False, default="ACTIVE")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)

    step_definition = relationship("ApprovalPolicyStepDefinitionModel", back_populates="escalation_rules")


# ---------------------------------------------------------------------------
# 3. Approval Request & Runtime Models
# ---------------------------------------------------------------------------
class ProcurementApprovalRequestModel(Base):
    """Runtime instance of an approval request for a purchasing resource."""
    __tablename__ = "procurement_approval_requests"
    __allow_unmapped__ = True

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    request_code = Column(String(50), nullable=False, index=True)
    subject_type = Column(String(50), nullable=False, index=True)  # PURCHASE_ORDER, REVISION, etc.
    subject_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    subject_revision_id = Column(UUID(as_uuid=True), nullable=True)
    subject_code = Column(String(100), nullable=True)
    subject_snapshot = Column(JSONB, nullable=False)
    subject_snapshot_hash = Column(String(64), nullable=False)
    policy_resolution_snapshot = Column(JSONB, nullable=False)
    compiled_chain = Column(JSONB, nullable=False)
    chain_hash = Column(String(64), nullable=False)
    status = Column(String(30), nullable=False, default="CREATED", index=True)  # CREATED, IN_PROGRESS, APPROVED, REJECTED, RETURNED_FOR_CHANGES, CANCELLED
    current_sequence = Column(Integer, nullable=False, default=1)
    amount = Column(Numeric(28, 10), nullable=False)
    currency_code = Column(String(3), nullable=False)
    comparison_amount = Column(Numeric(28, 10), nullable=True)
    comparison_currency_code = Column(String(3), nullable=True)
    cost_center_snapshot = Column(JSONB, nullable=True)
    category_snapshots = Column(JSONB, nullable=True)
    branch_snapshot = Column(JSONB, nullable=True)
    requester_user_id = Column(UUID(as_uuid=True), nullable=False)
    requester_snapshot = Column(JSONB, nullable=False)
    creator_user_id = Column(UUID(as_uuid=True), nullable=False)
    creator_snapshot = Column(JSONB, nullable=False)
    submitted_by = Column(UUID(as_uuid=True), nullable=False)
    submitted_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    final_decision = Column(String(30), nullable=True)
    final_decision_at = Column(DateTime(timezone=True), nullable=True)
    final_decision_by = Column(UUID(as_uuid=True), nullable=True)
    supersedes_request_id = Column(UUID(as_uuid=True), nullable=True)
    superseded_by_request_id = Column(UUID(as_uuid=True), nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    return_reason = Column(Text, nullable=True)
    audit_seal_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now, onupdate=_utc_now)
    row_version = Column(Integer, nullable=False, default=1)

    steps = relationship("ApprovalStepInstanceModel", back_populates="request", cascade="all, delete-orphan")
    assignments = relationship("ApprovalAssignmentModel", back_populates="request", cascade="all, delete-orphan")
    decisions = relationship("ApprovalDecisionModel", back_populates="request", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("status IN ('CREATED', 'RESOLVING', 'READY', 'IN_PROGRESS', 'WAITING_INFORMATION', 'APPROVED', 'REJECTED', 'RETURNED_FOR_CHANGES', 'CANCELLED', 'EXPIRED', 'SUPERSEDED', 'FAILED', 'ARCHIVED')", name="ck_proc_appr_req_status"),
        CheckConstraint("amount >= 0", name="ck_proc_appr_req_amount_ge_zero"),
    )


class ApprovalExchangeRateSnapshotModel(Base):
    """Frozen exchange rate snapshot for currency conversion during approval."""
    __tablename__ = "approval_exchange_rate_snapshots"
    __allow_unmapped__ = True

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    approval_request_id = Column(UUID(as_uuid=True), ForeignKey("procurement_approval_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    source_currency = Column(String(3), nullable=False)
    target_currency = Column(String(3), nullable=False)
    rate = Column(Numeric(28, 10), nullable=False)
    source_name = Column(String(100), nullable=False, default="SYSTEM_OFFICIAL_RATE")
    source_reference = Column(String(100), nullable=True)
    source_date = Column(DateTime(timezone=True), nullable=False, default=_utc_now)
    captured_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)
    approved_by = Column(UUID(as_uuid=True), nullable=True)
    content_hash = Column(String(64), nullable=False)

    __table_args__ = (
        CheckConstraint("rate > 0", name="ck_proc_appr_rate_gt_zero"),
    )


class ApprovalStepInstanceModel(Base):
    """Runtime instance of a step within an approval request."""
    __tablename__ = "approval_step_instances"
    __allow_unmapped__ = True

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    approval_request_id = Column(UUID(as_uuid=True), ForeignKey("procurement_approval_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    step_definition_id = Column(UUID(as_uuid=True), nullable=False)
    step_code = Column(String(50), nullable=False)
    name_snapshot = Column(String(150), nullable=False)
    sequence_number = Column(Integer, nullable=False, default=1)
    execution_mode = Column(String(20), nullable=False, default="SEQUENTIAL")
    completion_mode = Column(String(30), nullable=False, default="ALL")
    minimum_approvals = Column(Integer, nullable=False, default=1)
    required_approvals = Column(Integer, nullable=False, default=1)
    status = Column(String(20), nullable=False, default="PENDING", index=True)  # PENDING, READY, ACTIVE, APPROVED, REJECTED, RETURNED, SKIPPED, CANCELLED
    activated_at = Column(DateTime(timezone=True), nullable=True)
    due_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    completion_result = Column(String(30), nullable=True)
    escalation_level = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now, onupdate=_utc_now)
    row_version = Column(Integer, nullable=False, default=1)

    request = relationship("ProcurementApprovalRequestModel", back_populates="steps")
    assignments = relationship("ApprovalAssignmentModel", back_populates="step_instance", cascade="all, delete-orphan")


class ApprovalAssignmentModel(Base):
    """Assignment task for an effective approver."""
    __tablename__ = "approval_assignments"
    __allow_unmapped__ = True

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    approval_request_id = Column(UUID(as_uuid=True), ForeignKey("procurement_approval_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    step_instance_id = Column(UUID(as_uuid=True), ForeignKey("approval_step_instances.id", ondelete="CASCADE"), nullable=False, index=True)
    original_approver_user_id = Column(UUID(as_uuid=True), nullable=False)
    effective_approver_user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    approver_snapshot = Column(JSONB, nullable=False)
    assignment_source_type = Column(String(50), nullable=False)
    assignment_source_reference = Column(String(100), nullable=True)
    delegation_id = Column(UUID(as_uuid=True), nullable=True)
    status = Column(String(20), nullable=False, default="ASSIGNED", index=True)  # ASSIGNED, VIEWED, ACTED, DELEGATED, ESCALATED, REVOKED, CANCELLED
    assigned_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)
    due_at = Column(DateTime(timezone=True), nullable=True)
    viewed_at = Column(DateTime(timezone=True), nullable=True)
    acted_at = Column(DateTime(timezone=True), nullable=True)
    escalated_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revocation_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)

    request = relationship("ProcurementApprovalRequestModel", back_populates="assignments")
    step_instance = relationship("ApprovalStepInstanceModel", back_populates="assignments")
    decisions = relationship("ApprovalDecisionModel", back_populates="assignment")


class ApprovalDecisionModel(Base):
    """Append-only record of an approval decision."""
    __tablename__ = "approval_decisions"
    __allow_unmapped__ = True

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    approval_request_id = Column(UUID(as_uuid=True), ForeignKey("procurement_approval_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    step_instance_id = Column(UUID(as_uuid=True), ForeignKey("approval_step_instances.id", ondelete="CASCADE"), nullable=False, index=True)
    assignment_id = Column(UUID(as_uuid=True), ForeignKey("approval_assignments.id", ondelete="CASCADE"), nullable=False, index=True)
    decision_type = Column(String(30), nullable=False)  # APPROVE, REJECT, RETURN_FOR_CHANGES, ABSTAIN, REQUEST_INFORMATION
    status = Column(String(20), nullable=False, default="RECORDED")
    decided_by_user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    approver_snapshot = Column(JSONB, nullable=False)
    acting_on_behalf_of_user_id = Column(UUID(as_uuid=True), nullable=True)
    delegation_id = Column(UUID(as_uuid=True), nullable=True)
    reason = Column(Text, nullable=True)
    conditions = Column(JSONB, nullable=True)
    step_up_assurance_level = Column(String(20), nullable=False, default="HIGH")
    decision_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)
    request_snapshot_hash = Column(String(64), nullable=False)
    step_snapshot_hash = Column(String(64), nullable=False)
    previous_event_hash = Column(String(64), nullable=True)
    decision_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)

    request = relationship("ProcurementApprovalRequestModel", back_populates="decisions")
    assignment = relationship("ApprovalAssignmentModel", back_populates="decisions")


class ApprovalInformationRequestModel(Base):
    """Clarification request raised during approval."""
    __tablename__ = "approval_information_requests"
    __allow_unmapped__ = True

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    approval_request_id = Column(UUID(as_uuid=True), ForeignKey("procurement_approval_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    step_instance_id = Column(UUID(as_uuid=True), nullable=False)
    assignment_id = Column(UUID(as_uuid=True), nullable=False)
    question = Column(Text, nullable=False)
    requested_by = Column(UUID(as_uuid=True), nullable=False)
    requested_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)
    due_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), nullable=False, default="OPEN")  # OPEN, ANSWERED, CANCELLED, EXPIRED
    answered_by = Column(UUID(as_uuid=True), nullable=True)
    answer = Column(Text, nullable=True)
    answered_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)


# ---------------------------------------------------------------------------
# 4. Delegation, Emergency & Security Models
# ---------------------------------------------------------------------------
class ApprovalDelegationModel(Base):
    """Temporary delegation of approval authority."""
    __tablename__ = "approval_delegations"
    __allow_unmapped__ = True

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    delegator_user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    delegate_user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    scope_type = Column(String(30), nullable=False, default="ALL_APPROVALS")  # ALL_APPROVALS, SUBJECT_TYPES, COST_CENTERS, CATEGORIES
    subject_types = Column(JSONB, nullable=True)
    cost_center_ids = Column(JSONB, nullable=True)
    category_ids = Column(JSONB, nullable=True)
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_until = Column(DateTime(timezone=True), nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="ACTIVE", index=True)  # DRAFT, PENDING_APPROVAL, ACTIVE, EXPIRED, REVOKED
    created_by = Column(UUID(as_uuid=True), nullable=False)
    approved_by = Column(UUID(as_uuid=True), nullable=True)
    revoked_by = Column(UUID(as_uuid=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)

    __table_args__ = (
        CheckConstraint("delegator_user_id <> delegate_user_id", name="ck_proc_appr_delegation_distinct"),
        CheckConstraint("valid_from < valid_until", name="ck_proc_appr_delegation_dates"),
    )


class ApprovalEmergencyOverrideModel(Base):
    """Break-glass emergency override record."""
    __tablename__ = "approval_emergency_overrides"
    __allow_unmapped__ = True

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    approval_request_id = Column(UUID(as_uuid=True), ForeignKey("procurement_approval_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    override_type = Column(String(50), nullable=False)
    reason = Column(Text, nullable=False)
    incident_reference = Column(String(100), nullable=False)
    requested_by = Column(UUID(as_uuid=True), nullable=False)
    approved_by = Column(UUID(as_uuid=True), nullable=False)
    applied_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    affected_rules = Column(JSONB, nullable=False)
    audit_seal_id = Column(UUID(as_uuid=True), nullable=True)
    status = Column(String(20), nullable=False, default="APPLIED")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)

    __table_args__ = (
        CheckConstraint("requested_by <> approved_by", name="ck_proc_appr_override_distinct"),
    )


# ---------------------------------------------------------------------------
# 5. Audit Seal, Integrity Chain & Auxiliary Models
# ---------------------------------------------------------------------------
class ApprovalAuditSealModel(Base):
    """Immutable audit seal and KMS digital signature for a completed approval chain."""
    __tablename__ = "approval_audit_seals"
    __allow_unmapped__ = True

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    approval_request_id = Column(UUID(as_uuid=True), ForeignKey("procurement_approval_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_type = Column(String(50), nullable=False)
    subject_id = Column(UUID(as_uuid=True), nullable=False)
    subject_revision_id = Column(UUID(as_uuid=True), nullable=True)
    subject_snapshot_hash = Column(String(64), nullable=False)
    policy_versions_hash = Column(String(64), nullable=False)
    chain_hash = Column(String(64), nullable=False)
    decisions_hash = Column(String(64), nullable=False)
    event_chain_hash = Column(String(64), nullable=False)
    final_status = Column(String(30), nullable=False)
    final_decision = Column(String(30), nullable=False)
    sealed_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)
    sealed_by_service = Column(String(100), nullable=False, default="ProcurementApprovalEngine")
    hash_algorithm = Column(String(20), nullable=False, default="SHA-256")
    canonicalization_version = Column(String(20), nullable=False, default="1.0.0")
    seal_hash = Column(String(64), nullable=False)
    signature_algorithm = Column(String(50), nullable=True)
    signature_value = Column(Text, nullable=True)
    kms_key_reference = Column(String(255), nullable=True)
    kms_key_version = Column(String(100), nullable=True)
    verification_status = Column(String(30), nullable=False, default="HASH_VERIFIED")  # HASH_VERIFIED, SIGNATURE_VERIFIED, HASH_MISMATCH
    last_verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)


class ApprovalIntegrityEventModel(Base):
    """Append-only tamper-evident hash event log for an approval request."""
    __tablename__ = "approval_integrity_events"
    __allow_unmapped__ = True

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    approval_request_id = Column(UUID(as_uuid=True), ForeignKey("procurement_approval_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    sequence_number = Column(Integer, nullable=False)
    event_type = Column(String(50), nullable=False)
    actor_reference = Column(String(100), nullable=False)
    event_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)
    payload_hash = Column(String(64), nullable=False)
    previous_event_hash = Column(String(64), nullable=True)
    event_hash = Column(String(64), nullable=False)
    correlation_id = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)

    __table_args__ = (
        UniqueConstraint("approval_request_id", "sequence_number", name="uq_proc_appr_integrity_seq"),
    )


class ApprovalNotificationJobModel(Base):
    """Transactional outbox job for approval notifications."""
    __tablename__ = "approval_notification_jobs"
    __allow_unmapped__ = True

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    approval_request_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)
    recipient_user_id = Column(UUID(as_uuid=True), nullable=False)
    payload = Column(JSONB, nullable=False)
    status = Column(String(20), nullable=False, default="PENDING", index=True)  # PENDING, SENT, FAILED
    retry_count = Column(Integer, nullable=False, default=0)
    scheduled_for = Column(DateTime(timezone=True), nullable=False, default=_utc_now)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)


class ApprovalMigrationRecordModel(Base):
    """Audit log of legacy/transitional approval migrations to Phase 035 engine."""
    __tablename__ = "approval_migration_records"
    __allow_unmapped__ = True

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    purchase_order_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    previous_approval_status = Column(String(50), nullable=False)
    migration_action = Column(String(50), nullable=False)  # MIGRATED, REQUIRES_REAPPROVAL, PRESERVED_AS_LEGACY
    new_approval_request_id = Column(UUID(as_uuid=True), nullable=True)
    notes = Column(Text, nullable=True)
    migrated_by = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)
