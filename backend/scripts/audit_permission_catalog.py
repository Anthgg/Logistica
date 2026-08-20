"""Integridad del catálogo de permisos y artefactos derivados (Fase 006 PR 2).

El catálogo canónico vive en ``rbac/permission_catalog.py``. Este script no es una
segunda fuente de verdad: lee esa y comprueba invariantes, o exporta un artefacto
legible por máquina derivado de ella. Si alguna vez divergen, es que alguien editó el
artefacto a mano, que es justamente lo que no debe pasar.

Comprobaciones:

* códigos duplicados, con y sin distinguir mayúsculas;
* referencias desde el código a permisos que no existen;
* metadata obligatoria presente en cada permiso;
* convención de nomenclatura;
* cada permiso con step-up tiene política;
* la matriz de roles cubre exactamente los roles de sistema, sin ninguno vacío.

Uso:
    python scripts/audit_permission_catalog.py
    python scripts/audit_permission_catalog.py --check
    python scripts/audit_permission_catalog.py --export docs/phase-006/permission_catalog.json
"""

from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
import sys

#: Claves que todo permiso canónico debe traer explícitas. El resto tiene valor por
#: defecto en el modelo y no hace falta repetirlo 549 veces.
REQUIRED_METADATA = ("code", "resource", "action", "name", "description", "category", "risk_level")

#: Riesgos admitidos.
VALID_RISK_LEVELS = frozenset({"low", "medium", "high", "critical"})

#: Convención: minúsculas separadas por puntos, con al menos dominio y acción.
CODE_PATTERN = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z0-9_]+)+$")

#: Cómo se referencia un permiso desde el código. `require_capability` cubre el libro
#: de inventario, que no usa `require_permission` — ignorarlo daba por huérfanos
#: permisos que sí se usan.
REFERENCE_PATTERNS = (
    re.compile(r"require_permission\(\s*[\"']([^\"']+)[\"']"),
    re.compile(r"require_capability\(\s*[\"']([^\"']+)[\"']"),
    re.compile(r"has_permission\(\s*[\"']([^\"']+)[\"']"),
    re.compile(r"has_any_permission\(\s*[\"']([^\"']+)[\"']"),
)


def code_references(root: pathlib.Path) -> collections.Counter[str]:
    found: collections.Counter[str] = collections.Counter()
    for file in root.rglob("*.py"):
        if "__pycache__" in str(file):
            continue
        text = file.read_text(encoding="utf-8", errors="replace")
        for pattern in REFERENCE_PATTERNS:
            for match in pattern.finditer(text):
                found[match.group(1)] += 1
    return found


def build_report() -> tuple[dict[str, object], list[str]]:
    from app.modules.logistics.rbac.catalog import SYSTEM_ROLES
    from app.modules.logistics.rbac.permission_catalog import (
        CATALOG_VERSION,
        PERMISSIONS,
        ROLE_PERMISSION_MATRIX,
    )
    from app.modules.logistics.security.step_up_policy import POLICY_CATALOG

    problems: list[str] = []
    codes = [str(p["code"]) for p in PERMISSIONS]
    catalog = set(codes)

    duplicates = sorted(c for c, n in collections.Counter(codes).items() if n > 1)
    if duplicates:
        problems.append(f"códigos duplicados: {duplicates}")

    case_collisions = sorted(
        c for c, n in collections.Counter(c.lower() for c in codes).items() if n > 1
    )
    if case_collisions:
        problems.append(f"códigos que solo difieren en mayúsculas: {case_collisions}")

    missing_metadata = [
        f"{p.get('code', '<sin código>')}:{key}"
        for p in PERMISSIONS
        for key in REQUIRED_METADATA
        if not p.get(key)
    ]
    if missing_metadata:
        problems.append(f"metadata obligatoria ausente: {missing_metadata[:10]}")

    bad_risk = sorted({str(p["code"]) for p in PERMISSIONS if str(p["risk_level"]) not in VALID_RISK_LEVELS})
    if bad_risk:
        problems.append(f"riesgo fuera del vocabulario: {bad_risk[:10]}")

    bad_naming = sorted(c for c in catalog if not CODE_PATTERN.fullmatch(c))
    if bad_naming:
        problems.append(f"códigos fuera de convención: {bad_naming[:10]}")

    references = code_references(pathlib.Path("app"))
    unknown = sorted(set(references) - catalog)
    if unknown:
        problems.append(f"referencias a permisos inexistentes: {unknown}")

    step_up = {str(p["code"]) for p in PERMISSIONS if p.get("requires_step_up")}
    without_policy = sorted(step_up - set(POLICY_CATALOG))
    if without_policy:
        problems.append(f"permisos con step-up sin política: {without_policy[:10]}")

    system_roles = {str(r["code"]) for r in SYSTEM_ROLES}
    roles_without_permissions = sorted(system_roles - set(ROLE_PERMISSION_MATRIX))
    if roles_without_permissions:
        problems.append(f"roles de sistema sin permisos: {roles_without_permissions}")
    orphan_mappings = sorted(set(ROLE_PERMISSION_MATRIX) - system_roles)
    if orphan_mappings:
        problems.append(f"mappings de roles inexistentes: {orphan_mappings}")
    empty_roles = sorted(code for code, perms in ROLE_PERMISSION_MATRIX.items() if not perms)
    if empty_roles:
        problems.append(f"roles sin ningún permiso: {empty_roles}")

    assigned = {code for perms in ROLE_PERMISSION_MATRIX.values() for code in perms}
    report = {
        "catalog_version": CATALOG_VERSION,
        "total_permissions": len(PERMISSIONS),
        "duplicate_codes": len(duplicates),
        "unknown_references": len(unknown),
        "distinct_references": len(references),
        "step_up_permissions": len(step_up),
        "step_up_with_policy": len(step_up & set(POLICY_CATALOG)),
        "domains": sorted({str(p["category"]) for p in PERMISSIONS}),
        "risk_distribution": dict(collections.Counter(str(p["risk_level"]) for p in PERMISSIONS)),
        "role_permission_mappings": sum(len(v) for v in ROLE_PERMISSION_MATRIX.values()),
        "classification": {
            # Un permiso "usado" no es solo el que aparece en `require_permission`:
            # también cuenta el que algún rol concede, o el que un guard por capacidad
            # exige. Mirar una sola vía convertía en huérfanos permisos vivos.
            "ACTIVE_USED": len(catalog & set(references)),
            "ACTIVE_ASSIGNED": len((catalog & assigned) - set(references)),
            "ORPHAN_CANDIDATE": len(catalog - set(references) - assigned),
        },
        "permissions": [
            {
                "code": str(p["code"]),
                "domain": str(p["category"]),
                "resource": str(p["resource"]),
                "action": str(p["action"]),
                "description": str(p["description"]),
                "risk": str(p["risk_level"]),
                "requires_step_up": str(p["code"]) in POLICY_CATALOG,
                "requires_reason": bool(p.get("requires_reason", False)),
                "is_sensitive": bool(p.get("is_sensitive", False)),
                "referenced_in_code": references.get(str(p["code"]), 0),
                "granted_by_roles": sorted(
                    role for role, perms in ROLE_PERMISSION_MATRIX.items() if str(p["code"]) in perms
                ),
            }
            for p in sorted(PERMISSIONS, key=lambda x: str(x["code"]))
        ],
    }
    return report, problems


def main() -> int:
    parser = argparse.ArgumentParser(description="Integridad del catálogo de permisos.")
    parser.add_argument("--check", action="store_true", help="Salir con error si hay problemas.")
    parser.add_argument("--export", default=None, help="Escribir el catálogo derivado en JSON.")
    args = parser.parse_args()

    report, problems = build_report()

    print(f"CATALOG_VERSION            = {report['catalog_version']}")
    print(f"TOTAL_PERMISSIONS          = {report['total_permissions']}")
    print(f"DUPLICATE_PERMISSION_CODES = {report['duplicate_codes']}")
    print(f"UNKNOWN_PERMISSION_REFERENCES = {report['unknown_references']}")
    print(f"STEP_UP_PERMISSIONS        = {report['step_up_permissions']}")
    print(f"STEP_UP_WITH_POLICY        = {report['step_up_with_policy']}")
    print(f"ROLE_PERMISSION_MAPPINGS   = {report['role_permission_mappings']}")
    print(f"DOMAINS                    = {len(report['domains'])}")
    print(f"RISK_DISTRIBUTION          = {report['risk_distribution']}")
    print(f"CLASSIFICATION             = {report['classification']}")

    if args.export:
        path = pathlib.Path(args.export)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2, sort_keys=True)
        print(f"\nCatálogo derivado escrito en {path}")

    if problems:
        print(f"\nPROBLEMAS = {len(problems)}", file=sys.stderr)
        for problem in problems:
            print(f"  FAIL: {problem}", file=sys.stderr)
        if args.check:
            print("\nRESULTADO=FAIL", file=sys.stderr)
            return 1

    print("\nRESULTADO=OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
