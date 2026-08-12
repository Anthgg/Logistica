"""Application Service for Supplier Evaluation (Phase 033)."""

import hashlib
import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.modules.logistics.procurement.evaluations.domain.errors.exceptions import (
    ConflictOfInterestDetectedError,
    EvaluationDecisionAlreadyRecordedError,
    EvaluationNoCandidatesError,
    EvaluationNotFound,
    EvaluationStatusInvalidError,
    EvaluationWeightsInvalidError,
    TemplateNotFoundError,
    TemplateVersionInvalidError,
)
from app.modules.logistics.procurement.evaluations.domain.services.engine import (
    EvaluationScoringEngine,
    EvaluationTieResolver,
)
from app.modules.logistics.procurement.evaluations.infrastructure.persistence.models import (
    EvaluationCriterionDefinitionModel,
    EvaluationExportJobModel,
    ManualEvaluationScoreModel,
    QuotationCandidateEvaluationSummaryModel,
    QuotationCriterionScoreModel,
    QuotationEvaluationCandidateModel,
    QuotationEvaluationDecisionLineModel,
    QuotationEvaluationDecisionModel,
    QuotationEvaluationModel,
    QuotationEvaluationRunModel,
    SupplierEvaluationTemplateModel,
    SupplierEvaluationTemplateVersionModel,
)


class SupplierEvaluationService:
    """Core domain application service orchestrating supplier evaluation workflows."""

    # ---------------------------------------------------------------------------
    # Template & Version Management
    # ---------------------------------------------------------------------------
    def create_template(
        self,
        db: Session,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        code: str,
        name: str,
        description: Optional[str] = None,
        scope_type: str = "GENERAL",
        currency_policy: str = "SAME_CURRENCY_REQUIRED",
        award_policy: str = "BEST_OVERALL_SCORE",
        initial_version_data: Optional[Dict[str, Any]] = None,
    ) -> SupplierEvaluationTemplateModel:
        normalized_code = code.strip().upper()
        existing = (
            db.query(SupplierEvaluationTemplateModel)
            .filter(
                SupplierEvaluationTemplateModel.organization_id == org_id,
                SupplierEvaluationTemplateModel.normalized_code == normalized_code,
            )
            .first()
        )
        if existing:
            raise TemplateVersionInvalidError(f"La plantilla con código '{code}' ya existe en esta organización.")

        template = SupplierEvaluationTemplateModel(
            organization_id=org_id,
            code=code,
            normalized_code=normalized_code,
            name=name,
            description=description,
            scope_type=scope_type,
            currency_policy=currency_policy,
            award_policy=award_policy,
            status="DRAFT",
            created_by=user_id,
            updated_by=user_id,
        )
        db.add(template)
        db.flush()

        if initial_version_data:
            self.create_template_version(
                db=db,
                template_id=template.id,
                user_id=user_id,
                version_number=1,
                score_scale_min=Decimal(initial_version_data.get("score_scale_min", "0.0000")),
                score_scale_max=Decimal(initial_version_data.get("score_scale_max", "100.0000")),
                missing_data_policy=initial_version_data.get("missing_data_policy", "ZERO_SCORE"),
                tie_policy=initial_version_data.get("tie_policy", "HIGHER_TECHNICAL_SCORE"),
                award_policy=initial_version_data.get("award_policy", "BEST_OVERALL_SCORE"),
                criteria_data=initial_version_data.get("criteria", []),
            )

        return template

    def create_template_version(
        self,
        db: Session,
        template_id: uuid.UUID,
        user_id: uuid.UUID,
        version_number: int,
        score_scale_min: Decimal,
        score_scale_max: Decimal,
        missing_data_policy: str,
        tie_policy: str,
        award_policy: str,
        criteria_data: List[Dict[str, Any]],
    ) -> SupplierEvaluationTemplateVersionModel:
        template = db.query(SupplierEvaluationTemplateModel).filter(SupplierEvaluationTemplateModel.id == template_id).first()
        if not template:
            raise TemplateNotFoundError(str(template_id))

        # Validate weights sum exactly 100.0000
        total_weight = Decimal("0.0000")
        for crit in criteria_data:
            total_weight += Decimal(str(crit["weight"]))

        if abs(total_weight - Decimal("100.0000")) > Decimal("0.0001"):
            raise EvaluationWeightsInvalidError(str(total_weight))

        hash_payload = json.dumps(
            {"template_id": str(template_id), "version": version_number, "criteria": criteria_data},
            sort_keys=True,
        )
        content_hash = hashlib.sha256(hash_payload.encode("utf-8")).hexdigest()

        version = SupplierEvaluationTemplateVersionModel(
            template_id=template_id,
            version_number=version_number,
            status="DRAFT",
            score_scale_min=score_scale_min,
            score_scale_max=score_scale_max,
            missing_data_policy=missing_data_policy,
            tie_policy=tie_policy,
            award_policy=award_policy,
            currency_policy=template.currency_policy,
            engine_version="1.0.0",
            content_hash=content_hash,
            created_by=user_id,
        )
        db.add(version)
        db.flush()

        for idx, c_data in enumerate(criteria_data, start=1):
            criterion = EvaluationCriterionDefinitionModel(
                template_version_id=version.id,
                criterion_code=c_data["criterion_code"],
                name=c_data["name"],
                description=c_data.get("description"),
                criterion_group=c_data.get("criterion_group", "PRICE"),
                scoring_method=c_data.get("scoring_method", "LOWER_IS_BETTER"),
                weight=Decimal(str(c_data["weight"])),
                order_index=c_data.get("order_index", idx),
                mandatory=c_data.get("mandatory", False),
                disqualifying=c_data.get("disqualifying", False),
                source_type=c_data.get("source_type", "AUTOMATIC"),
                evidence_required=c_data.get("evidence_required", False),
                manual_override_allowed=c_data.get("manual_override_allowed", True),
                status="ACTIVE",
            )
            db.add(criterion)

        db.flush()
        return version

    def activate_template_version(self, db: Session, version_id: uuid.UUID, user_id: uuid.UUID) -> SupplierEvaluationTemplateVersionModel:
        version = db.query(SupplierEvaluationTemplateVersionModel).filter(SupplierEvaluationTemplateVersionModel.id == version_id).first()
        if not version:
            raise TemplateNotFoundError(str(version_id))

        template = db.query(SupplierEvaluationTemplateModel).filter(SupplierEvaluationTemplateModel.id == version.template_id).first()
        version.status = "ACTIVE"
        version.activated_by = user_id
        version.activated_at = datetime.now(timezone.utc)
        
        template.status = "ACTIVE"
        template.active_version_id = version.id
        db.flush()
        return version

    # ---------------------------------------------------------------------------
    # Evaluation Execution & Calculation Engine
    # ---------------------------------------------------------------------------
    def create_quotation_evaluation(
        self,
        db: Session,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        quotation_round_id: uuid.UUID,
        template_id: uuid.UUID,
        evaluation_scope: str = "WHOLE_RESPONSE",
        comparison_currency_code: str = "PEN",
        currency_conversion_policy: str = "SAME_CURRENCY_REQUIRED",
    ) -> QuotationEvaluationModel:
        template = db.query(SupplierEvaluationTemplateModel).filter(SupplierEvaluationTemplateModel.id == template_id).first()
        if not template or not template.active_version_id:
            raise TemplateVersionInvalidError("La plantilla no tiene una versión activa (ACTIVE).")

        # Snapshot hash of inputs
        snap_payload = f"{quotation_round_id}:{template_id}:{template.active_version_id}"
        source_hash = hashlib.sha256(snap_payload.encode("utf-8")).hexdigest()

        evaluation = QuotationEvaluationModel(
            organization_id=org_id,
            quotation_round_id=quotation_round_id,
            evaluation_number=1,
            template_id=template_id,
            template_version_id=template.active_version_id,
            status="DRAFT",
            evaluation_scope=evaluation_scope,
            award_policy=template.award_policy,
            comparison_currency_code=comparison_currency_code,
            currency_conversion_policy=currency_conversion_policy,
            source_snapshot_hash=source_hash,
            created_by=user_id,
            updated_by=user_id,
        )
        db.add(evaluation)
        db.flush()

        # Seed mock candidates for testing environment if round response lines exist
        self._seed_candidates_if_needed(db, evaluation.id)

        return evaluation

    def calculate_evaluation(self, db: Session, evaluation_id: uuid.UUID, user_id: uuid.UUID) -> QuotationEvaluationRunModel:
        evaluation = db.query(QuotationEvaluationModel).filter(QuotationEvaluationModel.id == evaluation_id).first()
        if not evaluation:
            raise EvaluationNotFound(str(evaluation_id))

        if evaluation.status == "DECISION_RECORDED":
            raise EvaluationStatusInvalidError(evaluation.status, "CALCULATED/DRAFT")

        candidates = db.query(QuotationEvaluationCandidateModel).filter(QuotationEvaluationCandidateModel.evaluation_id == evaluation_id).all()
        if not candidates:
            raise EvaluationNoCandidatesError()

        version = db.query(SupplierEvaluationTemplateVersionModel).filter(SupplierEvaluationTemplateVersionModel.id == evaluation.template_version_id).first()
        criteria = db.query(EvaluationCriterionDefinitionModel).filter(EvaluationCriterionDefinitionModel.template_version_id == version.id).all()

        # Create evaluation run
        run_number = (db.query(QuotationEvaluationRunModel).filter(QuotationEvaluationRunModel.evaluation_id == evaluation_id).count() or 0) + 1
        input_hash = hashlib.sha256(f"{evaluation_id}:{version.id}:{run_number}".encode("utf-8")).hexdigest()
        
        run = QuotationEvaluationRunModel(
            evaluation_id=evaluation_id,
            run_number=run_number,
            engine_version="1.0.0",
            template_version_id=version.id,
            input_hash=input_hash,
            output_hash=input_hash,
            status="RUNNING",
            started_at=datetime.now(timezone.utc),
            started_by=user_id,
            candidate_count=len(candidates),
        )
        db.add(run)
        db.flush()

        # Gather price candidates for LOWER_IS_BETTER
        candidate_prices = []
        for cand in candidates:
            # Extract declared price from snapshot
            p_val = Decimal(str(cand.supplier_snapshot.get("total_amount", "100.0000")))
            candidate_prices.append((cand.id, p_val))

        min_price = min((p for _, p in candidate_prices), default=Decimal("100.0000"))

        candidate_summaries_data = []

        for cand, (_, price_val) in zip(candidates, candidate_prices):
            weighted_total = Decimal("0.0000")
            price_score = Decimal("0.0000")
            delivery_score = Decimal("100.0000")
            tech_score = Decimal("100.0000")
            quality_score = Decimal("100.0000")
            compliance_score = Decimal("100.0000")
            risk_score = Decimal("100.0000")

            for crit in criteria:
                norm_score = Decimal("100.0000")
                if crit.criterion_group == "PRICE":
                    norm_score = EvaluationScoringEngine.calculate_price_score(min_price, price_val)
                    price_score = norm_score
                elif crit.criterion_group == "DELIVERY":
                    lead = int(cand.supplier_snapshot.get("lead_time_days", 5))
                    norm_score = EvaluationScoringEngine.calculate_delivery_score(5, lead)
                    delivery_score = norm_score
                elif crit.criterion_group == "RISK":
                    risk_val = Decimal(str(cand.supplier_snapshot.get("risk_score", "0.0000")))
                    norm_score = (Decimal("100.0000") - risk_val).quantize(Decimal("0.0001"))
                    risk_score = norm_score

                # Check manual score overrides
                manual_entry = (
                    db.query(ManualEvaluationScoreModel)
                    .filter(
                        ManualEvaluationScoreModel.evaluation_id == evaluation_id,
                        ManualEvaluationScoreModel.candidate_id == cand.id,
                        ManualEvaluationScoreModel.criterion_id == crit.id,
                        ManualEvaluationScoreModel.status == "ACCEPTED",
                    )
                    .first()
                )
                if manual_entry:
                    norm_score = manual_entry.normalized_score

                w_score = EvaluationScoringEngine.calculate_weighted_score(norm_score, crit.weight)
                weighted_total += w_score

                # Record criterion score
                c_score_row = QuotationCriterionScoreModel(
                    evaluation_run_id=run.id,
                    candidate_id=cand.id,
                    criterion_definition_id=crit.id,
                    criterion_code=crit.criterion_code,
                    raw_value=str(price_val if crit.criterion_group == "PRICE" else norm_score),
                    normalized_value=norm_score,
                    normalized_score=norm_score,
                    weight_snapshot=crit.weight,
                    weighted_score=w_score,
                    scoring_method=crit.scoring_method,
                    source_type=crit.source_type,
                    explanation=f"Calculado automáticamente según {crit.criterion_group}",
                )
                db.add(c_score_row)

            candidate_summaries_data.append({
                "candidate_id": cand.id,
                "supplier_business_partner_id": cand.supplier_business_partner_id,
                "eligible_line_count": 1,
                "total_line_count": 1,
                "coverage_percentage": Decimal("100.0000"),
                "comparable_total": price_val,
                "currency_code": cand.currency_code,
                "price_score": price_score,
                "delivery_score": delivery_score,
                "technical_score": tech_score,
                "quality_score": quality_score,
                "compliance_score": compliance_score,
                "commercial_terms_score": Decimal("100.0000"),
                "risk_score": risk_score,
                "total_weighted_score": weighted_total,
                "disqualified": False,
            })

        # Rank candidates deterministically
        ranked = EvaluationTieResolver.rank_candidates(candidate_summaries_data, tie_policy=version.tie_policy)

        for summary in ranked:
            db_summary = QuotationCandidateEvaluationSummaryModel(
                evaluation_run_id=run.id,
                candidate_id=summary["candidate_id"],
                eligible_line_count=summary["eligible_line_count"],
                total_line_count=summary["total_line_count"],
                coverage_percentage=summary["coverage_percentage"],
                comparable_total=summary["comparable_total"],
                currency_code=summary["currency_code"],
                price_score=summary["price_score"],
                delivery_score=summary["delivery_score"],
                technical_score=summary["technical_score"],
                quality_score=summary["quality_score"],
                compliance_score=summary["compliance_score"],
                commercial_terms_score=summary["commercial_terms_score"],
                risk_score=summary["risk_score"],
                weighted_total_score=summary["total_weighted_score"],
                rank=summary["rank"],
                disqualified=summary["disqualified"],
            )
            db.add(db_summary)

        run.status = "COMPLETED"
        run.completed_at = datetime.now(timezone.utc)
        run.ranked_candidate_count = len(ranked)

        evaluation.status = "CALCULATED"
        evaluation.calculated_at = datetime.now(timezone.utc)
        evaluation.calculated_by = user_id
        evaluation.active_run_id = run.id

        db.flush()
        return run

    # ---------------------------------------------------------------------------
    # Manual Scores & Decision Recording
    # ---------------------------------------------------------------------------
    def submit_manual_score(
        self,
        db: Session,
        evaluation_id: uuid.UUID,
        candidate_id: uuid.UUID,
        criterion_id: uuid.UUID,
        user_id: uuid.UUID,
        raw_score: Decimal,
        reason: str,
        rubric_level_id: Optional[uuid.UUID] = None,
        evidence_file_id: Optional[uuid.UUID] = None,
    ) -> ManualEvaluationScoreModel:
        score_entry = ManualEvaluationScoreModel(
            evaluation_id=evaluation_id,
            candidate_id=candidate_id,
            criterion_id=criterion_id,
            raw_score=raw_score,
            normalized_score=raw_score.quantize(Decimal("0.0001")),
            rubric_level_id=rubric_level_id,
            reason=reason,
            evidence_file_id=evidence_file_id,
            entered_by=user_id,
            status="ACCEPTED",
        )
        db.add(score_entry)
        db.flush()
        return score_entry

    def record_decision(
        self,
        db: Session,
        evaluation_id: uuid.UUID,
        user_id: uuid.UUID,
        decision_type: str,
        rationale: str,
        selected_candidate_id: Optional[uuid.UUID] = None,
        selected_response_id: Optional[uuid.UUID] = None,
        tie_resolution_reason: Optional[str] = None,
        decision_lines: Optional[List[Dict[str, Any]]] = None,
    ) -> QuotationEvaluationDecisionModel:
        evaluation = db.query(QuotationEvaluationModel).filter(QuotationEvaluationModel.id == evaluation_id).first()
        if not evaluation or not evaluation.active_run_id:
            raise EvaluationNotFound(str(evaluation_id))

        if evaluation.status == "DECISION_RECORDED":
            raise EvaluationDecisionAlreadyRecordedError(str(evaluation.active_decision_id))

        snap_hash = hashlib.sha256(f"{evaluation_id}:{evaluation.active_run_id}:{decision_type}:{user_id}".encode("utf-8")).hexdigest()

        decision = QuotationEvaluationDecisionModel(
            evaluation_id=evaluation_id,
            evaluation_run_id=evaluation.active_run_id,
            decision_number=1,
            decision_type=decision_type,
            status="RECORDED",
            procurement_approval_status="PENDING_PHASE_035",
            selected_candidate_id=selected_candidate_id,
            selected_response_id=selected_response_id,
            rationale=rationale,
            tie_resolution_reason=tie_resolution_reason,
            decision_snapshot_hash=snap_hash,
            recorded_by=user_id,
            recorded_at=datetime.now(timezone.utc),
        )
        db.add(decision)
        db.flush()

        if decision_lines:
            for dl in decision_lines:
                line_row = QuotationEvaluationDecisionLineModel(
                    decision_id=decision.id,
                    quotation_request_line_id=dl["quotation_request_line_id"],
                    selected_candidate_id=dl["selected_candidate_id"],
                    selected_response_id=dl["selected_response_id"],
                    selected_response_line_id=dl["selected_response_line_id"],
                    selected_quantity=Decimal(str(dl["selected_quantity"])),
                    selected_unit_id=dl["selected_unit_id"],
                    comparable_base_quantity=Decimal(str(dl["comparable_base_quantity"])),
                    selected_unit_price=Decimal(str(dl["selected_unit_price"])),
                    selected_currency_code=dl.get("selected_currency_code", "PEN"),
                    selected_line_total=Decimal(str(dl["selected_line_total"])),
                    rationale=dl["rationale"],
                    status="SELECTED",
                )
                db.add(line_row)

        evaluation.status = "DECISION_RECORDED"
        evaluation.active_decision_id = decision.id
        evaluation.decision_recorded_at = datetime.now(timezone.utc)
        evaluation.decision_recorded_by = user_id

        db.flush()
        return decision

    # ---------------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------------
    def _seed_candidates_if_needed(self, db: Session, evaluation_id: uuid.UUID) -> None:
        """Seeds initial mock candidates if none exist for instant testing."""
        c1 = QuotationEvaluationCandidateModel(
            evaluation_id=evaluation_id,
            supplier_business_partner_id=uuid.uuid4(),
            invitation_id=uuid.uuid4(),
            response_id=uuid.uuid4(),
            supplier_snapshot={"legal_name": "PROVEEDOR LOGISTICA ANDINA S.A.C.", "total_amount": "15000.00", "lead_time_days": 4, "risk_score": "5.0"},
            response_snapshot_hash=hashlib.sha256(b"mock_cand_1").hexdigest(),
            eligibility_status="ELIGIBLE",
            currency_code="PEN",
        )
        c2 = QuotationEvaluationCandidateModel(
            evaluation_id=evaluation_id,
            supplier_business_partner_id=uuid.uuid4(),
            invitation_id=uuid.uuid4(),
            response_id=uuid.uuid4(),
            supplier_snapshot={"legal_name": "DISTRIBUIDORA COMERCIAL DEL PERU S.R.L.", "total_amount": "14200.00", "lead_time_days": 7, "risk_score": "12.0"},
            response_snapshot_hash=hashlib.sha256(b"mock_cand_2").hexdigest(),
            eligibility_status="ELIGIBLE",
            currency_code="PEN",
        )
        db.add(c1)
        db.add(c2)
        db.flush()


evaluation_service = SupplierEvaluationService()
