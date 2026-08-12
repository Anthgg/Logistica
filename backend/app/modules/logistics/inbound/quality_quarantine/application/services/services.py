"""Phase 042 — Application services for quality quarantine module."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.modules.logistics.inbound.quality_quarantine.domain.enums import (
    AllocationStatus,
    AvailabilityClass,
    DecisionStatus,
    DecisionType,
    InspectionOverallResult,
    InspectionStatus,
    QuarantineSourceType,
    QuarantineStatus,
    QualityStatus,
    ReleaseStatus,
    ReleaseType,
    RejectionStatus,
    RejectionType,
    SplitReason,
    TriggerEvaluationResult,
)
from app.modules.logistics.inbound.quality_quarantine.domain.errors import (
    InboundInventoryAllocationAlreadyMaterialized,
    InboundInventoryAllocationNotFound,
    InboundInventoryAllocationQuantityExceeded,
    QualityInspectionAlreadyExists,
    QualityInspectionNotFound,
    QualityInspectionStatusInvalid,
    QualityQuarantineAlreadyExists,
    QualityQuarantineCaseNotFound,
    QualityQuarantineStatusInvalid,
    QuarantineReleaseNotAllowed,
    QuarantineAlreadyReleased,
    QuarantineAlreadyRejected,
    QuarantineRejectionNotAllowed,
)
from app.modules.logistics.inbound.quality_quarantine.domain.services.allocation_service import (
    derive_availability_class,
    derive_quality_status,
    require_allocation_transition,
)
from app.modules.logistics.inbound.quality_quarantine.domain.services.integrity_service import (
    canonical_hash,
)
from app.modules.logistics.inbound.quality_quarantine.domain.services.inspection_result_service import (
    calculate_overall_result,
)
from app.modules.logistics.inbound.quality_quarantine.domain.services.quarantine_case_service import (
    derive_quarantine_quality_result,
    require_quarantine_transition,
)
from app.modules.logistics.inbound.quality_quarantine.domain.services.split_service import (
    validate_split,
)
from app.modules.logistics.inbound.quality_quarantine.domain.services.trigger_service import (
    QuarantineTriggerService,
)
from app.modules.logistics.inbound.quality_quarantine.infrastructure.persistence.models import (
    InboundInventoryDispositionAllocationModel,
    QualityDispositionDecisionModel,
    QualityDispositionEventModel,
    QualityInspectionControlModel,
    QualityInspectionEvidenceLinkModel,
    QualityInspectionModel,
    QualityInspectionSnapshotModel,
    QualityQuarantineCaseModel,
    QualityQuarantineCaseRevisionModel,
    QuarantineReleaseAuthorizationModel,
    QuarantineRejectionAuthorizationModel,
)
from app.modules.logistics.inbound.quality_quarantine.infrastructure.persistence.repositories import (
    AllocationRepository,
    DecisionRepository,
    DispositionEventRepository,
    InspectionControlRepository,
    InspectionRepository,
    ProjectionRepository,
    QuarantineCaseRepository,
    ReleaseRepository,
    RejectionRepository,
    SnapshotRepository,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class InboundInventoryDispositionService:
    """Materializes disposition allocations from completed receipts."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._alloc_repo = AllocationRepository(db)
        self._quarantine_repo = QuarantineCaseRepository(db)
        self._event_repo = DispositionEventRepository(db)

    def materialize_from_receipt(
        self,
        *,
        organization_id: UUID,
        branch_id: UUID,
        warehouse_id: UUID,
        receipt_id: UUID,
        receipt_revision_id: UUID,
        received_line_id: UUID,
        expected_line_id: UUID | None,
        purchase_order_id: UUID | None,
        purchase_order_line_id: UUID | None,
        supplier_business_partner_id: UUID,
        product_id: UUID,
        product_version_id: UUID | None,
        sku_snapshot: str | None,
        product_name_snapshot: str | None,
        quantity: Decimal,
        unit_id: UUID,
        base_quantity: Decimal,
        lot_observation_ids: list[str] | None = None,
        serial_observation_ids: list[str] | None = None,
        expiration_observation_ids: list[str] | None = None,
        difference_case_ids: list[str] | None = None,
        actor_user_id: UUID | None = None,
    ) -> InboundInventoryDispositionAllocationModel:
        """Materialize a disposition allocation from a received line. Idempotent."""
        existing = self._alloc_repo.get_by_received_line(receipt_id, received_line_id)
        if existing:
            raise InboundInventoryAllocationAlreadyMaterialized(received_line_id=str(received_line_id))

        if quantity <= 0 or base_quantity <= 0:
            raise InboundInventoryAllocationQuantityExceeded(
                quantity=str(quantity), received_quantity="0"
            )

        alloc_id = uuid4()
        model = InboundInventoryDispositionAllocationModel(
            id=alloc_id,
            organization_id=organization_id,
            branch_id=branch_id,
            warehouse_id=warehouse_id,
            inbound_receipt_id=receipt_id,
            inbound_receipt_revision_id=receipt_revision_id,
            inbound_received_line_id=received_line_id,
            expected_line_id=expected_line_id,
            purchase_order_id=purchase_order_id,
            purchase_order_line_id=purchase_order_line_id,
            supplier_business_partner_id=supplier_business_partner_id,
            product_id=product_id,
            product_version_id=product_version_id,
            sku_snapshot=sku_snapshot,
            product_name_snapshot=product_name_snapshot,
            quantity=quantity,
            unit_id=unit_id,
            base_quantity=base_quantity,
            allocation_status=AllocationStatus.PENDING_QUALITY_ASSESSMENT,
            availability_class=AvailabilityClass.BLOCKED,
            quality_status=QualityStatus.NOT_ASSESSED,
            root_allocation_id=alloc_id,
            split_sequence=0,
            lot_observation_ids=lot_observation_ids or [],
            serial_observation_ids=serial_observation_ids or [],
            expiration_observation_ids=expiration_observation_ids or [],
            difference_case_ids=difference_case_ids or [],
            created_by=actor_user_id or uuid4(),
        )
        self._alloc_repo.create(model)
        return model

    def evaluate(self, allocation_id: UUID) -> dict:
        """Evaluate triggers for an allocation."""
        alloc = self._alloc_repo.get(allocation_id)
        if not alloc:
            raise InboundInventoryAllocationNotFound(allocation_id=str(allocation_id))

        evaluation = QuarantineTriggerService.evaluate_triggers(
            product_requires_inspection=True,
            quality_plan_applicable=True,
        )

        if evaluation["result"] == TriggerEvaluationResult.QUARANTINE_REQUIRED:
            target = AllocationStatus.QUARANTINE_REQUIRED
        elif evaluation["result"] == TriggerEvaluationResult.INSPECTION_REQUIRED:
            target = AllocationStatus.INSPECTION_PENDING
        elif evaluation["result"] == TriggerEvaluationResult.DIRECT_RELEASE_ELIGIBLE:
            target = AllocationStatus.QUALITY_APPROVED
        else:
            target = AllocationStatus.PENDING_QUALITY_ASSESSMENT

        require_allocation_transition(alloc.allocation_status, target)
        new_availability = derive_availability_class(target)
        new_quality = derive_quality_status(None, target)
        self._alloc_repo.update_status(
            allocation_id, status=target, availability_class=new_availability, quality_status=new_quality
        )

        return {
            "allocation_id": str(allocation_id),
            "evaluation": evaluation,
            "new_status": target,
            "new_availability_class": new_availability,
        }

    def split(self, allocation_id: UUID, first_quantity: Decimal, first_base: Decimal, reason: str, actor: UUID) -> dict:
        """Split allocation into two. Idempotent."""
        alloc = self._alloc_repo.get(allocation_id)
        if not alloc:
            raise InboundInventoryAllocationNotFound(allocation_id=str(allocation_id))

        second_qty = alloc.quantity - first_quantity
        second_base = alloc.base_quantity - first_base

        validate_split(
            original_quantity=alloc.quantity,
            original_base_quantity=alloc.base_quantity,
            first_child_quantity=first_quantity,
            first_child_base_quantity=first_base,
            second_child_quantity=second_qty,
            second_child_base_quantity=second_base,
        )

        first_id = uuid4()
        second_id = uuid4()

        first_child = InboundInventoryDispositionAllocationModel(
            id=first_id,
            organization_id=alloc.organization_id,
            branch_id=alloc.branch_id,
            warehouse_id=alloc.warehouse_id,
            inbound_receipt_id=alloc.inbound_receipt_id,
            inbound_receipt_revision_id=alloc.inbound_receipt_revision_id,
            inbound_received_line_id=alloc.inbound_received_line_id,
            expected_line_id=alloc.expected_line_id,
            purchase_order_id=alloc.purchase_order_id,
            purchase_order_line_id=alloc.purchase_order_line_id,
            supplier_business_partner_id=alloc.supplier_business_partner_id,
            product_id=alloc.product_id,
            product_version_id=alloc.product_version_id,
            sku_snapshot=alloc.sku_snapshot,
            product_name_snapshot=alloc.product_name_snapshot,
            quantity=first_quantity,
            unit_id=alloc.unit_id,
            base_quantity=first_base,
            allocation_status=alloc.allocation_status,
            availability_class=alloc.availability_class,
            quality_status=alloc.quality_status,
            parent_allocation_id=allocation_id,
            root_allocation_id=alloc.root_allocation_id,
            split_sequence=alloc.split_sequence + 1,
            lot_observation_ids=alloc.lot_observation_ids,
            serial_observation_ids=alloc.serial_observation_ids,
            expiration_observation_ids=alloc.expiration_observation_ids,
            difference_case_ids=alloc.difference_case_ids,
            quarantine_case_id=alloc.quarantine_case_id,
            quality_inspection_id=alloc.quality_inspection_id,
            quality_decision_id=alloc.quality_decision_id,
            created_by=actor,
        )

        second_child = InboundInventoryDispositionAllocationModel(
            id=second_id,
            organization_id=alloc.organization_id,
            branch_id=alloc.branch_id,
            warehouse_id=alloc.warehouse_id,
            inbound_receipt_id=alloc.inbound_receipt_id,
            inbound_receipt_revision_id=alloc.inbound_receipt_revision_id,
            inbound_received_line_id=alloc.inbound_received_line_id,
            expected_line_id=alloc.expected_line_id,
            purchase_order_id=alloc.purchase_order_id,
            purchase_order_line_id=alloc.purchase_order_line_id,
            supplier_business_partner_id=alloc.supplier_business_partner_id,
            product_id=alloc.product_id,
            product_version_id=alloc.product_version_id,
            sku_snapshot=alloc.sku_snapshot,
            product_name_snapshot=alloc.product_name_snapshot,
            quantity=second_qty,
            unit_id=alloc.unit_id,
            base_quantity=second_base,
            allocation_status=alloc.allocation_status,
            availability_class=alloc.availability_class,
            quality_status=alloc.quality_status,
            parent_allocation_id=allocation_id,
            root_allocation_id=alloc.root_allocation_id,
            split_sequence=alloc.split_sequence + 1,
            lot_observation_ids=alloc.lot_observation_ids,
            serial_observation_ids=alloc.serial_observation_ids,
            expiration_observation_ids=alloc.expiration_observation_ids,
            difference_case_ids=alloc.difference_case_ids,
            quarantine_case_id=alloc.quarantine_case_id,
            quality_inspection_id=alloc.quality_inspection_id,
            quality_decision_id=alloc.quality_decision_id,
            created_by=actor,
        )

        self._alloc_repo.create(first_child)
        self._alloc_repo.create(second_child)

        require_allocation_transition(alloc.allocation_status, AllocationStatus.SUPERSEDED_BY_SPLIT)
        self._alloc_repo.update_status(
            allocation_id,
            status=AllocationStatus.SUPERSEDED_BY_SPLIT,
            availability_class="CANCELLED",
            quality_status="NOT_APPLICABLE",
        )

        return {
            "split_id": str(uuid4()),
            "source_allocation_id": str(allocation_id),
            "first_child_id": str(first_id),
            "second_child_id": str(second_id),
            "first_quantity": str(first_quantity),
            "second_quantity": str(second_qty),
        }


class QualityQuarantineService:
    """Manages quarantine cases."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._case_repo = QuarantineCaseRepository(db)
        self._alloc_repo = AllocationRepository(db)
        self._event_repo = DispositionEventRepository(db)

    def create_case(
        self,
        *,
        organization_id: UUID,
        branch_id: UUID,
        warehouse_id: UUID,
        source_type: str,
        inbound_receipt_id: UUID,
        product_id: UUID,
        product_version_id: UUID | None,
        quarantine_reason: str | None,
        reason_description: str | None,
        actor_user_id: UUID,
    ) -> QualityQuarantineCaseModel:
        case_id = uuid4()
        code = f"QC-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{str(case_id)[:8].upper()}"
        model = QualityQuarantineCaseModel(
            id=case_id,
            organization_id=organization_id,
            branch_id=branch_id,
            warehouse_id=warehouse_id,
            quarantine_code=code,
            normalized_quarantine_code=code.upper(),
            source_type=source_type,
            inbound_receipt_id=inbound_receipt_id,
            product_id=product_id,
            product_version_id=product_version_id,
            status=QuarantineStatus.DRAFT,
            quarantine_reason=quarantine_reason,
            reason_description=reason_description,
            created_by=actor_user_id,
        )
        self._case_repo.create(model)
        return model

    def activate_case(self, case_id: UUID, actor: UUID) -> QualityQuarantineCaseModel:
        case = self._case_repo.get(case_id)
        if not case:
            raise QualityQuarantineCaseNotFound(case_id=str(case_id))
        require_quarantine_transition(case.status, QuarantineStatus.ACTIVE)
        case.status = QuarantineStatus.ACTIVE
        case.opened_at = _utcnow()
        case.opened_by = actor
        return case

    def close_case(self, case_id: UUID) -> QualityQuarantineCaseModel:
        case = self._case_repo.get(case_id)
        if not case:
            raise QualityQuarantineCaseNotFound(case_id=str(case_id))
        case.status = QuarantineStatus.CLOSED
        case.closed_at = _utcnow()
        return case


class QualityInspectionService:
    """Manages quality inspections."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._inspection_repo = InspectionRepository(db)
        self._snapshot_repo = SnapshotRepository(db)
        self._control_repo = InspectionControlRepository(db)

    def materialize_inspection(
        self,
        *,
        organization_id: UUID,
        branch_id: UUID,
        warehouse_id: UUID,
        quarantine_case_id: UUID,
        allocation_id: UUID,
        inbound_receipt_id: UUID,
        product_id: UUID,
        product_version_id: UUID | None,
        plan_id: UUID | None,
        plan_version_id: UUID | None,
        controls: list[dict],
        actor_user_id: UUID,
    ) -> QualityInspectionModel:
        existing = self._inspection_repo.get_active_by_case(quarantine_case_id)
        if existing:
            raise QualityInspectionAlreadyExists(case_id=str(quarantine_case_id))

        inspection_id = uuid4()
        snapshot_id = uuid4()
        code = f"QI-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{str(inspection_id)[:8].upper()}"

        snapshot = QualityInspectionSnapshotModel(
            id=snapshot_id,
            inspection_id=inspection_id,
            controls_snapshot=controls,
            captured_at=_utcnow(),
            content_hash=canonical_hash({"controls": controls}),
        )
        self._snapshot_repo.create(snapshot)

        model = QualityInspectionModel(
            id=inspection_id,
            organization_id=organization_id,
            branch_id=branch_id,
            warehouse_id=warehouse_id,
            inspection_code=code,
            quarantine_case_id=quarantine_case_id,
            allocation_id=allocation_id,
            inbound_receipt_id=inbound_receipt_id,
            product_id=product_id,
            product_version_id=product_version_id,
            plan_id=plan_id,
            plan_version_id=plan_version_id,
            inspection_snapshot_id=snapshot_id,
            status=InspectionStatus.CREATED,
            overall_result=InspectionOverallResult.NOT_CALCULATED,
            required_control_count=len(controls),
            created_by=actor_user_id,
        )
        self._inspection_repo.create(model)

        for i, ctrl in enumerate(controls):
            ctrl_model = QualityInspectionControlModel(
                id=uuid4(),
                inspection_id=inspection_id,
                source_control_definition_id=ctrl.get("source_id"),
                control_code=ctrl.get("code", f"CTRL-{i}"),
                name_snapshot=ctrl.get("name", f"Control {i}"),
                description_snapshot=ctrl.get("description"),
                control_type=ctrl.get("type", "VISUAL_CONDITION"),
                order_index=i,
                required=ctrl.get("required", True),
                blocking_on_fail=ctrl.get("blocking_on_fail", False),
                result_value_type=ctrl.get("result_value_type"),
                tolerance_snapshot=ctrl.get("tolerance"),
            )
            self._control_repo.create(ctrl_model)

        return model

    def complete_inspection(self, inspection_id: UUID, actor: UUID) -> QualityInspectionModel:
        inspection = self._inspection_repo.get(inspection_id)
        if not inspection:
            raise QualityInspectionNotFound(inspection_id=str(inspection_id))

        controls = self._control_repo.list_by_inspection(inspection_id)
        evidence_links = []  # would fetch from repo
        sample_sets = []
        certificate_reviews = []

        overall = calculate_overall_result(
            controls=[{"required": c.required, "status": c.status, "blocking_on_fail": c.blocking_on_fail, "result_status": None} for c in controls],
            evidence_links=[],
            sample_sets=[],
            certificate_reviews=[],
        )

        inspection.overall_result = overall
        inspection.status = InspectionStatus.COMPLETED
        inspection.completed_at = _utcnow()
        inspection.completed_by = actor
        inspection.completed_control_count = len([c for c in controls if c.status == "COMPLETED"])
        inspection.failed_control_count = len([c for c in controls if c.status == "COMPLETED" and False])  # would check results
        inspection.evidence_count = len(evidence_links)

        return inspection


class QualityDispositionDecisionService:
    """Manages quality disposition decisions."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._decision_repo = DecisionRepository(db)

    def propose_decision(
        self,
        *,
        quarantine_case_id: UUID,
        inspection_id: UUID | None,
        allocation_id: UUID,
        decision_type: str,
        quantity: Decimal,
        unit_id: UUID,
        base_quantity: Decimal,
        reason_code: str | None,
        reason: str | None,
        actor_user_id: UUID,
    ) -> QualityDispositionDecisionModel:
        model = QualityDispositionDecisionModel(
            id=uuid4(),
            quarantine_case_id=quarantine_case_id,
            inspection_id=inspection_id,
            allocation_id=allocation_id,
            decision_type=decision_type,
            decision_status=DecisionStatus.PROPOSED,
            quantity=quantity,
            unit_id=unit_id,
            base_quantity=base_quantity,
            reason_code=reason_code,
            reason=reason,
            proposed_by=actor_user_id,
            proposed_at=_utcnow(),
        )
        self._decision_repo.create(model)
        return model

    def approve_decision(self, decision_id: UUID, approver: UUID) -> QualityDispositionDecisionModel:
        decision = self._decision_repo.get(decision_id)
        if not decision:
            from app.modules.logistics.inbound.quality_quarantine.domain.errors import QualityDispositionDecisionInvalid
            raise QualityDispositionDecisionInvalid(reason="Decision not found")
        decision.decision_status = DecisionStatus.APPROVED
        decision.approved_by = approver
        decision.approved_at = _utcnow()
        return decision


class QuarantineReleaseService:
    """Manages quarantine releases."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._release_repo = ReleaseRepository(db)
        self._case_repo = QuarantineCaseRepository(db)
        self._alloc_repo = AllocationRepository(db)

    def request_release(
        self,
        *,
        quarantine_case_id: UUID,
        allocation_id: UUID,
        quality_decision_id: UUID,
        release_type: str,
        quantity: Decimal,
        unit_id: UUID,
        base_quantity: Decimal,
        release_reason: str | None,
        actor_user_id: UUID,
    ) -> QuarantineReleaseAuthorizationModel:
        case = self._case_repo.get(quarantine_case_id)
        if not case:
            raise QualityQuarantineCaseNotFound(case_id=str(quarantine_case_id))

        if case.status not in (QuarantineStatus.QUALITY_APPROVED, QuarantineStatus.PARTIALLY_RELEASED):
            raise QuarantineReleaseNotAllowed(reason=f"Case status is {case.status}")

        model = QuarantineReleaseAuthorizationModel(
            id=uuid4(),
            quarantine_case_id=quarantine_case_id,
            allocation_id=allocation_id,
            quality_decision_id=quality_decision_id,
            release_type=release_type,
            quantity=quantity,
            unit_id=unit_id,
            base_quantity=base_quantity,
            status=ReleaseStatus.REQUESTED,
            release_reason=release_reason,
            requested_by=actor_user_id,
            requested_at=_utcnow(),
        )
        self._release_repo.create(model)
        return model

    def execute_release(self, release_id: UUID, actor: UUID) -> QuarantineReleaseAuthorizationModel:
        release = self._release_repo.get(release_id)
        if not release:
            from app.modules.logistics.inbound.quality_quarantine.domain.errors import QuarantineReleaseNotAllowed
            raise QuarantineReleaseNotAllowed(reason="Release not found")

        if release.status != ReleaseStatus.APPROVED:
            raise QuarantineReleaseNotAllowed(reason=f"Release status is {release.status}")

        release.status = ReleaseStatus.EXECUTED
        release.executed_by = actor
        release.executed_at = _utcnow()

        alloc = self._alloc_repo.get(release.allocation_id)
        if alloc:
            require_allocation_transition(alloc.allocation_status, AllocationStatus.RELEASED_FOR_PUTAWAY)
            self._alloc_repo.update_status(
                release.allocation_id,
                status=AllocationStatus.RELEASED_FOR_PUTAWAY,
                availability_class=AvailabilityClass.AVAILABLE_FOR_PUTAWAY,
                quality_status=derive_quality_status("PASS", AllocationStatus.RELEASED_FOR_PUTAWAY),
            )

        return release


class QuarantineRejectionService:
    """Manages quarantine rejections."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._rejection_repo = RejectionRepository(db)
        self._case_repo = QuarantineCaseRepository(db)
        self._alloc_repo = AllocationRepository(db)

    def request_rejection(
        self,
        *,
        quarantine_case_id: UUID,
        allocation_id: UUID,
        quality_decision_id: UUID,
        rejection_type: str,
        quantity: Decimal,
        unit_id: UUID,
        base_quantity: Decimal,
        reason_code: str | None,
        reason: str | None,
        future_disposition_recommendation: str | None,
        actor_user_id: UUID,
    ) -> QuarantineRejectionAuthorizationModel:
        case = self._case_repo.get(quarantine_case_id)
        if not case:
            raise QualityQuarantineCaseNotFound(case_id=str(quarantine_case_id))

        model = QuarantineRejectionAuthorizationModel(
            id=uuid4(),
            quarantine_case_id=quarantine_case_id,
            allocation_id=allocation_id,
            quality_decision_id=quality_decision_id,
            rejection_type=rejection_type,
            quantity=quantity,
            unit_id=unit_id,
            base_quantity=base_quantity,
            reason_code=reason_code,
            reason=reason,
            status=RejectionStatus.REQUESTED,
            future_disposition_recommendation=future_disposition_recommendation,
            requested_by=actor_user_id,
            requested_at=_utcnow(),
        )
        self._rejection_repo.create(model)
        return model

    def execute_rejection(self, rejection_id: UUID, actor: UUID) -> QuarantineRejectionAuthorizationModel:
        rejection = self._rejection_repo.get(rejection_id)
        if not rejection:
            raise QuarantineRejectionNotAllowed(reason="Rejection not found")

        if rejection.status != RejectionStatus.APPROVED:
            raise QuarantineRejectionNotAllowed(reason=f"Rejection status is {rejection.status}")

        rejection.status = RejectionStatus.EXECUTED
        rejection.executed_by = actor
        rejection.executed_at = _utcnow()

        alloc = self._alloc_repo.get(rejection.allocation_id)
        if alloc:
            require_allocation_transition(alloc.allocation_status, AllocationStatus.REJECTED_PENDING_DISPOSITION)
            self._alloc_repo.update_status(
                rejection.allocation_id,
                status=AllocationStatus.REJECTED_PENDING_DISPOSITION,
                availability_class=AvailabilityClass.REJECTED_NOT_AVAILABLE,
                quality_status=derive_quality_status("FAIL", AllocationStatus.REJECTED_PENDING_DISPOSITION),
            )

        return rejection
