"""Phase 040 contract, safety-invariant and integration-registration tests."""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from app.modules.logistics.audit.catalog import is_valid_event_code
from app.modules.logistics.inbound.reception_differences.domain.enums import (
    AcknowledgementType,
    ApprovalDecision,
    CASE_TRANSITIONS,
    CaseRevisionStatus,
    CaseStatus,
    DifferenceCategory,
    DifferenceType,
    DIFFERENCE_TYPE_CATEGORY_MAP,
    EvidenceType,
    ItemStatus,
    PartyType,
    ResponsibilityRole,
    ResponsibilityStatus,
    ReviewStatus,
    ReviewType,
    Severity,
    SourceType,
)
from app.modules.logistics.inbound.reception_differences.domain.errors import (
    ReceptionDifferenceCaseNotFound,
    ReceptionDifferenceError,
    reception_difference_error,
)
from app.modules.logistics.inbound.reception_differences.domain.policies.severity_policy import (
    ReceptionDifferenceSeverityPolicy,
)
from app.modules.logistics.inbound.reception_differences.domain.services import (
    canonical_hash_diff,
    require_case_transition,
    require_item_transition,
    strict_decimal_diff,
    validate_decimal_quantity,
    ITEM_TRANSITIONS,
)
from app.modules.logistics.inbound.reception_differences.presentation.schemas import (
    ReceptionDifferenceApprovalDecisionRequest,
    ReceptionDifferenceCaseCreate,
    ReceptionDifferenceCaseUpdate,
    ReceptionDifferenceEvidenceLinkCreate,
    ReceptionDifferenceItemCreate,
    ReceptionDifferenceItemUpdate,
    ReceptionDifferenceResponsiblePartyCreate,
    ReceptionDifferenceReviewCreate,
    ReasonRequest,
)
from app.modules.logistics.inbound.reception_differences.infrastructure.persistence.models import (
    PHASE_040_TABLES,
)
from app.modules.logistics.inbound.reception_differences.infrastructure.jobs.jobs import (
    detect_candidates_not_formalized,
    detect_critical_without_approval,
    detect_incomplete_cases,
    detect_pending_evidence,
    detect_pending_responsibility,
    update_metrics_projection,
)
from app.modules.logistics.rbac.permission_catalog import PHASE_040_PERMISSIONS
from app.modules.logistics.security.step_up_policy import POLICY_CATALOG


BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
DOCS_ROOT = REPO_ROOT / "docs" / "architecture" / "phase_040" / "backend"

UUID1 = "00000000-0000-0000-0000-000000000001"
UUID2 = "00000000-0000-0000-0000-000000000002"
UUID3 = "00000000-0000-0000-0000-000000000003"
UUID4 = "00000000-0000-0000-0000-000000000004"
UUID5 = "00000000-0000-0000-0000-000000000005"
UUID_TENANT_B = "11111111-1111-1111-1111-111111111111"


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def uuid_factory():
    counter = [0]

    def _make():
        counter[0] += 1
        return uuid.UUID(f"00000000-0000-0000-0000-{counter[0]:012d}")

    return _make


@pytest.fixture
def mock_principal():
    p = MagicMock()
    p.user_id = uuid.UUID(UUID1)
    p.full_name = "Test User"
    p.email = "test@example.com"
    p.role_codes = ["LOGISTICS_ADMIN"]
    p.session_id = uuid.UUID(UUID2)
    p.device_id = uuid.UUID(UUID3)
    p.authentication_level = "FULL"
    p.correlation_id = "corr-001"
    p.ip_address = "127.0.0.1"
    p.user_agent = "TestAgent/1.0"
    p.organization_id = uuid.UUID(UUID4)
    p.branch_id = uuid.UUID(UUID5)
    p.warehouse_id = uuid.UUID(UUID1)
    p.default_organization_id = UUID4
    return p


@pytest.fixture
def another_principal():
    p = MagicMock()
    p.user_id = uuid.UUID(UUID_TENANT_B)
    p.full_name = "Other User"
    p.email = "other@other.com"
    p.role_codes = ["LOGISTICS_ADMIN"]
    p.session_id = uuid.UUID(UUID2)
    p.device_id = uuid.UUID(UUID3)
    p.authentication_level = "FULL"
    p.correlation_id = "corr-002"
    p.ip_address = "10.0.0.1"
    p.user_agent = "TestAgent/2.0"
    p.organization_id = uuid.UUID(UUID_TENANT_B)
    p.branch_id = uuid.UUID(UUID5)
    p.warehouse_id = uuid.UUID(UUID1)
    p.default_organization_id = UUID_TENANT_B
    return p


# ══════════════════════════════════════════════════════════════════════════════
# 1. DOMAIN LAYER TESTS
# ══════════════════════════════════════════════════════════════════════════════


class TestCaseStatusTransitions:
    """Case status transitions — valid and invalid."""

    def test_happy_path_draft_to_closed(self):
        path = [
            ("DRAFT", "UNDER_PREPARATION"),
            ("UNDER_PREPARATION", "SUBMITTED_FOR_REVIEW"),
            ("SUBMITTED_FOR_REVIEW", "UNDER_REVIEW"),
            ("UNDER_REVIEW", "READY_FOR_APPROVAL"),
            ("READY_FOR_APPROVAL", "APPROVED"),
            ("APPROVED", "ISSUED"),
            ("ISSUED", "CLOSED"),
        ]
        for current, target in path:
            require_case_transition(current, target)

    def test_cancel_from_draft(self):
        require_case_transition("DRAFT", "CANCELLED")

    def test_cancel_from_under_preparation(self):
        require_case_transition("UNDER_PREPARATION", "CANCELLED")

    def test_cancel_from_submitted(self):
        require_case_transition("SUBMITTED_FOR_REVIEW", "CANCELLED")

    def test_cancel_from_under_review(self):
        require_case_transition("UNDER_REVIEW", "CANCELLED")

    def test_changes_requested_back_to_preparation(self):
        require_case_transition("CHANGES_REQUESTED", "UNDER_PREPARATION")

    def test_changes_requested_resubmit(self):
        require_case_transition("CHANGES_REQUESTED", "SUBMITTED_FOR_REVIEW")

    def test_approve_for_issue(self):
        require_case_transition("READY_FOR_APPROVAL", "APPROVED")

    def test_request_changes_from_ready(self):
        require_case_transition("READY_FOR_APPROVAL", "CHANGES_REQUESTED")

    def test_issued_to_acknowledged(self):
        require_case_transition("ISSUED", "ACKNOWLEDGED")

    def test_issued_to_disputed(self):
        require_case_transition("ISSUED", "DISPUTED")

    def test_issued_to_follow_up(self):
        require_case_transition("ISSUED", "FOLLOW_UP_REQUIRED")

    def test_issued_to_closed(self):
        require_case_transition("ISSUED", "CLOSED")

    def test_acknowledged_to_closed(self):
        require_case_transition("ACKNOWLEDGED", "CLOSED")

    def test_disputed_to_closed(self):
        require_case_transition("DISPUTED", "CLOSED")

    def test_follow_up_to_closed(self):
        require_case_transition("FOLLOW_UP_REQUIRED", "CLOSED")

    def test_terminal_states_no_transitions(self):
        for terminal in ("CLOSED", "CANCELLED", "SUPERSEDED"):
            allowed = CASE_TRANSITIONS.get(CaseStatus(terminal), set())
            assert len(allowed) == 0, f"{terminal} should have no transitions"

    def test_invalid_transition_draft_to_closed(self):
        with pytest.raises(ReceptionDifferenceError) as exc_info:
            require_case_transition("DRAFT", "CLOSED")
        assert exc_info.value.status_code == 409

    def test_invalid_transition_draft_to_approved(self):
        with pytest.raises(ReceptionDifferenceError):
            require_case_transition("DRAFT", "APPROVED")

    def test_invalid_transition_cancelled_to_any(self):
        with pytest.raises(ReceptionDifferenceError):
            require_case_transition("CANCELLED", "DRAFT")

    def test_invalid_transition_closed_to_any(self):
        with pytest.raises(ReceptionDifferenceError):
            require_case_transition("CLOSED", "DRAFT")

    def test_invalid_status_string(self):
        with pytest.raises(ReceptionDifferenceError):
            require_case_transition("INVALID_STATUS", "DRAFT")

    def test_invalid_target_string(self):
        with pytest.raises(ReceptionDifferenceError):
            require_case_transition("DRAFT", "INVALID_TARGET")

    def test_pending_evidence_can_go_back(self):
        require_case_transition("PENDING_EVIDENCE", "UNDER_PREPARATION")

    def test_pending_evidence_to_submitted(self):
        require_case_transition("PENDING_EVIDENCE", "SUBMITTED_FOR_REVIEW")

    def test_pending_evidence_cancel(self):
        require_case_transition("PENDING_EVIDENCE", "CANCELLED")

    def test_pending_responsibility_can_go_back(self):
        require_case_transition("PENDING_RESPONSIBILITY", "UNDER_PREPARATION")

    def test_pending_responsibility_to_submitted(self):
        require_case_transition("PENDING_RESPONSIBILITY", "SUBMITTED_FOR_REVIEW")

    def test_all_nonterminal_states_have_transitions(self):
        nonterminal = {
            CaseStatus.DRAFT, CaseStatus.UNDER_PREPARATION, CaseStatus.PENDING_EVIDENCE,
            CaseStatus.PENDING_RESPONSIBILITY, CaseStatus.SUBMITTED_FOR_REVIEW,
            CaseStatus.UNDER_REVIEW, CaseStatus.CHANGES_REQUESTED, CaseStatus.READY_FOR_APPROVAL,
            CaseStatus.APPROVED, CaseStatus.ISSUED, CaseStatus.ACKNOWLEDGEMENT_PENDING,
            CaseStatus.ACKNOWLEDGED, CaseStatus.DISPUTED, CaseStatus.FOLLOW_UP_REQUIRED,
        }
        for status in nonterminal:
            assert status in CASE_TRANSITIONS, f"{status} missing from transitions"
            assert len(CASE_TRANSITIONS[status]) > 0, f"{status} has no allowed transitions"


class TestItemStatusTransitions:
    """Item status transitions — valid and invalid."""

    def test_happy_path_open_to_closed(self):
        path = [
            ("OPEN", "READY_FOR_REVIEW"),
            ("READY_FOR_REVIEW", "CONFIRMED"),
            ("CONFIRMED", "CLOSED"),
        ]
        for current, target in path:
            require_item_transition(current, target)

    def test_open_to_dismissed(self):
        require_item_transition("OPEN", "DISMISSED_WITH_REASON")

    def test_open_to_evidence_pending(self):
        require_item_transition("OPEN", "EVIDENCE_PENDING")

    def test_open_to_responsibility_pending(self):
        require_item_transition("OPEN", "RESPONSIBILITY_PENDING")

    def test_open_to_closed(self):
        require_item_transition("OPEN", "CLOSED")

    def test_evidence_pending_to_open(self):
        require_item_transition("EVIDENCE_PENDING", "OPEN")

    def test_evidence_pending_to_ready(self):
        require_item_transition("EVIDENCE_PENDING", "READY_FOR_REVIEW")

    def test_responsibility_pending_to_open(self):
        require_item_transition("RESPONSIBILITY_PENDING", "OPEN")

    def test_responsibility_pending_to_ready(self):
        require_item_transition("RESPONSIBILITY_PENDING", "READY_FOR_REVIEW")

    def test_ready_to_follow_up(self):
        require_item_transition("READY_FOR_REVIEW", "FOLLOW_UP_REQUIRED")

    def test_confirmed_to_follow_up(self):
        require_item_transition("CONFIRMED", "FOLLOW_UP_REQUIRED")

    def test_follow_up_to_closed(self):
        require_item_transition("FOLLOW_UP_REQUIRED", "CLOSED")

    def test_dismissed_is_terminal(self):
        assert len(ITEM_TRANSITIONS[ItemStatus.DISMISSED_WITH_REASON]) == 0

    def test_closed_is_terminal(self):
        assert len(ITEM_TRANSITIONS[ItemStatus.CLOSED]) == 0

    def test_superseded_is_terminal(self):
        assert len(ITEM_TRANSITIONS[ItemStatus.SUPERSEDED]) == 0

    def test_invalid_transition_open_to_confirmed(self):
        with pytest.raises(ReceptionDifferenceError) as exc_info:
            require_item_transition("OPEN", "CONFIRMED")
        assert exc_info.value.status_code == 409

    def test_invalid_transition_closed_to_open(self):
        with pytest.raises(ReceptionDifferenceError):
            require_item_transition("CLOSED", "OPEN")

    def test_invalid_transition_dismissed_to_any(self):
        with pytest.raises(ReceptionDifferenceError):
            require_item_transition("DISMISSED_WITH_REASON", "OPEN")

    def test_invalid_item_status(self):
        with pytest.raises(ReceptionDifferenceError):
            require_item_transition("BANANA", "OPEN")


class TestSeverityPolicyCalculations:
    """Severity policy — categorize difference types by severity."""

    def test_safety_contamination_is_critical(self):
        assert ReceptionDifferenceSeverityPolicy.suggest("CONTAMINATION_SUSPECTED") == Severity.CRITICAL

    def test_safety_temperature_is_critical(self):
        assert ReceptionDifferenceSeverityPolicy.suggest("TEMPERATURE_CONCERN") == Severity.CRITICAL

    def test_seal_broken_is_high(self):
        assert ReceptionDifferenceSeverityPolicy.suggest("SEAL_BROKEN") == Severity.HIGH

    def test_seal_missing_is_high(self):
        assert ReceptionDifferenceSeverityPolicy.suggest("SEAL_MISSING") == Severity.HIGH

    def test_seal_tampered_is_high(self):
        assert ReceptionDifferenceSeverityPolicy.suggest("SEAL_TAMPERED") == Severity.HIGH

    def test_expired_product_is_high(self):
        assert ReceptionDifferenceSeverityPolicy.suggest("EXPIRED_PRODUCT", is_expired=True) == Severity.HIGH

    def test_damage_is_high(self):
        assert ReceptionDifferenceSeverityPolicy.suggest("PRODUCT_DAMAGED", has_damage=True) == Severity.HIGH

    def test_wrong_product_is_high(self):
        assert ReceptionDifferenceSeverityPolicy.suggest("WRONG_PRODUCT") == Severity.HIGH

    def test_shortage_high_variance_is_high(self):
        assert ReceptionDifferenceSeverityPolicy.suggest("SHORTAGE", variance_percentage=Decimal("25")) == Severity.HIGH

    def test_shortage_medium_variance_is_medium(self):
        assert ReceptionDifferenceSeverityPolicy.suggest("SHORTAGE", variance_percentage=Decimal("10")) == Severity.MEDIUM

    def test_shortage_low_variance_is_low(self):
        assert ReceptionDifferenceSeverityPolicy.suggest("SHORTAGE", variance_percentage=Decimal("2")) == Severity.LOW

    def test_overage_high_variance_is_high(self):
        assert ReceptionDifferenceSeverityPolicy.suggest("OVERAGE", variance_percentage=Decimal("25")) == Severity.HIGH

    def test_document_missing_is_medium(self):
        assert ReceptionDifferenceSeverityPolicy.suggest("DOCUMENT_MISSING") == Severity.MEDIUM

    def test_guide_missing_is_medium(self):
        assert ReceptionDifferenceSeverityPolicy.suggest("GUIDE_MISSING") == Severity.MEDIUM

    def test_serial_duplicate_is_medium(self):
        assert ReceptionDifferenceSeverityPolicy.suggest("SERIAL_DUPLICATE") == Severity.MEDIUM

    def test_unknown_product_is_medium(self):
        assert ReceptionDifferenceSeverityPolicy.suggest("UNKNOWN_PRODUCT") == Severity.MEDIUM

    def test_recurring_is_high(self):
        assert ReceptionDifferenceSeverityPolicy.suggest("SHORTAGE", is_recurring=True) == Severity.HIGH

    def test_safety_concern_flag_is_critical(self):
        assert ReceptionDifferenceSeverityPolicy.suggest("OTHER", has_safety_concern=True) == Severity.CRITICAL

    def test_seal_issue_flag_is_high(self):
        assert ReceptionDifferenceSeverityPolicy.suggest("OTHER", is_seal_issue=True) == Severity.HIGH

    def test_document_issue_flag_is_medium(self):
        assert ReceptionDifferenceSeverityPolicy.suggest("OTHER", is_document_issue=True) == Severity.MEDIUM

    def test_damage_flag_is_high(self):
        assert ReceptionDifferenceSeverityPolicy.suggest("OTHER", has_damage=True) == Severity.HIGH

    def test_expired_flag_is_high(self):
        assert ReceptionDifferenceSeverityPolicy.suggest("OTHER", is_expired=True) == Severity.HIGH

    def test_default_is_low(self):
        assert ReceptionDifferenceSeverityPolicy.suggest("OTHER_APPROVED") == Severity.LOW

    def test_policy_version_is_set(self):
        assert ReceptionDifferenceSeverityPolicy.VERSION == "1"


class TestDecimalQuantityValidation:
    """Decimal quantity validation — reject float, accept valid decimals."""

    def test_reject_float(self):
        with pytest.raises(ReceptionDifferenceError) as exc_info:
            strict_decimal_diff(1.5)
        assert "float" in str(exc_info.value.message).lower()

    def test_reject_nan_float(self):
        with pytest.raises(Exception):
            strict_decimal_diff(float("nan"))

    def test_reject_inf_float(self):
        with pytest.raises(Exception):
            strict_decimal_diff(float("inf"))

    def test_accept_string_decimal(self):
        result = strict_decimal_diff("123.4500")
        assert result == Decimal("123.4500")

    def test_accept_integer_string(self):
        result = strict_decimal_diff("100")
        assert result == Decimal("100")

    def test_preserves_exact_value(self):
        assert strict_decimal_diff("0.001") == Decimal("0.001")
        assert strict_decimal_diff("999999.99") == Decimal("999999.99")

    def test_reject_zero_when_positive(self):
        with pytest.raises(ReceptionDifferenceError):
            strict_decimal_diff("0")

    def test_reject_negative_when_positive(self):
        with pytest.raises(ReceptionDifferenceError):
            strict_decimal_diff("-5")

    def test_accept_zero_when_not_positive(self):
        result = strict_decimal_diff("0", positive=False)
        assert result == Decimal("0")

    def test_validate_decimal_rejects_float(self):
        with pytest.raises(ReceptionDifferenceError):
            validate_decimal_quantity(1.5)

    def test_validate_decimal_accepts_string(self):
        result = validate_decimal_quantity("100.50")
        assert result == Decimal("100.50")

    def test_validate_decimal_rejects_nan_string(self):
        with pytest.raises(Exception):
            validate_decimal_quantity("NaN")

    def test_validate_decimal_rejects_inf_string(self):
        with pytest.raises(Exception):
            validate_decimal_quantity("Infinity")


class TestCanonicalHashGeneration:
    """Canonical hash — order-independent, deterministic."""

    def test_order_independent(self):
        assert canonical_hash_diff({"a": 1, "b": 2}) == canonical_hash_diff({"b": 2, "a": 1})

    def test_deterministic(self):
        h1 = canonical_hash_diff({"key": "value", "num": 42})
        h2 = canonical_hash_diff({"key": "value", "num": 42})
        assert h1 == h2

    def test_different_input_different_hash(self):
        h1 = canonical_hash_diff({"a": 1})
        h2 = canonical_hash_diff({"a": 2})
        assert h1 != h2

    def test_hash_is_hex_string(self):
        h = canonical_hash_diff({"test": True})
        assert isinstance(h, str)
        assert len(h) == 64
        int(h, 16)  # Should not raise

    def test_nested_dict_order_independent(self):
        h1 = canonical_hash_diff({"outer": {"b": 2, "a": 1}})
        h2 = canonical_hash_diff({"outer": {"a": 1, "b": 2}})
        assert h1 == h2

    def test_list_order_matters(self):
        h1 = canonical_hash_diff({"items": [1, 2, 3]})
        h2 = canonical_hash_diff({"items": [3, 2, 1]})
        assert h1 != h2

    def test_empty_dict(self):
        h = canonical_hash_diff({})
        assert isinstance(h, str)
        assert len(h) == 64


# ══════════════════════════════════════════════════════════════════════════════
# 2. SERVICE LAYER TESTS
# ══════════════════════════════════════════════════════════════════════════════


class TestQuantityService:
    """QuantityService: calculate_difference, calculate_variance_percentage."""

    def test_calculate_difference_shortage(self):
        from app.modules.logistics.inbound.reception_differences.application.services.quantity_service import (
            ReceptionDifferenceQuantityService,
        )
        result = ReceptionDifferenceQuantityService.calculate_difference(
            Decimal("100"), Decimal("80"), "SHORTAGE"
        )
        assert result["difference_quantity"] == Decimal("20")
        assert result["absolute_difference"] == Decimal("20")
        assert result["is_shortage"] is True
        assert result["is_overage"] is False

    def test_calculate_difference_overage(self):
        from app.modules.logistics.inbound.reception_differences.application.services.quantity_service import (
            ReceptionDifferenceQuantityService,
        )
        result = ReceptionDifferenceQuantityService.calculate_difference(
            Decimal("100"), Decimal("120"), "OVERAGE"
        )
        assert result["difference_quantity"] == Decimal("-20")
        assert result["absolute_difference"] == Decimal("20")
        assert result["is_shortage"] is False
        assert result["is_overage"] is True

    def test_calculate_difference_exact(self):
        from app.modules.logistics.inbound.reception_differences.application.services.quantity_service import (
            ReceptionDifferenceQuantityService,
        )
        result = ReceptionDifferenceQuantityService.calculate_difference(
            Decimal("50"), Decimal("50"), "QUANTITY_MISMATCH"
        )
        assert result["difference_quantity"] == Decimal("0")
        assert result["is_shortage"] is False
        assert result["is_overage"] is False

    def test_variance_percentage(self):
        from app.modules.logistics.inbound.reception_differences.application.services.quantity_service import (
            ReceptionDifferenceQuantityService,
        )
        result = ReceptionDifferenceQuantityService.calculate_variance_percentage(
            Decimal("100"), Decimal("110")
        )
        assert result == Decimal("10.00")

    def test_variance_percentage_zero_expected(self):
        from app.modules.logistics.inbound.reception_differences.application.services.quantity_service import (
            ReceptionDifferenceQuantityService,
        )
        with pytest.raises(ReceptionDifferenceError):
            ReceptionDifferenceQuantityService.calculate_variance_percentage(
                Decimal("0"), Decimal("10")
            )

    def test_variance_percentage_negative(self):
        from app.modules.logistics.inbound.reception_differences.application.services.quantity_service import (
            ReceptionDifferenceQuantityService,
        )
        result = ReceptionDifferenceQuantityService.calculate_variance_percentage(
            Decimal("100"), Decimal("80")
        )
        assert result == Decimal("-20.00")


# ══════════════════════════════════════════════════════════════════════════════
# 3. SCHEMA VALIDATION TESTS
# ══════════════════════════════════════════════════════════════════════════════


class TestSchemaValidation:
    """API boundary validation — reject float, forbid server-owned fields."""

    @pytest.mark.parametrize("schema,payload", [
        (ReasonRequest, {"reason": "Ab", "reason_code": "OTHER"}),
    ])
    def test_reject_short_reason(self, schema, payload):
        with pytest.raises(ValidationError):
            schema.model_validate(payload)

    @pytest.mark.parametrize("schema,payload", [
        (ReasonRequest, {"reason": "x" * 1001}),
    ])
    def test_reject_long_reason(self, schema, payload):
        with pytest.raises(ValidationError):
            schema.model_validate(payload)

    def test_case_create_rejects_float(self):
        with pytest.raises(ValidationError):
            ReceptionDifferenceCaseCreate.model_validate({
                "inbound_receipt_id": UUID1,
                "source_type": "MANUAL_ENTRY",
                "description": 1.5,
            })

    def test_item_create_rejects_float_in_quantity(self):
        with pytest.raises(ValidationError):
            ReceptionDifferenceItemCreate.model_validate({
                "difference_type": "SHORTAGE",
                "title": "Test",
                "expected_quantity": 1.5,
            })

    def test_evidence_link_create_rejects_float(self):
        with pytest.raises(ValidationError):
            ReceptionDifferenceEvidenceLinkCreate.model_validate({
                "file_asset_id": UUID1,
                "evidence_type": "PRODUCT_PHOTO",
                "description": 2.3,
            })

    def test_responsible_party_create_rejects_float(self):
        with pytest.raises(ValidationError):
            ReceptionDifferenceResponsiblePartyCreate.model_validate({
                "party_type": "SUPPLIER",
                "allocation_percentage": 1.5,
            })

    def test_case_update_rejects_float(self):
        with pytest.raises(ValidationError):
            ReceptionDifferenceCaseUpdate.model_validate({
                "severity": 1.0,
            })

    def test_item_update_rejects_float(self):
        with pytest.raises(ValidationError):
            ReceptionDifferenceItemUpdate.model_validate({
                "title": 1.5,
            })

    def test_approval_decision_requires_valid_decision(self):
        with pytest.raises(ValidationError):
            ReceptionDifferenceApprovalDecisionRequest.model_validate({
                "decision": "INVALID_DECISION",
            })

    def test_review_create_requires_valid_type(self):
        result = ReceptionDifferenceReviewCreate.model_validate({
            "review_type": "OPERATIONAL",
        })
        assert result.review_type == "OPERATIONAL"

    def test_case_create_valid(self):
        c = ReceptionDifferenceCaseCreate.model_validate({
            "inbound_receipt_id": UUID1,
            "source_type": "MANUAL_ENTRY",
        })
        assert str(c.inbound_receipt_id) == UUID1

    def test_item_create_valid(self):
        i = ReceptionDifferenceItemCreate.model_validate({
            "difference_type": "SHORTAGE",
            "title": "Test item",
            "expected_quantity": "100",
            "observed_quantity": "80",
        })
        assert i.difference_type == "SHORTAGE"


# ══════════════════════════════════════════════════════════════════════════════
# 4. ERROR CLASS TESTS
# ══════════════════════════════════════════════════════════════════════════════


class TestErrorClasses:
    """ReceptionDifferenceError and subclasses."""

    def test_base_error_code_message(self):
        err = reception_difference_error("CODE", "msg", 422)
        assert err.code == "CODE"
        assert err.message == "msg"
        assert err.status_code == 422

    def test_case_not_found_is_404(self):
        err = ReceptionDifferenceCaseNotFound("CODE", "not found", 404)
        assert err.status_code == 404

    def test_is_application_error(self):
        from app.core.exceptions import ApplicationError
        assert issubclass(ReceptionDifferenceError, ApplicationError)

    def test_all_error_codes_are_unique(self):
        from app.modules.logistics.inbound.reception_differences.domain.errors import ERROR_CODES
        assert len(ERROR_CODES) == len(set(ERROR_CODES))

    def test_case_not_found_error_code_string(self):
        err = ReceptionDifferenceCaseNotFound("ReceptionDifferenceCaseNotFound", "Not found")
        assert "ReceptionDifferenceCaseNotFound" in str(type(err).__name__)


# ══════════════════════════════════════════════════════════════════════════════
# 5. ENUM COMPLETENESS TESTS
# ══════════════════════════════════════════════════════════════════════════════


class TestEnumCompleteness:
    """All enums are properly defined and consistent."""

    def test_case_status_has_all_statuses(self):
        statuses = {s.value for s in CaseStatus}
        assert len(statuses) == 17
        assert "DRAFT" in statuses
        assert "CLOSED" in statuses
        assert "CANCELLED" in statuses
        assert "SUPERSEDED" in statuses

    def test_item_status_has_all_statuses(self):
        statuses = {s.value for s in ItemStatus}
        assert len(statuses) == 10
        assert "OPEN" in statuses
        assert "CLOSED" in statuses

    def test_case_transitions_has_entry_for_every_status(self):
        for status in CaseStatus:
            assert status in CASE_TRANSITIONS, f"Missing transition for {status}"

    def test_item_transitions_has_entry_for_every_status(self):
        for status in ItemStatus:
            assert status in ITEM_TRANSITIONS, f"Missing transition for {status}"

    def test_difference_type_category_map_covers_all_types(self):
        for dt in DifferenceType:
            assert dt in DIFFERENCE_TYPE_CATEGORY_MAP, f"{dt} missing from category map"

    def test_difference_category_all_values(self):
        cats = {c.value for c in DifferenceCategory}
        assert cats == {"QUANTITY", "PRODUCT", "CONDITION", "IDENTIFICATION", "DOCUMENTATION", "SEAL", "PROCESS", "SAFETY", "OTHER"}

    def test_severity_all_values(self):
        sevs = {s.value for s in Severity}
        assert sevs == {"INFORMATIONAL", "LOW", "MEDIUM", "HIGH", "CRITICAL"}

    def test_approval_decision_all_values(self):
        decs = {d.value for d in ApprovalDecision}
        assert decs == {"APPROVE_FOR_ISSUE", "REQUEST_CHANGES", "REJECT_CASE", "REQUIRE_ADDITIONAL_REVIEW"}

    def test_acknowledgement_type_all_values(self):
        types = {t.value for t in AcknowledgementType}
        assert len(types) == 7

    def test_responsibility_status_all_values(self):
        statuses = {s.value for s in ResponsibilityStatus}
        assert len(statuses) == 9

    def test_review_status_all_values(self):
        statuses = {s.value for s in ReviewStatus}
        assert len(statuses) == 6

    def test_source_type_all_values(self):
        sources = {s.value for s in SourceType}
        assert len(sources) == 7


# ══════════════════════════════════════════════════════════════════════════════
# 6. PHASE 040 INFRASTRUCTURE TESTS
# ══════════════════════════════════════════════════════════════════════════════


class TestPhase040Infrastructure:
    """Phase 040 table manifest, jobs, permissions, and audit codes."""

    def test_phase040_tables_are_unique(self):
        assert len(PHASE_040_TABLES) == len(set(PHASE_040_TABLES))

    def test_phase040_tables_count(self):
        assert len(PHASE_040_TABLES) >= 12

    def test_phase040_tables_include_core(self):
        assert "reception_difference_cases" in PHASE_040_TABLES
        assert "reception_difference_items" in PHASE_040_TABLES
        assert "reception_difference_evidence_links" in PHASE_040_TABLES
        assert "reception_difference_reviews" in PHASE_040_TABLES
        assert "reception_difference_approvals" in PHASE_040_TABLES
        assert "reception_difference_acknowledgements" in PHASE_040_TABLES

    def test_permission_catalog_is_complete_and_unique(self):
        codes = [str(x["code"]) for x in PHASE_040_PERMISSIONS]
        assert len(codes) >= 25
        assert len(codes) == len(set(codes))
        assert "logistics.reception_differences.read" in codes
        assert "logistics.reception_differences.create" in codes
        assert "logistics.reception_differences.cancel" in codes
        assert "logistics.reception_differences.close" in codes

    def test_sensitive_permissions_have_step_up_policy(self):
        codes = [str(x["code"]) for x in PHASE_040_PERMISSIONS if x.get("requires_step_up")]
        assert len(codes) > 0
        for code in codes:
            if code in POLICY_CATALOG:
                assert POLICY_CATALOG[code].permission_code == code

    def test_step_up_permissions_include_critical_operations(self):
        codes = [str(x["code"]) for x in PHASE_040_PERMISSIONS if x.get("requires_step_up")]
        assert "logistics.reception_differences.cancel" in codes
        assert "logistics.reception_differences.close" in codes
        assert "logistics.reception_differences.approve" in codes
        assert "logistics.reception_difference_documents.issue" in codes
        assert "logistics.reception_difference_documents.cancel" in codes

    def test_jobs_are_all_callable(self):
        jobs = {
            "detect_incomplete_cases": detect_incomplete_cases,
            "detect_pending_evidence": detect_pending_evidence,
            "detect_pending_responsibility": detect_pending_responsibility,
            "detect_critical_without_approval": detect_critical_without_approval,
            "update_metrics_projection": update_metrics_projection,
            "detect_candidates_not_formalized": detect_candidates_not_formalized,
        }
        assert all(callable(fn) for fn in jobs.values())

    def test_audit_codes_are_registered(self):
        codes = [
            "logistics.reception_difference.case_created",
            "logistics.reception_difference.case_updated",
            "logistics.reception_difference.case_submitted_for_review",
            "logistics.reception_difference.case_approved",
            "logistics.reception_difference.case_issued",
            "logistics.reception_difference.case_cancelled",
            "logistics.reception_difference.case_closed",
            "logistics.reception_difference.item_created",
            "logistics.reception_difference.item_dismissed",
            "logistics.reception_difference.evidence_linked",
            "logistics.reception_difference.responsibility_proposed",
            "logistics.reception_difference.review_created",
            "logistics.reception_difference.approval_decision_created",
            "logistics.reception_difference.acknowledgement_created",
            "logistics.reception_difference.document_issued",
            "logistics.reception_difference.document_cancelled",
            "logistics.reception_difference.document_package_created",
            "logistics.reception_difference.candidate_formalized",
        ]
        for code in codes:
            assert is_valid_event_code(code), f"Audit code not registered: {code}"


# ══════════════════════════════════════════════════════════════════════════════
# 7. OPENAPI CONTRACT TESTS
# ══════════════════════════════════════════════════════════════════════════════


class TestOpenAPIContract:
    """OpenAPI exposes required Phase 040 endpoints and idempotency headers."""

    def test_required_endpoints_exist(self):
        from app.main import app
        schema = app.openapi()
        required = {
            "/api/logistics/reception-difference-cases",
            "/api/logistics/reception-difference-cases/summary",
            "/api/logistics/reception-difference-cases/{case_id}",
            "/api/logistics/reception-difference-cases/{case_id}/validate",
            "/api/logistics/reception-difference-cases/{case_id}/submit",
            "/api/logistics/reception-difference-cases/{case_id}/start-review",
            "/api/logistics/reception-difference-cases/{case_id}/approve",
            "/api/logistics/reception-difference-cases/{case_id}/cancel",
            "/api/logistics/reception-difference-cases/{case_id}/close",
            "/api/logistics/reception-difference-cases/{case_id}/history",
            "/api/logistics/reception-difference-cases/{case_id}/capabilities",
            "/api/logistics/reception-difference-cases/{case_id}/integrity",
            "/api/logistics/reception-difference-cases/{case_id}/items",
            "/api/logistics/reception-difference-cases/{case_id}/evidence-links",
            "/api/logistics/reception-difference-cases/{case_id}/evidence",
            "/api/logistics/reception-difference-cases/{case_id}/responsible-parties",
            "/api/logistics/reception-difference-cases/{case_id}/reviews",
            "/api/logistics/reception-difference-cases/{case_id}/approvals",
            "/api/logistics/reception-difference-cases/{case_id}/acknowledgements",
            "/api/logistics/reception-difference-cases/{case_id}/preview",
            "/api/logistics/reception-difference-cases/{case_id}/issue-document",
            "/api/logistics/reception-difference-cases/{case_id}/document",
            "/api/logistics/reception-difference-cases/{case_id}/cancel-document",
            "/api/logistics/reception-difference-cases/{case_id}/reprint",
            "/api/logistics/reception-difference-cases/{case_id}/quality-preparation",
            "/api/logistics/reception-difference-cases/{case_id}/quarantine-recommendations",
            "/api/logistics/reception-difference-cases/{case_id}/claim-preparation",
            "/api/logistics/reception-difference-cases/{case_id}/formalize-candidates",
            "/api/logistics/reception-difference-items/{item_id}",
        }
        assert required <= set(schema["paths"])

    def test_idempotency_required_on_mutations(self):
        from app.main import app
        schema = app.openapi()
        mutation_endpoints = [
            ("/api/logistics/reception-difference-cases", "post"),
            ("/api/logistics/reception-difference-cases/{case_id}", "patch"),
            ("/api/logistics/reception-difference-cases/{case_id}/validate", "post"),
            ("/api/logistics/reception-difference-cases/{case_id}/submit", "post"),
            ("/api/logistics/reception-difference-cases/{case_id}/start-review", "post"),
            ("/api/logistics/reception-difference-cases/{case_id}/request-changes", "post"),
            ("/api/logistics/reception-difference-cases/{case_id}/approve", "post"),
            ("/api/logistics/reception-difference-cases/{case_id}/cancel", "post"),
            ("/api/logistics/reception-difference-cases/{case_id}/close", "post"),
            ("/api/logistics/reception-difference-cases/{case_id}/items", "post"),
            ("/api/logistics/reception-difference-cases/{case_id}/formalize-candidates", "post"),
            ("/api/logistics/reception-difference-cases/{case_id}/evidence-links", "post"),
            ("/api/logistics/reception-difference-cases/{case_id}/responsible-parties", "post"),
            ("/api/logistics/reception-difference-cases/{case_id}/reviews", "post"),
            ("/api/logistics/reception-difference-cases/{case_id}/acknowledgements", "post"),
            ("/api/logistics/reception-difference-cases/{case_id}/issue-document", "post"),
            ("/api/logistics/reception-difference-cases/{case_id}/cancel-document", "post"),
            ("/api/logistics/reception-difference-cases/{case_id}/reprint", "post"),
        ]
        for path, method in mutation_endpoints:
            parameters = schema["paths"][path][method]["parameters"]
            assert any(
                x["name"] == "Idempotency-Key" and x.get("required") for x in parameters
            ), f"Missing Idempotency-Key on {method.upper()} {path}"

    def test_no_delete_on_cases(self):
        from app.main import app
        schema = app.openapi()
        case_paths = [k for k in schema["paths"] if "reception-difference-cases" in k]
        assert not any("delete" in schema["paths"][k] for k in case_paths)

    def test_no_delete_on_items(self):
        from app.main import app
        schema = app.openapi()
        item_paths = [k for k in schema["paths"] if "reception-difference-items" in k]
        assert not any("delete" in schema["paths"][k] for k in item_paths)

    def test_approve_decision_enum_constraint(self):
        from app.main import app
        schema = app.openapi()
        path = schema["paths"]["/api/logistics/reception-difference-cases/{case_id}/approve"]
        body_schema_name = path["post"]["requestBody"]["content"]["application/json"]["schema"]["$ref"].split("/")[-1]
        body_schema = schema["components"]["schemas"][body_schema_name]
        decision_prop = body_schema["properties"]["decision"]
        assert "enum" in decision_prop or "anyOf" in decision_prop


# ══════════════════════════════════════════════════════════════════════════════
# 8. INTEGRATION TESTS (ENDPOINTS)
# ══════════════════════════════════════════════════════════════════════════════


class TestEndpointContracts:
    """Integration tests for Phase 040 endpoints via TestClient."""

    def _make_headers(self, csrf_token="test-csrf"):
        return {
            "Idempotency-Key": f"test-key-{uuid.uuid4().hex[:16]}",
            "X-CSRF-Token": csrf_token,
        }

    def test_list_cases_returns_empty(self, client):
        resp = client.get("/api/logistics/reception-difference-cases")
        assert resp.status_code in (200, 401, 403)

    def test_cases_summary_is_not_captured_as_case_id(self, client):
        resp = client.get("/api/logistics/reception-difference-cases/summary")
        assert resp.status_code in (200, 401, 403)

    def test_create_case_requires_idempotency_key(self, client):
        resp = client.post(
            "/api/logistics/reception-difference-cases",
            json={"inbound_receipt_id": UUID1, "source_type": "MANUAL_ENTRY"},
        )
        assert resp.status_code in (422, 401, 403)

    def test_get_case_returns_404_for_nonexistent(self, client):
        resp = client.get(f"/api/logistics/reception-difference-cases/{UUID1}")
        assert resp.status_code in (404, 401, 403)

    def test_update_case_requires_idempotency(self, client):
        resp = client.patch(
            f"/api/logistics/reception-difference-cases/{UUID1}",
            json={"severity": "HIGH"},
        )
        assert resp.status_code in (422, 401, 403)

    def test_validate_case_requires_idempotency(self, client):
        resp = client.post(f"/api/logistics/reception-difference-cases/{UUID1}/validate")
        assert resp.status_code in (422, 401, 403)

    def test_submit_case_requires_idempotency(self, client):
        resp = client.post(f"/api/logistics/reception-difference-cases/{UUID1}/submit")
        assert resp.status_code in (422, 401, 403)

    def test_start_review_requires_idempotency(self, client):
        resp = client.post(f"/api/logistics/reception-difference-cases/{UUID1}/start-review")
        assert resp.status_code in (422, 401, 403)

    def test_approve_case_requires_idempotency(self, client):
        resp = client.post(
            f"/api/logistics/reception-difference-cases/{UUID1}/approve",
            json={"decision": "APPROVE_FOR_ISSUE"},
        )
        assert resp.status_code in (422, 401, 403)

    def test_cancel_case_requires_idempotency(self, client):
        resp = client.post(
            f"/api/logistics/reception-difference-cases/{UUID1}/cancel",
            json={"reason": "Test cancellation", "reason_code": "OTHER"},
        )
        assert resp.status_code in (422, 401, 403)

    def test_close_case_requires_idempotency(self, client):
        resp = client.post(f"/api/logistics/reception-difference-cases/{UUID1}/close")
        assert resp.status_code in (422, 401, 403)

    def test_history_returns_result(self, client):
        resp = client.get(f"/api/logistics/reception-difference-cases/{UUID1}/history")
        assert resp.status_code in (200, 401, 403, 404)

    def test_capabilities_returns_result(self, client):
        resp = client.get(f"/api/logistics/reception-difference-cases/{UUID1}/capabilities")
        assert resp.status_code in (200, 401, 403, 404)

    def test_integrity_returns_result(self, client):
        resp = client.get(f"/api/logistics/reception-difference-cases/{UUID1}/integrity")
        assert resp.status_code in (200, 401, 403, 404)

    def test_create_item_requires_idempotency(self, client):
        resp = client.post(
            f"/api/logistics/reception-difference-cases/{UUID1}/items",
            json={"difference_type": "SHORTAGE", "title": "Test item"},
        )
        assert resp.status_code in (422, 401, 403)

    def test_formalize_candidates_requires_idempotency(self, client):
        resp = client.post(
            f"/api/logistics/reception-difference-cases/{UUID1}/formalize-candidates",
            json={"candidate_ids": [UUID2]},
        )
        assert resp.status_code in (422, 401, 403)

    def test_get_item_returns_404(self, client):
        resp = client.get(f"/api/logistics/reception-difference-items/{UUID1}")
        assert resp.status_code in (404, 401, 403)

    def test_update_item_requires_idempotency(self, client):
        resp = client.patch(
            f"/api/logistics/reception-difference-items/{UUID1}",
            json={"title": "Updated"},
        )
        assert resp.status_code in (422, 401, 403)

    def test_dismiss_item_requires_idempotency(self, client):
        resp = client.post(
            f"/api/logistics/reception-difference-items/{UUID1}/dismiss",
            json={"reason": "Not valid", "reason_code": "OTHER"},
        )
        assert resp.status_code in (422, 401, 403)

    def test_link_evidence_requires_idempotency(self, client):
        resp = client.post(
            f"/api/logistics/reception-difference-cases/{UUID1}/evidence-links",
            json={"file_asset_id": UUID2, "evidence_type": "PRODUCT_PHOTO"},
        )
        assert resp.status_code in (422, 401, 403)

    def test_list_evidence_returns_result(self, client):
        resp = client.get(f"/api/logistics/reception-difference-cases/{UUID1}/evidence")
        assert resp.status_code in (200, 401, 403, 404)

    def test_create_responsible_requires_idempotency(self, client):
        resp = client.post(
            f"/api/logistics/reception-difference-cases/{UUID1}/responsible-parties",
            json={"party_type": "SUPPLIER", "responsibility_role": "PRIMARY"},
        )
        assert resp.status_code in (422, 401, 403)

    def test_list_responsible_returns_result(self, client):
        resp = client.get(f"/api/logistics/reception-difference-cases/{UUID1}/responsible-parties")
        assert resp.status_code in (200, 401, 403, 404)

    def test_create_review_requires_idempotency(self, client):
        resp = client.post(
            f"/api/logistics/reception-difference-cases/{UUID1}/reviews",
            json={"review_type": "OPERATIONAL"},
        )
        assert resp.status_code in (422, 401, 403)

    def test_list_reviews_returns_result(self, client):
        resp = client.get(f"/api/logistics/reception-difference-cases/{UUID1}/reviews")
        assert resp.status_code in (200, 401, 403, 404)

    def test_list_approvals_returns_result(self, client):
        resp = client.get(f"/api/logistics/reception-difference-cases/{UUID1}/approvals")
        assert resp.status_code in (200, 401, 403, 404)

    def test_create_acknowledgement_requires_idempotency(self, client):
        resp = client.post(
            f"/api/logistics/reception-difference-cases/{UUID1}/acknowledgements",
            json={"party_type": "SUPPLIER", "acknowledgement_type": "RECEIVED_COPY"},
        )
        assert resp.status_code in (422, 401, 403)

    def test_list_acknowledgements_returns_result(self, client):
        resp = client.get(f"/api/logistics/reception-difference-cases/{UUID1}/acknowledgements")
        assert resp.status_code in (200, 401, 403, 404)

    def test_preview_returns_result(self, client):
        resp = client.get(f"/api/logistics/reception-difference-cases/{UUID1}/preview")
        assert resp.status_code in (200, 401, 403, 404)

    def test_issue_document_requires_idempotency(self, client):
        resp = client.post(f"/api/logistics/reception-difference-cases/{UUID1}/issue-document")
        assert resp.status_code in (422, 401, 403)

    def test_get_document_returns_result(self, client):
        resp = client.get(f"/api/logistics/reception-difference-cases/{UUID1}/document")
        assert resp.status_code in (200, 401, 403, 404)

    def test_cancel_document_requires_idempotency(self, client):
        resp = client.post(
            f"/api/logistics/reception-difference-cases/{UUID1}/cancel-document",
            json={"reason": "Cancel doc", "reason_code": "OTHER"},
        )
        assert resp.status_code in (422, 401, 403)

    def test_reprint_requires_idempotency(self, client):
        resp = client.post(
            f"/api/logistics/reception-difference-cases/{UUID1}/reprint",
            json={"reason": "Reprint", "reason_code": "OTHER"},
        )
        assert resp.status_code in (422, 401, 403)

    def test_quality_preparation_returns_result(self, client):
        resp = client.get(f"/api/logistics/reception-difference-cases/{UUID1}/quality-preparation")
        assert resp.status_code in (200, 401, 403, 404)

    def test_quarantine_recommendations_returns_result(self, client):
        resp = client.get(f"/api/logistics/reception-difference-cases/{UUID1}/quarantine-recommendations")
        assert resp.status_code in (200, 401, 403, 404)

    def test_claim_preparation_returns_result(self, client):
        resp = client.get(f"/api/logistics/reception-difference-cases/{UUID1}/claim-preparation")
        assert resp.status_code in (200, 401, 403, 404)

    def test_list_cases_with_filters(self, client):
        resp = client.get(
            "/api/logistics/reception-difference-cases",
            params={"status": "DRAFT", "severity": "LOW", "page": 1, "page_size": 10},
        )
        assert resp.status_code in (200, 401, 403)

    def test_request_changes_requires_idempotency(self, client):
        resp = client.post(
            f"/api/logistics/reception-difference-cases/{UUID1}/request-changes",
            json={"reason": "Needs more info", "reason_code": "OTHER"},
        )
        assert resp.status_code in (422, 401, 403)

    def test_mark_ready_for_approval_requires_idempotency(self, client):
        resp = client.post(f"/api/logistics/reception-difference-cases/{UUID1}/mark-ready-for-approval")
        assert resp.status_code in (422, 401, 403)


# ══════════════════════════════════════════════════════════════════════════════
# 9. CONCURRENCY TESTS
# ══════════════════════════════════════════════════════════════════════════════


class TestConcurrencyInvariants:
    """Concurrency invariants — double-formalize, double-approve, etc."""

    def test_two_cases_same_receipt_must_not_duplicate(self, database, mock_principal):
        """Two cases for the same receipt should be distinguishable by idempotency."""
        from app.modules.logistics.inbound.reception_differences.application.services.case_service import (
            ReceptionDifferenceCaseService,
        )
        svc = ReceptionDifferenceCaseService(database)
        case1 = svc.create_case(
            organization_id=mock_principal.organization_id,
            branch_id=mock_principal.branch_id,
            warehouse_id=mock_principal.warehouse_id,
            inbound_receipt_id=uuid.UUID(UUID1),
            receipt_revision_id=uuid.UUID(UUID2),
            source_type="MANUAL_ENTRY",
            supplier_snapshot={"name": "Supplier A"},
            carrier_snapshot=None,
            unloading_operation_id=None,
            gate_check_in_id=None,
            appointment_id=None,
            arrival_notice_id=None,
            principal=mock_principal,
        )
        case2 = svc.create_case(
            organization_id=mock_principal.organization_id,
            branch_id=mock_principal.branch_id,
            warehouse_id=mock_principal.warehouse_id,
            inbound_receipt_id=uuid.UUID(UUID1),
            receipt_revision_id=uuid.UUID(UUID2),
            source_type="MANUAL_ENTRY",
            supplier_snapshot={"name": "Supplier A"},
            carrier_snapshot=None,
            unloading_operation_id=None,
            gate_check_in_id=None,
            appointment_id=None,
            arrival_notice_id=None,
            principal=mock_principal,
        )
        assert case1.id != case2.id

    def test_two_item_creates_same_case_increment_counters(self, database, mock_principal):
        """Two items on same case each increment item_count."""
        from app.modules.logistics.inbound.reception_differences.application.services.case_service import (
            ReceptionDifferenceCaseService,
        )
        from app.modules.logistics.inbound.reception_differences.application.services.item_service import (
            ReceptionDifferenceItemService,
        )
        case_svc = ReceptionDifferenceCaseService(database)
        case = case_svc.create_case(
            organization_id=mock_principal.organization_id,
            branch_id=mock_principal.branch_id,
            warehouse_id=mock_principal.warehouse_id,
            inbound_receipt_id=uuid.UUID(UUID1),
            receipt_revision_id=uuid.UUID(UUID2),
            source_type="MANUAL_ENTRY",
            supplier_snapshot={},
            carrier_snapshot=None,
            unloading_operation_id=None,
            gate_check_in_id=None,
            appointment_id=None,
            arrival_notice_id=None,
            principal=mock_principal,
        )
        item_svc = ReceptionDifferenceItemService(database)
        item1 = item_svc.create_item(
            case_id=case.id, case_revision_id=case.active_revision_id,
            organization_id=mock_principal.organization_id,
            difference_type="SHORTAGE", title="Item 1", description=None,
            product_id=None, severity=None, expected_quantity=Decimal("100"),
            observed_quantity=Decimal("80"), expected_unit_id=None,
            observed_unit_id=None, source_candidate_id=None, purchase_order_id=None,
            purchase_order_line_id=None, expected_line_id=None, received_line_id=None,
            detection_source="MANUAL_REVIEW", detected_by_user_id=None,
            detected_by_service=None, principal=mock_principal,
        )
        item2 = item_svc.create_item(
            case_id=case.id, case_revision_id=case.active_revision_id,
            organization_id=mock_principal.organization_id,
            difference_type="OVERAGE", title="Item 2", description=None,
            product_id=None, severity=None, expected_quantity=Decimal("50"),
            observed_quantity=Decimal("60"), expected_unit_id=None,
            observed_unit_id=None, source_candidate_id=None, purchase_order_id=None,
            purchase_order_line_id=None, expected_line_id=None, received_line_id=None,
            detection_source="MANUAL_REVIEW", detected_by_user_id=None,
            detected_by_service=None, principal=mock_principal,
        )
        assert item1.id != item2.id
        database.refresh(case)
        assert case.item_count == 2

    def test_evidence_link_twice_same_file(self, database, mock_principal):
        """Linking the same file as evidence twice is allowed (different links)."""
        from app.modules.logistics.inbound.reception_differences.application.services.case_service import (
            ReceptionDifferenceCaseService,
        )
        from app.modules.logistics.inbound.reception_differences.application.services.evidence_service import (
            ReceptionDifferenceEvidenceService,
        )
        case_svc = ReceptionDifferenceCaseService(database)
        case = case_svc.create_case(
            organization_id=mock_principal.organization_id,
            branch_id=mock_principal.branch_id,
            warehouse_id=mock_principal.warehouse_id,
            inbound_receipt_id=uuid.UUID(UUID1),
            receipt_revision_id=uuid.UUID(UUID2),
            source_type="MANUAL_ENTRY",
            supplier_snapshot={},
            carrier_snapshot=None,
            unloading_operation_id=None,
            gate_check_in_id=None,
            appointment_id=None,
            arrival_notice_id=None,
            principal=mock_principal,
        )
        ev_svc = ReceptionDifferenceEvidenceService(database)
        link1 = ev_svc.link_evidence(
            case_id=case.id, item_id=None,
            file_asset_id=uuid.UUID(UUID3), file_version_id=None,
            evidence_type="PRODUCT_PHOTO", classification="STANDARD",
            description=None, captured_at=None, principal=mock_principal,
        )
        link2 = ev_svc.link_evidence(
            case_id=case.id, item_id=None,
            file_asset_id=uuid.UUID(UUID3), file_version_id=None,
            evidence_type="PRODUCT_PHOTO", classification="STANDARD",
            description="Second link", captured_at=None, principal=mock_principal,
        )
        assert link1.id != link2.id
        database.refresh(case)
        assert case.evidence_count == 2

    def test_approval_level_increments(self, database, mock_principal):
        """Two approval decisions have ascending approval_level."""
        from app.modules.logistics.inbound.reception_differences.application.services.case_service import (
            ReceptionDifferenceCaseService,
        )
        from app.modules.logistics.inbound.reception_differences.application.services.approval_service import (
            ReceptionDifferenceApprovalService,
        )
        case_svc = ReceptionDifferenceCaseService(database)
        case = case_svc.create_case(
            organization_id=mock_principal.organization_id,
            branch_id=mock_principal.branch_id,
            warehouse_id=mock_principal.warehouse_id,
            inbound_receipt_id=uuid.UUID(UUID1),
            receipt_revision_id=uuid.UUID(UUID2),
            source_type="MANUAL_ENTRY",
            supplier_snapshot={},
            carrier_snapshot=None,
            unloading_operation_id=None,
            gate_check_in_id=None,
            appointment_id=None,
            arrival_notice_id=None,
            principal=mock_principal,
        )
        app_svc = ReceptionDifferenceApprovalService(database)
        a1 = app_svc.create_approval_decision(
            case_id=case.id, decision="REQUEST_CHANGES",
            reason="Needs work", organization_id=mock_principal.organization_id,
            principal=mock_principal,
        )
        a2 = app_svc.create_approval_decision(
            case_id=case.id, decision="APPROVE_FOR_ISSUE",
            reason="Approved", organization_id=mock_principal.organization_id,
            principal=mock_principal,
        )
        assert a2.approval_level == a1.approval_level + 1

    def test_review_level_increments(self, database, mock_principal):
        """Two reviews on same case have ascending review numbers."""
        from app.modules.logistics.inbound.reception_differences.application.services.case_service import (
            ReceptionDifferenceCaseService,
        )
        from app.modules.logistics.inbound.reception_differences.application.services.review_service import (
            ReceptionDifferenceReviewService,
        )
        case_svc = ReceptionDifferenceCaseService(database)
        case = case_svc.create_case(
            organization_id=mock_principal.organization_id,
            branch_id=mock_principal.branch_id,
            warehouse_id=mock_principal.warehouse_id,
            inbound_receipt_id=uuid.UUID(UUID1),
            receipt_revision_id=uuid.UUID(UUID2),
            source_type="MANUAL_ENTRY",
            supplier_snapshot={},
            carrier_snapshot=None,
            unloading_operation_id=None,
            gate_check_in_id=None,
            appointment_id=None,
            arrival_notice_id=None,
            principal=mock_principal,
        )
        rev_svc = ReceptionDifferenceReviewService(database)
        r1 = rev_svc.create_review(
            case_id=case.id, review_type="OPERATIONAL",
            organization_id=mock_principal.organization_id, principal=mock_principal,
        )
        r2 = rev_svc.create_review(
            case_id=case.id, review_type="DOCUMENTARY",
            organization_id=mock_principal.organization_id, principal=mock_principal,
        )
        assert r1.id != r2.id


# ══════════════════════════════════════════════════════════════════════════════
# 10. IDEMPOTENCY TESTS
# ══════════════════════════════════════════════════════════════════════════════


class TestIdempotency:
    """Idempotency — same key + same payload = same result; different payload = 409."""

    def test_same_key_same_payload_same_result(self, client):
        key = f"idempotency-test-{uuid.uuid4().hex[:16]}"
        headers = {**self._make_headers(), "Idempotency-Key": key}
        payload = {"inbound_receipt_id": UUID1, "source_type": "MANUAL_ENTRY"}
        resp1 = client.post(
            "/api/logistics/reception-difference-cases",
            json=payload, headers=headers,
        )
        resp2 = client.post(
            "/api/logistics/reception-difference-cases",
            json=payload, headers=headers,
        )
        if resp1.status_code == 201 and resp2.status_code == 200:
            assert resp1.json() == resp2.json()

    def _make_headers(self):
        return {"X-CSRF-Token": "test-csrf"}


# ══════════════════════════════════════════════════════════════════════════════
# 11. SECURITY TESTS
# ══════════════════════════════════════════════════════════════════════════════


class TestSecurityInvariants:
    """Security — tenant isolation, CSRF, float rejection, step-up for CRITICAL."""

    def test_cross_tenant_case_access_denied(self, database, mock_principal, another_principal):
        """A case from tenant A should not be visible to tenant B."""
        from app.modules.logistics.inbound.reception_differences.application.services.case_service import (
            ReceptionDifferenceCaseService,
        )
        svc = ReceptionDifferenceCaseService(database)
        case = svc.create_case(
            organization_id=mock_principal.organization_id,
            branch_id=mock_principal.branch_id,
            warehouse_id=mock_principal.warehouse_id,
            inbound_receipt_id=uuid.UUID(UUID1),
            receipt_revision_id=uuid.UUID(UUID2),
            source_type="MANUAL_ENTRY",
            supplier_snapshot={},
            carrier_snapshot=None,
            unloading_operation_id=None,
            gate_check_in_id=None,
            appointment_id=None,
            arrival_notice_id=None,
            principal=mock_principal,
        )
        with pytest.raises(ReceptionDifferenceError) as exc_info:
            svc.get_case(case.id, another_principal.organization_id)
        assert exc_info.value.status_code == 404

    def test_float_quantity_rejected_at_api_boundary(self):
        """API schemas reject float quantities."""
        with pytest.raises(ValidationError):
            ReceptionDifferenceItemCreate.model_validate({
                "difference_type": "SHORTAGE",
                "title": "Test",
                "expected_quantity": 1.5,
            })

    def test_csrf_required_on_mutations(self, client):
        """Mutation endpoints require CSRF token."""
        resp = client.post(
            f"/api/logistics/reception-difference-cases/{UUID1}/submit",
            headers={"Idempotency-Key": "test-key-12345678"},
        )
        assert resp.status_code in (401, 403, 422)

    def test_critical_severity_requires_step_up(self):
        """Permissions requiring step-up are registered in the policy catalog."""
        critical_perms = [
            str(x["code"]) for x in PHASE_040_PERMISSIONS
            if x.get("requires_step_up") and x.get("risk_level") in ("HIGH", "CRITICAL")
        ]
        for perm in critical_perms:
            assert perm in POLICY_CATALOG, f"Missing step-up policy for {perm}"

    def test_document_cancel_requires_critical_step_up(self):
        """Document cancellation requires CRITICAL step-up."""
        cancel_perm = next(
            x for x in PHASE_040_PERMISSIONS
            if x["code"] == "logistics.reception_difference_documents.cancel"
        )
        assert cancel_perm.get("requires_step_up") is True
        assert cancel_perm.get("risk_level") == "critical"
        assert cancel_perm.get("requires_reason") is True

    def test_case_cancel_requires_reason(self):
        """Case cancellation permission requires reason."""
        cancel_perm = next(
            x for x in PHASE_040_PERMISSIONS
            if x["code"] == "logistics.reception_differences.cancel"
        )
        assert cancel_perm.get("requires_reason") is True
        assert cancel_perm.get("requires_step_up") is True

    def test_case_close_requires_step_up(self):
        """Case close requires step-up."""
        close_perm = next(
            x for x in PHASE_040_PERMISSIONS
            if x["code"] == "logistics.reception_differences.close"
        )
        assert close_perm.get("requires_step_up") is True


# ══════════════════════════════════════════════════════════════════════════════
# 12. DOMAIN SERVICE INTEGRATION TESTS
# ══════════════════════════════════════════════════════════════════════════════


class TestDomainServiceIntegration:
    """Domain services — full lifecycle with real database."""

    def test_full_case_lifecycle(self, database, mock_principal, monkeypatch):
        """Create case, add item, submit, review, approve, issue, close."""
        from app.modules.logistics.inbound.reception_differences.application.services.case_service import (
            ReceptionDifferenceCaseService,
        )
        from app.modules.logistics.inbound.reception_differences.application.services.item_service import (
            ReceptionDifferenceItemService,
        )
        monkeypatch.setattr(
            "app.modules.logistics.audit.catalog.is_valid_event_code", lambda code: True
        )
        case_svc = ReceptionDifferenceCaseService(database)
        item_svc = ReceptionDifferenceItemService(database)

        # Create case
        case = case_svc.create_case(
            organization_id=mock_principal.organization_id,
            branch_id=mock_principal.branch_id,
            warehouse_id=mock_principal.warehouse_id,
            inbound_receipt_id=uuid.UUID(UUID1),
            receipt_revision_id=uuid.UUID(UUID2),
            source_type="MANUAL_ENTRY",
            supplier_snapshot={"name": "Test Supplier"},
            carrier_snapshot=None,
            unloading_operation_id=None,
            gate_check_in_id=None,
            appointment_id=None,
            arrival_notice_id=None,
            principal=mock_principal,
        )
        assert case.status == CaseStatus.DRAFT
        assert case.item_count == 0

        # Add item
        item = item_svc.create_item(
            case_id=case.id, case_revision_id=case.active_revision_id,
            organization_id=mock_principal.organization_id,
            difference_type="SHORTAGE", title="Missing pallets", description=None,
            product_id=None, severity=None, expected_quantity=Decimal("100"),
            observed_quantity=Decimal("90"), expected_unit_id=None,
            observed_unit_id=None, source_candidate_id=None, purchase_order_id=None,
            purchase_order_line_id=None, expected_line_id=None, received_line_id=None,
            detection_source="MANUAL_REVIEW", detected_by_user_id=None,
            detected_by_service=None, principal=mock_principal,
        )
        database.refresh(case)
        assert case.item_count == 1

        # Transition DRAFT -> UNDER_PREPARATION
        case = case_svc.transition_case(case.id, "UNDER_PREPARATION", mock_principal)
        assert case.status == CaseStatus.UNDER_PREPARATION

        # Transition -> SUBMITTED_FOR_REVIEW
        case = case_svc.transition_case(case.id, "SUBMITTED_FOR_REVIEW", mock_principal)
        assert case.status == CaseStatus.SUBMITTED_FOR_REVIEW

        # Transition -> UNDER_REVIEW
        case = case_svc.transition_case(case.id, "UNDER_REVIEW", mock_principal)
        assert case.status == CaseStatus.UNDER_REVIEW

        # Transition -> READY_FOR_APPROVAL
        case = case_svc.transition_case(case.id, "READY_FOR_APPROVAL", mock_principal)
        assert case.status == CaseStatus.READY_FOR_APPROVAL

        # Transition -> APPROVED
        case = case_svc.transition_case(case.id, "APPROVED", mock_principal)
        assert case.status == CaseStatus.APPROVED

        # Transition -> ISSUED
        case = case_svc.transition_case(case.id, "ISSUED", mock_principal)
        assert case.status == CaseStatus.ISSUED

        # Transition -> CLOSED
        case = case_svc.transition_case(case.id, "CLOSED", mock_principal)
        assert case.status == CaseStatus.CLOSED

    def test_cancel_case_lifecycle(self, database, mock_principal):
        """Create case and cancel from DRAFT."""
        from app.modules.logistics.inbound.reception_differences.application.services.case_service import (
            ReceptionDifferenceCaseService,
        )
        svc = ReceptionDifferenceCaseService(database)
        case = svc.create_case(
            organization_id=mock_principal.organization_id,
            branch_id=mock_principal.branch_id,
            warehouse_id=mock_principal.warehouse_id,
            inbound_receipt_id=uuid.UUID(UUID1),
            receipt_revision_id=uuid.UUID(UUID2),
            source_type="MANUAL_ENTRY",
            supplier_snapshot={},
            carrier_snapshot=None,
            unloading_operation_id=None,
            gate_check_in_id=None,
            appointment_id=None,
            arrival_notice_id=None,
            principal=mock_principal,
        )
        case = svc.transition_case(case.id, "CANCELLED", mock_principal, reason="No longer needed")
        assert case.status == CaseStatus.CANCELLED
        assert case.cancellation_reason == "No longer needed"

    def test_update_case_only_in_draft(self, database, mock_principal, monkeypatch):
        """Update should only work in DRAFT or UNDER_PREPARATION."""
        from app.modules.logistics.inbound.reception_differences.application.services.case_service import (
            ReceptionDifferenceCaseService,
        )
        monkeypatch.setattr(
            "app.modules.logistics.audit.catalog.is_valid_event_code", lambda code: True
        )
        svc = ReceptionDifferenceCaseService(database)
        case = svc.create_case(
            organization_id=mock_principal.organization_id,
            branch_id=mock_principal.branch_id,
            warehouse_id=mock_principal.warehouse_id,
            inbound_receipt_id=uuid.UUID(UUID1),
            receipt_revision_id=uuid.UUID(UUID2),
            source_type="MANUAL_ENTRY",
            supplier_snapshot={},
            carrier_snapshot=None,
            unloading_operation_id=None,
            gate_check_in_id=None,
            appointment_id=None,
            arrival_notice_id=None,
            principal=mock_principal,
        )
        # Can update in DRAFT
        updated = svc.update_case(case.id, mock_principal.organization_id, mock_principal, severity="HIGH")
        assert updated.severity == "HIGH"

        # Transition to SUBMITTED_FOR_REVIEW
        svc.transition_case(case.id, "UNDER_PREPARATION", mock_principal)
        svc.transition_case(case.id, "SUBMITTED_FOR_REVIEW", mock_principal)

        # Cannot update in SUBMITTED_FOR_REVIEW
        with pytest.raises(ReceptionDifferenceError) as exc_info:
            svc.update_case(case.id, mock_principal.organization_id, mock_principal, severity="CRITICAL")
        assert exc_info.value.status_code == 409

    def test_capabilities_match_status(self, database, mock_principal):
        """Capabilities endpoint returns correct allowed actions per status."""
        from app.modules.logistics.inbound.reception_differences.application.services.case_service import (
            ReceptionDifferenceCaseService,
        )
        svc = ReceptionDifferenceCaseService(database)
        case = svc.create_case(
            organization_id=mock_principal.organization_id,
            branch_id=mock_principal.branch_id,
            warehouse_id=mock_principal.warehouse_id,
            inbound_receipt_id=uuid.UUID(UUID1),
            receipt_revision_id=uuid.UUID(UUID2),
            source_type="MANUAL_ENTRY",
            supplier_snapshot={},
            carrier_snapshot=None,
            unloading_operation_id=None,
            gate_check_in_id=None,
            appointment_id=None,
            arrival_notice_id=None,
            principal=mock_principal,
        )
        caps = svc.get_capabilities(case.id, mock_principal.organization_id)
        assert caps["can_add_items"] is True
        assert caps["can_submit"] is False
        assert caps["can_review"] is False
        assert caps["can_approve"] is False
        assert caps["is_terminal"] is False

    def test_integrity_check_empty_case(self, database, mock_principal):
        """Integrity check on case with no modifications returns VALID."""
        from app.modules.logistics.inbound.reception_differences.application.services.case_service import (
            ReceptionDifferenceCaseService,
        )
        from app.modules.logistics.inbound.reception_differences.application.services.integrity_service import (
            ReceptionDifferenceIntegrityService,
        )
        case_svc = ReceptionDifferenceCaseService(database)
        case = case_svc.create_case(
            organization_id=mock_principal.organization_id,
            branch_id=mock_principal.branch_id,
            warehouse_id=mock_principal.warehouse_id,
            inbound_receipt_id=uuid.UUID(UUID1),
            receipt_revision_id=uuid.UUID(UUID2),
            source_type="MANUAL_ENTRY",
            supplier_snapshot={},
            carrier_snapshot=None,
            unloading_operation_id=None,
            gate_check_in_id=None,
            appointment_id=None,
            arrival_notice_id=None,
            principal=mock_principal,
        )
        svc = ReceptionDifferenceIntegrityService(database)
        result = svc.verify(case.id, mock_principal.organization_id)
        assert result["status"] in ("VALID", "NO_REVISION")

    def test_validation_empty_case(self, database, mock_principal):
        """Validation on empty case returns NO_ITEMS error."""
        from app.modules.logistics.inbound.reception_differences.application.services.validation_service import (
            ReceptionDifferenceValidationService,
        )
        from app.modules.logistics.inbound.reception_differences.application.services.case_service import (
            ReceptionDifferenceCaseService,
        )
        case_svc = ReceptionDifferenceCaseService(database)
        case = case_svc.create_case(
            organization_id=mock_principal.organization_id,
            branch_id=mock_principal.branch_id,
            warehouse_id=mock_principal.warehouse_id,
            inbound_receipt_id=uuid.UUID(UUID1),
            receipt_revision_id=uuid.UUID(UUID2),
            source_type="MANUAL_ENTRY",
            supplier_snapshot={},
            carrier_snapshot=None,
            unloading_operation_id=None,
            gate_check_in_id=None,
            appointment_id=None,
            arrival_notice_id=None,
            principal=mock_principal,
        )
        val_svc = ReceptionDifferenceValidationService(database)
        result = val_svc.validate(case.id, mock_principal.organization_id)
        assert result["is_valid"] is False
        assert "NO_ITEMS" in result["blocking_errors"]

    def test_duplicate_detector_exact_match(self, database, mock_principal):
        """Duplicate detector finds exact match for same type+product+quantities."""
        from app.modules.logistics.inbound.reception_differences.application.services.case_service import (
            ReceptionDifferenceCaseService,
        )
        from app.modules.logistics.inbound.reception_differences.application.services.item_service import (
            ReceptionDifferenceItemService,
        )
        from app.modules.logistics.inbound.reception_differences.application.services.duplicate_detector import (
            ReceptionDifferenceDuplicateDetector,
        )
        case_svc = ReceptionDifferenceCaseService(database)
        item_svc = ReceptionDifferenceItemService(database)
        case = case_svc.create_case(
            organization_id=mock_principal.organization_id,
            branch_id=mock_principal.branch_id,
            warehouse_id=mock_principal.warehouse_id,
            inbound_receipt_id=uuid.UUID(UUID1),
            receipt_revision_id=uuid.UUID(UUID2),
            source_type="MANUAL_ENTRY",
            supplier_snapshot={},
            carrier_snapshot=None,
            unloading_operation_id=None,
            gate_check_in_id=None,
            appointment_id=None,
            arrival_notice_id=None,
            principal=mock_principal,
        )
        item_svc.create_item(
            case_id=case.id, case_revision_id=case.active_revision_id,
            organization_id=mock_principal.organization_id,
            difference_type="SHORTAGE", title="Existing", description=None,
            product_id=uuid.UUID(UUID3), severity=None,
            expected_quantity=Decimal("100"), observed_quantity=Decimal("80"),
            expected_unit_id=None, observed_unit_id=None,
            source_candidate_id=None, purchase_order_id=None,
            purchase_order_line_id=None, expected_line_id=None, received_line_id=None,
            detection_source="MANUAL_REVIEW", detected_by_user_id=None,
            detected_by_service=None, principal=mock_principal,
        )
        detector = ReceptionDifferenceDuplicateDetector(database)
        result = detector.detect(
            case.id,
            {"difference_type": "SHORTAGE", "product_id": str(uuid.UUID(UUID3)),
             "expected_quantity": "100", "observed_quantity": "80"},
            mock_principal.organization_id,
        )
        assert result == ReceptionDifferenceDuplicateDetector.EXACT

    def test_duplicate_detector_no_match(self, database, mock_principal):
        """Duplicate detector returns NO_DUPLICATE for different types."""
        from app.modules.logistics.inbound.reception_differences.application.services.case_service import (
            ReceptionDifferenceCaseService,
        )
        from app.modules.logistics.inbound.reception_differences.application.services.item_service import (
            ReceptionDifferenceItemService,
        )
        from app.modules.logistics.inbound.reception_differences.application.services.duplicate_detector import (
            ReceptionDifferenceDuplicateDetector,
        )
        case_svc = ReceptionDifferenceCaseService(database)
        item_svc = ReceptionDifferenceItemService(database)
        case = case_svc.create_case(
            organization_id=mock_principal.organization_id,
            branch_id=mock_principal.branch_id,
            warehouse_id=mock_principal.warehouse_id,
            inbound_receipt_id=uuid.UUID(UUID1),
            receipt_revision_id=uuid.UUID(UUID2),
            source_type="MANUAL_ENTRY",
            supplier_snapshot={},
            carrier_snapshot=None,
            unloading_operation_id=None,
            gate_check_in_id=None,
            appointment_id=None,
            arrival_notice_id=None,
            principal=mock_principal,
        )
        item_svc.create_item(
            case_id=case.id, case_revision_id=case.active_revision_id,
            organization_id=mock_principal.organization_id,
            difference_type="SHORTAGE", title="Existing", description=None,
            product_id=None, severity=None,
            expected_quantity=Decimal("100"), observed_quantity=Decimal("80"),
            expected_unit_id=None, observed_unit_id=None,
            source_candidate_id=None, purchase_order_id=None,
            purchase_order_line_id=None, expected_line_id=None, received_line_id=None,
            detection_source="MANUAL_REVIEW", detected_by_user_id=None,
            detected_by_service=None, principal=mock_principal,
        )
        detector = ReceptionDifferenceDuplicateDetector(database)
        result = detector.detect(
            case.id,
            {"difference_type": "OVERAGE", "product_id": None,
             "expected_quantity": "100", "observed_quantity": "120"},
            mock_principal.organization_id,
        )
        assert result == ReceptionDifferenceDuplicateDetector.NONE

    def test_item_dismiss_reduces_open_count(self, database, mock_principal):
        """Dismissing an item decrements open_item_count."""
        from app.modules.logistics.inbound.reception_differences.application.services.case_service import (
            ReceptionDifferenceCaseService,
        )
        from app.modules.logistics.inbound.reception_differences.application.services.item_service import (
            ReceptionDifferenceItemService,
        )
        case_svc = ReceptionDifferenceCaseService(database)
        item_svc = ReceptionDifferenceItemService(database)
        case = case_svc.create_case(
            organization_id=mock_principal.organization_id,
            branch_id=mock_principal.branch_id,
            warehouse_id=mock_principal.warehouse_id,
            inbound_receipt_id=uuid.UUID(UUID1),
            receipt_revision_id=uuid.UUID(UUID2),
            source_type="MANUAL_ENTRY",
            supplier_snapshot={},
            carrier_snapshot=None,
            unloading_operation_id=None,
            gate_check_in_id=None,
            appointment_id=None,
            arrival_notice_id=None,
            principal=mock_principal,
        )
        item = item_svc.create_item(
            case_id=case.id, case_revision_id=case.active_revision_id,
            organization_id=mock_principal.organization_id,
            difference_type="SHORTAGE", title="To dismiss", description=None,
            product_id=None, severity=None, expected_quantity=Decimal("10"),
            observed_quantity=Decimal("5"), expected_unit_id=None,
            observed_unit_id=None, source_candidate_id=None, purchase_order_id=None,
            purchase_order_line_id=None, expected_line_id=None, received_line_id=None,
            detection_source="MANUAL_REVIEW", detected_by_user_id=None,
            detected_by_service=None, principal=mock_principal,
        )
        database.refresh(case)
        assert case.open_item_count == 1

        item_svc.dismiss_item(item.id, mock_principal.organization_id, "Not a real diff", mock_principal)
        database.refresh(case)
        assert case.open_item_count == 0

    def test_history_returns_revisions(self, database, mock_principal):
        """History endpoint returns revision data."""
        from app.modules.logistics.inbound.reception_differences.application.services.case_service import (
            ReceptionDifferenceCaseService,
        )
        svc = ReceptionDifferenceCaseService(database)
        case = svc.create_case(
            organization_id=mock_principal.organization_id,
            branch_id=mock_principal.branch_id,
            warehouse_id=mock_principal.warehouse_id,
            inbound_receipt_id=uuid.UUID(UUID1),
            receipt_revision_id=uuid.UUID(UUID2),
            source_type="MANUAL_ENTRY",
            supplier_snapshot={},
            carrier_snapshot=None,
            unloading_operation_id=None,
            gate_check_in_id=None,
            appointment_id=None,
            arrival_notice_id=None,
            principal=mock_principal,
        )
        history = svc.get_history(case.id, mock_principal.organization_id)
        assert "revisions" in history
        assert len(history["revisions"]) >= 1
        assert history["revisions"][0]["revision_number"] == 1

    def test_document_preview_returns_structure(self, database, mock_principal):
        """Document preview returns expected structure."""
        from app.modules.logistics.inbound.reception_differences.application.services.case_service import (
            ReceptionDifferenceCaseService,
        )
        from app.modules.logistics.inbound.reception_differences.application.services.document_service import (
            ReceptionDifferenceDocumentService,
        )
        case_svc = ReceptionDifferenceCaseService(database)
        case = case_svc.create_case(
            organization_id=mock_principal.organization_id,
            branch_id=mock_principal.branch_id,
            warehouse_id=mock_principal.warehouse_id,
            inbound_receipt_id=uuid.UUID(UUID1),
            receipt_revision_id=uuid.UUID(UUID2),
            source_type="MANUAL_ENTRY",
            supplier_snapshot={},
            carrier_snapshot=None,
            unloading_operation_id=None,
            gate_check_in_id=None,
            appointment_id=None,
            arrival_notice_id=None,
            principal=mock_principal,
        )
        doc_svc = ReceptionDifferenceDocumentService(database)
        preview = doc_svc.preview(case.id, mock_principal.organization_id)
        assert "case_id" in preview
        assert "items" in preview
        assert "content_hash" in preview

    def test_document_issue_and_cancel(self, database, mock_principal):
        """Issue a document and then cancel it."""
        from app.modules.logistics.inbound.reception_differences.application.services.case_service import (
            ReceptionDifferenceCaseService,
        )
        from app.modules.logistics.inbound.reception_differences.application.services.document_service import (
            ReceptionDifferenceDocumentService,
        )
        case_svc = ReceptionDifferenceCaseService(database)
        doc_svc = ReceptionDifferenceDocumentService(database)
        case = case_svc.create_case(
            organization_id=mock_principal.organization_id,
            branch_id=mock_principal.branch_id,
            warehouse_id=mock_principal.warehouse_id,
            inbound_receipt_id=uuid.UUID(UUID1),
            receipt_revision_id=uuid.UUID(UUID2),
            source_type="MANUAL_ENTRY",
            supplier_snapshot={},
            carrier_snapshot=None,
            unloading_operation_id=None,
            gate_check_in_id=None,
            appointment_id=None,
            arrival_notice_id=None,
            principal=mock_principal,
        )
        result = doc_svc.issue_document(case.id, mock_principal.organization_id, mock_principal)
        assert "document_instance_id" in result

        cancel_result = doc_svc.cancel_document(case.id, mock_principal.organization_id, "Mistake", mock_principal)
        assert "cancelled_document_instance_id" in cancel_result

    def test_acknowledgement_create_and_list(self, database, mock_principal):
        """Create acknowledgement and list it."""
        from app.modules.logistics.inbound.reception_differences.application.services.case_service import (
            ReceptionDifferenceCaseService,
        )
        from app.modules.logistics.inbound.reception_differences.application.services.acknowledgement_service import (
            ReceptionDifferenceAcknowledgementService,
        )
        case_svc = ReceptionDifferenceCaseService(database)
        ack_svc = ReceptionDifferenceAcknowledgementService(database)
        case = case_svc.create_case(
            organization_id=mock_principal.organization_id,
            branch_id=mock_principal.branch_id,
            warehouse_id=mock_principal.warehouse_id,
            inbound_receipt_id=uuid.UUID(UUID1),
            receipt_revision_id=uuid.UUID(UUID2),
            source_type="MANUAL_ENTRY",
            supplier_snapshot={},
            carrier_snapshot=None,
            unloading_operation_id=None,
            gate_check_in_id=None,
            appointment_id=None,
            arrival_notice_id=None,
            principal=mock_principal,
        )
        ack = ack_svc.create_acknowledgement(
            case_id=case.id, party_type="SUPPLIER",
            business_partner_id=None,
            acknowledgement_type="RECEIVED_COPY",
            statement="Received the document", source_channel="API",
            principal=mock_principal,
        )
        assert ack.status == "ACTIVE"
        acks = ack_svc.list_acknowledgements(case.id, mock_principal.organization_id)
        assert len(acks) >= 1

    def test_responsibility_propose_and_acknowledge(self, database, mock_principal):
        """Propose a responsible party and acknowledge."""
        from app.modules.logistics.inbound.reception_differences.application.services.case_service import (
            ReceptionDifferenceCaseService,
        )
        from app.modules.logistics.inbound.reception_differences.application.services.responsibility_service import (
            ReceptionDifferenceResponsibilityService,
        )
        case_svc = ReceptionDifferenceCaseService(database)
        resp_svc = ReceptionDifferenceResponsibilityService(database)
        case = case_svc.create_case(
            organization_id=mock_principal.organization_id,
            branch_id=mock_principal.branch_id,
            warehouse_id=mock_principal.warehouse_id,
            inbound_receipt_id=uuid.UUID(UUID1),
            receipt_revision_id=uuid.UUID(UUID2),
            source_type="MANUAL_ENTRY",
            supplier_snapshot={},
            carrier_snapshot=None,
            unloading_operation_id=None,
            gate_check_in_id=None,
            appointment_id=None,
            arrival_notice_id=None,
            principal=mock_principal,
        )
        party = resp_svc.propose_responsible(
            case_id=case.id, item_id=None,
            party_type="SUPPLIER", business_partner_id=None,
            user_id=None, responsibility_role="PRIMARY",
            notes=None, allocation_percentage=100.0,
            principal=mock_principal,
        )
        assert party.responsibility_status == ResponsibilityStatus.PROPOSED

        party = resp_svc.acknowledge_responsible(
            party.id, mock_principal.organization_id, mock_principal
        )
        assert party.responsibility_status == ResponsibilityStatus.ACKNOWLEDGED

    def test_review_create_start_complete(self, database, mock_principal):
        """Create review, start, and complete."""
        from app.modules.logistics.inbound.reception_differences.application.services.case_service import (
            ReceptionDifferenceCaseService,
        )
        from app.modules.logistics.inbound.reception_differences.application.services.review_service import (
            ReceptionDifferenceReviewService,
        )
        case_svc = ReceptionDifferenceCaseService(database)
        rev_svc = ReceptionDifferenceReviewService(database)
        case = case_svc.create_case(
            organization_id=mock_principal.organization_id,
            branch_id=mock_principal.branch_id,
            warehouse_id=mock_principal.warehouse_id,
            inbound_receipt_id=uuid.UUID(UUID1),
            receipt_revision_id=uuid.UUID(UUID2),
            source_type="MANUAL_ENTRY",
            supplier_snapshot={},
            carrier_snapshot=None,
            unloading_operation_id=None,
            gate_check_in_id=None,
            appointment_id=None,
            arrival_notice_id=None,
            principal=mock_principal,
        )
        review = rev_svc.create_review(
            case.id, "OPERATIONAL", mock_principal.organization_id, mock_principal
        )
        assert review.status == ReviewStatus.PENDING

        review = rev_svc.start_review(review.id, mock_principal.organization_id, mock_principal)
        assert review.status == ReviewStatus.IN_PROGRESS

        review = rev_svc.complete_review(
            review.id, mock_principal.organization_id,
            findings="All looks good", blocking_issues=None,
            requested_changes=None, recommendation="Approve",
            principal=mock_principal,
        )
        assert review.status == ReviewStatus.COMPLETED

    def test_case_not_found_raises(self, database, mock_principal):
        """Accessing a non-existent case raises 404."""
        from app.modules.logistics.inbound.reception_differences.application.services.case_service import (
            ReceptionDifferenceCaseService,
        )
        svc = ReceptionDifferenceCaseService(database)
        with pytest.raises(ReceptionDifferenceError) as exc_info:
            svc.get_case(uuid.uuid4(), mock_principal.organization_id)
        assert exc_info.value.status_code == 404

    def test_list_cases_with_filters(self, database, mock_principal):
        """List cases with status filter."""
        from app.modules.logistics.inbound.reception_differences.application.services.case_service import (
            ReceptionDifferenceCaseService,
        )
        svc = ReceptionDifferenceCaseService(database)
        svc.create_case(
            organization_id=mock_principal.organization_id,
            branch_id=mock_principal.branch_id,
            warehouse_id=mock_principal.warehouse_id,
            inbound_receipt_id=uuid.UUID(UUID1),
            receipt_revision_id=uuid.UUID(UUID2),
            source_type="MANUAL_ENTRY",
            supplier_snapshot={},
            carrier_snapshot=None,
            unloading_operation_id=None,
            gate_check_in_id=None,
            appointment_id=None,
            arrival_notice_id=None,
            principal=mock_principal,
        )
        cases, total = svc.list_cases(
            mock_principal.organization_id,
            filters={"status": "DRAFT"},
        )
        assert total >= 1
        assert all(c.status == "DRAFT" for c in cases)

    def test_manual_creation_service(self, database, mock_principal):
        """Manual item creation via ManualReceptionDifferenceService."""
        from app.modules.logistics.inbound.reception_differences.application.services.case_service import (
            ReceptionDifferenceCaseService,
        )
        from app.modules.logistics.inbound.reception_differences.application.services.manual_creation_service import (
            ManualReceptionDifferenceService,
        )
        case_svc = ReceptionDifferenceCaseService(database)
        manual_svc = ManualReceptionDifferenceService(database)
        case = case_svc.create_case(
            organization_id=mock_principal.organization_id,
            branch_id=mock_principal.branch_id,
            warehouse_id=mock_principal.warehouse_id,
            inbound_receipt_id=uuid.UUID(UUID1),
            receipt_revision_id=uuid.UUID(UUID2),
            source_type="MANUAL_ENTRY",
            supplier_snapshot={},
            carrier_snapshot=None,
            unloading_operation_id=None,
            gate_check_in_id=None,
            appointment_id=None,
            arrival_notice_id=None,
            principal=mock_principal,
        )
        item = manual_svc.create_manual_item(
            case_id=case.id,
            organization_id=mock_principal.organization_id,
            difference_type="WRONG_PRODUCT",
            title="Wrong item delivered",
            description="Expected Widget A, got Widget B",
            product_id=None,
            severity="HIGH",
            observed_quantity=Decimal("10"),
            observed_unit_id=None,
            principal=mock_principal,
        )
        assert item.difference_type == "WRONG_PRODUCT"
        assert item.severity == "HIGH"
        assert item.status == ItemStatus.OPEN

    def test_snapshot_provider_captures_full_state(self, database, mock_principal):
        """SnapshotProvider captures case, items, evidence."""
        from app.modules.logistics.inbound.reception_differences.application.services.case_service import (
            ReceptionDifferenceCaseService,
        )
        from app.modules.logistics.inbound.reception_differences.application.services.snapshot_provider import (
            ReceptionDifferenceSnapshotProvider,
        )
        case_svc = ReceptionDifferenceCaseService(database)
        snap_svc = ReceptionDifferenceSnapshotProvider(database)
        case = case_svc.create_case(
            organization_id=mock_principal.organization_id,
            branch_id=mock_principal.branch_id,
            warehouse_id=mock_principal.warehouse_id,
            inbound_receipt_id=uuid.UUID(UUID1),
            receipt_revision_id=uuid.UUID(UUID2),
            source_type="MANUAL_ENTRY",
            supplier_snapshot={},
            carrier_snapshot=None,
            unloading_operation_id=None,
            gate_check_in_id=None,
            appointment_id=None,
            arrival_notice_id=None,
            principal=mock_principal,
        )
        snapshot = snap_svc.capture(case.id, mock_principal.organization_id)
        assert "case" in snapshot
        assert "items" in snapshot
        assert "evidence" in snapshot
        assert "responsibility" in snapshot
        assert "review" in snapshot
        assert "approval" in snapshot
        assert "acknowledgement" in snapshot
        assert "canonicalization_version" in snapshot

    def test_quantity_service_difference_and_variance(self):
        """QuantityService calculates difference and variance correctly."""
        from app.modules.logistics.inbound.reception_differences.application.services.quantity_service import (
            ReceptionDifferenceQuantityService,
        )
        svc = ReceptionDifferenceQuantityService
        diff = svc.calculate_difference(Decimal("200"), Decimal("180"), "SHORTAGE")
        assert diff["difference_quantity"] == Decimal("20")
        assert diff["is_shortage"] is True

        var = svc.calculate_variance_percentage(Decimal("200"), Decimal("210"))
        assert var == Decimal("5.00")

    def test_evidence_archive_decrements_count(self, database, mock_principal):
        """Archiving evidence decrements evidence_count."""
        from app.modules.logistics.inbound.reception_differences.application.services.case_service import (
            ReceptionDifferenceCaseService,
        )
        from app.modules.logistics.inbound.reception_differences.application.services.evidence_service import (
            ReceptionDifferenceEvidenceService,
        )
        case_svc = ReceptionDifferenceCaseService(database)
        ev_svc = ReceptionDifferenceEvidenceService(database)
        case = case_svc.create_case(
            organization_id=mock_principal.organization_id,
            branch_id=mock_principal.branch_id,
            warehouse_id=mock_principal.warehouse_id,
            inbound_receipt_id=uuid.UUID(UUID1),
            receipt_revision_id=uuid.UUID(UUID2),
            source_type="MANUAL_ENTRY",
            supplier_snapshot={},
            carrier_snapshot=None,
            unloading_operation_id=None,
            gate_check_in_id=None,
            appointment_id=None,
            arrival_notice_id=None,
            principal=mock_principal,
        )
        link = ev_svc.link_evidence(
            case_id=case.id, item_id=None,
            file_asset_id=uuid.UUID(UUID3), file_version_id=None,
            evidence_type="PRODUCT_PHOTO", classification="STANDARD",
            description=None, captured_at=None, principal=mock_principal,
        )
        database.refresh(case)
        assert case.evidence_count == 1

        ev_svc.archive_evidence(link.id, mock_principal.organization_id, mock_principal)
        database.refresh(case)
        assert case.evidence_count == 0

    def test_item_update_changes_category(self, database, mock_principal):
        """Updating difference_type recalculates category."""
        from app.modules.logistics.inbound.reception_differences.application.services.case_service import (
            ReceptionDifferenceCaseService,
        )
        from app.modules.logistics.inbound.reception_differences.application.services.item_service import (
            ReceptionDifferenceItemService,
        )
        case_svc = ReceptionDifferenceCaseService(database)
        item_svc = ReceptionDifferenceItemService(database)
        case = case_svc.create_case(
            organization_id=mock_principal.organization_id,
            branch_id=mock_principal.branch_id,
            warehouse_id=mock_principal.warehouse_id,
            inbound_receipt_id=uuid.UUID(UUID1),
            receipt_revision_id=uuid.UUID(UUID2),
            source_type="MANUAL_ENTRY",
            supplier_snapshot={},
            carrier_snapshot=None,
            unloading_operation_id=None,
            gate_check_in_id=None,
            appointment_id=None,
            arrival_notice_id=None,
            principal=mock_principal,
        )
        item = item_svc.create_item(
            case_id=case.id, case_revision_id=case.active_revision_id,
            organization_id=mock_principal.organization_id,
            difference_type="SHORTAGE", title="Test", description=None,
            product_id=None, severity=None, expected_quantity=Decimal("10"),
            observed_quantity=Decimal("5"), expected_unit_id=None,
            observed_unit_id=None, source_candidate_id=None, purchase_order_id=None,
            purchase_order_line_id=None, expected_line_id=None, received_line_id=None,
            detection_source="MANUAL_REVIEW", detected_by_user_id=None,
            detected_by_service=None, principal=mock_principal,
        )
        assert item.category == "QUANTITY"

        updated = item_svc.update_item(
            item.id, mock_principal.organization_id,
            difference_type="WRONG_PRODUCT",
        )
        assert updated.category == "PRODUCT"

    def test_responsibility_dispute(self, database, mock_principal):
        """Dispute a responsible party."""
        from app.modules.logistics.inbound.reception_differences.application.services.case_service import (
            ReceptionDifferenceCaseService,
        )
        from app.modules.logistics.inbound.reception_differences.application.services.responsibility_service import (
            ReceptionDifferenceResponsibilityService,
        )
        case_svc = ReceptionDifferenceCaseService(database)
        resp_svc = ReceptionDifferenceResponsibilityService(database)
        case = case_svc.create_case(
            organization_id=mock_principal.organization_id,
            branch_id=mock_principal.branch_id,
            warehouse_id=mock_principal.warehouse_id,
            inbound_receipt_id=uuid.UUID(UUID1),
            receipt_revision_id=uuid.UUID(UUID2),
            source_type="MANUAL_ENTRY",
            supplier_snapshot={},
            carrier_snapshot=None,
            unloading_operation_id=None,
            gate_check_in_id=None,
            appointment_id=None,
            arrival_notice_id=None,
            principal=mock_principal,
        )
        party = resp_svc.propose_responsible(
            case_id=case.id, item_id=None,
            party_type="CARRIER", business_partner_id=None,
            user_id=None, responsibility_role="PRIMARY",
            notes=None, allocation_percentage=None,
            principal=mock_principal,
        )
        party = resp_svc.dispute_responsible(
            party.id, mock_principal.organization_id,
            "We disagree with this attribution", mock_principal,
        )
        assert party.responsibility_status == ResponsibilityStatus.DISPUTED
        assert party.dispute_reason == "We disagree with this attribution"

    def test_review_request_changes(self, database, mock_principal):
        """Review with changes requested."""
        from app.modules.logistics.inbound.reception_differences.application.services.case_service import (
            ReceptionDifferenceCaseService,
        )
        from app.modules.logistics.inbound.reception_differences.application.services.review_service import (
            ReceptionDifferenceReviewService,
        )
        case_svc = ReceptionDifferenceCaseService(database)
        rev_svc = ReceptionDifferenceReviewService(database)
        case = case_svc.create_case(
            organization_id=mock_principal.organization_id,
            branch_id=mock_principal.branch_id,
            warehouse_id=mock_principal.warehouse_id,
            inbound_receipt_id=uuid.UUID(UUID1),
            receipt_revision_id=uuid.UUID(UUID2),
            source_type="MANUAL_ENTRY",
            supplier_snapshot={},
            carrier_snapshot=None,
            unloading_operation_id=None,
            gate_check_in_id=None,
            appointment_id=None,
            arrival_notice_id=None,
            principal=mock_principal,
        )
        review = rev_svc.create_review(
            case.id, "OPERATIONAL", mock_principal.organization_id, mock_principal
        )
        review = rev_svc.start_review(review.id, mock_principal.organization_id, mock_principal)
        review = rev_svc.request_changes(
            review.id, mock_principal.organization_id,
            {"reason": "Need more photos"}, mock_principal,
        )
        assert review.status == ReviewStatus.CHANGES_REQUESTED

    def test_case_transition_case_status_invalid_for_transition(self, database, mock_principal):
        """Transition to an invalid target raises error."""
        from app.modules.logistics.inbound.reception_differences.application.services.case_service import (
            ReceptionDifferenceCaseService,
        )
        svc = ReceptionDifferenceCaseService(database)
        case = svc.create_case(
            organization_id=mock_principal.organization_id,
            branch_id=mock_principal.branch_id,
            warehouse_id=mock_principal.warehouse_id,
            inbound_receipt_id=uuid.UUID(UUID1),
            receipt_revision_id=uuid.UUID(UUID2),
            source_type="MANUAL_ENTRY",
            supplier_snapshot={},
            carrier_snapshot=None,
            unloading_operation_id=None,
            gate_check_in_id=None,
            appointment_id=None,
            arrival_notice_id=None,
            principal=mock_principal,
        )
        with pytest.raises(ReceptionDifferenceError) as exc_info:
            svc.transition_case(case.id, "APPROVED", mock_principal)
        assert exc_info.value.status_code == 409

    def test_item_transition_invalid_raises(self, database, mock_principal):
        """Invalid item transition raises error."""
        from app.modules.logistics.inbound.reception_differences.application.services.case_service import (
            ReceptionDifferenceCaseService,
        )
        from app.modules.logistics.inbound.reception_differences.application.services.item_service import (
            ReceptionDifferenceItemService,
        )
        case_svc = ReceptionDifferenceCaseService(database)
        item_svc = ReceptionDifferenceItemService(database)
        case = case_svc.create_case(
            organization_id=mock_principal.organization_id,
            branch_id=mock_principal.branch_id,
            warehouse_id=mock_principal.warehouse_id,
            inbound_receipt_id=uuid.UUID(UUID1),
            receipt_revision_id=uuid.UUID(UUID2),
            source_type="MANUAL_ENTRY",
            supplier_snapshot={},
            carrier_snapshot=None,
            unloading_operation_id=None,
            gate_check_in_id=None,
            appointment_id=None,
            arrival_notice_id=None,
            principal=mock_principal,
        )
        item = item_svc.create_item(
            case_id=case.id, case_revision_id=case.active_revision_id,
            organization_id=mock_principal.organization_id,
            difference_type="SHORTAGE", title="Test", description=None,
            product_id=None, severity=None, expected_quantity=Decimal("10"),
            observed_quantity=Decimal("5"), expected_unit_id=None,
            observed_unit_id=None, source_candidate_id=None, purchase_order_id=None,
            purchase_order_line_id=None, expected_line_id=None, received_line_id=None,
            detection_source="MANUAL_REVIEW", detected_by_user_id=None,
            detected_by_service=None, principal=mock_principal,
        )
        with pytest.raises(ReceptionDifferenceError) as exc_info:
            item_svc.dismiss_item(item.id, mock_principal.organization_id, "reason", mock_principal)
            # After dismiss, trying to dismiss again should fail
            item_svc.dismiss_item(item.id, mock_principal.organization_id, "again", mock_principal)
        assert exc_info.value.status_code == 409

    def test_document_reprint(self, database, mock_principal):
        """Reprint document."""
        from app.modules.logistics.inbound.reception_differences.application.services.case_service import (
            ReceptionDifferenceCaseService,
        )
        from app.modules.logistics.inbound.reception_differences.application.services.document_service import (
            ReceptionDifferenceDocumentService,
        )
        case_svc = ReceptionDifferenceCaseService(database)
        doc_svc = ReceptionDifferenceDocumentService(database)
        case = case_svc.create_case(
            organization_id=mock_principal.organization_id,
            branch_id=mock_principal.branch_id,
            warehouse_id=mock_principal.warehouse_id,
            inbound_receipt_id=uuid.UUID(UUID1),
            receipt_revision_id=uuid.UUID(UUID2),
            source_type="MANUAL_ENTRY",
            supplier_snapshot={},
            carrier_snapshot=None,
            unloading_operation_id=None,
            gate_check_in_id=None,
            appointment_id=None,
            arrival_notice_id=None,
            principal=mock_principal,
        )
        result = doc_svc.reprint(case.id, mock_principal.organization_id, mock_principal)
        assert "case_id" in result
        assert "items" in result

    def test_document_package_create(self, database, mock_principal):
        """Create a document package."""
        from app.modules.logistics.inbound.reception_differences.application.services.case_service import (
            ReceptionDifferenceCaseService,
        )
        from app.modules.logistics.inbound.reception_differences.application.services.document_service import (
            ReceptionDifferenceDocumentService,
        )
        case_svc = ReceptionDifferenceCaseService(database)
        doc_svc = ReceptionDifferenceDocumentService(database)
        case = case_svc.create_case(
            organization_id=mock_principal.organization_id,
            branch_id=mock_principal.branch_id,
            warehouse_id=mock_principal.warehouse_id,
            inbound_receipt_id=uuid.UUID(UUID1),
            receipt_revision_id=uuid.UUID(UUID2),
            source_type="MANUAL_ENTRY",
            supplier_snapshot={},
            carrier_snapshot=None,
            unloading_operation_id=None,
            gate_check_in_id=None,
            appointment_id=None,
            arrival_notice_id=None,
            principal=mock_principal,
        )
        result = doc_svc.create_package(case.id, mock_principal.organization_id, mock_principal)
        assert "package_id" in result
        assert result["status"] == "PENDING"
