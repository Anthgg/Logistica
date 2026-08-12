"""Domain Value Objects and Validation Logic for Document Codes (Phase 012).

Standard Pattern: TIPO-SEDE-AÑO-CORRELATIVO (e.g. OC-LIM-2026-000001)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re
from typing import Any, NamedTuple
import zoneinfo

DOCUMENT_CODE_REGEX = re.compile(r"^[A-Z0-9]{2,8}-[A-Z0-9]{2,10}-[0-9]{4}-[0-9]{6}$")


class DocumentCodeValidationError(ValueError):
    """Exception raised when document code formatting or parsing fails."""


@dataclass(frozen=True)
class DocumentInternalCodeParts:
    document_type_code: str
    site_code: str
    year: int
    sequence: int

    def __str__(self) -> str:
        return f"{self.document_type_code}-{self.site_code}-{self.year:04d}-{self.sequence:06d}"


class DocumentCodeFormatter:
    @staticmethod
    def format(
        document_type_code: str,
        site_code: str,
        year: int,
        sequence: int,
    ) -> str:
        doc_type_clean = document_type_code.strip().upper()
        site_clean = site_code.strip().upper()

        if not (2 <= len(doc_type_clean) <= 8) or not doc_type_clean.isalnum():
            raise DocumentCodeValidationError(f"Invalid document_type_code segment: '{document_type_code}'")
        if not (2 <= len(site_clean) <= 10) or not site_clean.isalnum():
            raise DocumentCodeValidationError(f"Invalid site_code segment: '{site_code}'")
        if not (2000 <= year <= 2100):
            raise DocumentCodeValidationError(f"Invalid year segment: '{year}'")
        if not (1 <= sequence <= 999999):
            raise DocumentCodeValidationError(f"Invalid sequence segment (must be 1..999999): '{sequence}'")

        formatted = f"{doc_type_clean}-{site_clean}-{year:04d}-{sequence:06d}"
        if not DOCUMENT_CODE_REGEX.match(formatted):
            raise DocumentCodeValidationError(f"Formatted code failed regex check: '{formatted}'")
        return formatted


class DocumentCodeParser:
    @staticmethod
    def parse(code: str, strict: bool = True) -> DocumentInternalCodeParts:
        raw = code.strip()
        if strict and not DOCUMENT_CODE_REGEX.match(raw):
            raise DocumentCodeValidationError(f"Code does not match standard pattern TIPO-SEDE-AÑO-CORRELATIVO: '{code}'")

        parts = raw.split("-")
        if len(parts) != 4:
            raise DocumentCodeValidationError(f"Invalid number of code segments in '{code}' (expected 4)")

        doc_type_code, site_code, year_str, seq_str = parts

        try:
            year = int(year_str)
            seq = int(seq_str)
        except ValueError as exc:
            raise DocumentCodeValidationError(f"Invalid integer segment in code '{code}'") from exc

        if seq == 0:
            raise DocumentCodeValidationError("Sequence segment cannot be 000000")

        return DocumentInternalCodeParts(
            document_type_code=doc_type_code.upper(),
            site_code=site_code.upper(),
            year=year,
            sequence=seq,
        )


class DocumentCodeNormalizer:
    @staticmethod
    def normalize(code: str) -> str:
        parts = DocumentCodeParser.parse(code, strict=False)
        return DocumentCodeFormatter.format(
            document_type_code=parts.document_type_code,
            site_code=parts.site_code,
            year=parts.year,
            sequence=parts.sequence,
        )


class DocumentCodeValidator:
    @staticmethod
    def validate_structure(code: str) -> dict[str, Any]:
        errors: list[str] = []
        parsed_parts: DocumentInternalCodeParts | None = None
        normalized: str | None = None

        try:
            parsed_parts = DocumentCodeParser.parse(code, strict=True)
            normalized = str(parsed_parts)
        except DocumentCodeValidationError as err:
            errors.append(str(err))

        return {
            "valid": len(errors) == 0,
            "code": code,
            "normalized_code": normalized,
            "standard_version": "1.0.0",
            "errors": errors,
            "parts": {
                "document_type_code": parsed_parts.document_type_code if parsed_parts else None,
                "site_code": parsed_parts.site_code if parsed_parts else None,
                "year": parsed_parts.year if parsed_parts else None,
                "sequence": parsed_parts.sequence if parsed_parts else None,
            } if parsed_parts else None,
        }


class YearResolverService:
    @staticmethod
    def resolve_year(issued_at: datetime | None = None, tz_name: str = "America/Lima") -> int:
        target_dt = issued_at if issued_at else datetime.now(timezone.utc)
        try:
            local_tz = zoneinfo.ZoneInfo(tz_name)
            local_dt = target_dt.astimezone(local_tz)
            return local_dt.year
        except Exception:
            return target_dt.year
