"""Contrato de permisos para el frontend, derivado del catálogo canónico.

El frontend necesita saber qué códigos existen, con qué riesgo y si exigen verificación
reforzada. No necesita las descripciones ni la matriz de roles, así que este artefacto
no las lleva: es el mismo catálogo, recortado a lo que un cliente puede usar.

Existe porque mantener la lista a mano no funcionó. El frontend llegó a declarar 131
códigos que el backend no conocía —23 de ellos exigidos por pantallas vivas, es decir
funciones ocultas para todo el mundo sin que nada avisara— y F006 PR 3.1 tuvo que
reconciliarlos uno a uno. Con el contrato generado, un código inventado deja de compilar
en el frontend en lugar de convertirse en una pantalla vacía.

La fuente sigue siendo ``rbac/permission_catalog.py``. Este script no decide nada.

Uso:
    python scripts/generate_permission_contract.py --out ../docs/phase-006/permission-contract.json
    python scripts/generate_permission_contract.py --check ../docs/phase-006/permission-contract.json
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys


def current_commit() -> str:
    """SHA del que se generó el contrato, para que el frontend pueda anclarse a él."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "UNKNOWN"


def build_contract(backend_sha: str) -> dict[str, object]:
    from app.modules.logistics.rbac.permission_catalog import CATALOG_VERSION, PERMISSIONS
    from app.modules.logistics.security.step_up_policy import POLICY_CATALOG

    permissions = [
        {
            "code": str(p["code"]),
            "risk": str(p["risk_level"]),
            "requires_step_up": str(p["code"]) in POLICY_CATALOG,
            "is_sensitive": bool(p.get("is_sensitive", False)),
        }
        for p in sorted(PERMISSIONS, key=lambda x: str(x["code"]))
    ]
    return {
        "_comment": (
            "Artefacto DERIVADO del catalogo canonico del backend "
            "(rbac/permission_catalog.py), generado por "
            "backend/scripts/generate_permission_contract.py. No editar a mano."
        ),
        "backend_sha": backend_sha,
        "catalog_version": CATALOG_VERSION,
        "total_permissions": len(permissions),
        "permissions": permissions,
    }


def render(contract: dict[str, object]) -> str:
    return json.dumps(contract, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Contrato de permisos para el frontend.")
    parser.add_argument("--out", default=None, help="Ruta donde escribir el contrato.")
    parser.add_argument(
        "--check",
        default=None,
        help="Comprobar que el fichero dado corresponde al catálogo actual.",
    )
    parser.add_argument(
        "--sha",
        default=None,
        help="SHA a registrar (por defecto, el HEAD actual).",
    )
    args = parser.parse_args()

    if not args.out and not args.check:
        parser.error("indica --out o --check")

    if args.check:
        path = pathlib.Path(args.check)
        if not path.exists():
            print(f"FAIL: no existe {path}", file=sys.stderr)
            return 1
        existing = json.loads(path.read_text(encoding="utf-8"))
        # El SHA cambia en cada commit y no dice nada sobre el contenido: lo que debe
        # coincidir es el catálogo.
        expected = build_contract(str(existing.get("backend_sha", "UNKNOWN")))
        if render(expected) != path.read_text(encoding="utf-8"):
            print(
                "GENERATED_PERMISSION_CONTRACT_DRIFT=1\n"
                f"FAIL: {path} no corresponde al catálogo actual.\n"
                "Regenéralo con: python scripts/generate_permission_contract.py "
                f"--out {path}",
                file=sys.stderr,
            )
            return 1
        print("GENERATED_PERMISSION_CONTRACT_DRIFT=0")
        return 0

    contract = build_contract(args.sha or current_commit())
    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(contract), encoding="utf-8")
    print(
        f"Contrato escrito en {out}: "
        f"{contract['total_permissions']} permisos (catálogo {contract['catalog_version']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
