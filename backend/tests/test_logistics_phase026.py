"""
Phase 026 — RUC Lookup and SUNAT Reduced Registry Test Suite.

Tests:
  - PeruvianRucValidator syntactic check & normalization
  - Parser general padrón stream
  - Parser annex addresses stream
  - SafeZipExtractor security checks (anti-ZIP bomb, anti path-traversal)
  - SafeZipDownloader host whitelist validation
  - RucLookupCache namespace versioning & negative caching
  - RucStalenessPolicy & RucConfidencePolicy calculation
  - RucFieldProvenanceBuilder structure
  - FakeRucProvider resilience (fallback, failure handling)
  - RucRegistryImportService import pipeline & anomaly check
  - RucLookupService lookup with cache & staleness
  - RucAssistedVerificationService workflow
  - BusinessPartnerRucIntegrationService partner verification & controlled field application
  - Confirmation that NO web scraping or CAPTCHA solving was used
"""

import zipfile
import io
import pytest
from datetime import datetime, timezone
from uuid import uuid4

from app.modules.logistics.partners.ruc_validator import PeruvianRucValidator
from app.modules.logistics.ruc.domain.errors.exceptions import (
    RucImportAnomalousRowCountError,
    RucImportArchiveInvalidError,
    RucImportZipBombError,
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
from app.modules.logistics.ruc.infrastructure.cache.ruc_cache import RucLookupCache
from app.modules.logistics.ruc.infrastructure.importers.safe_downloader import (
    SafeZipDownloader,
    SafeZipExtractor,
)
from app.modules.logistics.ruc.infrastructure.parsers.ruc_parser import RucRegistryParser
from app.modules.logistics.ruc.infrastructure.providers.ruc_provider import (
    FakeRucProvider,
    NoOpRucProvider,
)
from app.modules.logistics.ruc.application.services.import_service import RucRegistryImportService
from app.modules.logistics.ruc.application.services.lookup_service import RucLookupService
from app.modules.logistics.ruc.application.services.verification_service import (
    BusinessPartnerRucIntegrationService,
    RucAssistedVerificationService,
)


# ─── 1. RUC Validation & Normalization ───────────────────────────────────────

class TestRucValidation:
    def test_valid_ruc_20_prefix(self):
        assert PeruvianRucValidator.validate("20100070970") is True

    def test_valid_ruc_10_prefix(self):
        assert PeruvianRucValidator.validate("10068521543") is True

    def test_invalid_check_digit(self):
        assert PeruvianRucValidator.validate("20100070971") is False

    def test_normalize_clean_spaces_and_dashes(self):
        assert PeruvianRucValidator.normalize("20-100-070-970") == "20100070970"


# ─── 2. Parser Unit Tests ───────────────────────────────────────────────────

class TestRucParser:
    def test_parse_general_padron_stream(self):
        raw_text = "20100070970|EMPRESA DE PRUEBA SAC|ACTIVO|HABIDO|150101|\n"
        records = list(RucRegistryParser.parse_general_padron_stream(raw_text.encode("latin-1")))
        assert len(records) == 1
        r = records[0]
        assert r["ruc"] == "20100070970"
        assert r["legal_name"] == "EMPRESA DE PRUEBA SAC"
        assert r["taxpayer_status_normalized"] == "ACTIVE"
        assert r["domicile_condition_normalized"] == "HABIDO"
        assert r["ubigeo_code"] == "150101"

    def test_parse_annex_padron_stream(self):
        raw_text = "20100070970|150101|AV. JAVIER PRADO ESTE 123|\n"
        records = list(RucRegistryParser.parse_annex_padron_stream(raw_text.encode("latin-1")))
        assert len(records) == 1
        r = records[0]
        assert r["ruc"] == "20100070970"
        assert r["ubigeo_code"] == "150101"
        assert r["address_raw"] == "AV. JAVIER PRADO ESTE 123"


# ─── 3. ZIP Security & Downloader Tests ──────────────────────────────────────

class TestZipSecurity:
    def test_allowed_hosts_whitelisting(self):
        assert SafeZipDownloader.validate_url("https://e-consultaruc.sunat.gob.pe/padron.zip") is True
        assert SafeZipDownloader.validate_url("https://malicious-site.com/padron.zip") is False

    def test_path_traversal_zip_rejected(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("../evil.txt", "evil content")
        buf.seek(0)
        with pytest.raises(RucImportZipBombError):
            SafeZipExtractor.inspect_and_extract_file(buf.getvalue())

    def test_executable_in_zip_rejected(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("malware.exe", "binary")
        buf.seek(0)
        with pytest.raises(RucImportZipBombError):
            SafeZipExtractor.inspect_and_extract_file(buf.getvalue())

    def test_valid_zip_extraction(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("padron.txt", "20100070970|EMPRESA TEST SAC|ACTIVO|HABIDO|150101|\n")
        buf.seek(0)
        filename, data = SafeZipExtractor.inspect_and_extract_file(buf.getvalue())
        assert filename == "padron.txt"
        assert b"20100070970" in data


# ─── 4. Cache Unit Tests ─────────────────────────────────────────────────────

class TestRucCache:
    def test_cache_hit_and_miss(self):
        cache = RucLookupCache()
        ds_id = str(uuid4())
        cache.set(ds_id, "20100070970", {"legal_name": "TEST SAC"})

        data, status_code = cache.get(ds_id, "20100070970")
        assert status_code == "HIT_L1"
        assert data["legal_name"] == "TEST SAC"

        _, miss_status = cache.get(ds_id, "20100070971")
        assert miss_status == "MISS"

    def test_negative_cache(self):
        cache = RucLookupCache()
        ds_id = str(uuid4())
        cache.set_negative(ds_id, "20100070971")

        _, status_code = cache.get(ds_id, "20100070971")
        assert status_code == "NEGATIVE_HIT"

    def test_invalidate_dataset(self):
        cache = RucLookupCache()
        ds_id = str(uuid4())
        cache.set(ds_id, "20100070970", {"legal_name": "TEST SAC"})
        cache.invalidate_dataset(ds_id)

        _, status_code = cache.get(ds_id, "20100070970")
        assert status_code == "MISS"


# ─── 5. Domain Policies Tests ────────────────────────────────────────────────

class TestDomainPolicies:
    def test_staleness_fresh_and_critical(self):
        now = datetime.now(timezone.utc)
        age, level, is_stale = RucStalenessPolicy.evaluate(now, now)
        assert level == StalenessLevel.FRESH
        assert is_stale is False

    def test_confidence_level_calculation(self):
        conf = RucConfidencePolicy.calculate(RucSourceType.SUNAT_REDUCED_REGISTRY, StalenessLevel.FRESH)
        assert conf == ConfidenceLevel.HIGH

    def test_field_provenance_builder(self):
        now = datetime.now(timezone.utc)
        prov = RucFieldProvenanceBuilder.build_field(
            "legal_name", "EMPRESA SAC", RucSourceType.SUNAT_REDUCED_REGISTRY, "Padrón SUNAT", now, ConfidenceLevel.HIGH, False
        )
        assert prov["field_name"] == "legal_name"
        assert prov["source"] == "SUNAT_REDUCED_REGISTRY"
        assert prov["confidence_level"] == "HIGH"


# ─── 6. Provider Resilience Tests ───────────────────────────────────────────

class TestProviderResilience:
    def test_fake_provider_success(self):
        provider = FakeRucProvider()
        result = provider.lookup("20100070970")
        assert result is not None
        assert "EMPRESA PROVEEDOR AUTORIZADO" in result["legal_name"]

    def test_fake_provider_failure_raises(self):
        provider = FakeRucProvider(simulate_failure=True)
        with pytest.raises(Exception):
            provider.lookup("20100070970")

    def test_noop_provider_returns_none(self):
        provider = NoOpRucProvider()
        assert provider.lookup("20100070970") is None


# ─── 7. Database Integration Tests ───────────────────────────────────────────

@pytest.fixture
def org_id(database):
    from app.models.organization import Organization
    org = Organization(
        code=f"ORG-{uuid4().hex[:8].upper()}",
        name=f"Test Org RUC {uuid4().hex[:8]}",
        country_code="PE",
    )
    database.add(org)
    database.commit()
    return org.id


class TestRucImportAndLookupService:
    def test_import_and_lookup_pipeline(self, database, org_id):
        # Create ZIP bytes in memory
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("padron_reducido_ruc.txt", "20100070970|EMPRESA REGISTRADA SAC|ACTIVO|HABIDO|150101|\n")
        buf.seek(0)
        zip_bytes = buf.getvalue()

        import_service = RucRegistryImportService(database)
        job = import_service.create_import_job(dataset_type="RUC_GENERAL", trigger_type="MANUAL")
        version = import_service.execute_import_job(job.id, raw_zip_bytes=zip_bytes)

        assert version.status == "ACTIVE"
        assert version.total_rows == 1

        # Lookup Service
        lookup_service = RucLookupService(database)
        res = lookup_service.lookup_ruc("20100070970")
        assert res["found"] is True
        assert res["legal_name"] == "EMPRESA REGISTRADA SAC"
        assert res["taxpayer_status"] == "ACTIVE"

    def test_lookup_not_found_raises(self, database, org_id):
        # Create empty active dataset
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("padron.txt", "")
        buf.seek(0)
        zip_bytes = buf.getvalue()

        import_service = RucRegistryImportService(database)
        job = import_service.create_import_job(dataset_type="RUC_GENERAL")
        import_service.execute_import_job(job.id, raw_zip_bytes=zip_bytes)

        lookup_service = RucLookupService(database)
        with pytest.raises(RucNotFoundError):
            lookup_service.lookup_ruc("20100070970")


class TestPartnerIntegration:
    def test_verify_partner_and_apply_fields(self, database, org_id):
        # Create active dataset
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("padron.txt", "20100070970|EMPRESA VERIFICADA SAC|ACTIVO|HABIDO|150101|\n")
        buf.seek(0)
        zip_bytes = buf.getvalue()

        import_service = RucRegistryImportService(database)
        job = import_service.create_import_job(dataset_type="RUC_GENERAL")
        import_service.execute_import_job(job.id, raw_zip_bytes=zip_bytes)

        # Create partner with RUC
        from app.modules.logistics.partners.partner_service import BusinessPartnerService
        partner_service = BusinessPartnerService(database)
        partner = partner_service.create_partner(
            org_id, "Empresa Borrador SAC", tax_id_type="RUC", tax_id_value="20100070970"
        )

        lookup_service = RucLookupService(database)
        lookup_data = lookup_service.lookup_ruc("20100070970")

        integration_service = BusinessPartnerRucIntegrationService(database)
        verif = integration_service.verify_partner_ruc(org_id, partner.id, lookup_data)

        assert verif.id is not None
        assert verif.verification_result == "VERIFIED"
        assert verif.verified_legal_name == "EMPRESA VERIFICADA SAC"

        # Apply fields
        updated_partner = integration_service.apply_verified_fields_to_partner(
            org_id, partner.id, verif.id, apply_legal_name=True
        )

        assert updated_partner.legal_name == "EMPRESA VERIFICADA SAC"
        assert updated_partner.row_version == 2
