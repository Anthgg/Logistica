"""ApprovalSubjectRegistry — registry of approvable purchasing subject types.

Provides registry definitions, capability resolvers, and metadata for:
- PURCHASE_ORDER
- PURCHASE_ORDER_REVISION
- PURCHASE_ORDER_AMENDMENT
- PURCHASE_ORDER_VARIANCE
- SINGLE_SOURCE_EXCEPTION

Extensible for future procurement subjects.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable
from uuid import UUID

from app.modules.logistics.procurement.approvals.domain.errors.exceptions import (
    ProcurementApprovalDomainError,
)


@dataclass(frozen=True)
class SubjectTypeDefinition:
    """Definition of an approvable subject type."""
    code: str
    module_name: str
    description: str
    is_active: bool
    requires_revision: bool
    supports_variances: bool
    default_approval_permission: str


class ApprovalSubjectRegistry:
    """Registry for all approvable procurement subject types."""

    _SUBJECTS: dict[str, SubjectTypeDefinition] = {
        "PURCHASE_ORDER": SubjectTypeDefinition(
            code="PURCHASE_ORDER",
            module_name="logistics.procurement.purchase_orders",
            description="Purchase Order Aggregate Root",
            is_active=True,
            requires_revision=True,
            supports_variances=True,
            default_approval_permission="logistics.purchase_orders.approve",
        ),
        "PURCHASE_ORDER_REVISION": SubjectTypeDefinition(
            code="PURCHASE_ORDER_REVISION",
            module_name="logistics.procurement.purchase_orders",
            description="Purchase Order Revision",
            is_active=True,
            requires_revision=True,
            supports_variances=False,
            default_approval_permission="logistics.purchase_orders.approve",
        ),
        "PURCHASE_ORDER_AMENDMENT": SubjectTypeDefinition(
            code="PURCHASE_ORDER_AMENDMENT",
            module_name="logistics.procurement.purchase_orders",
            description="Purchase Order Post-Issuance Amendment",
            is_active=True,
            requires_revision=False,
            supports_variances=True,
            default_approval_permission="logistics.purchase_orders.approve",
        ),
        "PURCHASE_ORDER_VARIANCE": SubjectTypeDefinition(
            code="PURCHASE_ORDER_VARIANCE",
            module_name="logistics.procurement.purchase_orders",
            description="Purchase Order Source Variance / Price Deviation",
            is_active=True,
            requires_revision=False,
            supports_variances=False,
            default_approval_permission="logistics.purchase_orders.approve",
        ),
        "SINGLE_SOURCE_EXCEPTION": SubjectTypeDefinition(
            code="SINGLE_SOURCE_EXCEPTION",
            module_name="logistics.procurement.evaluations",
            description="Single Source Supplier Adjudication Exception",
            is_active=True,
            requires_revision=False,
            supports_variances=False,
            default_approval_permission="logistics.quotation_evaluations.approve",
        ),
        # Prepared for future phases (disabled until enabled)
        "PURCHASE_REQUISITION": SubjectTypeDefinition(
            code="PURCHASE_REQUISITION",
            module_name="logistics.procurement.requisitions",
            description="Purchase Requisition",
            is_active=False,
            requires_revision=True,
            supports_variances=False,
            default_approval_permission="logistics.purchase_requisitions.approve",
        ),
        "QUOTATION_EVALUATION_DECISION": SubjectTypeDefinition(
            code="QUOTATION_EVALUATION_DECISION",
            module_name="logistics.procurement.evaluations",
            description="Quotation Evaluation Award Decision",
            is_active=False,
            requires_revision=False,
            supports_variances=False,
            default_approval_permission="logistics.quotation_evaluations.approve",
        ),
    }

    @classmethod
    def get(cls, subject_type_code: str) -> SubjectTypeDefinition:
        """Fetch subject definition or raise ValueError."""
        clean_code = str(subject_type_code).strip().upper()
        subj = cls._SUBJECTS.get(clean_code)
        if not subj:
            raise ValueError(
                f"Subject type {subject_type_code!r} is not registered. "
                f"Allowed: {sorted(cls._SUBJECTS.keys())}"
            )
        if not subj.is_active:
            raise ProcurementApprovalDomainError(
                f"Subject type {clean_code!r} is registered but currently inactive."
            )
        return subj

    @classmethod
    def is_registered(cls, subject_type_code: str) -> bool:
        clean_code = str(subject_type_code).strip().upper()
        return clean_code in cls._SUBJECTS and cls._SUBJECTS[clean_code].is_active

    @classmethod
    def list_active(cls) -> list[SubjectTypeDefinition]:
        return [s for s in cls._SUBJECTS.values() if s.is_active]
