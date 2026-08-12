"""Service layer for Document Code Standard operations (Phase 012)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.logistics.documents.codes.code_models import (
    DocumentCodeStandardModel,
    DocumentSiteCodeModel,
)
from app.modules.logistics.documents.codes.code_repository import (
    DocumentCodeStandardRepository,
    DocumentSiteCodeRepository,
    DocumentTypeCodePolicyRepository,
)
from app.modules.logistics.documents.codes.code_schemas import (
    DocumentCodeExampleItem,
    DocumentCodeExamplesResponse,
    DocumentCodeParseResponse,
    DocumentCodePartsRequest,
    DocumentCodePartsResponse,
    DocumentCodePreviewRequest,
    DocumentCodePreviewResponse,
    DocumentCodeStandardResponse,
    DocumentCodeValidationResponse,
    DocumentSiteCodeResponse,
)
from app.modules.logistics.documents.codes.domain import (
    DocumentCodeFormatter,
    DocumentCodeNormalizer,
    DocumentCodeParser,
    DocumentCodeValidationError,
    DocumentCodeValidator,
    YearResolverService,
)
from app.modules.logistics.documents.repository import DocumentTypeRepository


class DocumentCodeStandardService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.std_repo = DocumentCodeStandardRepository(db)
        self.site_repo = DocumentSiteCodeRepository(db)
        self.policy_repo = DocumentTypeCodePolicyRepository(db)
        self.type_repo = DocumentTypeRepository(db)

    def get_active_standard(self) -> DocumentCodeStandardResponse:
        active_std = self.std_repo.get_active()
        if not active_std:
            active_std = DocumentCodeStandardModel(
                code="STD_LOGISTICS_CODE",
                version="1.0.0",
                name="Estándar TIPO-SEDE-AÑO-CORRELATIVO",
                description="Norma técnica oficial para códigos internos de Proyecto T1",
                pattern="^[A-Z0-9]{2,8}-[A-Z0-9]{2,10}-[0-9]{4}-[0-9]{6}$",
                separator="-",
            )
            self.std_repo.save(active_std)
            self.db.commit()
        return DocumentCodeStandardResponse.model_validate(active_std)

    def format_code(self, req: DocumentCodePartsRequest) -> DocumentCodePartsResponse:
        formatted = DocumentCodeFormatter.format(
            document_type_code=req.document_type_code,
            site_code=req.site_code,
            year=req.year,
            sequence=req.sequence,
        )
        return DocumentCodePartsResponse(
            document_type_code=req.document_type_code.upper(),
            site_code=req.site_code.upper(),
            year=req.year,
            sequence=req.sequence,
            formatted_code=formatted,
            standard_version="1.0.0",
        )

    def validate_code(self, code: str) -> DocumentCodeValidationResponse:
        report = DocumentCodeValidator.validate_structure(code)
        if report["valid"] and report["parts"]:
            # Semantic check against DocumentType catalog
            doc_type_code = report["parts"]["document_type_code"]
            dt = self.type_repo.get_by_code(doc_type_code)
            if not dt:
                report["valid"] = False
                report["errors"].append(f"El tipo documental '{doc_type_code}' no existe en el catálogo.")
            elif dt.catalog_status != "ACTIVE":
                report["valid"] = False
                report["errors"].append(f"El tipo documental '{doc_type_code}' no está activo.")

        return DocumentCodeValidationResponse(
            valid=report["valid"],
            code=report["code"],
            normalized_code=report["normalized_code"],
            standard_version="1.0.0",
            errors=report["errors"],
            parts=report["parts"],
        )

    def parse_code(self, code: str) -> DocumentCodeParseResponse:
        parts = DocumentCodeParser.parse(code, strict=True)
        return DocumentCodeParseResponse(
            code=code,
            document_type_code=parts.document_type_code,
            site_code=parts.site_code,
            year=parts.year,
            sequence=parts.sequence,
            standard_version="1.0.0",
        )

    def preview_code(self, req: DocumentCodePreviewRequest) -> DocumentCodePreviewResponse:
        doc_type_code = req.document_type_code.upper()
        site_code = req.site_code.upper() if req.site_code else "LIM"
        year = req.year if req.year else YearResolverService.resolve_year()
        seq = req.example_sequence

        preview_formatted = DocumentCodeFormatter.format(
            document_type_code=doc_type_code,
            site_code=site_code,
            year=year,
            sequence=seq,
        )

        return DocumentCodePreviewResponse(
            code_preview=preview_formatted,
            standard_version="1.0.0",
            document_type_code=doc_type_code,
            site_code=site_code,
            year=year,
            sequence_example=seq,
            is_reserved=False,
            warning="Este código es solo una vista previa y NO reserva el correlativo.",
        )

    def get_approved_examples(self) -> DocumentCodeExamplesResponse:
        types = self.type_repo.list(catalog_status="ACTIVE")
        examples: list[DocumentCodeExampleItem] = []
        for t in types:
            ex_code = DocumentCodeFormatter.format(
                document_type_code=t.code,
                site_code="LIM",
                year=2026,
                sequence=1,
            )
            examples.append(
                DocumentCodeExampleItem(
                    family_code=t.family.code if t.family else "",
                    document_type_code=t.code,
                    document_name=t.name,
                    canonical_example=ex_code,
                )
            )
        return DocumentCodeExamplesResponse(
            standard_version="1.0.0",
            pattern="TIPO-SEDE-AÑO-CORRELATIVO",
            examples=examples,
        )

    def list_site_codes(self, organization_id: UUID) -> list[DocumentSiteCodeResponse]:
        site_codes = self.site_repo.list_by_organization(organization_id)
        return [DocumentSiteCodeResponse.model_validate(sc) for sc in site_codes]
