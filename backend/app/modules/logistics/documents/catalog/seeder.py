"""Catalog seeder module.

Populates the database with document catalog families, types, versions,
and retention policies from the central JSON source. Idempotent and safe.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any
from sqlalchemy.orm import Session

from app.modules.logistics.documents.catalog.loader import load_catalog_json
from app.modules.logistics.documents.catalog.validator import validate_catalog_data
from app.modules.logistics.documents.models import (
    DocumentCatalogVersionModel,
    DocumentFamilyModel,
    DocumentRetentionPolicyModel,
    DocumentTypeModel,
    DocumentTypeVersionModel,
)
from app.modules.logistics.documents.repository import (
    DocumentCatalogVersionRepository,
    DocumentFamilyRepository,
    DocumentRetentionPolicyRepository,
    DocumentTypeRepository,
    DocumentTypeVersionRepository,
)


def seed_document_catalog(db: Session, dry_run: bool = False) -> dict[str, Any]:
    """Reads, validates, and seeds the central document catalog into PostgreSQL.

    Idempotent: updates or skips existing items without creating duplicates.
    """
    catalog_data = load_catalog_json()
    validation_report = validate_catalog_data(catalog_data)
    if not validation_report["valid"]:
        raise ValueError(f"Catalog validation failed: {validation_report['errors']}")

    raw_json = json.dumps(catalog_data, sort_keys=True)
    checksum = hashlib.sha256(raw_json.encode("utf-8")).hexdigest()

    if dry_run:
        return {
            "dry_run": True,
            "status": "VALIDATED",
            "catalog_version": catalog_data.get("catalog_version"),
            "checksum": checksum,
            "summary": validation_report,
        }

    fam_repo = DocumentFamilyRepository(db)
    ret_repo = DocumentRetentionPolicyRepository(db)
    type_repo = DocumentTypeRepository(db)
    ver_repo = DocumentTypeVersionRepository(db)
    cat_ver_repo = DocumentCatalogVersionRepository(db)

    # 1. Seed Retention Policies
    ret_map: dict[str, Any] = {}
    for rdata in catalog_data.get("retention_policies", []):
        rcode = rdata["code"]
        existing_ret = ret_repo.get_by_code(rcode)
        if not existing_ret:
            existing_ret = DocumentRetentionPolicyModel(
                code=rcode,
                name=rdata["name"],
                description=rdata.get("description"),
                retention_class=rdata["retention_class"],
                minimum_retention_days=rdata["minimum_retention_days"],
                maximum_retention_days=rdata.get("maximum_retention_days"),
                archive_after_days=rdata.get("archive_after_days"),
                deletion_allowed=rdata.get("deletion_allowed", False),
                legal_hold_supported=rdata.get("legal_hold_supported", True),
                requires_manual_review=rdata.get("requires_manual_review", True),
                applies_to_origin_type=rdata.get("applies_to_origin_type", "INTERNAL_GENERATED"),
                status=rdata.get("status", "ACTIVE"),
                version=rdata.get("version", "1.0.0"),
            )
            ret_repo.save(existing_ret)
            db.flush()
        ret_map[rcode] = existing_ret

    # 2. Seed Families
    fam_map: dict[str, Any] = {}
    for fdata in catalog_data.get("families", []):
        fcode = fdata["code"]
        existing_fam = fam_repo.get_by_code(fcode)
        if not existing_fam:
            existing_fam = DocumentFamilyModel(
                code=fcode,
                name=fdata["name"],
                description=fdata.get("description"),
                owner_module=fdata["owner_module"],
                display_order=fdata.get("display_order", 0),
                status=fdata.get("status", "ACTIVE"),
            )
            fam_repo.save(existing_fam)
            db.flush()
        fam_map[fcode] = existing_fam

    # 3. Seed Document Types and Versions
    for tdata in catalog_data.get("document_types", []):
        tcode = tdata["code"]
        existing_type = type_repo.get_by_code(tcode)
        family_obj = fam_map[tdata["family_code"]]

        if not existing_type:
            existing_type = DocumentTypeModel(
                code=tcode,
                name=tdata["name"],
                short_name=tdata.get("short_name"),
                description=tdata.get("description"),
                family_id=family_obj.id,
                origin_type=tdata["origin_type"],
                owner_module=tdata["owner_module"],
                resource_type=tdata["resource_type"],
                operation_type=tdata["operation_type"],
                catalog_status=tdata.get("catalog_status", "ACTIVE"),
                is_system=tdata.get("is_system", True),
                is_official_external=tdata.get("is_official_external", False),
                supports_internal_number=tdata.get("supports_internal_number", True),
                supports_external_number=tdata.get("supports_external_number", False),
                supports_series=tdata.get("supports_series", True),
                supports_talonario=tdata.get("supports_talonario", False),
                supports_preview=tdata.get("supports_preview", True),
                supports_issue=tdata.get("supports_issue", True),
                supports_download=tdata.get("supports_download", True),
                supports_bulk_download=tdata.get("supports_bulk_download", False),
                supports_reprint=tdata.get("supports_reprint", True),
                supports_cancel=tdata.get("supports_cancel", True),
                supports_public_verification=tdata.get("supports_public_verification", False),
                requires_qr=tdata.get("requires_qr", False),
                requires_signature=tdata.get("requires_signature", False),
                requires_reason_on_reprint=tdata.get("requires_reason_on_reprint", True),
                requires_reason_on_cancel=tdata.get("requires_reason_on_cancel", True),
                is_sensitive=tdata.get("is_sensitive", False),
                display_order=tdata.get("display_order", 0),
            )
            type_repo.save(existing_type)
            db.flush()

        # Seed Version 1.0.0 for this Document Type
        existing_ver = ver_repo.get_by_type_and_version(existing_type.id, "1.0.0")
        ret_policy_obj = ret_map.get(tdata.get("retention_policy_code", ""))

        if not existing_ver:
            existing_ver = DocumentTypeVersionModel(
                document_type_id=existing_type.id,
                version="1.0.0",
                schema_version="1.0.0",
                status="ACTIVE",
                required_fields_schema=tdata.get("required_fields_schema", {"fields": []}),
                allowed_statuses=tdata.get("allowed_statuses", []),
                permission_policy=tdata.get("permission_policy", {}),
                retention_policy_id=ret_policy_obj.id if ret_policy_obj else None,
                template_key="PENDING_PHASE_014",
                template_version=None,
                notes="Initial release from Catalog v1.0.0",
            )
            ver_repo.save(existing_ver)
            db.flush()

            # Link Active Version ID to Document Type
            existing_type.active_version_id = existing_ver.id
            type_repo.save(existing_type)
            db.flush()

    # 4. Seed Global Catalog Version
    current_cat_ver = cat_ver_repo.get_current_active()
    if not current_cat_ver:
        current_cat_ver = DocumentCatalogVersionModel(
            version=catalog_data.get("catalog_version", "1.0.0"),
            status="ACTIVE",
            checksum=checksum,
            manifest_data={
                "total_families": len(fam_map),
                "total_document_types": len(catalog_data.get("document_types", [])),
                "total_proposed_types": len(catalog_data.get("proposed_types", [])),
                "status": "SEEDED_SUCCESSFULLY",
            },
        )
        cat_ver_repo.save(current_cat_ver)

    db.commit()

    return {
        "dry_run": False,
        "status": "SEEDED_SUCCESSFULLY",
        "catalog_version": catalog_data.get("catalog_version"),
        "checksum": checksum,
        "summary": validation_report,
    }
