"""Domain services for Phase 029 — Driver Master Data."""

import hashlib
import json
import re
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.base import utc_now
from app.modules.logistics.drivers.domain.value_objects.enums import (
    DriverComplianceStatus,
    DriverEligibilityStatus,
    DriverLifecycleStatus,
    DriverVehicleCompatibilityStatus,
    DuplicateMatchLevel,
)
from app.modules.logistics.drivers.infrastructure.persistence.models import (
    DriverCarrierAssignmentModel,
    DriverContactModel,
    DriverDocumentModel,
    DriverIdentityDocumentModel,
    DriverLicenseCategoryAssignmentModel,
    DriverLicenseModel,
    DriverLicenseVehicleTypeRuleModel,
    DriverModel,
    DriverOperationalRestrictionModel,
)


class DriverCodeService:
    """Service for generating and validating internal driver codes."""

    PREFIX = "DRV-"
    PADDING = 6

    @classmethod
    def generate_code(cls, db: Session, organization_id: UUID) -> str:
        stmt = (
            select(func.count(DriverModel.id))
            .where(DriverModel.organization_id == organization_id)
        )
        count = db.scalar(stmt) or 0
        seq = count + 1

        while True:
            candidate = f"{cls.PREFIX}{seq:0{cls.PADDING}d}"
            norm_candidate = candidate.upper().strip()
            existing = db.scalar(
                select(DriverModel.id).where(
                    DriverModel.organization_id == organization_id,
                    DriverModel.normalized_driver_code == norm_candidate,
                )
            )
            if not existing:
                return candidate
            seq += 1

    @classmethod
    def normalize_code(cls, code: str) -> str:
        if not code:
            raise ValueError("El código de conductor no puede estar vacío.")
        cleaned = code.strip().upper()
        if not re.match(r"^[A-Z0-9\-_]{3,30}$", cleaned):
            raise ValueError(f"El código de conductor '{code}' contiene caracteres no permitidos.")
        return cleaned


class DriverIdentityDocumentNormalizer:
    """Normalizes and masks driver identity documents (DNI, CE, Passport)."""

    @classmethod
    def normalize(cls, doc_type: str, value: str) -> str:
        if not value:
            raise ValueError("El valor del documento de identidad no puede estar vacío.")
        cleaned = value.strip().upper()
        # Remove internal spaces or non-alphanumeric chars except hyphen/slash for foreign docs
        cleaned = re.sub(r"[\s]", "", cleaned)
        if doc_type == "DNI":
            cleaned = re.sub(r"\D", "", cleaned)
            if len(cleaned) != 8:
                raise ValueError("El DNI peruano debe contener exactamente 8 dígitos.")
        elif doc_type == "CE":
            if not (6 <= len(cleaned) <= 12):
                raise ValueError("El Carnet de Extranjería (CE) debe tener entre 6 y 12 caracteres.")
        elif doc_type == "PASSPORT":
            if not (6 <= len(cleaned) <= 15):
                raise ValueError("El Pasaporte debe tener entre 6 y 15 caracteres.")
        return cleaned

    @classmethod
    def mask(cls, value: str, visible_suffix_len: int = 3) -> str:
        if not value or len(value) <= visible_suffix_len:
            return "*****"
        masked_len = len(value) - visible_suffix_len
        return ("*" * masked_len) + value[-visible_suffix_len:]


class DriverLicenseNormalizer:
    """Normalizes and masks driver license numbers."""

    @classmethod
    def normalize(cls, license_number: str) -> str:
        if not license_number:
            raise ValueError("El número de licencia de conducir no puede estar vacío.")
        cleaned = re.sub(r"[\s\-_]", "", license_number.strip().upper())
        if not (5 <= len(cleaned) <= 30):
            raise ValueError("El número de licencia de conducir debe contener entre 5 y 30 caracteres alfanuméricos.")
        return cleaned

    @classmethod
    def mask(cls, license_number: str, visible_suffix_len: int = 4) -> str:
        if not license_number or len(license_number) <= visible_suffix_len:
            return "****"
        masked_len = len(license_number) - visible_suffix_len
        return ("*" * masked_len) + license_number[-visible_suffix_len:]


class DriverDocumentComplianceResolver:
    """Resolves driver document compliance state."""

    @classmethod
    def resolve_compliance(cls, db: Session, driver_id: UUID) -> DriverComplianceStatus:
        driver = db.get(DriverModel, driver_id)
        if not driver:
            return DriverComplianceStatus.NOT_EVALUATED

        if driver.lifecycle_status in {DriverLifecycleStatus.DRAFT, DriverLifecycleStatus.ARCHIVED}:
            return DriverComplianceStatus.NOT_EVALUATED

        today = date.today()

        # Check Primary Identity Document
        id_doc = db.scalar(
            select(DriverIdentityDocumentModel).where(
                DriverIdentityDocumentModel.driver_id == driver_id,
                DriverIdentityDocumentModel.is_primary == True,
                DriverIdentityDocumentModel.status == "ACTIVE",
            )
        )
        if not id_doc:
            return DriverComplianceStatus.NON_COMPLIANT
        if id_doc.expires_at and id_doc.expires_at < today:
            return DriverComplianceStatus.DOCUMENTS_EXPIRED

        # Check License
        license_obj = db.scalar(
            select(DriverLicenseModel).where(
                DriverLicenseModel.driver_id == driver_id,
                DriverLicenseModel.primary_license == True,
                DriverLicenseModel.status.in_(["ACTIVE", "SUSPENDED", "EXPIRED"]),
            )
        )
        if not license_obj:
            return DriverComplianceStatus.NON_COMPLIANT
        if license_obj.status == "SUSPENDED":
            return DriverComplianceStatus.LICENSE_SUSPENDED
        if license_obj.expires_at < today or license_obj.status == "EXPIRED":
            return DriverComplianceStatus.LICENSE_EXPIRED

        # Check Active Categories
        active_cats = db.scalars(
            select(DriverLicenseCategoryAssignmentModel).where(
                DriverLicenseCategoryAssignmentModel.driver_license_id == license_obj.id,
                DriverLicenseCategoryAssignmentModel.status == "ACTIVE",
            )
        ).all()
        if not active_cats:
            return DriverComplianceStatus.NON_COMPLIANT
        if any(cat.expires_at < today for cat in active_cats):
            return DriverComplianceStatus.LICENSE_EXPIRED

        return DriverComplianceStatus.COMPLIANT


class DriverOperationalEligibilityResolver:
    """Resolves driver operational eligibility for logistics transportation."""

    @classmethod
    def resolve_eligibility(cls, db: Session, driver_id: UUID) -> DriverEligibilityStatus:
        driver = db.get(DriverModel, driver_id)
        if not driver:
            return DriverEligibilityStatus.NOT_EVALUATED

        if driver.lifecycle_status == DriverLifecycleStatus.BLOCKED:
            return DriverEligibilityStatus.BLOCKED
        if driver.lifecycle_status in {DriverLifecycleStatus.DRAFT, DriverLifecycleStatus.INACTIVE, DriverLifecycleStatus.RETIRED, DriverLifecycleStatus.ARCHIVED}:
            return DriverEligibilityStatus.INELIGIBLE
        if driver.lifecycle_status == DriverLifecycleStatus.SUSPENDED:
            return DriverEligibilityStatus.INELIGIBLE

        # Check Active Blocking Operational Restrictions
        now_dt = utc_now()
        blocking_rest = db.scalar(
            select(DriverOperationalRestrictionModel.id).where(
                DriverOperationalRestrictionModel.driver_id == driver_id,
                DriverOperationalRestrictionModel.status == "ACTIVE",
                DriverOperationalRestrictionModel.blocking == True,
                DriverOperationalRestrictionModel.valid_from <= now_dt,
                (DriverOperationalRestrictionModel.valid_until.is_(None) | (DriverOperationalRestrictionModel.valid_until >= now_dt)),
            )
        )
        if blocking_rest:
            return DriverEligibilityStatus.BLOCKED

        # Check Compliance State
        compliance = DriverDocumentComplianceResolver.resolve_compliance(db, driver_id)
        if compliance in {DriverComplianceStatus.LICENSE_EXPIRED, DriverComplianceStatus.LICENSE_SUSPENDED}:
            return DriverEligibilityStatus.LICENSE_EXPIRED
        if compliance in {DriverComplianceStatus.NON_COMPLIANT, DriverComplianceStatus.DOCUMENTS_EXPIRED}:
            return DriverEligibilityStatus.DOCUMENTS_INCOMPLETE

        # Check Carrier Assignment
        today = date.today()
        carrier_assign = db.scalar(
            select(DriverCarrierAssignmentModel).where(
                DriverCarrierAssignmentModel.driver_id == driver_id,
                DriverCarrierAssignmentModel.status == "CURRENT",
                DriverCarrierAssignmentModel.valid_from <= today,
                (DriverCarrierAssignmentModel.valid_until.is_(None) | (DriverCarrierAssignmentModel.valid_until >= today)),
            )
        )
        if not carrier_assign:
            return DriverEligibilityStatus.CARRIER_INACTIVE

        # Check Non-blocking Restrictions (Restricted Status)
        non_blocking_rest = db.scalar(
            select(DriverOperationalRestrictionModel.id).where(
                DriverOperationalRestrictionModel.driver_id == driver_id,
                DriverOperationalRestrictionModel.status == "ACTIVE",
                DriverOperationalRestrictionModel.blocking == False,
                DriverOperationalRestrictionModel.valid_from <= now_dt,
                (DriverOperationalRestrictionModel.valid_until.is_(None) | (DriverOperationalRestrictionModel.valid_until >= now_dt)),
            )
        )
        if non_blocking_rest:
            return DriverEligibilityStatus.RESTRICTED

        return DriverEligibilityStatus.ELIGIBLE


class EvaluateDriverVehicleCompatibility:
    """Evaluates qualitative compatibility between a driver and a vehicle type."""

    @classmethod
    def evaluate(
        cls,
        db: Session,
        driver_id: UUID,
        vehicle_type: str,
        body_type: Optional[str] = None,
        effective_at: Optional[date] = None,
    ) -> Dict[str, Any]:
        eval_date = effective_at or date.today()

        eligibility = DriverOperationalEligibilityResolver.resolve_eligibility(db, driver_id)
        if eligibility not in {DriverEligibilityStatus.ELIGIBLE, DriverEligibilityStatus.RESTRICTED}:
            return {
                "status": DriverVehicleCompatibilityStatus.INELIGIBLE,
                "eligibility_status": eligibility,
                "allowed": False,
                "blocking_reasons": [f"El conductor no está operacionalmente elegible ({eligibility.value})."],
                "warnings": [],
                "matching_categories": [],
                "missing_categories": [],
                "evaluated_at": utc_now().isoformat(),
            }

        # Fetch active categories for driver's primary license
        license_obj = db.scalar(
            select(DriverLicenseModel).where(
                DriverLicenseModel.driver_id == driver_id,
                DriverLicenseModel.primary_license == True,
                DriverLicenseModel.status == "ACTIVE",
                DriverLicenseModel.expires_at >= eval_date,
            )
        )
        if not license_obj:
            return {
                "status": DriverVehicleCompatibilityStatus.INELIGIBLE,
                "allowed": False,
                "blocking_reasons": ["El conductor no posee una licencia de conducir primaria activa."],
                "warnings": [],
                "matching_categories": [],
                "missing_categories": [],
                "evaluated_at": utc_now().isoformat(),
            }

        cat_assignments = db.scalars(
            select(DriverLicenseCategoryAssignmentModel).where(
                DriverLicenseCategoryAssignmentModel.driver_license_id == license_obj.id,
                DriverLicenseCategoryAssignmentModel.status == "ACTIVE",
                DriverLicenseCategoryAssignmentModel.expires_at >= eval_date,
            )
        ).all()

        category_ids = [ca.category_id for ca in cat_assignments]
        if not category_ids:
            return {
                "status": DriverVehicleCompatibilityStatus.INELIGIBLE,
                "allowed": False,
                "blocking_reasons": ["La licencia del conductor no posee categorías vigentes asignadas."],
                "warnings": [],
                "matching_categories": [],
                "missing_categories": [vehicle_type],
                "evaluated_at": utc_now().isoformat(),
            }

        # Check vehicle rules matching categories
        rules = db.scalars(
            select(DriverLicenseVehicleTypeRuleModel).where(
                DriverLicenseVehicleTypeRuleModel.license_category_id.in_(category_ids),
                DriverLicenseVehicleTypeRuleModel.vehicle_type == vehicle_type,
                DriverLicenseVehicleTypeRuleModel.status == "ACTIVE",
                DriverLicenseVehicleTypeRuleModel.allowed == True,
            )
        ).all()

        if not rules:
            return {
                "status": DriverVehicleCompatibilityStatus.INELIGIBLE,
                "allowed": False,
                "blocking_reasons": [f"Las categorías del conductor no autorizan el tipo de vehículo '{vehicle_type}'."],
                "warnings": [],
                "matching_categories": [],
                "missing_categories": [vehicle_type],
                "evaluated_at": utc_now().isoformat(),
            }

        matching_cat_ids = [r.license_category_id for r in rules]
        warnings = []
        if any(r.requires_additional_certificate for r in rules):
            warnings.append("Requiere certificado de capacitación adicional para el tipo de vehículo.")

        return {
            "status": DriverVehicleCompatibilityStatus.ELIGIBLE if not warnings else DriverVehicleCompatibilityStatus.REQUIRES_REVIEW,
            "allowed": True,
            "blocking_reasons": [],
            "warnings": warnings,
            "matching_categories": [str(cid) for cid in matching_cat_ids],
            "missing_categories": [],
            "evaluated_at": utc_now().isoformat(),
        }


class DriverDuplicateDetectionService:
    """Service to detect potential duplicate drivers without auto-merging."""

    @classmethod
    def check_duplicates(
        cls,
        db: Session,
        organization_id: UUID,
        identity_document_value: Optional[str] = None,
        license_number: Optional[str] = None,
        first_name: Optional[str] = None,
        paternal_last_name: Optional[str] = None,
        phone: Optional[str] = None,
    ) -> Dict[str, Any]:
        matches = []

        if identity_document_value:
            norm_id = re.sub(r"\D", "", identity_document_value.strip())
            existing_doc = db.scalar(
                select(DriverIdentityDocumentModel).where(
                    DriverIdentityDocumentModel.organization_id == organization_id,
                    DriverIdentityDocumentModel.normalized_value == norm_id,
                    DriverIdentityDocumentModel.status == "ACTIVE",
                )
            )
            if existing_doc:
                matches.append({
                    "driver_id": str(existing_doc.driver_id),
                    "match_reason": "MATCH_IDENTITY_DOCUMENT",
                    "confidence": DuplicateMatchLevel.DUPLICATE_CONFIRMED,
                })

        if license_number:
            norm_lic = re.sub(r"[\s\-_]", "", license_number.strip().upper())
            existing_lic = db.scalar(
                select(DriverLicenseModel).where(
                    DriverLicenseModel.organization_id == organization_id,
                    DriverLicenseModel.normalized_license_number == norm_lic,
                    DriverLicenseModel.status.in_(["DRAFT", "ACTIVE"]),
                )
            )
            if existing_lic:
                matches.append({
                    "driver_id": str(existing_lic.driver_id),
                    "match_reason": "MATCH_LICENSE_NUMBER",
                    "confidence": DuplicateMatchLevel.DUPLICATE_CONFIRMED,
                })

        if first_name and paternal_last_name:
            fn_clean = first_name.strip().upper()
            ln_clean = paternal_last_name.strip().upper()
            existing_name = db.scalars(
                select(DriverModel).where(
                    DriverModel.organization_id == organization_id,
                    func.upper(DriverModel.first_name) == fn_clean,
                    func.upper(DriverModel.paternal_last_name) == ln_clean,
                    DriverModel.lifecycle_status.notin_(["ARCHIVED", "RETIRED"]),
                )
            ).all()
            for d in existing_name:
                if not any(m["driver_id"] == str(d.id) for m in matches):
                    matches.append({
                        "driver_id": str(d.id),
                        "match_reason": "MATCH_FULL_NAME",
                        "confidence": DuplicateMatchLevel.HIGH_PROBABILITY_DUPLICATE,
                    })

        match_level = (
            DuplicateMatchLevel.DUPLICATE_CONFIRMED
            if any(m["confidence"] == DuplicateMatchLevel.DUPLICATE_CONFIRMED for m in matches)
            else (DuplicateMatchLevel.HIGH_PROBABILITY_DUPLICATE if matches else DuplicateMatchLevel.NOT_DUPLICATE)
        )

        return {
            "duplicate_found": len(matches) > 0,
            "match_level": match_level,
            "candidate_matches": matches,
        }


class DriverExpirationAlertService:
    """Service for computing expiration alerts for drivers."""

    @classmethod
    def get_driver_alerts(cls, db: Session, driver_id: UUID, warning_days: int = 30) -> List[Dict[str, Any]]:
        alerts = []
        today = date.today()

        # Check License
        license_obj = db.scalar(
            select(DriverLicenseModel).where(
                DriverLicenseModel.driver_id == driver_id,
                DriverLicenseModel.primary_license == True,
                DriverLicenseModel.status == "ACTIVE",
            )
        )
        if license_obj:
            days_left = (license_obj.expires_at - today).days
            if days_left < 0:
                alerts.append({
                    "alert_type": "LICENSE_EXPIRED",
                    "severity": "CRITICAL",
                    "message": f"La licencia de conducir expiró hace {abs(days_left)} días.",
                    "expires_at": license_obj.expires_at.isoformat(),
                    "days_remaining": days_left,
                })
            elif days_left <= warning_days:
                alerts.append({
                    "alert_type": "LICENSE_EXPIRING_SOON",
                    "severity": "HIGH",
                    "message": f"La licencia de conducir vencerá en {days_left} días.",
                    "expires_at": license_obj.expires_at.isoformat(),
                    "days_remaining": days_left,
                })

        # Check Documents
        docs = db.scalars(
            select(DriverDocumentModel).where(
                DriverDocumentModel.driver_id == driver_id,
                DriverDocumentModel.status == "ACTIVE",
                DriverDocumentModel.expires_at.isnot(None),
            )
        ).all()
        for doc in docs:
            days_left = (doc.expires_at - today).days
            if days_left < 0:
                alerts.append({
                    "alert_type": "DOCUMENT_EXPIRED",
                    "severity": "HIGH",
                    "message": f"El documento '{doc.document_type}' expiró hace {abs(days_left)} días.",
                    "expires_at": doc.expires_at.isoformat(),
                    "days_remaining": days_left,
                })
            elif days_left <= warning_days:
                alerts.append({
                    "alert_type": "DOCUMENT_EXPIRING_SOON",
                    "severity": "MEDIUM",
                    "message": f"El documento '{doc.document_type}' vencerá en {days_left} días.",
                    "expires_at": doc.expires_at.isoformat(),
                    "days_remaining": days_left,
                })

        return alerts


class DriverSnapshotProvider:
    """Computes reproducible JSONB snapshots and content hashes for DriverVersionModel."""

    @classmethod
    def create_snapshots(cls, db: Session, driver_id: UUID) -> Dict[str, Any]:
        driver = db.get(DriverModel, driver_id)
        if not driver:
            raise ValueError("Driver not found")

        id_doc = db.scalar(
            select(DriverIdentityDocumentModel).where(
                DriverIdentityDocumentModel.driver_id == driver_id,
                DriverIdentityDocumentModel.is_primary == True,
                DriverIdentityDocumentModel.status == "ACTIVE",
            )
        )
        license_obj = db.scalar(
            select(DriverLicenseModel).where(
                DriverLicenseModel.driver_id == driver_id,
                DriverLicenseModel.primary_license == True,
                DriverLicenseModel.status == "ACTIVE",
            )
        )
        cat_assignments = []
        if license_obj:
            cat_assignments = db.scalars(
                select(DriverLicenseCategoryAssignmentModel).where(
                    DriverLicenseCategoryAssignmentModel.driver_license_id == license_obj.id,
                    DriverLicenseCategoryAssignmentModel.status == "ACTIVE",
                )
            ).all()

        carrier_assign = db.scalar(
            select(DriverCarrierAssignmentModel).where(
                DriverCarrierAssignmentModel.driver_id == driver_id,
                DriverCarrierAssignmentModel.status == "CURRENT",
            )
        )
        contact = db.scalar(
            select(DriverContactModel).where(
                DriverContactModel.driver_id == driver_id,
                DriverContactModel.is_primary == True,
                DriverContactModel.status == "ACTIVE",
            )
        )

        identity_snapshot = {
            "driver_code": driver.driver_code,
            "display_name": driver.display_name,
            "first_name": driver.first_name,
            "paternal_last_name": driver.paternal_last_name,
            "identity_document_masked": id_doc.masked_value if id_doc else None,
            "identity_document_type": id_doc.document_type if id_doc else None,
        }

        license_snapshot = {
            "license_number_masked": license_obj.masked_license_number if license_obj else None,
            "issuing_authority": license_obj.issuing_authority if license_obj else None,
            "expires_at": license_obj.expires_at.isoformat() if license_obj else None,
            "status": license_obj.status if license_obj else None,
        }

        categories_snapshot = [
            {
                "category_id": str(ca.category_id),
                "expires_at": ca.expires_at.isoformat(),
            }
            for ca in cat_assignments
        ]

        carrier_snapshot = {
            "carrier_id": str(carrier_assign.carrier_business_partner_id) if carrier_assign else None,
            "assignment_type": carrier_assign.assignment_type if carrier_assign else None,
        }

        contact_snapshot = {
            "contact_type": contact.contact_type if contact else None,
            "email": contact.email if contact else None,
            "phone": contact.phone if contact else None,
        }

        photo_snapshot = {
            "current_photo_id": str(driver.current_photo_id) if driver.current_photo_id else None,
        }

        restrictions_snapshot = []
        compliance_status = DriverDocumentComplianceResolver.resolve_compliance(db, driver_id)
        eligibility_status = DriverOperationalEligibilityResolver.resolve_eligibility(db, driver_id)

        compliance_snapshot = {"status": compliance_status.value}
        eligibility_snapshot = {"status": eligibility_status.value}

        full_payload = {
            "identity": identity_snapshot,
            "license": license_snapshot,
            "categories": categories_snapshot,
            "carrier": carrier_snapshot,
            "contact": contact_snapshot,
            "photo": photo_snapshot,
            "restrictions": restrictions_snapshot,
            "compliance": compliance_snapshot,
            "eligibility": eligibility_snapshot,
        }

        serialized = json.dumps(full_payload, sort_keys=True)
        content_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()

        return {
            "identity_snapshot": identity_snapshot,
            "license_snapshot": license_snapshot,
            "categories_snapshot": categories_snapshot,
            "carrier_snapshot": carrier_snapshot,
            "contact_snapshot": contact_snapshot,
            "photo_snapshot": photo_snapshot,
            "restrictions_snapshot": restrictions_snapshot,
            "compliance_snapshot": compliance_snapshot,
            "eligibility_snapshot": eligibility_snapshot,
            "content_hash": content_hash,
        }
