"""VehicleVerification Core Application Service (Phase 028)."""

from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import and_, select, update
from sqlalchemy.orm import Session

from app.database.base import utc_now
from app.modules.logistics.audit.service import AuditEventCommand, audit_service
from app.modules.logistics.vehicle_verifications.domain.errors.exceptions import (
    VehicleVerificationAlreadyCompleted,
    VehicleVerificationConflictDetected,
    VehicleVerificationDomainUnsupported,
    VehicleVerificationNotFound,
    VehicleVerificationSourceDisabled,
    VehicleVerificationSourceNotAuthorized,
)
from app.modules.logistics.vehicle_verifications.domain.providers.provider_interface import (
    FakeVehicleVerificationProvider,
    NoOpVehicleVerificationProvider,
    ProviderVerificationRequest,
    VehicleVerificationProvider,
)
from app.modules.logistics.vehicle_verifications.domain.services.services import (
    VehicleVerificationComplianceResolver,
    VehicleVerificationConflictDetector,
    VehicleVerificationNormalizer,
    VehicleVerificationStalenessPolicy,
)
from app.modules.logistics.vehicle_verifications.domain.value_objects.enums import (
    ConfidenceLevel,
    ConflictSeverity,
    ConflictStatus,
    ConflictType,
    SourceAuthorizationStatus,
    StalenessStatus,
    VerificationAutomationMode,
    VerificationComplianceStatus,
    VerificationDomain,
    VerificationMethod,
    VerificationResultStatus,
    VerificationStatus,
)
from app.modules.logistics.vehicle_verifications.infrastructure.persistence.models import (
    VehicleVerificationConflictModel,
    VehicleVerificationEvidenceModel,
    VehicleVerificationFieldProvenanceModel,
    VehicleVerificationModel,
    VehicleVerificationRequirementModel,
    VehicleVerificationResultModel,
    VehicleVerificationSourceModel,
)
from app.modules.logistics.vehicles.infrastructure.persistence.models import (
    VehicleModel,
    VehiclePlateAssignmentModel,
)


class VehicleVerificationService:
    def __init__(self, db: Session):
        self.db = db

    def request_verification(
        self,
        organization_id: UUID,
        vehicle_id: UUID,
        domain: str,
        source_code: str,
        actor_id: UUID,
        purpose: str = "LOGISTICS_COMPLIANCE",
        file_reference_id: Optional[str] = None,
    ) -> VehicleVerificationModel:
        # Validate Vehicle
        vehicle = self.db.scalars(
            select(VehicleModel).where(
                and_(VehicleModel.id == vehicle_id, VehicleModel.organization_id == organization_id)
            )
        ).first()

        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehículo no encontrado.")

        # Get Current Plate Assignment
        plate_ass = self.db.scalars(
            select(VehiclePlateAssignmentModel).where(
                and_(
                    VehiclePlateAssignmentModel.vehicle_id == vehicle.id,
                    VehiclePlateAssignmentModel.status == "CURRENT",
                )
            )
        ).first()

        # Validate Source
        source = self.db.scalars(
            select(VehicleVerificationSourceModel).where(VehicleVerificationSourceModel.code == source_code)
        ).first()

        if not source:
            raise HTTPException(status_code=404, detail=f"Fuente de verificación '{source_code}' no encontrada.")

        if not source.enabled or source.status != "ACTIVE":
            raise VehicleVerificationSourceDisabled(source_code)

        if domain not in source.verification_domains:
            raise VehicleVerificationDomainUnsupported(domain, source_code)

        method = VerificationMethod.AUTHORIZED_API.value if source.automation_mode == VerificationAutomationMode.API.value else VerificationMethod.MANUAL_ASSISTED.value

        verif = VehicleVerificationModel(
            id=uuid4(),
            organization_id=organization_id,
            vehicle_id=vehicle.id,
            vehicle_version_id=vehicle.active_version_id,
            plate_assignment_id=plate_ass.id if plate_ass else None,
            normalized_plate=vehicle.normalized_plate,
            verification_domain=domain,
            verification_method=method,
            source_id=source.id,
            provider_code=source.provider_code,
            status=VerificationStatus.REQUESTED.value,
            result_status=VerificationResultStatus.UNKNOWN.value,
            confidence_level=ConfidenceLevel.NOT_EVALUATED.value,
            requested_at=utc_now(),
            verified_by_user_id=actor_id,
            evidence_status="HAS_EVIDENCE" if file_reference_id else "NO_EVIDENCE",
        )
        self.db.add(verif)
        self.db.commit()

        if file_reference_id:
            ev = VehicleVerificationEvidenceModel(
                id=uuid4(),
                verification_id=verif.id,
                evidence_type="DOCUMENT_REFERENCE",
                file_reference_id=file_reference_id,
                captured_at=utc_now(),
                captured_by=actor_id,
                status="ACTIVE",
            )
            self.db.add(ev)
            self.db.commit()

        audit_service.write_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.vehicle_verification.requested",
                severity="medium",
                actor_user_id=actor_id,
                organization_id=organization_id,
                resource_type="vehicle_verification",
                resource_id=str(verif.id),
                resource_code=vehicle.display_plate,
                new_data={"domain": domain, "source": source_code},
            ),
        )

        # Auto-execute if provider available
        if source.automation_mode == VerificationAutomationMode.API.value and source.authorization_status == SourceAuthorizationStatus.AUTHORIZED.value:
            self.execute_provider_verification(verif.id, organization_id, actor_id)

        return verif

    def execute_provider_verification(
        self, verification_id: UUID, organization_id: UUID, actor_id: UUID
    ) -> VehicleVerificationModel:
        verif = self.db.scalars(
            select(VehicleVerificationModel).where(
                and_(VehicleVerificationModel.id == verification_id, VehicleVerificationModel.organization_id == organization_id)
            )
        ).first()

        if not verif:
            raise VehicleVerificationNotFound(str(verification_id))

        if verif.status == VerificationStatus.COMPLETED.value:
            raise VehicleVerificationAlreadyCompleted(str(verification_id))

        source = verif.source

        if source.authorization_status != SourceAuthorizationStatus.AUTHORIZED.value:
            verif.status = VerificationStatus.FAILED.value
            verif.failure_code = "SOURCE_NOT_AUTHORIZED"
            verif.failure_summary = f"La fuente '{source.code}' no cuenta con contrato/autorización activa."
            self.db.commit()
            raise VehicleVerificationSourceNotAuthorized(source.code)

        # Instantiate Provider Adapter (using Fake for testing if provider_code is FAKE_AUTH_PROVIDER)
        if source.provider_code == "FAKE_AUTH_PROVIDER":
            provider = FakeVehicleVerificationProvider(code="FAKE_AUTH_PROVIDER")
        else:
            provider = NoOpVehicleVerificationProvider()

        verif.status = VerificationStatus.RUNNING.value
        verif.started_at = utc_now()
        self.db.commit()

        try:
            req = ProviderVerificationRequest(
                plate=verif.normalized_plate,
                domain=verif.verification_domain,
                organization_id=organization_id,
                correlation_id=str(verif.id),
            )
            resp = provider.verify_plate(req)

            # Record Verification Result
            res = VehicleVerificationResultModel(
                id=uuid4(),
                verification_id=verif.id,
                queried_plate=resp.queried_plate,
                registered_owner_name=resp.registered_owner_name,
                registered_owner_identifier_masked=resp.registered_owner_identifier_masked,
                make=resp.make,
                model=resp.model,
                manufacturing_year=resp.manufacturing_year,
                vin_masked=resp.vin_masked,
                registration_status=resp.registration_status,
                technical_inspection_status=resp.technical_inspection_status,
                technical_inspection_expires_at=resp.technical_inspection_expires_at,
                insurance_type=resp.insurance_type,
                insurance_status=resp.insurance_status,
                insurance_provider=resp.insurance_provider,
                insurance_policy_masked=resp.insurance_policy_masked,
                insurance_expires_at=resp.insurance_expires_at,
                normalized_payload=resp.normalized_payload,
            )
            self.db.add(res)

            verif.status = VerificationStatus.COMPLETED.value
            verif.result_status = resp.result_status.value
            verif.confidence_level = resp.confidence_level.value
            verif.source_data_at = resp.source_data_at
            verif.completed_at = utc_now()
            verif.valid_from = resp.valid_from
            verif.expires_at = resp.expires_at
            verif.original_response_hash = resp.raw_response_hash
            verif.external_reference = resp.external_reference
            self.db.commit()

            # Record Field Provenance
            provenance_fields = [
                ("plate", resp.queried_plate),
                ("owner", resp.registered_owner_name),
                ("make", resp.make),
                ("model", resp.model),
                ("year", str(resp.manufacturing_year) if resp.manufacturing_year else None),
                ("vin", resp.vin_masked),
            ]
            for fname, fval in provenance_fields:
                if fval:
                    fp = VehicleVerificationFieldProvenanceModel(
                        id=uuid4(),
                        verification_id=verif.id,
                        field_name=fname,
                        normalized_value=fval,
                        source_id=source.id,
                        source_reference=resp.external_reference,
                        source_data_at=resp.source_data_at,
                        confidence_level=resp.confidence_level.value,
                        selected=True,
                    )
                    self.db.add(fp)
            self.db.commit()

            # Detect Conflicts with Master Vehicle
            vehicle = self.db.get(VehicleModel, verif.vehicle_id)
            conflicts = VehicleVerificationConflictDetector.detect_conflicts(
                master_plate=vehicle.display_plate,
                master_vin=vehicle.vin,
                master_make=None,  # compared by ID in master, name in verif
                master_model=None,
                master_year=vehicle.manufacturing_year,
                verified_plate=resp.queried_plate,
                verified_vin=resp.vin_masked,
                verified_make=resp.make,
                verified_model=resp.model,
                verified_year=resp.manufacturing_year,
                verified_status=resp.registration_status,
            )

            if conflicts:
                verif.conflict_status = "HAS_CONFLICTS"
                for c in conflicts:
                    conf = VehicleVerificationConflictModel(
                        id=uuid4(),
                        organization_id=organization_id,
                        vehicle_id=vehicle.id,
                        verification_id=verif.id,
                        conflict_type=c.conflict_type.value,
                        master_display_value=c.master_display,
                        verified_display_value=c.verified_display,
                        severity=c.severity,
                        status=ConflictStatus.OPEN.value,
                        detected_at=utc_now(),
                    )
                    self.db.add(conf)
                self.db.commit()

            audit_service.write_event(
                self.db,
                AuditEventCommand(
                    event_code="logistics.vehicle_verification.completed",
                    severity="high",
                    actor_user_id=actor_id,
                    organization_id=organization_id,
                    resource_type="vehicle_verification",
                    resource_id=str(verif.id),
                    resource_code=vehicle.display_plate,
                    new_data={"result_status": verif.result_status, "conflicts_count": len(conflicts)},
                ),
            )

        except Exception as ex:
            verif.status = VerificationStatus.FAILED.value
            verif.failure_code = "PROVIDER_ERROR"
            verif.failure_summary = str(ex)
            self.db.commit()

            audit_service.write_event(
                self.db,
                AuditEventCommand(
                    event_code="logistics.vehicle_verification.failed",
                    severity="medium",
                    actor_user_id=actor_id,
                    organization_id=organization_id,
                    resource_type="vehicle_verification",
                    resource_id=str(verif.id),
                    reason_text=str(ex),
                ),
            )
            raise ex

        return verif

    def list_verifications(self, vehicle_id: UUID, organization_id: UUID) -> List[VehicleVerificationModel]:
        return list(
            self.db.scalars(
                select(VehicleVerificationModel)
                .where(and_(VehicleVerificationModel.vehicle_id == vehicle_id, VehicleVerificationModel.organization_id == organization_id))
                .order_by(VehicleVerificationModel.requested_at.desc())
            ).all()
        )

    def get_verification_compliance(self, vehicle_id: UUID, organization_id: UUID) -> dict:
        vehicle = self.db.scalars(
            select(VehicleModel).where(
                and_(VehicleModel.id == vehicle_id, VehicleModel.organization_id == organization_id)
            )
        ).first()

        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehículo no encontrado.")

        # Get active requirements
        reqs = self.db.scalars(
            select(VehicleVerificationRequirementModel).where(
                and_(
                    VehicleVerificationRequirementModel.organization_id == organization_id,
                    VehicleVerificationRequirementModel.status == "ACTIVE",
                )
            )
        ).all()

        req_tuples = [(r.verification_domain, r.blocking, r.maximum_age_days) for r in reqs]

        # Get completed verifications
        verifs = self.db.scalars(
            select(VehicleVerificationModel).where(
                and_(
                    VehicleVerificationModel.vehicle_id == vehicle_id,
                    VehicleVerificationModel.organization_id == organization_id,
                )
            )
        ).all()

        verif_tuples = [
            (v.verification_domain, v.status, v.source_data_at or v.completed_at or v.requested_at, v.expires_at, v.result_status)
            for v in verifs
        ]

        # Check open conflicts
        open_conflicts = self.db.scalar(
            select(VehicleVerificationConflictModel).where(
                and_(
                    VehicleVerificationConflictModel.vehicle_id == vehicle_id,
                    VehicleVerificationConflictModel.status.in_([ConflictStatus.OPEN.value, ConflictStatus.UNDER_REVIEW.value]),
                )
            )
        ) is not None

        result = VehicleVerificationComplianceResolver.resolve_compliance(
            required_requirements=req_tuples,
            verifications_summary=verif_tuples,
            has_open_conflicts=open_conflicts,
        )

        return {
            "vehicle_id": str(vehicle.id),
            "vehicle_code": vehicle.vehicle_code,
            "display_plate": vehicle.display_plate,
            "compliance_status": result.compliance_status.value,
            "required_domains": result.required_domains,
            "completed_domains": result.completed_domains,
            "missing_domains": result.missing_domains,
            "expired_domains": result.expired_domains,
            "stale_domains": result.stale_domains,
            "has_open_conflicts": result.has_open_conflicts,
            "blocking_reasons": result.blocking_reasons,
            "warnings": result.warnings,
            "evaluated_at": utc_now().isoformat(),
        }
