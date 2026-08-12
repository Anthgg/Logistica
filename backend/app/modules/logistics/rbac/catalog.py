"""Logistics role catalog constants — system roles and their allowed scopes."""

from enum import StrEnum


class ScopeType(StrEnum):
    GLOBAL = "global"
    ORGANIZATION = "organization"
    BRANCH = "branch"
    WAREHOUSE = "warehouse"


class AssignmentStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    REVOKED = "revoked"
    EXPIRED = "expired"
    SCHEDULED = "scheduled"


class ConflictType(StrEnum):
    PROHIBITED = "prohibited"
    REQUIRES_REVIEW = "requires_review"
    ALLOWED_WITH_CONTROL = "allowed_with_control"
    ALLOWED = "allowed"


# ---------------------------------------------------------------------------
# System role definitions
# ---------------------------------------------------------------------------

SYSTEM_ROLES: list[dict[str, object]] = [
    {
        "code": "LOGISTICS_ADMIN",
        "name": "Administrador logístico",
        "description": "Configuración general del dominio logístico y administración controlada de roles.",
        "allowed_scopes": [ScopeType.GLOBAL, ScopeType.ORGANIZATION],
    },
    {
        "code": "LOGISTICS_MANAGER",
        "name": "Gerencia logística",
        "description": "Supervisión general, consultas y aprobaciones de alto nivel.",
        "allowed_scopes": [ScopeType.ORGANIZATION, ScopeType.BRANCH],
    },
    {
        "code": "PURCHASING",
        "name": "Compras",
        "description": "Requerimientos, cotizaciones, proveedores y órdenes de compra.",
        "allowed_scopes": [ScopeType.ORGANIZATION, ScopeType.BRANCH],
    },
    {
        "code": "PURCHASING_APPROVER",
        "name": "Aprobador de compras",
        "description": "Aprobación o rechazo de operaciones de compra según políticas futuras.",
        "allowed_scopes": [ScopeType.ORGANIZATION, ScopeType.BRANCH],
    },
    {
        "code": "GATE_CONTROL",
        "name": "Control de puerta",
        "description": "Registro de vehículos, conductores, llegada y documentación de ingreso.",
        "allowed_scopes": [ScopeType.BRANCH],
    },
    {
        "code": "RECEIVING",
        "name": "Recepción",
        "description": "Descarga, conteo y recepción física de mercadería.",
        "allowed_scopes": [ScopeType.BRANCH, ScopeType.WAREHOUSE],
    },
    {
        "code": "QUALITY",
        "name": "Control de calidad",
        "description": "Inspección, cuarentena, liberación y no conformidades.",
        "allowed_scopes": [ScopeType.ORGANIZATION, ScopeType.BRANCH, ScopeType.WAREHOUSE],
    },
    {
        "code": "WAREHOUSE_OPERATOR",
        "name": "Operador de almacén",
        "description": "Ubicación, movimientos físicos, picking y tareas operativas.",
        "allowed_scopes": [ScopeType.WAREHOUSE],
    },
    {
        "code": "INVENTORY_CONTROLLER",
        "name": "Control de inventario",
        "description": "Conteos, conciliaciones, transferencias y revisión de saldos.",
        "allowed_scopes": [ScopeType.ORGANIZATION, ScopeType.BRANCH, ScopeType.WAREHOUSE],
    },
    {
        "code": "INVENTORY_OPERATOR",
        "name": "Operador del libro de inventario",
        "description": "Valida y materializa eventos autorizados en el libro de inventario.",
        "allowed_scopes": [ScopeType.BRANCH, ScopeType.WAREHOUSE],
    },
    {
        "code": "INVENTORY_AUDITOR",
        "name": "Auditor del libro de inventario",
        "description": "Consulta kardex, fuentes, integridad y exportaciones sin publicar movimientos.",
        "allowed_scopes": [ScopeType.ORGANIZATION, ScopeType.BRANCH, ScopeType.WAREHOUSE],
    },
    {
        "code": "SYSTEM_INTEGRATION_SERVICE",
        "name": "Servicio de integración logística",
        "description": "Identidad técnica para ingerir eventos fuente autorizados e idempotentes.",
        "allowed_scopes": [ScopeType.ORGANIZATION],
    },
    {
        "code": "LEDGER_ADMIN",
        "name": "Administrador del libro de inventario",
        "description": "Administra integridad, conciliación y compensaciones del libro append-only.",
        "allowed_scopes": [ScopeType.ORGANIZATION],
    },
    {
        "code": "DISPATCH",
        "name": "Despacho",
        "description": "Packing, carga, precintos, documentos y liberación operativa.",
        "allowed_scopes": [ScopeType.BRANCH, ScopeType.WAREHOUSE],
    },
    {
        "code": "TRANSPORT_PLANNER",
        "name": "Planificador de transporte",
        "description": "Viajes, vehículos, conductores, rutas y planificación.",
        "allowed_scopes": [ScopeType.ORGANIZATION, ScopeType.BRANCH],
    },
    {
        "code": "TRANSPORT_MONITOR",
        "name": "Monitor de transporte",
        "description": "Seguimiento de viajes, GPS, desvíos e incidencias.",
        "allowed_scopes": [ScopeType.ORGANIZATION, ScopeType.BRANCH],
    },
    {
        "code": "DRIVER",
        "name": "Conductor",
        "description": "Viajes asignados, GPS, incidencias y prueba de entrega.",
        "allowed_scopes": [ScopeType.ORGANIZATION, ScopeType.BRANCH],
    },
    {
        "code": "DOCUMENT_CONTROLLER",
        "name": "Control documental",
        "description": "Consulta, emisión, revisión y administración documental según permisos futuros.",
        "allowed_scopes": [ScopeType.ORGANIZATION, ScopeType.BRANCH],
    },
    {
        "code": "LOGISTICS_AUDITOR",
        "name": "Auditor logístico",
        "description": "Consulta de procesos, documentos y eventos de auditoría sin modificar operaciones.",
        "allowed_scopes": [ScopeType.ORGANIZATION, ScopeType.BRANCH],
    },
    {
        "code": "LOGISTICS_VIEWER",
        "name": "Consulta logística",
        "description": "Acceso de solo lectura limitado por alcance.",
        "allowed_scopes": [ScopeType.ORGANIZATION, ScopeType.BRANCH, ScopeType.WAREHOUSE],
    },
]


# ---------------------------------------------------------------------------
# Conflict rules (initial set)
# ---------------------------------------------------------------------------

CONFLICT_RULES: list[dict[str, str]] = [
    {
        "role_a": "PURCHASING",
        "role_b": "PURCHASING_APPROVER",
        "conflict_type": ConflictType.REQUIRES_REVIEW,
        "description": "Comprador y aprobador pueden coexistir solo si la política organiza- "
        "cional lo permite y se impide autoaprobación.",
    },
    {
        "role_a": "DRIVER",
        "role_b": "TRANSPORT_PLANNER",
        "conflict_type": ConflictType.PROHIBITED,
        "description": "Un conductor no debe tener permisos de planificación de transporte.",
    },
    {
        "role_a": "LOGISTICS_AUDITOR",
        "role_b": "WAREHOUSE_OPERATOR",
        "conflict_type": ConflictType.PROHIBITED,
        "description": "Un auditor no debe tener permisos operativos de almacén.",
    },
    {
        "role_a": "LOGISTICS_VIEWER",
        "role_b": "WAREHOUSE_OPERATOR",
        "conflict_type": ConflictType.ALLOWED_WITH_CONTROL,
        "description": "Consulta y operación pueden coexistir con control.",
    },
]
