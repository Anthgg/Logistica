"""Auditoría de cobertura de autorización por endpoint (Fase 006).

Recorre las rutas reales de la aplicación FastAPI —no el OpenAPI, que no dice quién
protege qué— e inspecciona el árbol de dependencias de cada operación para determinar
con qué se protege. El resultado es verificable y se regenera solo: una hoja mantenida
a mano queda obsoleta en el siguiente endpoint.

Clasificación de cada operación:

    PUBLIC              sin ninguna dependencia de autenticación
    AUTH_ONLY           exige sesión, pero no comprueba permisos
    ROLE_PROTECTED      autoriza por nombre de rol (antipatrón: no usa el catálogo)
    PERMISSION_PROTECTED  exige uno o más permisos del catálogo

Además señala las operaciones **mutadoras** que solo exigen sesión, que son las que
importan: una lectura sin permiso puede ser una decisión de diseño, pero un POST que
cambia datos de negocio y solo pide estar logueado casi nunca lo es.

Uso:
    python scripts/audit_permission_coverage.py
    python scripts/audit_permission_coverage.py --json artefacto.json
    python scripts/audit_permission_coverage.py --check   # falla si hay hallazgos
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import asdict, dataclass, field
from typing import Any

#: Métodos que modifican estado. Un GET sin permiso puede justificarse; un POST rara vez.
MUTATING_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})

#: Prefijos cuyo contenido es de negocio. Fuera de aquí viven salud, auth y utilidades.
BUSINESS_PREFIXES = ("/api/logistics", "/api/inventory", "/api/purchase", "/api/documents")

#: Operaciones que legítimamente no exigen sesión.
PUBLIC_ALLOWLIST = frozenset(
    {
        "/health",
        "/api/health",
        "/api/health/live",
        "/api/health/ready",
        "/api/auth/login",
        "/api/auth/register",
        "/api/auth/csrf",
        "/api/auth/refresh",
        "/api/auth/logout",
        "/openapi.json",
        "/docs",
        "/docs/oauth2-redirect",
        "/redoc",
    }
)

#: Operaciones mutadoras de negocio que hoy solo exigen sesión. F006 PR 1 cerró las
#: que no pedían ni sesión; estas son una categoría distinta y se abordan en PR 2.
#: El número solo puede bajar.
MAX_SENSITIVE_BASELINE = 25

AUTH_DEPENDENCY_NAMES = frozenset(
    {
        "get_current_user",
        "get_current_session",
        "require_active_user",
        "get_logistics_principal",
        "require_logistics_principal",
        "require_logistics_access",
    }
)


@dataclass
class Operation:
    method: str
    path: str
    operation_id: str | None
    auth_class: str
    permissions: list[str] = field(default_factory=list)
    roles: list[str] = field(default_factory=list)
    mutating: bool = False
    business: bool = False


def closure_values(func: Any) -> list[Any]:
    """Valores capturados por un closure. Es donde viven los códigos de permiso."""
    cells = getattr(func, "__closure__", None)
    if not cells:
        return []
    values: list[Any] = []
    for cell in cells:
        try:
            values.append(cell.cell_contents)
        except ValueError:  # celda todavía sin asignar
            continue
    return values


def flatten_strings(values: list[Any]) -> list[str]:
    out: list[str] = []
    for v in values:
        if isinstance(v, str):
            out.append(v)
        elif isinstance(v, (tuple, list, set, frozenset)):
            out.extend(x for x in v if isinstance(x, str))
    return out


def walk_dependant(dependant: Any, seen: set[int] | None = None):
    """Recorre el árbol de dependencias completo, no solo el primer nivel."""
    if seen is None:
        seen = set()
    if id(dependant) in seen:
        return
    seen.add(id(dependant))
    yield dependant
    for sub in getattr(dependant, "dependencies", []):
        yield from walk_dependant(sub, seen)


def inspect_callable(call: Any) -> tuple[bool, list[str], list[str]]:
    """Devuelve (exige sesión, permisos exigidos, roles exigidos) para una dependencia."""
    name = getattr(call, "__name__", "")
    qual = getattr(call, "__qualname__", "")

    if name in AUTH_DEPENDENCY_NAMES:
        return True, [], []
    # Las fábricas devuelven un closure llamado `dependency`; el nombre real de la
    # fábrica sobrevive en __qualname__.
    if "require_logistics_permission" in qual or "require_permission" in qual:
        return True, flatten_strings(closure_values(call)), []
    if "require_permissions" in qual:
        return True, [], flatten_strings(closure_values(call))
    return False, [], []


#: El libro de inventario no usa `require_permission`: marca cada handler con
#: `@require_capability(...)`, que deja el código en un atributo de la función y lo
#: exige una dependencia a nivel de router. Sin mirar ese atributo, sus operaciones
#: parecerían protegidas solo por sesión.
CAPABILITY_ATTRIBUTES = ("__inventory_capability__",)


def endpoint_capabilities(route: Any) -> list[str]:
    endpoint = getattr(route, "endpoint", None)
    if endpoint is None:
        return []
    return [
        value
        for attribute in CAPABILITY_ATTRIBUTES
        if isinstance(value := getattr(endpoint, attribute, None), str)
    ]


def classify(route: Any, full_path: str, extra_dependencies: list[Any]) -> Operation:
    method = min(route.methods - {"HEAD", "OPTIONS"}, default="GET")

    permissions: list[str] = list(endpoint_capabilities(route))
    roles: list[str] = []
    has_auth = False

    for dep in walk_dependant(route.dependant):
        call = getattr(dep, "call", None)
        if call is None:
            continue
        auth, perms, rls = inspect_callable(call)
        has_auth = has_auth or auth
        permissions.extend(perms)
        roles.extend(rls)

    # Guards aplicados al incluir el router: protegen todas sus rutas por igual y no
    # aparecen en el dependant de cada operación.
    for dependency in extra_dependencies:
        call = getattr(dependency, "dependency", None)
        if call is None:
            continue
        auth, perms, rls = inspect_callable(call)
        has_auth = has_auth or auth
        permissions.extend(perms)
        roles.extend(rls)

    permissions = sorted({p for p in permissions if "." in p})
    roles = sorted(set(roles))

    if permissions:
        auth_class = "PERMISSION_PROTECTED"
    elif roles:
        auth_class = "ROLE_PROTECTED"
    elif has_auth:
        auth_class = "AUTH_ONLY"
    else:
        auth_class = "PUBLIC"

    return Operation(
        method=method,
        path=full_path,
        operation_id=getattr(route, "operation_id", None) or getattr(route, "name", None),
        auth_class=auth_class,
        permissions=permissions,
        roles=roles,
        mutating=method in MUTATING_METHODS,
        business=full_path.startswith(BUSINESS_PREFIXES),
    )


def collect() -> list[Operation]:
    """Recorre el árbol de routers.

    FastAPI 0.141 incluye los routers de forma perezosa (`_IncludedRouter`), así que
    `app.routes` solo muestra el primer nivel. Hay que descender y componer el prefijo
    y las dependencias de cada nivel para obtener la ruta real y sus guards.
    """
    from app.main import app

    ops: list[Operation] = []
    seen: set[tuple[str, str]] = set()

    def visit(routes: list[Any], prefix: str, inherited: list[Any]) -> None:
        for route in routes:
            if type(route).__name__ == "_IncludedRouter":
                context = route.include_context
                visit(
                    route.original_router.routes,
                    prefix + (getattr(context, "prefix", "") or ""),
                    inherited + list(getattr(context, "dependencies", []) or []),
                )
                continue
            if not hasattr(route, "dependant") or not getattr(route, "methods", None):
                continue
            full_path = prefix + route.path
            op = classify(route, full_path, inherited)
            key = (op.method, op.path)
            if key in seen:
                continue
            seen.add(key)
            ops.append(op)

    visit(app.routes, "", [])
    return ops


def main() -> int:
    parser = argparse.ArgumentParser(description="Auditoría de cobertura de autorización.")
    parser.add_argument("--json", dest="json_path", default=None, help="Volcar el detalle a un fichero.")
    parser.add_argument("--check", action="store_true", help="Salir con error si hay hallazgos.")
    parser.add_argument(
        "--max-sensitive",
        type=int,
        default=MAX_SENSITIVE_BASELINE,
        help=(
            "Máximo de operaciones mutadoras de negocio protegidas solo por sesión. "
            "Es un trinquete: no puede subir, y cada fase que cierre alguna lo baja."
        ),
    )
    args = parser.parse_args()

    ops = collect()
    by_class = Counter(o.auth_class for o in ops)

    print(f"TOTAL_API_OPERATIONS            = {len(ops)}")
    for cls in ("PUBLIC", "AUTH_ONLY", "ROLE_PROTECTED", "PERMISSION_PROTECTED"):
        print(f"{cls + '_OPERATIONS':32s}= {by_class.get(cls, 0)}")

    unexpected_public = [o for o in ops if o.auth_class == "PUBLIC" and o.path not in PUBLIC_ALLOWLIST]
    sensitive_unprotected = [
        o for o in ops if o.auth_class == "AUTH_ONLY" and o.mutating and o.business
    ]
    role_protected = [o for o in ops if o.auth_class == "ROLE_PROTECTED"]

    print(f"\nUNEXPECTED_PUBLIC_OPERATIONS    = {len(unexpected_public)}")
    for o in unexpected_public[:20]:
        print(f"    {o.method:6s} {o.path}")

    print(f"\nSENSITIVE_OPERATIONS_WITHOUT_PERMISSION = {len(sensitive_unprotected)}")
    for o in sensitive_unprotected[:30]:
        print(f"    {o.method:6s} {o.path}")

    print(f"\nROLE_PROTECTED_OPERATIONS       = {len(role_protected)}")
    for o in role_protected[:20]:
        print(f"    {o.method:6s} {o.path}  roles={o.roles}")

    if args.json_path:
        payload = {
            "total_operations": len(ops),
            "by_auth_class": dict(by_class),
            "operations": [asdict(o) for o in sorted(ops, key=lambda x: (x.path, x.method))],
        }
        with open(args.json_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2, sort_keys=True)
        print(f"\nDetalle escrito en {args.json_path}")

    if args.check and (unexpected_public or sensitive_unprotected):
        print("\nRESULTADO=FAIL", file=sys.stderr)
        return 1

    print("\nRESULTADO=OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
