"""Separación de funciones (SoD) para roles logísticos — Fase 005.

El modelo de conflictos ya existía (`logistics_role_conflict_rules`, pares de roles)
pero estaba vacío y solo se consultaba al asignar roles a un usuario. F005 lo puebla
con reglas justificadas y añade el segundo punto de control que faltaba: la
**composición** de un rol personalizado.

Cómo se deriva un conflicto de permisos a partir de reglas expresadas en roles:

    regla activa (A, B)
        ↓
    permisos exclusivos de A  = perms(A) - perms(B)
    permisos exclusivos de B  = perms(B) - perms(A)
        ↓
    un rol candidato entra en conflicto si toma al menos un permiso
    exclusivo de cada lado

Es decir, el conflicto salta cuando el rol reúne de verdad las dos potestades
incompatibles, no cuando simplemente comparte permisos comunes a ambos —que los hay,
como leer un almacén—. Así no hace falta una segunda tabla de conflictos a nivel de
permiso: las reglas siguen viviendo donde ya vivían.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.logistics.rbac.models_conflict import LogisticsRoleConflictRule
from app.modules.logistics.rbac.models_permission import LogisticsPermission
from app.modules.logistics.rbac.models_role import LogisticsRole
from app.modules.logistics.rbac.models_role_permission import LogisticsRolePermission

#: Reglas canónicas de F005.
#:
#: Cada una separa quien ORIGINA una operación de quien la APRUEBA, CONTROLA o
#: AUDITA. Solo se declaran sobre roles que ya existen y cuyos permisos ya están
#: sembrados; no se inventan conflictos de fases futuras.
CANONICAL_SOD_RULES: list[dict[str, str]] = [
    {
        "rule_code": "SOD_PURCHASE_ORIGINATE_APPROVE",
        "role_a_code": "PURCHASING",
        "role_b_code": "PURCHASING_APPROVER",
        "conflict_type": "originate_approve",
        "description": (
            "Quien origina una solicitud o pedido de compra no puede además aprobarlo: "
            "una sola persona cerraría el ciclo de gasto sin contraparte."
        ),
    },
    {
        "rule_code": "SOD_RECEIVE_QUALITY_DECIDE",
        "role_a_code": "RECEIVING",
        "role_b_code": "QUALITY",
        "conflict_type": "execute_control",
        "description": (
            "Quien recepciona la mercadería no puede además dictaminar su conformidad "
            "de calidad: el control dejaría de ser independiente de la ejecución."
        ),
    },
    {
        "rule_code": "SOD_INVENTORY_ADJUST_AUDIT",
        "role_a_code": "INVENTORY_CONTROLLER",
        "role_b_code": "LOGISTICS_AUDITOR",
        "conflict_type": "execute_audit",
        "description": (
            "Quien ajusta inventario no puede auditar esos mismos ajustes: revisaría "
            "su propio trabajo."
        ),
    },
]


@dataclass(frozen=True)
class SodConflict:
    """Conflicto concreto, con las acciones que lo provocan."""

    rule_code: str
    role_a_code: str
    role_b_code: str
    reason: str
    conflicting_permissions: tuple[str, ...]


def _permission_codes_by_role(db: Session, role_ids: list[UUID]) -> dict[UUID, set[str]]:
    if not role_ids:
        return {}
    rows = (
        db.query(LogisticsRolePermission.role_id, LogisticsPermission.code)
        .join(LogisticsPermission, LogisticsPermission.id == LogisticsRolePermission.permission_id)
        .filter(LogisticsRolePermission.role_id.in_(role_ids))
        .all()
    )
    out: dict[UUID, set[str]] = {rid: set() for rid in role_ids}
    for role_id, code in rows:
        out.setdefault(role_id, set()).add(code)
    return out


def active_rules(db: Session) -> list[tuple[LogisticsRoleConflictRule, LogisticsRole, LogisticsRole]]:
    """Reglas activas junto con los dos roles que enfrentan."""
    rules = (
        db.query(LogisticsRoleConflictRule)
        .filter(LogisticsRoleConflictRule.status == "active")
        .all()
    )
    if not rules:
        return []
    role_ids = {r.role_a_id for r in rules} | {r.role_b_id for r in rules}
    roles = {
        r.id: r
        for r in db.query(LogisticsRole).filter(LogisticsRole.id.in_(list(role_ids))).all()
    }
    resolved = []
    for rule in rules:
        role_a = roles.get(rule.role_a_id)
        role_b = roles.get(rule.role_b_id)
        if role_a and role_b:
            resolved.append((rule, role_a, role_b))
    return resolved


def check_permission_composition(
    db: Session, permission_codes: set[str], *, exclude_role_id: UUID | None = None
) -> list[SodConflict]:
    """Conflictos que provoca reunir `permission_codes` en un mismo rol.

    `exclude_role_id` evita que un rol se declare en conflicto consigo mismo cuando
    se reeditan sus propios permisos.
    """
    conflicts: list[SodConflict] = []
    for rule, role_a, role_b in active_rules(db):
        if exclude_role_id in (role_a.id, role_b.id):
            continue
        perms = _permission_codes_by_role(db, [role_a.id, role_b.id])
        only_a = perms.get(role_a.id, set()) - perms.get(role_b.id, set())
        only_b = perms.get(role_b.id, set()) - perms.get(role_a.id, set())

        taken_a = sorted(permission_codes & only_a)
        taken_b = sorted(permission_codes & only_b)
        if taken_a and taken_b:
            conflicts.append(
                SodConflict(
                    rule_code=_rule_code(rule, role_a, role_b),
                    role_a_code=role_a.code,
                    role_b_code=role_b.code,
                    reason=rule.description,
                    # Se muestran unos pocos de cada lado: la lista completa puede
                    # tener cientos de códigos y no ayuda a entender el conflicto.
                    conflicting_permissions=tuple(taken_a[:5] + taken_b[:5]),
                )
            )
    return conflicts


def _rule_code(rule: LogisticsRoleConflictRule, role_a: LogisticsRole, role_b: LogisticsRole) -> str:
    for canonical in CANONICAL_SOD_RULES:
        if {canonical["role_a_code"], canonical["role_b_code"]} == {role_a.code, role_b.code}:
            return canonical["rule_code"]
    return f"SOD_{rule.conflict_type.upper()}"


def seed_canonical_rules(db: Session) -> dict[str, int]:
    """Siembra las reglas canónicas. Idempotente: reejecutarla no duplica nada."""
    created = 0
    skipped = 0
    missing_roles = 0
    for spec in CANONICAL_SOD_RULES:
        role_a = db.query(LogisticsRole).filter(LogisticsRole.code == spec["role_a_code"]).first()
        role_b = db.query(LogisticsRole).filter(LogisticsRole.code == spec["role_b_code"]).first()
        if not role_a or not role_b:
            missing_roles += 1
            continue
        existing = (
            db.query(LogisticsRoleConflictRule)
            .filter(
                LogisticsRoleConflictRule.role_a_id.in_([role_a.id, role_b.id]),
                LogisticsRoleConflictRule.role_b_id.in_([role_a.id, role_b.id]),
            )
            .first()
        )
        if existing:
            skipped += 1
            continue
        db.add(
            LogisticsRoleConflictRule(
                role_a_id=role_a.id,
                role_b_id=role_b.id,
                conflict_type=spec["conflict_type"],
                description=spec["description"],
                status="active",
            )
        )
        created += 1
    db.flush()
    return {"created": created, "skipped": skipped, "missing_roles": missing_roles}
