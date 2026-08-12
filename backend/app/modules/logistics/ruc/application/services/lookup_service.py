"""RucLookupService — Exact lookup, cache, staleness and field-level provenance (Phase 026)."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.database.base import utc_now
from app.modules.logistics.audit.service import AuditEventCommand, audit_service
from app.modules.logistics.partners.ruc_validator import PeruvianRucValidator
from app.modules.logistics.ruc.domain.errors.exceptions import (
    RucDatasetUnavailableError,
    RucInvalidError,
    RucNotFoundError,
)
from app.modules.logistics.ruc.domain.services.policies import (
    RucConfidencePolicy,
    RucFieldProvenanceBuilder,
    RucStalenessPolicy,
)
from app.modules.logistics.ruc.domain.value_objects.enums import (
    ConfidenceLevel,
    DomicileCondition,
    RucSourceType,
    StalenessLevel,
    TaxpayerStatus,
)
from app.modules.logistics.ruc.infrastructure.cache.ruc_cache import ruc_cache
from app.modules.logistics.ruc.infrastructure.persistence.models import (
    RucDatasetVersionModel,
    RucRegistryAnnexAddressModel,
    RucRegistryEntryModel,
)
from app.modules.logistics.ruc.infrastructure.providers.ruc_provider import RucEnrichmentProvider, NoOpRucProvider


class RucLookupService:
    """Core service for RUC lookup with cache, provenance, and provider resilience."""

    def __init__(self, db: Session, provider: Optional[RucEnrichmentProvider] = None):
        self.db = db
        self.provider = provider or NoOpRucProvider()

    def get_active_dataset_version(self, dataset_type: str = "RUC_GENERAL") -> RucDatasetVersionModel:
        ds = self.db.scalars(
            select(RucDatasetVersionModel)
            .where(
                and_(
                    RucDatasetVersionModel.dataset_type == dataset_type,
                    RucDatasetVersionModel.status == "ACTIVE",
                )
            )
            .order_by(RucDatasetVersionModel.activated_at.desc())
        ).first()

        if not ds:
            raise RucDatasetUnavailableError(f"No hay un dataset de RUC ({dataset_type}) activo.")
        return ds

    def lookup_ruc(
        self,
        raw_ruc: str,
        include_annexes: bool = False,
        allow_provider: bool = False,
        actor_id: Optional[UUID] = None,
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        normalized = PeruvianRucValidator.normalize(raw_ruc)
        if not PeruvianRucValidator.validate(normalized):
            raise RucInvalidError(f"El RUC '{raw_ruc}' es inválido.")

        # Try to find active general dataset
        try:
            dataset = self.get_active_dataset_version("RUC_GENERAL")
            dataset_id_str = str(dataset.id)
        except RucDatasetUnavailableError:
            dataset = None
            dataset_id_str = "NONE"

        # Check Cache if dataset exists
        if dataset:
            cached_data, cache_status = ruc_cache.get(dataset_id_str, normalized)
            if cache_status == "HIT_L1" and cached_data:
                cached_data["cache_status"] = "HIT_L1"
                return cached_data
            if cache_status == "NEGATIVE_HIT" and not allow_provider:
                raise RucNotFoundError(normalized)

        # Query DB Entry
        entry = None
        if dataset:
            entry = self.db.scalars(
                select(RucRegistryEntryModel).where(
                    and_(
                        RucRegistryEntryModel.dataset_version_id == dataset.id,
                        RucRegistryEntryModel.normalized_ruc == normalized,
                    )
                )
            ).first()

        provider_used = None
        provider_data = None

        if not entry and allow_provider:
            try:
                provider_data = self.provider.lookup(normalized)
                if provider_data:
                    provider_used = self.provider.provider_code
            except Exception:
                provider_data = None

        if not entry and not provider_data:
            if dataset:
                ruc_cache.set_negative(dataset_id_str, normalized)
            audit_service.log_event(
                self.db,
                AuditEventCommand(
                    event_code="logistics.ruc.lookup_not_found",
                    category="INTEGRATION",
                    severity="LOW",
                    description=f"RUC '{normalized}' no encontrado",
                    actor_user_id=actor_id,
                ),
            )
            raise RucNotFoundError(normalized)

        # Build Response
        source_type = RucSourceType.SUNAT_REDUCED_REGISTRY if entry else RucSourceType.AUTHORIZED_PROVIDER
        ref_date = entry.source_published_at if entry else (entry.imported_at if entry else utc_now())
        fetched_date = entry.imported_at if entry else utc_now()

        age_days, staleness_lvl, is_stale = RucStalenessPolicy.evaluate(ref_date, fetched_date)
        confidence = RucConfidencePolicy.calculate(source_type, staleness_lvl)

        legal_name = entry.legal_name if entry else provider_data.get("legal_name", "")
        status_norm = entry.taxpayer_status_normalized if entry else provider_data.get("taxpayer_status", TaxpayerStatus.UNKNOWN.value)
        status_raw = entry.taxpayer_status_raw if entry else status_norm
        cond_norm = entry.domicile_condition_normalized if entry else provider_data.get("domicile_condition", DomicileCondition.UNKNOWN.value)
        cond_raw = entry.domicile_condition_raw if entry else cond_norm
        ubigeo = entry.ubigeo_code if entry else provider_data.get("ubigeo_code")

        # Query Annexes if requested
        annexes_list = []
        if include_annexes:
            annex_ds = None
            try:
                annex_ds = self.get_active_dataset_version("RUC_ANNEX_ADDRESS")
            except RucDatasetUnavailableError:
                pass

            if annex_ds:
                annex_rows = self.db.scalars(
                    select(RucRegistryAnnexAddressModel).where(
                        and_(
                            RucRegistryAnnexAddressModel.dataset_version_id == annex_ds.id,
                            RucRegistryAnnexAddressModel.ruc == normalized,
                        )
                    )
                ).all()
                annexes_list = [
                    {
                        "ubigeo_code": r.ubigeo_code,
                        "address_raw": r.address_raw,
                        "address_normalized": r.address_normalized,
                    }
                    for r in annex_rows
                ]

        # Field Provenance
        provenance = {
            "legal_name": RucFieldProvenanceBuilder.build_field("legal_name", legal_name, source_type, "Padrón Reducido SUNAT", ref_date, confidence, is_stale),
            "taxpayer_status": RucFieldProvenanceBuilder.build_field("taxpayer_status", status_norm, source_type, "Padrón Reducido SUNAT", ref_date, confidence, is_stale),
            "domicile_condition": RucFieldProvenanceBuilder.build_field("domicile_condition", cond_norm, source_type, "Padrón Reducido SUNAT", ref_date, confidence, is_stale),
            "ubigeo_code": RucFieldProvenanceBuilder.build_field("ubigeo_code", ubigeo, source_type, "Padrón Reducido SUNAT", ref_date, confidence, is_stale),
        }

        response = {
            "query_ruc": raw_ruc,
            "normalized_ruc": normalized,
            "found": True,
            "legal_name": legal_name,
            "taxpayer_status": status_norm,
            "taxpayer_status_raw": status_raw,
            "domicile_condition": cond_norm,
            "domicile_condition_raw": cond_raw,
            "ubigeo_code": ubigeo,
            "annex_addresses": annexes_list,
            "source": source_type.value,
            "source_name": "SUNAT Padrón Reducido" if entry else "Proveedor Autorizado",
            "dataset_version_id": dataset_id_str,
            "source_published_at": ref_date.isoformat() if ref_date else None,
            "fetched_at": fetched_date.isoformat(),
            "lookup_at": utc_now().isoformat(),
            "data_age_days": age_days,
            "staleness_level": staleness_lvl.value,
            "is_stale": is_stale,
            "confidence_level": confidence.value,
            "verification_status": "FORMAT_VALID",
            "field_provenance": provenance,
            "conflicts": [],
            "warnings": ["Datos con antigüedad > 30 días"] if is_stale else [],
            "provider_used": provider_used,
            "cache_status": "MISS",
            "correlation_id": correlation_id,
        }

        if dataset:
            ruc_cache.set(dataset_id_str, normalized, response)

        audit_service.log_event(
            self.db,
            AuditEventCommand(
                event_code="logistics.ruc.lookup_performed",
                category="INTEGRATION",
                severity="LOW",
                description=f"Consulta de RUC realizada: {normalized}",
                actor_user_id=actor_id,
                payload={"ruc": normalized, "found": True, "source": source_type.value},
            ),
        )

        return response
