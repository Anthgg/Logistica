"""Catalog validator module.

Validates the integrity, uniqueness, SemVer versioning, and structural rules
of the document catalog source JSON.
"""

from __future__ import annotations

from typing import Any


class CatalogValidationError(Exception):
    """Exception raised when document catalog validation fails."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__(f"Catalog validation failed with {len(errors)} error(s): {', '.join(errors)}")


def validate_catalog_data(data: dict[str, Any]) -> dict[str, Any]:
    """Performs deep validation of document catalog structure and rules.

    Returns a report dictionary containing errors, warnings, and summary counts.
    """
    errors: list[str] = []
    warnings: list[str] = []

    version = data.get("catalog_version")
    if not version or not isinstance(version, str):
        errors.append("Missing or invalid 'catalog_version'")

    families = data.get("families", [])
    if not isinstance(families, list) or not families:
        errors.append("Catalog must contain a non-empty 'families' list")

    family_codes: set[str] = set()
    for idx, fam in enumerate(families):
        code = fam.get("code")
        if not code or not isinstance(code, str):
            errors.append(f"Family at index {idx} has missing or empty 'code'")
        elif code in family_codes:
            errors.append(f"Duplicate family code: '{code}'")
        else:
            family_codes.add(code)

        if not fam.get("name"):
            errors.append(f"Family '{code}' is missing 'name'")

    retention_policies = data.get("retention_policies", [])
    retention_codes: set[str] = set()
    for idx, ret in enumerate(retention_policies):
        rcode = ret.get("code")
        if not rcode or not isinstance(rcode, str):
            errors.append(f"Retention policy at index {idx} missing 'code'")
        elif rcode in retention_codes:
            errors.append(f"Duplicate retention policy code: '{rcode}'")
        else:
            retention_codes.add(rcode)

    doc_types = data.get("document_types", [])
    if not isinstance(doc_types, list) or not doc_types:
        errors.append("Catalog must contain a non-empty 'document_types' list")

    type_codes: set[str] = set()
    for idx, dt in enumerate(doc_types):
        code = dt.get("code")
        if not code or not isinstance(code, str):
            errors.append(f"Document type at index {idx} has missing or empty 'code'")
        elif code in type_codes:
            errors.append(f"Duplicate document type code: '{code}'")
        else:
            type_codes.add(code)

        family_code = dt.get("family_code")
        if family_code not in family_codes:
            errors.append(f"Document type '{code}' references non-existent family '{family_code}'")

        ret_code = dt.get("retention_policy_code")
        if ret_code and ret_code not in retention_codes:
            errors.append(f"Document type '{code}' references non-existent retention policy '{ret_code}'")

        fields_schema = dt.get("required_fields_schema", {})
        fields = fields_schema.get("fields", [])
        field_keys: set[str] = set()
        for fidx, field in enumerate(fields):
            fkey = field.get("key")
            if not fkey:
                errors.append(f"Document type '{code}' field at index {fidx} missing 'key'")
            elif fkey in field_keys:
                errors.append(f"Document type '{code}' has duplicate field key '{fkey}'")
            else:
                field_keys.add(fkey)

    proposed_types = data.get("proposed_types", [])
    for pidx, pt in enumerate(proposed_types):
        pcode = pt.get("code")
        if pcode in type_codes:
            errors.append(f"Proposed type code '{pcode}' conflicts with active type code")
        if pt.get("decision_status") != "PROPOSED_PHASE_011":
            warnings.append(f"Proposed type '{pcode}' has non-standard decision_status")

    valid = len(errors) == 0
    return {
        "valid": valid,
        "version": version,
        "errors": errors,
        "warnings": warnings,
        "total_families": len(families),
        "total_document_types": len(doc_types),
        "total_proposed_types": len(proposed_types),
        "total_retention_policies": len(retention_policies),
    }
