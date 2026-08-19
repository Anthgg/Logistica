"""Permission catalog — versioned, centralized definition of all logistics permissions.

Catalog version: 1.2.0
Convention: logistics.<resource>.<action>
"""

from enum import StrEnum

CATALOG_VERSION = "1.2.0"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


_ACTION_LABELS = {
    "activate": "Activar",
    "approve": "Aprobar",
    "block": "Bloquear",
    "create": "Crear",
    "execute": "Ejecutar",
    "manage": "Administrar",
    "read": "Consultar",
    "read_history": "Consultar historial de",
    "revoke": "Revocar",
    "rollback": "Revertir",
    "update": "Actualizar",
    "upload": "Cargar",
    "verify": "Verificar",
    "change": "Cambiar",
    "move": "Mover",
}


def _phase_permission(
    code: str,
    category: str,
    risk_level: RiskLevel = RiskLevel.LOW,
    *,
    is_sensitive: bool = False,
    requires_reason: bool = False,
    requires_step_up: bool = False,
) -> dict[str, object]:
    """Build catalog entries for the master-data modules added in phases 021–027."""
    resource, action = code.removeprefix("logistics.").rsplit(".", 1)
    resource_name = resource.replace("_", " ")
    action_name = _ACTION_LABELS.get(action, action.replace("_", " ").capitalize())
    return {
        "code": code,
        "resource": resource,
        "action": action,
        "name": f"{action_name} {resource_name}",
        "description": f"{action_name} {resource_name} en el dominio logístico",
        "category": category,
        "risk_level": risk_level,
        "is_sensitive": is_sensitive,
        "requires_reason": requires_reason,
        "requires_step_up": requires_step_up,
    }


class PermissionCategory(StrEnum):
    ORGANIZATION = "organization"
    BRANCHES = "branches"
    WAREHOUSES = "warehouses"
    RBAC = "rbac"
    PURCHASING = "purchasing"
    INBOUND = "inbound"
    QUALITY = "quality"
    INVENTORY = "inventory"
    OUTBOUND = "outbound"
    TRANSPORT = "transport"
    DELIVERY = "delivery"
    INCIDENTS = "incidents"
    DOCUMENTS = "documents"
    FILES = "files"
    AUDIT = "audit"
    KPIS = "kpis"
    INTEGRATIONS = "integrations"
    NOTIFICATIONS = "notifications"


# ---------------------------------------------------------------------------
# Permission definitions
# ---------------------------------------------------------------------------

PERMISSIONS: list[dict[str, object]] = [
    # --- Organization ---
    {
        "code": "logistics.organizations.read",
        "resource": "organizations",
        "action": "read",
        "name": "Consultar organizaciones",
        "description": "Listar y ver organizaciones",
        "category": "organization",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.organizations.create",
        "resource": "organizations",
        "action": "create",
        "name": "Crear organización",
        "description": "Crear nuevas organizaciones",
        "category": "organization",
        "risk_level": RiskLevel.HIGH,
        "is_sensitive": True,
    },
    {
        "code": "logistics.organizations.update",
        "resource": "organizations",
        "action": "update",
        "name": "Actualizar organización",
        "description": "Modificar datos de organización",
        "category": "organization",
        "risk_level": RiskLevel.MEDIUM,
    },
    {
        "code": "logistics.organizations.change_status",
        "resource": "organizations",
        "action": "change_status",
        "name": "Cambiar estado de organización",
        "description": "Activar/inactivar organización",
        "category": "organization",
        "risk_level": RiskLevel.CRITICAL,
        "is_sensitive": True,
        "requires_reason": True,
        "requires_step_up": True,
    },
    # --- Branches ---
    {
        "code": "logistics.branches.read",
        "resource": "branches",
        "action": "read",
        "name": "Consultar sedes",
        "description": "Listar y ver sedes",
        "category": "branches",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.branches.create",
        "resource": "branches",
        "action": "create",
        "name": "Crear sede",
        "description": "Crear nuevas sedes",
        "category": "branches",
        "risk_level": RiskLevel.MEDIUM,
    },
    {
        "code": "logistics.branches.update",
        "resource": "branches",
        "action": "update",
        "name": "Actualizar sede",
        "description": "Modificar datos de sede",
        "category": "branches",
        "risk_level": RiskLevel.MEDIUM,
    },
    {
        "code": "logistics.branches.change_status",
        "resource": "branches",
        "action": "change_status",
        "name": "Cambiar estado de sede",
        "description": "Activar/inactivar sede",
        "category": "branches",
        "risk_level": RiskLevel.HIGH,
        "is_sensitive": True,
        "requires_reason": True,
    },
    # --- Warehouses ---
    {
        "code": "logistics.warehouses.read",
        "resource": "warehouses",
        "action": "read",
        "name": "Consultar almacenes",
        "description": "Listar y ver almacenes",
        "category": "warehouses",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.warehouses.create",
        "resource": "warehouses",
        "action": "create",
        "name": "Crear almacén",
        "description": "Crear nuevos almacenes",
        "category": "warehouses",
        "risk_level": RiskLevel.MEDIUM,
    },
    {
        "code": "logistics.warehouses.update",
        "resource": "warehouses",
        "action": "update",
        "name": "Actualizar almacén",
        "description": "Modificar datos de almacén",
        "category": "warehouses",
        "risk_level": RiskLevel.MEDIUM,
    },
    {
        "code": "logistics.warehouses.change_status",
        "resource": "warehouses",
        "action": "change_status",
        "name": "Cambiar estado de almacén",
        "description": "Activar/inactivar almacén",
        "category": "warehouses",
        "risk_level": RiskLevel.HIGH,
        "is_sensitive": True,
        "requires_reason": True,
    },
    {
        "code": "logistics.warehouses.set_default",
        "resource": "warehouses",
        "action": "set_default",
        "name": "Establecer almacén predeterminado",
        "description": "Marcar almacén como predeterminado",
        "category": "warehouses",
        "risk_level": RiskLevel.MEDIUM,
    },
    # --- RBAC ---
    {
        "code": "logistics.roles.read",
        "resource": "roles",
        "action": "read",
        "name": "Consultar roles",
        "description": "Listar y ver roles logísticos",
        "category": "rbac",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.role_assignments.read",
        "resource": "role_assignments",
        "action": "read",
        "name": "Consultar asignaciones",
        "description": "Ver asignaciones de roles",
        "category": "rbac",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.role_assignments.create",
        "resource": "role_assignments",
        "action": "create",
        "name": "Asignar rol",
        "description": "Asignar rol a usuario",
        "category": "rbac",
        "risk_level": RiskLevel.CRITICAL,
        "is_sensitive": True,
        "requires_reason": True,
        "requires_step_up": True,
    },
    {
        "code": "logistics.role_assignments.update",
        "resource": "role_assignments",
        "action": "update",
        "name": "Actualizar asignación",
        "description": "Modificar fechas de asignación",
        "category": "rbac",
        "risk_level": RiskLevel.HIGH,
        "is_sensitive": True,
    },
    {
        "code": "logistics.role_assignments.revoke",
        "resource": "role_assignments",
        "action": "revoke",
        "name": "Revocar asignación",
        "description": "Revocar rol asignado",
        "category": "rbac",
        "risk_level": RiskLevel.CRITICAL,
        "is_sensitive": True,
        "requires_reason": True,
        "requires_step_up": True,
    },
    {
        "code": "logistics.permissions.read",
        "resource": "permissions",
        "action": "read",
        "name": "Consultar permisos",
        "description": "Listar catálogo de permisos",
        "category": "rbac",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.role_permissions.read",
        "resource": "role_permissions",
        "action": "read",
        "name": "Consultar permisos de rol",
        "description": "Ver qué permisos tiene cada rol",
        "category": "rbac",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.role_permissions.update",
        "resource": "role_permissions",
        "action": "update",
        "name": "Actualizar permisos de rol",
        "description": "Modificar matriz rol-permiso",
        "category": "rbac",
        "risk_level": RiskLevel.CRITICAL,
        "is_sensitive": True,
        "requires_reason": True,
        "requires_step_up": True,
    },
    # --- Purchasing ---
    {
        "code": "logistics.purchase_requests.read",
        "resource": "purchase_requests",
        "action": "read",
        "name": "Consultar requerimientos",
        "description": "Ver requerimientos de compra",
        "category": "purchasing",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.purchase_requests.create",
        "resource": "purchase_requests",
        "action": "create",
        "name": "Crear requerimiento",
        "description": "Crear requerimiento de compra",
        "category": "purchasing",
        "risk_level": RiskLevel.MEDIUM,
    },
    {
        "code": "logistics.purchase_requests.update",
        "resource": "purchase_requests",
        "action": "update",
        "name": "Actualizar requerimiento",
        "description": "Modificar requerimiento",
        "category": "purchasing",
        "risk_level": RiskLevel.MEDIUM,
    },
    {
        "code": "logistics.purchase_requests.submit",
        "resource": "purchase_requests",
        "action": "submit",
        "name": "Enviar requerimiento",
        "description": "Enviar para aprobación",
        "category": "purchasing",
        "risk_level": RiskLevel.MEDIUM,
    },
    {
        "code": "logistics.purchase_requests.approve",
        "resource": "purchase_requests",
        "action": "approve",
        "name": "Aprobar requerimiento",
        "description": "Aprobar requerimiento de compra",
        "category": "purchasing",
        "risk_level": RiskLevel.HIGH,
        "is_sensitive": True,
    },
    {
        "code": "logistics.purchase_requests.reject",
        "resource": "purchase_requests",
        "action": "reject",
        "name": "Rechazar requerimiento",
        "description": "Rechazar requerimiento",
        "category": "purchasing",
        "risk_level": RiskLevel.HIGH,
        "is_sensitive": True,
        "requires_reason": True,
    },
    {
        "code": "logistics.purchase_requests.cancel",
        "resource": "purchase_requests",
        "action": "cancel",
        "name": "Cancelar requerimiento",
        "description": "Cancelar requerimiento",
        "category": "purchasing",
        "risk_level": RiskLevel.HIGH,
        "requires_reason": True,
    },
    {
        "code": "logistics.purchase_orders.read",
        "resource": "purchase_orders",
        "action": "read",
        "name": "Consultar órdenes de compra",
        "description": "Ver órdenes de compra",
        "category": "purchasing",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.purchase_orders.create",
        "resource": "purchase_orders",
        "action": "create",
        "name": "Crear orden de compra",
        "description": "Crear orden de compra",
        "category": "purchasing",
        "risk_level": RiskLevel.MEDIUM,
    },
    {
        "code": "logistics.purchase_orders.update",
        "resource": "purchase_orders",
        "action": "update",
        "name": "Actualizar orden",
        "description": "Modificar orden de compra",
        "category": "purchasing",
        "risk_level": RiskLevel.MEDIUM,
    },
    {
        "code": "logistics.purchase_orders.issue",
        "resource": "purchase_orders",
        "action": "issue",
        "name": "Emitir orden",
        "description": "Emitir orden de compra",
        "category": "purchasing",
        "risk_level": RiskLevel.HIGH,
        "is_sensitive": True,
    },
    {
        "code": "logistics.purchase_orders.approve",
        "resource": "purchase_orders",
        "action": "approve",
        "name": "Aprobar orden",
        "description": "Aprobar orden de compra",
        "category": "purchasing",
        "risk_level": RiskLevel.HIGH,
        "is_sensitive": True,
        "requires_step_up": True,
    },
    {
        "code": "logistics.purchase_orders.cancel",
        "resource": "purchase_orders",
        "action": "cancel",
        "name": "Cancelar orden",
        "description": "Cancelar orden de compra",
        "category": "purchasing",
        "risk_level": RiskLevel.CRITICAL,
        "is_sensitive": True,
        "requires_reason": True,
    },
    # --- Inbound & Receiving ---
    {
        "code": "logistics.inbound_appointments.read",
        "resource": "inbound_appointments",
        "action": "read",
        "name": "Consultar citas",
        "description": "Ver citas de ingreso",
        "category": "inbound",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.inbound_appointments.create",
        "resource": "inbound_appointments",
        "action": "create",
        "name": "Crear cita",
        "description": "Programar cita de ingreso",
        "category": "inbound",
        "risk_level": RiskLevel.MEDIUM,
    },
    {
        "code": "logistics.gate_entries.read",
        "resource": "gate_entries",
        "action": "read",
        "name": "Consultar ingresos",
        "description": "Ver registros de garita",
        "category": "inbound",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.gate_entries.create",
        "resource": "gate_entries",
        "action": "create",
        "name": "Registrar ingreso",
        "description": "Registrar ingreso de vehículo",
        "category": "inbound",
        "risk_level": RiskLevel.MEDIUM,
    },
    {
        "code": "logistics.receptions.read",
        "resource": "receptions",
        "action": "read",
        "name": "Consultar recepciones",
        "description": "Ver actas de recepción",
        "category": "inbound",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.receptions.create",
        "resource": "receptions",
        "action": "create",
        "name": "Crear recepción",
        "description": "Crear acta de recepción",
        "category": "inbound",
        "risk_level": RiskLevel.MEDIUM,
    },
    {
        "code": "logistics.receptions.complete",
        "resource": "receptions",
        "action": "complete",
        "name": "Completar recepción",
        "description": "Finalizar recepción",
        "category": "inbound",
        "risk_level": RiskLevel.HIGH,
    },
    {
        "code": "logistics.receptions.cancel",
        "resource": "receptions",
        "action": "cancel",
        "name": "Cancelar recepción",
        "description": "Cancelar recepción",
        "category": "inbound",
        "risk_level": RiskLevel.HIGH,
        "requires_reason": True,
    },
    # --- Quality ---
    {
        "code": "logistics.quality_inspections.read",
        "resource": "quality_inspections",
        "action": "read",
        "name": "Consultar inspecciones",
        "description": "Ver inspecciones de calidad",
        "category": "quality",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.quality_inspections.create",
        "resource": "quality_inspections",
        "action": "create",
        "name": "Crear inspección",
        "description": "Registrar inspección de calidad",
        "category": "quality",
        "risk_level": RiskLevel.MEDIUM,
        # Este código estaba declarado dos veces: aquí y más abajo vía
        # `_phase_permission`, que sí exigía step-up. Al consolidar se conserva la
        # postura más estricta de las dos: quedarse con esta entrada tal cual habría
        # retirado la verificación reforzada sin que nadie lo pidiera.
        "requires_step_up": True,
    },
    {
        "code": "logistics.quality_inspections.approve",
        "resource": "quality_inspections",
        "action": "approve",
        "name": "Aprobar inspección",
        "description": "Aprobar resultado de calidad",
        "category": "quality",
        "risk_level": RiskLevel.HIGH,
        "is_sensitive": True,
    },
    {
        "code": "logistics.quality_inspections.reject",
        "resource": "quality_inspections",
        "action": "reject",
        "name": "Rechazar inspección",
        "description": "Rechazar calidad",
        "category": "quality",
        "risk_level": RiskLevel.HIGH,
        "is_sensitive": True,
        "requires_reason": True,
    },
    {
        "code": "logistics.quarantine.place",
        "resource": "quarantine",
        "action": "place",
        "name": "Enviar a cuarentena",
        "description": "Pasar lote a cuarentena",
        "category": "quality",
        "risk_level": RiskLevel.HIGH,
        "is_sensitive": True,
    },
    {
        "code": "logistics.quarantine.release",
        "resource": "quarantine",
        "action": "release",
        "name": "Liberar cuarentena",
        "description": "Liberar lote de cuarentena",
        "category": "quality",
        "risk_level": RiskLevel.CRITICAL,
        "is_sensitive": True,
        "requires_reason": True,
        "requires_step_up": True,
    },
    {
        "code": "logistics.non_conformities.read",
        "resource": "non_conformities",
        "action": "read",
        "name": "Consultar no conformidades",
        "description": "Ver no conformidades",
        "category": "quality",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.non_conformities.create",
        "resource": "non_conformities",
        "action": "create",
        "name": "Crear no conformidad",
        "description": "Registrar no conformidad",
        "category": "quality",
        "risk_level": RiskLevel.MEDIUM,
    },
    {
        "code": "logistics.non_conformities.close",
        "resource": "non_conformities",
        "action": "close",
        "name": "Cerrar no conformidad",
        "description": "Cerrar no conformidad",
        "category": "quality",
        "risk_level": RiskLevel.HIGH,
        "requires_reason": True,
    },
    # --- Inventory ---
    {
        "code": "logistics.inventory.read",
        "resource": "inventory",
        "action": "read",
        "name": "Consultar inventario",
        "description": "Ver saldos de inventario",
        "category": "inventory",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.inventory.rebuild",
        "resource": "inventory",
        "action": "rebuild",
        "name": "Reconstruir saldos de inventario",
        "description": "Ejecutar trabajo de reconstrucción de saldos",
        "category": "inventory",
        "risk_level": RiskLevel.HIGH,
        "is_sensitive": True,
        "requires_step_up": True,
    },
    {
        "code": "logistics.inventory.movements.read",
        "resource": "inventory",
        "action": "movements.read",
        "name": "Consultar movimientos",
        "description": "Ver movimientos de inventario",
        "category": "inventory",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.inventory.movements.create",
        "resource": "inventory",
        "action": "movements.create",
        "name": "Crear movimiento",
        "description": "Registrar movimiento de inventario",
        "category": "inventory",
        "risk_level": RiskLevel.MEDIUM,
    },
    {
        "code": "logistics.inventory.adjustments.read",
        "resource": "inventory",
        "action": "adjustments.read",
        "name": "Consultar ajustes",
        "description": "Ver ajustes de inventario",
        "category": "inventory",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.inventory.adjustments.create",
        "resource": "inventory",
        "action": "adjustments.create",
        "name": "Crear ajuste",
        "description": "Ajustar stock manualmente",
        "category": "inventory",
        "risk_level": RiskLevel.CRITICAL,
        "is_sensitive": True,
        "requires_reason": True,
        "requires_step_up": True,
    },
    {
        "code": "logistics.inventory.adjustments.approve",
        "resource": "inventory",
        "action": "adjustments.approve",
        "name": "Aprobar ajuste",
        "description": "Aprobar ajuste de inventario",
        "category": "inventory",
        "risk_level": RiskLevel.CRITICAL,
        "is_sensitive": True,
        "requires_step_up": True,
    },
    {
        "code": "logistics.inventory.transfers.read",
        "resource": "inventory",
        "action": "transfers.read",
        "name": "Consultar transferencias",
        "description": "Ver transferencias",
        "category": "inventory",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.inventory.transfers.create",
        "resource": "inventory",
        "action": "transfers.create",
        "name": "Crear transferencia",
        "description": "Crear traslado entre almacenes",
        "category": "inventory",
        "risk_level": RiskLevel.MEDIUM,
    },
    {
        "code": "logistics.inventory.transfers.approve",
        "resource": "inventory",
        "action": "transfers.approve",
        "name": "Aprobar transferencia",
        "description": "Aprobar traslado",
        "category": "inventory",
        "risk_level": RiskLevel.HIGH,
        "is_sensitive": True,
    },
    # --- Outbound & Dispatch ---
    {
        "code": "logistics.outbound_orders.read",
        "resource": "outbound_orders",
        "action": "read",
        "name": "Consultar pedidos de salida",
        "description": "Ver pedidos",
        "category": "outbound",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.outbound_orders.create",
        "resource": "outbound_orders",
        "action": "create",
        "name": "Crear pedido",
        "description": "Crear pedido de salida",
        "category": "outbound",
        "risk_level": RiskLevel.MEDIUM,
    },
    {
        "code": "logistics.picking.read",
        "resource": "picking",
        "action": "read",
        "name": "Consultar picking",
        "description": "Ver tareas de picking",
        "category": "outbound",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.picking.execute",
        "resource": "picking",
        "action": "execute",
        "name": "Ejecutar picking",
        "description": "Realizar recolección",
        "category": "outbound",
        "risk_level": RiskLevel.MEDIUM,
    },
    {
        "code": "logistics.picking.complete",
        "resource": "picking",
        "action": "complete",
        "name": "Completar picking",
        "description": "Finalizar tarea de picking",
        "category": "outbound",
        "risk_level": RiskLevel.MEDIUM,
    },
    {
        "code": "logistics.packing.read",
        "resource": "packing",
        "action": "read",
        "name": "Consultar packing",
        "description": "Ver empaque",
        "category": "outbound",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.packing.complete",
        "resource": "packing",
        "action": "complete",
        "name": "Completar packing",
        "description": "Finalizar empaque",
        "category": "outbound",
        "risk_level": RiskLevel.MEDIUM,
    },
    {
        "code": "logistics.dispatches.read",
        "resource": "dispatches",
        "action": "read",
        "name": "Consultar despachos",
        "description": "Ver despachos",
        "category": "outbound",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.dispatches.create",
        "resource": "dispatches",
        "action": "create",
        "name": "Crear despacho",
        "description": "Crear despacho",
        "category": "outbound",
        "risk_level": RiskLevel.MEDIUM,
    },
    {
        "code": "logistics.dispatches.release",
        "resource": "dispatches",
        "action": "release",
        "name": "Liberar despacho",
        "description": "Liberar carga de despacho",
        "category": "outbound",
        "risk_level": RiskLevel.HIGH,
        "is_sensitive": True,
        "requires_step_up": True,
    },
    {
        "code": "logistics.dispatches.cancel",
        "resource": "dispatches",
        "action": "cancel",
        "name": "Cancelar despacho",
        "description": "Cancelar despacho",
        "category": "outbound",
        "risk_level": RiskLevel.HIGH,
        "requires_reason": True,
    },
    # --- Transport ---
    {
        "code": "logistics.vehicles.read",
        "resource": "vehicles",
        "action": "read",
        "name": "Consultar vehículos",
        "description": "Ver flota",
        "category": "transport",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.vehicles.create",
        "resource": "vehicles",
        "action": "create",
        "name": "Crear vehículo",
        "description": "Registrar vehículo",
        "category": "transport",
        "risk_level": RiskLevel.MEDIUM,
    },
    {
        "code": "logistics.vehicles.update",
        "resource": "vehicles",
        "action": "update",
        "name": "Actualizar vehículo",
        "description": "Modificar vehículo",
        "category": "transport",
        "risk_level": RiskLevel.MEDIUM,
    },
    {
        "code": "logistics.vehicles.verify",
        "resource": "vehicles",
        "action": "verify",
        "name": "Verificar vehículo",
        "description": "Verificar SOAT/CITV",
        "category": "transport",
        "risk_level": RiskLevel.MEDIUM,
    },
    {
        "code": "logistics.drivers.read",
        "resource": "drivers",
        "action": "read",
        "name": "Consultar conductores",
        "description": "Ver conductores",
        "category": "transport",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.drivers.create",
        "resource": "drivers",
        "action": "create",
        "name": "Crear conductor",
        "description": "Registrar conductor",
        "category": "transport",
        "risk_level": RiskLevel.MEDIUM,
    },
    {
        "code": "logistics.drivers.update",
        "resource": "drivers",
        "action": "update",
        "name": "Actualizar conductor",
        "description": "Modificar conductor",
        "category": "transport",
        "risk_level": RiskLevel.MEDIUM,
    },
    {
        "code": "logistics.trips.read",
        "resource": "trips",
        "action": "read",
        "name": "Consultar viajes",
        "description": "Ver viajes",
        "category": "transport",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.trips.create",
        "resource": "trips",
        "action": "create",
        "name": "Crear viaje",
        "description": "Crear viaje",
        "category": "transport",
        "risk_level": RiskLevel.MEDIUM,
    },
    {
        "code": "logistics.trips.assign",
        "resource": "trips",
        "action": "assign",
        "name": "Asignar viaje",
        "description": "Asignar vehículo/conductor",
        "category": "transport",
        "risk_level": RiskLevel.HIGH,
        "is_sensitive": True,
    },
    {
        "code": "logistics.trips.start",
        "resource": "trips",
        "action": "start",
        "name": "Iniciar viaje",
        "description": "Iniciar viaje",
        "category": "transport",
        "risk_level": RiskLevel.MEDIUM,
    },
    {
        "code": "logistics.trips.close",
        "resource": "trips",
        "action": "close",
        "name": "Cerrar viaje",
        "description": "Cerrar viaje manualmente",
        "category": "transport",
        "risk_level": RiskLevel.CRITICAL,
        "is_sensitive": True,
        "requires_reason": True,
        "requires_step_up": True,
    },
    {
        "code": "logistics.trips.cancel",
        "resource": "trips",
        "action": "cancel",
        "name": "Cancelar viaje",
        "description": "Cancelar viaje",
        "category": "transport",
        "risk_level": RiskLevel.HIGH,
        "requires_reason": True,
    },
    {
        "code": "logistics.routes.read",
        "resource": "routes",
        "action": "read",
        "name": "Consultar rutas",
        "description": "Ver rutas",
        "category": "transport",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.routes.calculate",
        "resource": "routes",
        "action": "calculate",
        "name": "Calcular ruta",
        "description": "Calcular ruta",
        "category": "transport",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.routes.recalculate",
        "resource": "routes",
        "action": "recalculate",
        "name": "Recalcular ruta",
        "description": "Recalcular ruta activa",
        "category": "transport",
        "risk_level": RiskLevel.HIGH,
        "is_sensitive": True,
    },
    {
        "code": "logistics.routes.override",
        "resource": "routes",
        "action": "override",
        "name": "Modificar ruta activa",
        "description": "Modificar ruta en curso",
        "category": "transport",
        "risk_level": RiskLevel.CRITICAL,
        "is_sensitive": True,
        "requires_reason": True,
        "requires_step_up": True,
    },
    {
        "code": "logistics.gps.read",
        "resource": "gps",
        "action": "read",
        "name": "Consultar GPS",
        "description": "Ver posiciones GPS",
        "category": "transport",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.gps.write",
        "resource": "gps",
        "action": "write",
        "name": "Enviar posición GPS",
        "description": "Reportar posición GPS",
        "category": "transport",
        "risk_level": RiskLevel.LOW,
    },
    # --- Delivery & Returns ---
    {
        "code": "logistics.deliveries.read",
        "resource": "deliveries",
        "action": "read",
        "name": "Consultar entregas",
        "description": "Ver entregas",
        "category": "delivery",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.deliveries.confirm",
        "resource": "deliveries",
        "action": "confirm",
        "name": "Confirmar entrega",
        "description": "Confirmar entrega completa",
        "category": "delivery",
        "risk_level": RiskLevel.HIGH,
    },
    {
        "code": "logistics.deliveries.register_partial",
        "resource": "deliveries",
        "action": "register_partial",
        "name": "Registrar entrega parcial",
        "description": "Registrar entrega parcial",
        "category": "delivery",
        "risk_level": RiskLevel.HIGH,
    },
    {
        "code": "logistics.deliveries.reject",
        "resource": "deliveries",
        "action": "reject",
        "name": "Rechazar entrega",
        "description": "Rechazar entrega",
        "category": "delivery",
        "risk_level": RiskLevel.HIGH,
        "requires_reason": True,
    },
    {
        "code": "logistics.deliveries.manual_close",
        "resource": "deliveries",
        "action": "manual_close",
        "name": "Cierre manual de entrega",
        "description": "Cerrar entrega manualmente",
        "category": "delivery",
        "risk_level": RiskLevel.CRITICAL,
        "is_sensitive": True,
        "requires_reason": True,
        "requires_step_up": True,
    },
    {
        "code": "logistics.proof_of_delivery.read",
        "resource": "proof_of_delivery",
        "action": "read",
        "name": "Consultar POD",
        "description": "Ver prueba de entrega",
        "category": "delivery",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.proof_of_delivery.create",
        "resource": "proof_of_delivery",
        "action": "create",
        "name": "Crear POD",
        "description": "Registrar prueba de entrega",
        "category": "delivery",
        "risk_level": RiskLevel.HIGH,
    },
    {
        "code": "logistics.proof_of_download.download",
        "resource": "proof_of_delivery",
        "action": "download",
        "name": "Descargar POD",
        "description": "Descargar prueba de entrega",
        "category": "delivery",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.proof_of_delivery.invalidate",
        "resource": "proof_of_delivery",
        "action": "invalidate",
        "name": "Invalidar POD",
        "description": "Invalidar prueba de entrega",
        "category": "delivery",
        "risk_level": RiskLevel.CRITICAL,
        "is_sensitive": True,
        "requires_reason": True,
        "requires_step_up": True,
    },
    {
        "code": "logistics.returns.read",
        "resource": "returns",
        "action": "read",
        "name": "Consultar devoluciones",
        "description": "Ver devoluciones",
        "category": "delivery",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.returns.create",
        "resource": "returns",
        "action": "create",
        "name": "Crear devolución",
        "description": "Registrar devolución",
        "category": "delivery",
        "risk_level": RiskLevel.MEDIUM,
    },
    {
        "code": "logistics.returns.approve",
        "resource": "returns",
        "action": "approve",
        "name": "Aprobar devolución",
        "description": "Aprobar RMA",
        "category": "delivery",
        "risk_level": RiskLevel.HIGH,
        "is_sensitive": True,
    },
    {
        "code": "logistics.returns.receive",
        "resource": "returns",
        "action": "receive",
        "name": "Recibir devolución",
        "description": "Recibir mercadería devuelta",
        "category": "delivery",
        "risk_level": RiskLevel.MEDIUM,
    },
    {
        "code": "logistics.returns.close",
        "resource": "returns",
        "action": "close",
        "name": "Cerrar devolución",
        "description": "Cerrar RMA",
        "category": "delivery",
        "risk_level": RiskLevel.HIGH,
        "requires_reason": True,
    },
    # --- Incidents ---
    {
        "code": "logistics.incidents.read",
        "resource": "incidents",
        "action": "read",
        "name": "Consultar incidencias",
        "description": "Ver incidencias",
        "category": "incidents",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.incidents.create",
        "resource": "incidents",
        "action": "create",
        "name": "Crear incidencia",
        "description": "Registrar incidencia",
        "category": "incidents",
        "risk_level": RiskLevel.MEDIUM,
    },
    {
        "code": "logistics.incidents.update",
        "resource": "incidents",
        "action": "update",
        "name": "Actualizar incidencia",
        "description": "Modificar incidencia",
        "category": "incidents",
        "risk_level": RiskLevel.MEDIUM,
    },
    {
        "code": "logistics.incidents.close",
        "resource": "incidents",
        "action": "close",
        "name": "Cerrar incidencia",
        "description": "Cerrar incidencia",
        "category": "incidents",
        "risk_level": RiskLevel.HIGH,
        "requires_reason": True,
    },
    {
        "code": "logistics.incidents.reopen",
        "resource": "incidents",
        "action": "reopen",
        "name": "Reabrir incidencia",
        "description": "Reabrir incidencia cerrada",
        "category": "incidents",
        "risk_level": RiskLevel.HIGH,
        "is_sensitive": True,
        "requires_reason": True,
    },
    # --- Documents ---
    {
        "code": "logistics.documents.read",
        "resource": "documents",
        "action": "read",
        "name": "Consultar documentos",
        "description": "Ver documentos",
        "category": "documents",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.documents.preview",
        "resource": "documents",
        "action": "preview",
        "name": "Vista previa",
        "description": "Generar vista previa",
        "category": "documents",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.documents.issue",
        "resource": "documents",
        "action": "issue",
        "name": "Emitir documento",
        "description": "Emitir documento oficial",
        "category": "documents",
        "risk_level": RiskLevel.HIGH,
        "is_sensitive": True,
    },
    {
        "code": "logistics.documents.download",
        "resource": "documents",
        "action": "download",
        "name": "Descargar documento",
        "description": "Descargar PDF",
        "category": "documents",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.documents.download_bulk",
        "resource": "documents",
        "action": "download_bulk",
        "name": "Descarga masiva",
        "description": "Descargar paquete documental",
        "category": "documents",
        "risk_level": RiskLevel.HIGH,
        "is_sensitive": True,
        "requires_step_up": True,
    },
    {
        "code": "logistics.documents.reprint",
        "resource": "documents",
        "action": "reprint",
        "name": "Reimprimir documento",
        "description": "Reimprimir documento emitido",
        "category": "documents",
        "risk_level": RiskLevel.CRITICAL,
        "is_sensitive": True,
        "requires_reason": True,
        "requires_step_up": True,
    },
    {
        "code": "logistics.documents.cancel",
        "resource": "documents",
        "action": "cancel",
        "name": "Anular documento",
        "description": "Anular documento emitido",
        "category": "documents",
        "risk_level": RiskLevel.CRITICAL,
        "is_sensitive": True,
        "requires_reason": True,
        "requires_step_up": True,
    },
    {
        "code": "logistics.documents.verify",
        "resource": "documents",
        "action": "verify",
        "name": "Verificar documento",
        "description": "Validar código de verificación",
        "category": "documents",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.documents.export",
        "resource": "documents",
        "action": "export",
        "name": "Exportar documentos",
        "description": "Exportar listado documental",
        "category": "documents",
        "risk_level": RiskLevel.HIGH,
        "is_sensitive": True,
    },
    # --- Files ---
    {
        "code": "logistics.files.read",
        "resource": "files",
        "action": "read",
        "name": "Consultar archivos",
        "description": "Ver archivos",
        "category": "files",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.files.upload",
        "resource": "files",
        "action": "upload",
        "name": "Subir archivo",
        "description": "Cargar archivo",
        "category": "files",
        "risk_level": RiskLevel.MEDIUM,
    },
    {
        "code": "logistics.files.download",
        "resource": "files",
        "action": "download",
        "name": "Descargar archivo",
        "description": "Descargar archivo",
        "category": "files",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.files.delete",
        "resource": "files",
        "action": "delete",
        "name": "Eliminar archivo",
        "description": "Eliminar archivo",
        "category": "files",
        "risk_level": RiskLevel.HIGH,
        "is_sensitive": True,
        "requires_reason": True,
    },
    # --- Audit ---
    {
        "code": "logistics.audit.read",
        "resource": "audit",
        "action": "read",
        "name": "Consultar auditoría",
        "description": "Ver eventos de auditoría",
        "category": "audit",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.audit.export",
        "resource": "audit",
        "action": "export",
        "name": "Exportar auditoría",
        "description": "Exportar logs de auditoría",
        "category": "audit",
        "risk_level": RiskLevel.HIGH,
        "is_sensitive": True,
    },
    {
        "code": "logistics.audit.read_sensitive",
        "resource": "audit",
        "action": "read_sensitive",
        "name": "Auditoría sensible",
        "description": "Acceder a auditoría sensible",
        "category": "audit",
        "risk_level": RiskLevel.CRITICAL,
        "is_sensitive": True,
        "requires_step_up": True,
    },
    # --- KPIs & Reports ---
    {
        "code": "logistics.kpis.read",
        "resource": "kpis",
        "action": "read",
        "name": "Consultar KPIs",
        "description": "Ver indicadores",
        "category": "kpis",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.kpis.read_financial",
        "resource": "kpis",
        "action": "read_financial",
        "name": "KPIs financieros",
        "description": "Ver KPIs financieros",
        "category": "kpis",
        "risk_level": RiskLevel.HIGH,
        "is_sensitive": True,
    },
    {
        "code": "logistics.reports.read",
        "resource": "reports",
        "action": "read",
        "name": "Consultar reportes",
        "description": "Ver reportes",
        "category": "kpis",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.reports.export",
        "resource": "reports",
        "action": "export",
        "name": "Exportar reportes",
        "description": "Exportar reportes",
        "category": "kpis",
        "risk_level": RiskLevel.MEDIUM,
    },
    {
        "code": "logistics.reports.export_sensitive",
        "resource": "reports",
        "action": "export_sensitive",
        "name": "Exportación sensible",
        "description": "Exportar reportes sensibles",
        "category": "kpis",
        "risk_level": RiskLevel.CRITICAL,
        "is_sensitive": True,
        "requires_step_up": True,
    },
    # --- Integrations ---
    {
        "code": "logistics.integrations.read",
        "resource": "integrations",
        "action": "read",
        "name": "Consultar integraciones",
        "description": "Ver integraciones",
        "category": "integrations",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.integrations.execute",
        "resource": "integrations",
        "action": "execute",
        "name": "Ejecutar integración",
        "description": "Ejecutar consulta externa",
        "category": "integrations",
        "risk_level": RiskLevel.MEDIUM,
    },
    {
        "code": "logistics.integrations.configure",
        "resource": "integrations",
        "action": "configure",
        "name": "Configurar integración",
        "description": "Modificar configuración",
        "category": "integrations",
        "risk_level": RiskLevel.HIGH,
        "is_sensitive": True,
        "requires_step_up": True,
    },
    # --- Notifications ---
    {
        "code": "logistics.notifications.read",
        "resource": "notifications",
        "action": "read",
        "name": "Consultar notificaciones",
        "description": "Ver notificaciones",
        "category": "notifications",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.notifications.configure",
        "resource": "notifications",
        "action": "configure",
        "name": "Configurar notificaciones",
        "description": "Modificar preferencias",
        "category": "notifications",
        "risk_level": RiskLevel.MEDIUM,
    },
    # --- Company settings & master catalogs ---
    {
        "code": "logistics.company_settings.read",
        "resource": "company_settings",
        "action": "read",
        "name": "Consultar ficha empresa",
        "description": "Ver datos de la empresa",
        "category": "organization",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.company_settings.update",
        "resource": "company_settings",
        "action": "update",
        "name": "Actualizar ficha empresa",
        "description": "Modificar datos de la empresa",
        "category": "organization",
        "risk_level": RiskLevel.HIGH,
        "is_sensitive": True,
    },
    {
        "code": "logistics.catalog.read",
        "resource": "catalog",
        "action": "read",
        "name": "Consultar catálogo productos",
        "description": "Ver catálogo de productos",
        "category": "inventory",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.catalog.create",
        "resource": "catalog",
        "action": "create",
        "name": "Crear producto",
        "description": "Crear producto en catálogo",
        "category": "inventory",
        "risk_level": RiskLevel.MEDIUM,
    },
    {
        "code": "logistics.catalog.update",
        "resource": "catalog",
        "action": "update",
        "name": "Actualizar producto",
        "description": "Modificar producto del catálogo",
        "category": "inventory",
        "risk_level": RiskLevel.MEDIUM,
    },
    {
        "code": "logistics.units.read",
        "resource": "units",
        "action": "read",
        "name": "Consultar unidades",
        "description": "Ver unidades y conversiones",
        "category": "inventory",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.units.create",
        "resource": "units",
        "action": "create",
        "name": "Crear unidad",
        "description": "Registrar unidad de medida",
        "category": "inventory",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.units.update",
        "resource": "units",
        "action": "update",
        "name": "Actualizar unidad",
        "description": "Modificar unidad de medida",
        "category": "inventory",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.partners.read",
        "resource": "partners",
        "action": "read",
        "name": "Consultar socios de negocio",
        "description": "Ver socios de negocio",
        "category": "organization",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.partners.create",
        "resource": "partners",
        "action": "create",
        "name": "Crear socio de negocio",
        "description": "Registrar socio de negocio",
        "category": "organization",
        "risk_level": RiskLevel.MEDIUM,
    },
    {
        "code": "logistics.partners.update",
        "resource": "partners",
        "action": "update",
        "name": "Actualizar socio",
        "description": "Modificar socio de negocio",
        "category": "organization",
        "risk_level": RiskLevel.MEDIUM,
    },
    {
        "code": "logistics.ruc_integration.read",
        "resource": "ruc_integration",
        "action": "read",
        "name": "Consultar RUC y padrones",
        "description": "Ver integración RUC y padrones SUNAT",
        "category": "integrations",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.ruc_integration.execute",
        "resource": "ruc_integration",
        "action": "execute",
        "name": "Ejecutar consulta RUC",
        "description": "Consultar RUC y padrones SUNAT",
        "category": "integrations",
        "risk_level": RiskLevel.MEDIUM,
    },
]


# Permissions introduced by the deployed master-data modules.  These codes are
# deliberately explicit: route dependencies and the seeded database catalog
# must use exactly the same identifiers.
PHASE_021_027_PERMISSIONS = [
    # Company profile
    _phase_permission("logistics.company_profile.read", "organization"),
    _phase_permission("logistics.company_profile.create", "organization", RiskLevel.MEDIUM),
    _phase_permission("logistics.company_profile.update", "organization", RiskLevel.MEDIUM),
    _phase_permission(
        "logistics.company_profile.activate",
        "organization",
        RiskLevel.HIGH,
        is_sensitive=True,
        requires_step_up=True,
    ),
    _phase_permission("logistics.company_profile.read_history", "organization"),
    _phase_permission("logistics.company_addresses.read", "organization"),
    _phase_permission("logistics.company_addresses.manage", "organization", RiskLevel.MEDIUM),
    _phase_permission("logistics.company_contacts.read", "organization"),
    _phase_permission("logistics.company_contacts.manage", "organization", RiskLevel.MEDIUM),
    _phase_permission("logistics.company_assets.read", "organization"),
    _phase_permission("logistics.company_assets.upload", "organization", RiskLevel.MEDIUM),
    _phase_permission("logistics.company_assets.activate", "organization", RiskLevel.HIGH),
    _phase_permission(
        "logistics.company_assets.revoke",
        "organization",
        RiskLevel.HIGH,
        is_sensitive=True,
        requires_reason=True,
    ),
    _phase_permission("logistics.authorized_signers.read", "organization"),
    _phase_permission("logistics.authorized_signers.create", "organization", RiskLevel.HIGH),
    _phase_permission("logistics.authorized_signers.update", "organization", RiskLevel.HIGH),
    _phase_permission(
        "logistics.authorized_signers.activate",
        "organization",
        RiskLevel.HIGH,
        is_sensitive=True,
        requires_step_up=True,
    ),
    _phase_permission(
        "logistics.authorized_signers.revoke",
        "organization",
        RiskLevel.CRITICAL,
        is_sensitive=True,
        requires_reason=True,
        requires_step_up=True,
    ),
    _phase_permission("logistics.numbering_policies.read", "documents"),
    _phase_permission("logistics.numbering_policies.create", "documents", RiskLevel.MEDIUM),
    # Warehouses and locations
    _phase_permission("logistics.warehouses.manage", "warehouses", RiskLevel.MEDIUM),
    _phase_permission("logistics.warehouse_locations.create", "warehouses", RiskLevel.MEDIUM),
    _phase_permission("logistics.warehouse_locations.manage", "warehouses", RiskLevel.MEDIUM),
    _phase_permission("logistics.warehouse_locations.move", "warehouses", RiskLevel.HIGH),
    _phase_permission("logistics.warehouse_layouts.manage", "warehouses", RiskLevel.MEDIUM),
    _phase_permission(
        "logistics.warehouse_layouts.activate",
        "warehouses",
        RiskLevel.HIGH,
        is_sensitive=True,
    ),
    # Products and units
    _phase_permission("logistics.product_categories.read", "inventory"),
    _phase_permission("logistics.product_categories.create", "inventory", RiskLevel.MEDIUM),
    _phase_permission("logistics.product_brands.read", "inventory"),
    _phase_permission("logistics.product_brands.create", "inventory", RiskLevel.MEDIUM),
    _phase_permission("logistics.products.read", "inventory"),
    _phase_permission("logistics.products.create", "inventory", RiskLevel.MEDIUM),
    _phase_permission("logistics.products.update", "inventory", RiskLevel.MEDIUM),
    _phase_permission("logistics.products.activate", "inventory", RiskLevel.HIGH),
    _phase_permission("logistics.product_identifiers.read", "inventory"),
    _phase_permission("logistics.product_identifiers.create", "inventory", RiskLevel.MEDIUM),
    _phase_permission("logistics.product_tracking_policies.manage", "inventory", RiskLevel.MEDIUM),
    _phase_permission("logistics.product_storage_conditions.manage", "inventory", RiskLevel.MEDIUM),
    _phase_permission("logistics.product_units.read", "inventory"),
    _phase_permission("logistics.product_units.manage", "inventory", RiskLevel.MEDIUM),
    _phase_permission("logistics.product_packaging.manage", "inventory", RiskLevel.MEDIUM),
    _phase_permission("logistics.unit_conversions.create", "inventory", RiskLevel.MEDIUM),
    _phase_permission("logistics.unit_conversions.evaluate", "inventory"),
    # Business partners and RUC
    _phase_permission("logistics.business_partners.read", "organization"),
    _phase_permission("logistics.business_partners.create", "organization", RiskLevel.MEDIUM),
    _phase_permission("logistics.business_partners.activate", "organization", RiskLevel.HIGH),
    _phase_permission(
        "logistics.business_partners.block",
        "organization",
        RiskLevel.HIGH,
        is_sensitive=True,
        requires_reason=True,
    ),
    _phase_permission("logistics.business_partner_roles.manage", "organization", RiskLevel.MEDIUM),
    _phase_permission(
        "logistics.business_partner_addresses.manage", "organization", RiskLevel.MEDIUM
    ),
    _phase_permission(
        "logistics.business_partner_contacts.manage", "organization", RiskLevel.MEDIUM
    ),
    _phase_permission(
        "logistics.business_partner_evaluations.create", "organization", RiskLevel.MEDIUM
    ),
    _phase_permission("logistics.business_partners.ruc_verify", "integrations", RiskLevel.MEDIUM),
    _phase_permission(
        "logistics.business_partners.ruc_apply",
        "integrations",
        RiskLevel.HIGH,
        is_sensitive=True,
        requires_step_up=True,
    ),
    _phase_permission("logistics.ruc_lookup.read", "integrations"),
    _phase_permission("logistics.ruc_sources.read", "integrations"),
    _phase_permission("logistics.ruc_datasets.read", "integrations"),
    _phase_permission(
        "logistics.ruc_datasets.activate",
        "integrations",
        RiskLevel.CRITICAL,
        is_sensitive=True,
        requires_step_up=True,
    ),
    _phase_permission(
        "logistics.ruc_datasets.rollback",
        "integrations",
        RiskLevel.CRITICAL,
        is_sensitive=True,
        requires_reason=True,
        requires_step_up=True,
    ),
    _phase_permission("logistics.ruc_imports.read", "integrations"),
    _phase_permission(
        "logistics.ruc_imports.execute",
        "integrations",
        RiskLevel.HIGH,
        is_sensitive=True,
    ),
    _phase_permission("logistics.ruc_verifications.create", "integrations", RiskLevel.MEDIUM),
    _phase_permission(
        "logistics.ruc_verifications.approve",
        "integrations",
        RiskLevel.HIGH,
        is_sensitive=True,
        requires_step_up=True,
    ),
    # Vehicles
    _phase_permission("logistics.vehicle_makes.read", "transport"),
    _phase_permission("logistics.vehicle_makes.manage", "transport", RiskLevel.MEDIUM),
    _phase_permission("logistics.vehicle_models.read", "transport"),
    _phase_permission("logistics.vehicle_models.manage", "transport", RiskLevel.MEDIUM),
    _phase_permission("logistics.vehicles.activate", "transport", RiskLevel.HIGH),
    _phase_permission(
        "logistics.vehicles.block",
        "transport",
        RiskLevel.CRITICAL,
        is_sensitive=True,
        requires_reason=True,
    ),
    _phase_permission(
        "logistics.vehicle_plates.change",
        "transport",
        RiskLevel.HIGH,
        is_sensitive=True,
        requires_reason=True,
    ),
    _phase_permission("logistics.vehicle_capacity.manage", "transport", RiskLevel.MEDIUM),
    _phase_permission("logistics.vehicle_ownership.manage", "transport", RiskLevel.HIGH),
    _phase_permission(
        "logistics.vehicle_carrier_assignments.manage",
        "transport",
        RiskLevel.HIGH,
    ),
    _phase_permission("logistics.vehicle_documents.read", "transport"),
    _phase_permission("logistics.vehicle_documents.create", "transport", RiskLevel.MEDIUM),
    # Specialized rendered documents
    _phase_permission("logistics.transport_documents.read", "documents"),
    _phase_permission("logistics.delivery_documents.read", "documents"),
]

PERMISSIONS.extend(PHASE_021_027_PERMISSIONS)


# Phase 031 — Cost centers. The HTTP module was delivered with these guards,
# but the codes were never registered in the central RBAC catalog.
COST_CENTER_PERMISSIONS = [
    _phase_permission("logistics.cost_centers.read", "procurement", RiskLevel.LOW),
    _phase_permission("logistics.cost_centers.manage", "procurement", RiskLevel.MEDIUM),
]

PERMISSIONS.extend(COST_CENTER_PERMISSIONS)


# Phase 036 — expected arrivals and reception scheduling.
PHASE_036_PERMISSIONS = [
    _phase_permission("logistics.arrival_notices.read", "inbound"),
    _phase_permission("logistics.arrival_notices.read_all", "inbound"),
    _phase_permission("logistics.arrival_notices.create", "inbound", RiskLevel.MEDIUM),
    _phase_permission("logistics.arrival_notices.update", "inbound", RiskLevel.MEDIUM),
    _phase_permission("logistics.arrival_notices.validate", "inbound"),
    _phase_permission(
        "logistics.arrival_notices.submit",
        "inbound",
        RiskLevel.MEDIUM,
        requires_step_up=True,
    ),
    _phase_permission("logistics.arrival_notices.review", "inbound", RiskLevel.MEDIUM),
    _phase_permission(
        "logistics.arrival_notices.request_changes",
        "inbound",
        RiskLevel.MEDIUM,
        requires_reason=True,
    ),
    _phase_permission("logistics.arrival_notices.mark_ready", "inbound", RiskLevel.MEDIUM),
    _phase_permission(
        "logistics.arrival_notices.cancel",
        "inbound",
        RiskLevel.HIGH,
        requires_reason=True,
        requires_step_up=True,
    ),
    _phase_permission("logistics.arrival_notices.read_history", "inbound"),
    _phase_permission("logistics.arrival_notice_transport.read", "inbound"),
    _phase_permission(
        "logistics.arrival_notice_transport.manage",
        "inbound",
        RiskLevel.MEDIUM,
        requires_step_up=True,
    ),
    _phase_permission(
        "logistics.arrival_notice_transport.override_vehicle",
        "inbound",
        RiskLevel.HIGH,
        is_sensitive=True,
        requires_reason=True,
        requires_step_up=True,
    ),
    _phase_permission(
        "logistics.arrival_notice_transport.override_driver",
        "inbound",
        RiskLevel.HIGH,
        is_sensitive=True,
        requires_reason=True,
        requires_step_up=True,
    ),
    _phase_permission("logistics.reception_calendars.read", "inbound"),
    _phase_permission(
        "logistics.reception_calendars.manage",
        "inbound",
        RiskLevel.HIGH,
        requires_step_up=True,
    ),
    _phase_permission(
        "logistics.reception_calendars.manage_blackouts",
        "inbound",
        RiskLevel.CRITICAL,
        is_sensitive=True,
        requires_reason=True,
        requires_step_up=True,
    ),
    _phase_permission(
        "logistics.reception_calendars.override_capacity",
        "inbound",
        RiskLevel.CRITICAL,
        is_sensitive=True,
        requires_reason=True,
        requires_step_up=True,
    ),
    _phase_permission("logistics.reception_appointments.read", "inbound"),
    _phase_permission("logistics.reception_appointments.create", "inbound", RiskLevel.MEDIUM),
    _phase_permission(
        "logistics.reception_appointments.confirm",
        "inbound",
        RiskLevel.HIGH,
        is_sensitive=True,
        requires_step_up=True,
    ),
    _phase_permission(
        "logistics.reception_appointments.reschedule",
        "inbound",
        RiskLevel.HIGH,
        requires_reason=True,
        requires_step_up=True,
    ),
    _phase_permission(
        "logistics.reception_appointments.cancel",
        "inbound",
        RiskLevel.HIGH,
        requires_reason=True,
        requires_step_up=True,
    ),
    _phase_permission("logistics.reception_appointments.read_history", "inbound"),
    _phase_permission("logistics.reception_appointments.preview", "documents"),
    _phase_permission("logistics.reception_appointments.download", "documents"),
    _phase_permission(
        "logistics.reception_appointments.reprint",
        "documents",
        RiskLevel.HIGH,
        requires_step_up=True,
    ),
    _phase_permission(
        "logistics.reception_appointments.download_package",
        "documents",
        RiskLevel.MEDIUM,
    ),
]

PERMISSIONS.extend(PHASE_036_PERMISSIONS)


# Phase 038 — dock assignment and unloading execution (no receiving/inventory).
PHASE_038_PERMISSIONS = [
    _phase_permission("logistics.warehouse_docks.read", "inbound"),
    _phase_permission("logistics.warehouse_docks.manage", "inbound", RiskLevel.MEDIUM),
    _phase_permission(
        "logistics.warehouse_docks.activate", "inbound", RiskLevel.HIGH, requires_step_up=True
    ),
    _phase_permission(
        "logistics.warehouse_docks.block",
        "inbound",
        RiskLevel.CRITICAL,
        is_sensitive=True,
        requires_reason=True,
        requires_step_up=True,
    ),
    _phase_permission(
        "logistics.warehouse_docks.manage_blackouts",
        "inbound",
        RiskLevel.CRITICAL,
        is_sensitive=True,
        requires_reason=True,
        requires_step_up=True,
    ),
    _phase_permission("logistics.inbound_dock_queue.read", "inbound"),
    _phase_permission("logistics.inbound_dock_queue.manage", "inbound", RiskLevel.MEDIUM),
    _phase_permission(
        "logistics.inbound_dock_queue.change_priority",
        "inbound",
        RiskLevel.MEDIUM,
        requires_reason=True,
    ),
    _phase_permission(
        "logistics.inbound_dock_queue.override_priority",
        "inbound",
        RiskLevel.HIGH,
        is_sensitive=True,
        requires_reason=True,
        requires_step_up=True,
    ),
    _phase_permission("logistics.inbound_dock_assignments.read", "inbound"),
    _phase_permission("logistics.inbound_dock_assignments.plan", "inbound", RiskLevel.MEDIUM),
    _phase_permission(
        "logistics.inbound_dock_assignments.assign",
        "inbound",
        RiskLevel.HIGH,
        requires_step_up=True,
    ),
    _phase_permission(
        "logistics.inbound_dock_assignments.reassign",
        "inbound",
        RiskLevel.HIGH,
        requires_reason=True,
        requires_step_up=True,
    ),
    _phase_permission(
        "logistics.inbound_dock_assignments.cancel",
        "inbound",
        RiskLevel.HIGH,
        requires_reason=True,
        requires_step_up=True,
    ),
    _phase_permission("logistics.inbound_dock_assignments.release", "inbound", RiskLevel.MEDIUM),
    _phase_permission("logistics.unloading_operations.read", "inbound"),
    _phase_permission("logistics.unloading_operations.create", "inbound", RiskLevel.MEDIUM),
    _phase_permission(
        "logistics.unloading_operations.manage_readiness", "inbound", RiskLevel.MEDIUM
    ),
    _phase_permission(
        "logistics.unloading_operations.start", "inbound", RiskLevel.HIGH, requires_step_up=True
    ),
    _phase_permission(
        "logistics.unloading_operations.cancel",
        "inbound",
        RiskLevel.HIGH,
        requires_reason=True,
        requires_step_up=True,
    ),
    _phase_permission(
        "logistics.unloading_operations.pause", "inbound", RiskLevel.MEDIUM, requires_reason=True
    ),
    _phase_permission("logistics.unloading_operations.resume", "inbound", RiskLevel.MEDIUM),
    _phase_permission(
        "logistics.unloading_operations.abort",
        "inbound",
        RiskLevel.CRITICAL,
        is_sensitive=True,
        requires_reason=True,
        requires_step_up=True,
    ),
    _phase_permission(
        "logistics.unloading_operations.complete", "inbound", RiskLevel.HIGH, requires_step_up=True
    ),
    _phase_permission(
        "logistics.unloading_operations.manage_responsibles", "inbound", RiskLevel.MEDIUM
    ),
    _phase_permission(
        "logistics.unloading_operations.record_seal_opening",
        "inbound",
        RiskLevel.HIGH,
        requires_step_up=True,
    ),
    _phase_permission(
        "logistics.unloading_operations.request_override",
        "inbound",
        RiskLevel.HIGH,
        requires_reason=True,
        requires_step_up=True,
    ),
    _phase_permission(
        "logistics.unloading_operations.approve_override",
        "inbound",
        RiskLevel.CRITICAL,
        is_sensitive=True,
        requires_reason=True,
        requires_step_up=True,
    ),
    _phase_permission(
        "logistics.unloading_operations.correct_times",
        "inbound",
        RiskLevel.CRITICAL,
        is_sensitive=True,
        requires_reason=True,
        requires_step_up=True,
    ),
    _phase_permission("logistics.dock_operational_metrics.read", "inbound"),
    _phase_permission(
        "logistics.dock_operational_metrics.export",
        "inbound",
        RiskLevel.HIGH,
        requires_step_up=True,
    ),
    _phase_permission(
        "logistics.dock_operational_integrity.read",
        "audit",
        RiskLevel.HIGH,
        is_sensitive=True,
        requires_step_up=True,
    ),
]

PERMISSIONS.extend(PHASE_038_PERMISSIONS)


# Phase 039 — physical receiving by scan; does not grant inventory posting.
PHASE_039_PERMISSIONS = [
    _phase_permission("logistics.inbound_receipts.read", "inbound"),
    _phase_permission("logistics.inbound_receipts.read_all", "inbound"),
    _phase_permission("logistics.inbound_receipts.create", "inbound", RiskLevel.MEDIUM),
    _phase_permission("logistics.inbound_receipts.prepare", "inbound", RiskLevel.MEDIUM),
    _phase_permission(
        "logistics.inbound_receipts.start", "inbound", RiskLevel.HIGH, requires_step_up=True
    ),
    _phase_permission(
        "logistics.inbound_receipts.pause", "inbound", RiskLevel.MEDIUM, requires_reason=True
    ),
    _phase_permission("logistics.inbound_receipts.resume", "inbound", RiskLevel.MEDIUM),
    _phase_permission("logistics.inbound_receipts.validate", "inbound", RiskLevel.MEDIUM),
    _phase_permission(
        "logistics.inbound_receipts.complete", "inbound", RiskLevel.HIGH, requires_step_up=True
    ),
    _phase_permission(
        "logistics.inbound_receipts.cancel",
        "inbound",
        RiskLevel.HIGH,
        requires_reason=True,
        requires_step_up=True,
    ),
    _phase_permission("logistics.inbound_receipts.read_history", "audit"),
    _phase_permission(
        "logistics.inbound_receipts.read_integrity", "audit", RiskLevel.HIGH, requires_step_up=True
    ),
    _phase_permission("logistics.inbound_receipt_scans.create", "inbound"),
    _phase_permission("logistics.inbound_receipt_scans.batch", "inbound", RiskLevel.MEDIUM),
    _phase_permission(
        "logistics.inbound_receipt_scans.compensate",
        "inbound",
        RiskLevel.HIGH,
        requires_reason=True,
        requires_step_up=True,
    ),
    _phase_permission(
        "logistics.inbound_receipt_scans.resolve_unknown",
        "inbound",
        RiskLevel.HIGH,
        requires_reason=True,
        requires_step_up=True,
    ),
    _phase_permission(
        "logistics.inbound_receipt_scans.manual_entry",
        "inbound",
        RiskLevel.MEDIUM,
        requires_step_up=True,
    ),
    _phase_permission("logistics.inbound_receipt_lots.capture", "inbound"),
    _phase_permission("logistics.inbound_receipt_serials.capture", "inbound"),
    _phase_permission("logistics.inbound_receipt_expiration.capture", "inbound"),
    _phase_permission(
        "logistics.inbound_receipt_identifiers.read_sensitive",
        "audit",
        RiskLevel.HIGH,
        requires_step_up=True,
    ),
    _phase_permission("logistics.reception_difference_candidates.read", "inbound"),
    _phase_permission(
        "logistics.reception_difference_candidates.acknowledge", "inbound", RiskLevel.MEDIUM
    ),
    _phase_permission(
        "logistics.reception_difference_candidates.dismiss",
        "inbound",
        RiskLevel.HIGH,
        requires_reason=True,
        requires_step_up=True,
    ),
    _phase_permission(
        "logistics.reception_difference_candidates.prepare",
        "inbound",
        RiskLevel.HIGH,
        requires_step_up=True,
    ),
    _phase_permission(
        "logistics.inbound_receipts.export", "inbound", RiskLevel.HIGH, requires_step_up=True
    ),
]

PERMISSIONS.extend(PHASE_039_PERMISSIONS)


# ---------------------------------------------------------------------------
# Phase 040 — Reception differences
# ---------------------------------------------------------------------------

PHASE_040_PERMISSIONS = [
    # Cases
    _phase_permission("logistics.reception_differences.read", "inbound"),
    _phase_permission("logistics.reception_differences.read_all", "inbound"),
    _phase_permission("logistics.reception_differences.create", "inbound", RiskLevel.MEDIUM),
    _phase_permission("logistics.reception_differences.update", "inbound", RiskLevel.MEDIUM),
    _phase_permission(
        "logistics.reception_differences.formalize_candidates", "inbound", RiskLevel.MEDIUM
    ),
    _phase_permission("logistics.reception_differences.create_manual", "inbound", RiskLevel.MEDIUM),
    _phase_permission("logistics.reception_differences.submit", "inbound", RiskLevel.MEDIUM),
    _phase_permission(
        "logistics.reception_differences.cancel",
        "inbound",
        RiskLevel.HIGH,
        requires_reason=True,
        requires_step_up=True,
    ),
    _phase_permission(
        "logistics.reception_differences.close", "inbound", RiskLevel.HIGH, requires_step_up=True
    ),
    _phase_permission("logistics.reception_differences.read_history", "audit"),
    _phase_permission(
        "logistics.reception_differences.read_integrity",
        "audit",
        RiskLevel.HIGH,
        requires_step_up=True,
    ),
    # Evidence
    _phase_permission("logistics.reception_difference_evidence.read", "inbound"),
    _phase_permission("logistics.reception_difference_evidence.upload", "inbound"),
    _phase_permission(
        "logistics.reception_difference_evidence.archive", "inbound", RiskLevel.MEDIUM
    ),
    _phase_permission(
        "logistics.reception_difference_sensitive_evidence.read",
        "audit",
        RiskLevel.HIGH,
        requires_step_up=True,
    ),
    # Responsibility
    _phase_permission(
        "logistics.reception_difference_responsibility.propose", "inbound", RiskLevel.MEDIUM
    ),
    _phase_permission(
        "logistics.reception_difference_responsibility.review", "inbound", RiskLevel.MEDIUM
    ),
    _phase_permission(
        "logistics.reception_difference_responsibility.assign_internal",
        "inbound",
        RiskLevel.HIGH,
        requires_step_up=True,
    ),
    _phase_permission(
        "logistics.reception_difference_responsibility.acknowledge",
        "inbound",
        RiskLevel.HIGH,
        requires_step_up=True,
    ),
    _phase_permission(
        "logistics.reception_difference_responsibility.dispute", "inbound", RiskLevel.MEDIUM
    ),
    _phase_permission(
        "logistics.reception_difference_responsibility.mark_undetermined",
        "inbound",
        RiskLevel.MEDIUM,
    ),
    # Review
    _phase_permission("logistics.reception_differences.review", "inbound", RiskLevel.MEDIUM),
    _phase_permission(
        "logistics.reception_differences.request_changes", "inbound", RiskLevel.MEDIUM
    ),
    _phase_permission(
        "logistics.reception_differences.approve", "inbound", RiskLevel.HIGH, requires_step_up=True
    ),
    # Documents
    _phase_permission("logistics.reception_difference_documents.preview", "inbound"),
    _phase_permission(
        "logistics.reception_difference_documents.issue",
        "inbound",
        RiskLevel.HIGH,
        requires_step_up=True,
    ),
    _phase_permission("logistics.reception_difference_documents.download", "inbound"),
    _phase_permission("logistics.reception_difference_documents.reprint", "inbound"),
    _phase_permission(
        "logistics.reception_difference_documents.cancel",
        "inbound",
        RiskLevel.CRITICAL,
        requires_reason=True,
        requires_step_up=True,
    ),
    _phase_permission("logistics.reception_difference_documents.download_package", "inbound"),
    # Future preparation
    _phase_permission("logistics.reception_differences.read_quality_preparation", "inbound"),
    _phase_permission("logistics.reception_differences.read_quarantine_recommendations", "inbound"),
    _phase_permission("logistics.reception_differences.read_claim_preparation", "inbound"),
]

PERMISSIONS.extend(PHASE_040_PERMISSIONS)


# ---------------------------------------------------------------------------
# Phase 041 — Quality Inspection Plans
# ---------------------------------------------------------------------------

PHASE_041_PERMISSIONS = [
    _phase_permission("logistics.quality_plan.read", "quality"),
    _phase_permission("logistics.quality_plan.create", "quality", RiskLevel.MEDIUM),
    _phase_permission("logistics.quality_plan.update", "quality", RiskLevel.MEDIUM),
    _phase_permission(
        "logistics.quality_plan.delete",
        "quality",
        RiskLevel.HIGH,
        requires_reason=True,
        requires_step_up=True,
    ),
    _phase_permission(
        "logistics.quality_plan.activate", "quality", RiskLevel.HIGH, requires_step_up=True
    ),
    _phase_permission(
        "logistics.quality_plan.deactivate",
        "quality",
        RiskLevel.HIGH,
        requires_reason=True,
        requires_step_up=True,
    ),
    _phase_permission(
        "logistics.quality_plan.archive",
        "quality",
        RiskLevel.CRITICAL,
        requires_reason=True,
        requires_step_up=True,
    ),
    _phase_permission("logistics.quality_plan.create_version", "quality", RiskLevel.MEDIUM),
    _phase_permission(
        "logistics.quality_plan.activate_version", "quality", RiskLevel.HIGH, requires_step_up=True
    ),
    _phase_permission(
        "logistics.quality_plan.retire_version",
        "quality",
        RiskLevel.HIGH,
        requires_reason=True,
        requires_step_up=True,
    ),
    _phase_permission("logistics.quality_plan.create_scope", "quality", RiskLevel.MEDIUM),
    _phase_permission("logistics.quality_plan.update_scope", "quality", RiskLevel.MEDIUM),
    _phase_permission(
        "logistics.quality_plan.delete_scope", "quality", RiskLevel.HIGH, requires_reason=True
    ),
    _phase_permission("logistics.quality_plan.create_control", "quality", RiskLevel.MEDIUM),
    _phase_permission("logistics.quality_plan.update_control", "quality", RiskLevel.MEDIUM),
    _phase_permission(
        "logistics.quality_plan.delete_control", "quality", RiskLevel.HIGH, requires_reason=True
    ),
    _phase_permission("logistics.quality_plan.create_tolerance", "quality", RiskLevel.MEDIUM),
    _phase_permission("logistics.quality_plan.update_tolerance", "quality", RiskLevel.MEDIUM),
    _phase_permission(
        "logistics.quality_plan.delete_tolerance", "quality", RiskLevel.HIGH, requires_reason=True
    ),
    _phase_permission("logistics.quality_plan.create_sampling", "quality", RiskLevel.MEDIUM),
    _phase_permission("logistics.quality_plan.update_sampling", "quality", RiskLevel.MEDIUM),
    _phase_permission(
        "logistics.quality_plan.delete_sampling", "quality", RiskLevel.HIGH, requires_reason=True
    ),
    _phase_permission("logistics.quality_plan.create_certificate", "quality", RiskLevel.MEDIUM),
    _phase_permission("logistics.quality_plan.update_certificate", "quality", RiskLevel.MEDIUM),
    _phase_permission(
        "logistics.quality_plan.delete_certificate", "quality", RiskLevel.HIGH, requires_reason=True
    ),
    _phase_permission("logistics.quality_plan.create_condition", "quality", RiskLevel.MEDIUM),
    _phase_permission("logistics.quality_plan.update_condition", "quality", RiskLevel.MEDIUM),
    _phase_permission(
        "logistics.quality_plan.delete_condition", "quality", RiskLevel.HIGH, requires_reason=True
    ),
    _phase_permission("logistics.quality_plan.link_reference_file", "quality", RiskLevel.MEDIUM),
    _phase_permission(
        "logistics.quality_plan.unlink_reference_file",
        "quality",
        RiskLevel.HIGH,
        requires_reason=True,
    ),
    _phase_permission(
        "logistics.quality_plan.read_integrity", "audit", RiskLevel.HIGH, requires_step_up=True
    ),
    _phase_permission("logistics.quality_plan.read_history", "audit"),
]

PERMISSIONS.extend(PHASE_041_PERMISSIONS)


# ---------------------------------------------------------------------------
# Phase 042 — Quality Quarantine and Release
# ---------------------------------------------------------------------------

PHASE_042_PERMISSIONS = [
    # Disposition
    _phase_permission("logistics.inbound_inventory_disposition.read", "inbound", RiskLevel.LOW),
    _phase_permission(
        "logistics.inbound_inventory_disposition.materialize",
        "inbound",
        RiskLevel.MEDIUM,
        requires_step_up=True,
    ),
    _phase_permission(
        "logistics.inbound_inventory_disposition.split",
        "inbound",
        RiskLevel.HIGH,
        requires_step_up=True,
        requires_reason=True,
    ),
    _phase_permission(
        "logistics.inbound_inventory_disposition.cancel",
        "inbound",
        RiskLevel.HIGH,
        requires_step_up=True,
        requires_reason=True,
    ),
    # Quarantine
    _phase_permission("logistics.quality_quarantine.read", "quality", RiskLevel.LOW),
    _phase_permission("logistics.quality_quarantine.read_all", "quality", RiskLevel.MEDIUM),
    _phase_permission(
        "logistics.quality_quarantine.create", "quality", RiskLevel.MEDIUM, requires_step_up=True
    ),
    _phase_permission(
        "logistics.quality_quarantine.activate", "quality", RiskLevel.MEDIUM, requires_step_up=True
    ),
    _phase_permission(
        "logistics.quality_quarantine.cancel",
        "quality",
        RiskLevel.HIGH,
        requires_step_up=True,
        requires_reason=True,
    ),
    _phase_permission(
        "logistics.quality_quarantine.close", "quality", RiskLevel.HIGH, requires_step_up=True
    ),
    _phase_permission(
        "logistics.quality_quarantine.manage_zones",
        "quality",
        RiskLevel.HIGH,
        requires_step_up=True,
    ),
    _phase_permission(
        "logistics.quality_quarantine.confirm_placement",
        "quality",
        RiskLevel.MEDIUM,
        requires_step_up=True,
    ),
    # Inspection
    # `logistics.quality_inspections.read` y `.create` se declaran más arriba con
    # nombre y descripción escritos a mano. Estaban también aquí, y como el sembrado
    # actualiza por código, la versión generada sobrescribía el texto bueno con la
    # plantilla genérica. El step-up que aportaba `.create` se conservó allí.
    _phase_permission(
        "logistics.quality_inspections.start", "quality", RiskLevel.MEDIUM, requires_step_up=True
    ),
    _phase_permission("logistics.quality_inspections.pause", "quality", RiskLevel.LOW),
    _phase_permission("logistics.quality_inspections.resume", "quality", RiskLevel.LOW),
    _phase_permission("logistics.quality_inspections.record_results", "quality", RiskLevel.LOW),
    _phase_permission(
        "logistics.quality_inspections.record_measurements", "quality", RiskLevel.LOW
    ),
    _phase_permission("logistics.quality_inspections.record_samples", "quality", RiskLevel.LOW),
    _phase_permission(
        "logistics.quality_inspections.review_certificates", "quality", RiskLevel.MEDIUM
    ),
    _phase_permission("logistics.quality_inspections.upload_evidence", "quality", RiskLevel.LOW),
    _phase_permission(
        "logistics.quality_inspections.validate", "quality", RiskLevel.HIGH, requires_step_up=True
    ),
    _phase_permission(
        "logistics.quality_inspections.complete", "quality", RiskLevel.HIGH, requires_step_up=True
    ),
    _phase_permission(
        "logistics.quality_inspections.request_reinspection",
        "quality",
        RiskLevel.HIGH,
        requires_step_up=True,
    ),
    # Decisions
    _phase_permission("logistics.quality_disposition.read", "quality", RiskLevel.LOW),
    _phase_permission(
        "logistics.quality_disposition.propose", "quality", RiskLevel.HIGH, requires_step_up=True
    ),
    _phase_permission(
        "logistics.quality_disposition.review", "quality", RiskLevel.HIGH, requires_step_up=True
    ),
    _phase_permission(
        "logistics.quality_disposition.approve", "quality", RiskLevel.HIGH, requires_step_up=True
    ),
    _phase_permission(
        "logistics.quality_disposition.reject_proposal",
        "quality",
        RiskLevel.HIGH,
        requires_step_up=True,
        requires_reason=True,
    ),
    _phase_permission(
        "logistics.quality_disposition.keep_quarantined", "quality", RiskLevel.MEDIUM
    ),
    # Release
    _phase_permission(
        "logistics.quality_quarantine.request_release",
        "quality",
        RiskLevel.HIGH,
        requires_step_up=True,
    ),
    _phase_permission(
        "logistics.quality_quarantine.approve_release",
        "quality",
        RiskLevel.HIGH,
        requires_step_up=True,
    ),
    _phase_permission(
        "logistics.quality_quarantine.execute_release",
        "quality",
        RiskLevel.HIGH,
        requires_step_up=True,
    ),
    _phase_permission(
        "logistics.quality_quarantine.direct_release",
        "quality",
        RiskLevel.CRITICAL,
        requires_step_up=True,
    ),
    # Rejection
    _phase_permission(
        "logistics.quality_quarantine.request_rejection",
        "quality",
        RiskLevel.HIGH,
        requires_step_up=True,
    ),
    _phase_permission(
        "logistics.quality_quarantine.approve_rejection",
        "quality",
        RiskLevel.CRITICAL,
        requires_step_up=True,
    ),
    _phase_permission(
        "logistics.quality_quarantine.execute_rejection",
        "quality",
        RiskLevel.HIGH,
        requires_step_up=True,
    ),
    # Documents
    _phase_permission("logistics.quality_nonconformities.preview", "quality", RiskLevel.LOW),
    _phase_permission(
        "logistics.quality_nonconformities.issue", "quality", RiskLevel.HIGH, requires_step_up=True
    ),
    _phase_permission("logistics.quality_nonconformities.download", "quality", RiskLevel.LOW),
    _phase_permission(
        "logistics.quality_nonconformities.reprint",
        "quality",
        RiskLevel.HIGH,
        requires_step_up=True,
    ),
    _phase_permission(
        "logistics.quality_nonconformities.cancel",
        "quality",
        RiskLevel.CRITICAL,
        requires_step_up=True,
        requires_reason=True,
    ),
    # Audit & future
    _phase_permission("logistics.quality_quarantine.read_history", "audit"),
    _phase_permission(
        "logistics.quality_quarantine.read_integrity",
        "audit",
        RiskLevel.HIGH,
        requires_step_up=True,
    ),
    _phase_permission("logistics.quality_availability.read", "quality", RiskLevel.LOW),
    _phase_permission("logistics.quality_future_preparation.read", "quality", RiskLevel.LOW),
]

PERMISSIONS.extend(PHASE_042_PERMISSIONS)


# ---------------------------------------------------------------------------
# Role-Permission matrix
# ---------------------------------------------------------------------------

# Each role gets a list of permission codes.
# Only ALLOW effect is used (deny by default).

ROLE_PERMISSION_MATRIX: dict[str, list[str]] = {
    "LOGISTICS_ADMIN": [
        # Full admin within logistics (but not platform superuser)
        "logistics.organizations.read",
        "logistics.organizations.create",
        "logistics.organizations.update",
        "logistics.organizations.change_status",
        "logistics.branches.read",
        "logistics.branches.create",
        "logistics.branches.update",
        "logistics.branches.change_status",
        "logistics.warehouses.read",
        "logistics.warehouses.create",
        "logistics.warehouses.update",
        "logistics.warehouses.change_status",
        "logistics.warehouses.set_default",
        "logistics.roles.read",
        "logistics.role_assignments.read",
        "logistics.role_assignments.create",
        "logistics.role_assignments.update",
        "logistics.role_assignments.revoke",
        "logistics.permissions.read",
        "logistics.role_permissions.read",
        # Read across all categories
        "logistics.purchase_requests.read",
        "logistics.purchase_orders.read",
        "logistics.inbound_appointments.read",
        "logistics.gate_entries.read",
        "logistics.receptions.read",
        "logistics.quality_inspections.read",
        "logistics.quarantine.place",
        "logistics.non_conformities.read",
        "logistics.inventory.read",
        "logistics.inventory.movements.read",
        "logistics.inventory.adjustments.read",
        "logistics.inventory.transfers.read",
        "logistics.outbound_orders.read",
        "logistics.picking.read",
        "logistics.packing.read",
        "logistics.dispatches.read",
        "logistics.vehicles.read",
        "logistics.drivers.read",
        "logistics.trips.read",
        "logistics.routes.read",
        "logistics.gps.read",
        "logistics.deliveries.read",
        "logistics.proof_of_delivery.read",
        "logistics.returns.read",
        "logistics.incidents.read",
        "logistics.incidents.create",
        "logistics.incidents.update",
        "logistics.incidents.close",
        "logistics.incidents.reopen",
        "logistics.documents.read",
        "logistics.documents.preview",
        "logistics.documents.issue",
        "logistics.documents.download",
        "logistics.documents.reprint",
        "logistics.documents.cancel",
        "logistics.documents.verify",
        "logistics.files.read",
        "logistics.files.upload",
        "logistics.files.download",
        "logistics.audit.read",
        "logistics.audit.export",
        "logistics.kpis.read",
        "logistics.reports.read",
        "logistics.reports.export",
        "logistics.integrations.read",
        "logistics.integrations.execute",
        "logistics.notifications.read",
        # Company settings & master catalogs
        "logistics.company_settings.read",
        "logistics.company_settings.update",
        "logistics.catalog.read",
        "logistics.catalog.create",
        "logistics.catalog.update",
        "logistics.units.read",
        "logistics.units.create",
        "logistics.units.update",
        "logistics.partners.read",
        "logistics.partners.create",
        "logistics.partners.update",
        "logistics.ruc_integration.read",
        "logistics.ruc_integration.execute",
    ],
    "LOGISTICS_MANAGER": [
        "logistics.organizations.read",
        "logistics.branches.read",
        "logistics.warehouses.read",
        "logistics.roles.read",
        "logistics.role_assignments.read",
        "logistics.permissions.read",
        "logistics.role_permissions.read",
        "logistics.purchase_requests.read",
        "logistics.purchase_requests.approve",
        "logistics.purchase_requests.reject",
        "logistics.purchase_orders.read",
        "logistics.purchase_orders.approve",
        "logistics.purchase_orders.cancel",
        "logistics.inbound_appointments.read",
        "logistics.gate_entries.read",
        "logistics.receptions.read",
        "logistics.quality_inspections.read",
        "logistics.quarantine.read",
        "logistics.non_conformities.read",
        "logistics.inventory.read",
        "logistics.inventory.movements.read",
        "logistics.inventory.adjustments.read",
        "logistics.inventory.adjustments.approve",
        "logistics.inventory.transfers.read",
        "logistics.inventory.transfers.approve",
        "logistics.outbound_orders.read",
        "logistics.outbound_orders.approve",
        "logistics.picking.read",
        "logistics.packing.read",
        "logistics.dispatches.read",
        "logistics.vehicles.read",
        "logistics.drivers.read",
        "logistics.trips.read",
        "logistics.routes.read",
        "logistics.gps.read",
        "logistics.deliveries.read",
        "logistics.proof_of_delivery.read",
        "logistics.returns.read",
        "logistics.returns.approve",
        "logistics.incidents.read",
        "logistics.incidents.close",
        "logistics.incidents.reopen",
        "logistics.documents.read",
        "logistics.documents.download",
        "logistics.documents.verify",
        "logistics.files.read",
        "logistics.files.download",
        "logistics.audit.read",
        "logistics.audit.export",
        "logistics.kpis.read",
        "logistics.kpis.read_financial",
        "logistics.reports.read",
        "logistics.reports.export",
        "logistics.integrations.read",
        "logistics.notifications.read",
        # Master catalogs (read)
        "logistics.company_settings.read",
        "logistics.catalog.read",
        "logistics.units.read",
        "logistics.partners.read",
        "logistics.ruc_integration.read",
    ],
    "PURCHASING": [
        "logistics.organizations.read",
        "logistics.branches.read",
        "logistics.warehouses.read",
        "logistics.purchase_requests.read",
        "logistics.purchase_requests.create",
        "logistics.purchase_requests.update",
        "logistics.purchase_requests.submit",
        "logistics.purchase_requests.cancel",
        "logistics.purchase_orders.read",
        "logistics.purchase_orders.create",
        "logistics.purchase_orders.update",
        "logistics.purchase_orders.issue",
        "logistics.files.read",
        "logistics.files.upload",
        "logistics.files.download",
        "logistics.documents.read",
        "logistics.documents.download",
        # Master catalogs (read) for purchasing context
        "logistics.catalog.read",
        "logistics.units.read",
        "logistics.partners.read",
        "logistics.ruc_integration.read",
    ],
    "PURCHASING_APPROVER": [
        "logistics.organizations.read",
        "logistics.branches.read",
        "logistics.warehouses.read",
        "logistics.purchase_requests.read",
        "logistics.purchase_requests.approve",
        "logistics.purchase_requests.reject",
        "logistics.purchase_orders.read",
        "logistics.purchase_orders.approve",
        "logistics.purchase_orders.cancel",
        "logistics.documents.read",
        "logistics.documents.download",
    ],
    "GATE_CONTROL": [
        "logistics.branches.read",
        "logistics.warehouses.read",
        "logistics.inbound_appointments.read",
        "logistics.inbound_appointments.create",
        "logistics.inbound_appointments.update",
        "logistics.gate_entries.read",
        "logistics.gate_entries.create",
        "logistics.gate_entries.update",
        "logistics.vehicles.read",
        "logistics.drivers.read",
    ],
    "RECEIVING": [
        "logistics.branches.read",
        "logistics.warehouses.read",
        "logistics.inbound_appointments.read",
        "logistics.gate_entries.read",
        "logistics.receptions.read",
        "logistics.receptions.create",
        "logistics.receptions.complete",
        "logistics.receptions.cancel",
        "logistics.inventory.read",
        "logistics.inventory.movements.read",
        "logistics.files.read",
        "logistics.files.upload",
        "logistics.incidents.read",
        "logistics.incidents.create",
    ],
    "QUALITY": [
        "logistics.branches.read",
        "logistics.warehouses.read",
        "logistics.receptions.read",
        "logistics.quality_inspections.read",
        "logistics.quality_inspections.create",
        "logistics.quality_inspections.approve",
        "logistics.quality_inspections.reject",
        "logistics.quarantine.place",
        "logistics.quarantine.release",
        "logistics.non_conformities.read",
        "logistics.non_conformities.create",
        "logistics.non_conformities.close",
        "logistics.inventory.read",
        "logistics.files.read",
        "logistics.files.upload",
        "logistics.incidents.read",
        "logistics.incidents.create",
    ],
    "WAREHOUSE_OPERATOR": [
        "logistics.warehouses.read",
        "logistics.inventory.read",
        "logistics.inventory.movements.read",
        "logistics.inventory.movements.create",
        "logistics.inventory.transfers.read",
        "logistics.inventory.transfers.create",
        "logistics.picking.read",
        "logistics.picking.execute",
        "logistics.picking.complete",
        "logistics.packing.read",
        "logistics.packing.complete",
        "logistics.receptions.read",
        "logistics.files.read",
        "logistics.files.upload",
        "logistics.incidents.read",
        "logistics.incidents.create",
    ],
    "INVENTORY_CONTROLLER": [
        "logistics.branches.read",
        "logistics.warehouses.read",
        "logistics.inventory.read",
        "logistics.inventory.movements.read",
        "logistics.inventory.movements.create",
        "logistics.inventory.adjustments.read",
        "logistics.inventory.adjustments.create",
        "logistics.inventory.adjustments.approve",
        "logistics.inventory.transfers.read",
        "logistics.inventory.transfers.create",
        "logistics.inventory.transfers.approve",
        "logistics.files.read",
        "logistics.reports.read",
    ],
    "DISPATCH": [
        "logistics.branches.read",
        "logistics.warehouses.read",
        "logistics.outbound_orders.read",
        "logistics.outbound_orders.create",
        "logistics.picking.read",
        "logistics.picking.execute",
        "logistics.picking.complete",
        "logistics.packing.read",
        "logistics.packing.complete",
        "logistics.dispatches.read",
        "logistics.dispatches.create",
        "logistics.dispatches.release",
        "logistics.dispatches.cancel",
        "logistics.inventory.read",
        "logistics.documents.read",
        "logistics.documents.issue",
        "logistics.documents.download",
        "logistics.files.read",
        "logistics.files.upload",
        "logistics.incidents.read",
        "logistics.incidents.create",
    ],
    "TRANSPORT_PLANNER": [
        "logistics.branches.read",
        "logistics.warehouses.read",
        "logistics.vehicles.read",
        "logistics.vehicles.create",
        "logistics.vehicles.update",
        "logistics.vehicles.verify",
        "logistics.drivers.read",
        "logistics.drivers.create",
        "logistics.drivers.update",
        "logistics.trips.read",
        "logistics.trips.create",
        "logistics.trips.assign",
        "logistics.trips.start",
        "logistics.trips.cancel",
        "logistics.routes.read",
        "logistics.routes.calculate",
        "logistics.routes.recalculate",
        "logistics.dispatches.read",
        "logistics.deliveries.read",
        "logistics.incidents.read",
        "logistics.incidents.create",
    ],
    "TRANSPORT_MONITOR": [
        "logistics.trips.read",
        "logistics.routes.read",
        "logistics.gps.read",
        "logistics.deliveries.read",
        "logistics.incidents.read",
        "logistics.incidents.create",
        "logistics.incidents.update",
        "logistics.vehicles.read",
        "logistics.drivers.read",
    ],
    "DRIVER": [
        "logistics.trips.read",
        "logistics.gps.read",
        "logistics.gps.write",
        "logistics.deliveries.read",
        "logistics.deliveries.confirm",
        "logistics.deliveries.register_partial",
        "logistics.deliveries.reject",
        "logistics.proof_of_delivery.read",
        "logistics.proof_of_delivery.create",
        "logistics.incidents.read",
        "logistics.incidents.create",
        "logistics.files.read",
        "logistics.files.upload",
    ],
    "DOCUMENT_CONTROLLER": [
        "logistics.documents.read",
        "logistics.documents.preview",
        "logistics.documents.issue",
        "logistics.documents.download",
        "logistics.documents.verify",
        "logistics.documents.reprint",
        "logistics.files.read",
        "logistics.files.download",
        "logistics.dispatches.read",
        "logistics.receptions.read",
        "logistics.returns.read",
    ],
    "LOGISTICS_AUDITOR": [
        "logistics.organizations.read",
        "logistics.branches.read",
        "logistics.warehouses.read",
        "logistics.roles.read",
        "logistics.role_assignments.read",
        "logistics.permissions.read",
        "logistics.role_permissions.read",
        "logistics.purchase_requests.read",
        "logistics.purchase_orders.read",
        "logistics.inbound_appointments.read",
        "logistics.gate_entries.read",
        "logistics.receptions.read",
        "logistics.quality_inspections.read",
        "logistics.quarantine.read",
        "logistics.non_conformities.read",
        "logistics.inventory.read",
        "logistics.inventory.movements.read",
        "logistics.inventory.adjustments.read",
        "logistics.inventory.transfers.read",
        "logistics.outbound_orders.read",
        "logistics.picking.read",
        "logistics.packing.read",
        "logistics.dispatches.read",
        "logistics.vehicles.read",
        "logistics.drivers.read",
        "logistics.trips.read",
        "logistics.routes.read",
        "logistics.gps.read",
        "logistics.deliveries.read",
        "logistics.proof_of_delivery.read",
        "logistics.returns.read",
        "logistics.incidents.read",
        "logistics.documents.read",
        "logistics.documents.download",
        "logistics.documents.verify",
        "logistics.files.read",
        "logistics.audit.read",
        "logistics.audit.read_sensitive",
        "logistics.audit.export",
        "logistics.kpis.read",
        "logistics.reports.read",
        # Master catalogs (read)
        "logistics.company_settings.read",
        "logistics.catalog.read",
        "logistics.units.read",
        "logistics.partners.read",
        "logistics.ruc_integration.read",
    ],
    "LOGISTICS_VIEWER": [
        "logistics.organizations.read",
        "logistics.branches.read",
        "logistics.warehouses.read",
        "logistics.inventory.read",
        "logistics.outbound_orders.read",
        "logistics.dispatches.read",
        "logistics.trips.read",
        "logistics.routes.read",
        "logistics.deliveries.read",
        "logistics.incidents.read",
        "logistics.documents.read",
        "logistics.kpis.read",
        "logistics.reports.read",
        # Master catalogs (read)
        "logistics.company_settings.read",
        "logistics.catalog.read",
        "logistics.units.read",
        "logistics.partners.read",
        "logistics.ruc_integration.read",
    ],
}


def _extend_role_permissions(role_code: str, permission_codes: list[str]) -> None:
    current = ROLE_PERMISSION_MATRIX.get(role_code, [])
    ROLE_PERMISSION_MATRIX[role_code] = list(dict.fromkeys([*current, *permission_codes]))


_COST_CENTER_CODES = [str(permission["code"]) for permission in COST_CENTER_PERMISSIONS]
_extend_role_permissions("LOGISTICS_ADMIN", _COST_CENTER_CODES)
_extend_role_permissions("LOGISTICS_MANAGER", _COST_CENTER_CODES)
_extend_role_permissions("PURCHASING", ["logistics.cost_centers.read"])
_extend_role_permissions("PURCHASING_APPROVER", ["logistics.cost_centers.read"])
_extend_role_permissions("LOGISTICS_AUDITOR", ["logistics.cost_centers.read"])
_extend_role_permissions("LOGISTICS_VIEWER", ["logistics.cost_centers.read"])


_PHASE_PERMISSION_CODES = [str(permission["code"]) for permission in PHASE_021_027_PERMISSIONS]
_PHASE_READ_CODES = [
    code
    for code in _PHASE_PERMISSION_CODES
    if code.endswith(".read") or code.endswith(".read_history")
]
_COMPANY_MASTER_CODES = [
    code
    for code in _PHASE_PERMISSION_CODES
    if code.startswith(
        (
            "logistics.company_",
            "logistics.authorized_signers.",
            "logistics.numbering_policies.",
        )
    )
]
_WAREHOUSE_MASTER_CODES = [
    code
    for code in _PHASE_PERMISSION_CODES
    if code.startswith(("logistics.warehouses.", "logistics.warehouse_"))
]
_PRODUCT_MASTER_CODES = [
    code
    for code in _PHASE_PERMISSION_CODES
    if code.startswith(
        (
            "logistics.product_",
            "logistics.products.",
            "logistics.unit_conversions.",
        )
    )
]
_PARTNER_MASTER_CODES = [
    code
    for code in _PHASE_PERMISSION_CODES
    if code.startswith(("logistics.business_partner", "logistics.ruc_"))
]
_VEHICLE_MASTER_CODES = [
    code
    for code in _PHASE_PERMISSION_CODES
    if code.startswith(("logistics.vehicle_", "logistics.vehicles."))
]

_extend_role_permissions("LOGISTICS_ADMIN", _PHASE_PERMISSION_CODES)
_extend_role_permissions(
    "LOGISTICS_MANAGER",
    list(
        dict.fromkeys(
            [
                *_PHASE_READ_CODES,
                *_COMPANY_MASTER_CODES,
                *_WAREHOUSE_MASTER_CODES,
                *_PRODUCT_MASTER_CODES,
                *_PARTNER_MASTER_CODES,
                *_VEHICLE_MASTER_CODES,
            ]
        )
    ),
)
_extend_role_permissions(
    "PURCHASING",
    [
        code
        for code in [*_PRODUCT_MASTER_CODES, *_PARTNER_MASTER_CODES]
        if code.endswith(".read")
        or code.endswith(".create")
        or code.endswith(".evaluate")
        or code.endswith(".ruc_verify")
    ],
)
_extend_role_permissions(
    "PURCHASING_APPROVER",
    [code for code in [*_PRODUCT_MASTER_CODES, *_PARTNER_MASTER_CODES] if code.endswith(".read")],
)
_extend_role_permissions(
    "WAREHOUSE_OPERATOR",
    [
        code
        for code in [*_WAREHOUSE_MASTER_CODES, *_PRODUCT_MASTER_CODES]
        if code.endswith(".read") or code.endswith(".evaluate")
    ],
)
_extend_role_permissions("INVENTORY_CONTROLLER", [*_WAREHOUSE_MASTER_CODES, *_PRODUCT_MASTER_CODES])
_extend_role_permissions("TRANSPORT_PLANNER", _VEHICLE_MASTER_CODES)
_extend_role_permissions(
    "TRANSPORT_MONITOR",
    [code for code in _VEHICLE_MASTER_CODES if code.endswith(".read")],
)
_extend_role_permissions(
    "DOCUMENT_CONTROLLER",
    [
        code
        for code in [*_COMPANY_MASTER_CODES, *_PHASE_PERMISSION_CODES]
        if code.endswith(".read") or code.endswith(".read_history")
    ],
)
_extend_role_permissions("LOGISTICS_AUDITOR", _PHASE_READ_CODES)
_extend_role_permissions("LOGISTICS_VIEWER", _PHASE_READ_CODES)


_PHASE_036_CODES = [str(permission["code"]) for permission in PHASE_036_PERMISSIONS]
_PHASE_036_READ_CODES = [
    code
    for code in _PHASE_036_CODES
    if code.endswith((".read", ".read_all", ".read_history", ".preview", ".download"))
]
_PHASE_036_NOTICE_EDITOR_CODES = [
    code
    for code in _PHASE_036_CODES
    if code.startswith("logistics.arrival_notices.")
    or code.startswith("logistics.arrival_notice_transport.")
]
_PHASE_036_SCHEDULING_CODES = [
    code for code in _PHASE_036_CODES if code.startswith("logistics.reception_")
]

_extend_role_permissions("LOGISTICS_ADMIN", _PHASE_036_CODES)
_extend_role_permissions("LOGISTICS_MANAGER", _PHASE_036_CODES)
_extend_role_permissions("PURCHASING", _PHASE_036_NOTICE_EDITOR_CODES)
_extend_role_permissions(
    "PURCHASING_APPROVER",
    [
        "logistics.arrival_notices.read",
        "logistics.arrival_notices.read_all",
        "logistics.arrival_notices.review",
        "logistics.arrival_notices.request_changes",
        "logistics.arrival_notices.mark_ready",
        "logistics.arrival_notices.read_history",
        "logistics.arrival_notice_transport.read",
    ],
)
_extend_role_permissions(
    "GATE_CONTROL",
    [
        "logistics.arrival_notices.read",
        "logistics.arrival_notice_transport.read",
        "logistics.reception_appointments.read",
        "logistics.reception_appointments.preview",
        "logistics.reception_appointments.download",
    ],
)
_extend_role_permissions("RECEIVING", _PHASE_036_SCHEDULING_CODES)
_extend_role_permissions(
    "DOCUMENT_CONTROLLER",
    [
        code
        for code in _PHASE_036_CODES
        if code.startswith("logistics.reception_appointments.")
        or code.endswith(".read")
        or code.endswith(".read_history")
    ],
)
_extend_role_permissions("LOGISTICS_AUDITOR", _PHASE_036_READ_CODES)
_extend_role_permissions("LOGISTICS_VIEWER", _PHASE_036_READ_CODES)


_PHASE_038_CODES = [str(permission["code"]) for permission in PHASE_038_PERMISSIONS]
_PHASE_038_READ_CODES = [code for code in _PHASE_038_CODES if code.endswith(".read")]
_PHASE_038_OPERATIONAL_CODES = [
    code
    for code in _PHASE_038_CODES
    if code.startswith("logistics.inbound_dock_queue.")
    or code.startswith("logistics.inbound_dock_assignments.")
    or code.startswith("logistics.unloading_operations.")
]

_extend_role_permissions("LOGISTICS_ADMIN", _PHASE_038_CODES)
_extend_role_permissions("LOGISTICS_MANAGER", _PHASE_038_CODES)
_extend_role_permissions("WAREHOUSE_OPERATOR", _PHASE_038_OPERATIONAL_CODES)
_extend_role_permissions(
    "RECEIVING", [*_PHASE_038_READ_CODES, "logistics.inbound_dock_assignments.release"]
)
_extend_role_permissions(
    "GATE_CONTROL",
    [
        "logistics.inbound_dock_queue.read",
        "logistics.inbound_dock_queue.manage",
        "logistics.inbound_dock_assignments.read",
    ],
)
_extend_role_permissions(
    "LOGISTICS_AUDITOR", [*_PHASE_038_READ_CODES, "logistics.dock_operational_integrity.read"]
)
_extend_role_permissions("LOGISTICS_VIEWER", _PHASE_038_READ_CODES)

_PHASE_039_CODES = [str(permission["code"]) for permission in PHASE_039_PERMISSIONS]
_PHASE_039_READ_CODES = [
    code
    for code in _PHASE_039_CODES
    if code.endswith((".read", ".read_all", ".read_history", ".read_integrity"))
]
_PHASE_039_OPERATOR_CODES = [
    code
    for code in _PHASE_039_CODES
    if code.startswith("logistics.inbound_receipt")
    and not code.endswith(
        (".complete", ".cancel", ".compensate", ".resolve_unknown", ".read_integrity")
    )
]
_extend_role_permissions("LOGISTICS_ADMIN", _PHASE_039_CODES)
_extend_role_permissions("LOGISTICS_MANAGER", _PHASE_039_CODES)
_extend_role_permissions("RECEIVING", _PHASE_039_OPERATOR_CODES)
_extend_role_permissions("WAREHOUSE_OPERATOR", _PHASE_039_OPERATOR_CODES)
_extend_role_permissions(
    "PURCHASING",
    ["logistics.inbound_receipts.read", "logistics.reception_difference_candidates.read"],
)
_extend_role_permissions(
    "QUALITY", ["logistics.inbound_receipts.read", "logistics.reception_difference_candidates.read"]
)
_extend_role_permissions(
    "LOGISTICS_AUDITOR",
    [
        *_PHASE_039_READ_CODES,
        "logistics.inbound_receipt_identifiers.read_sensitive",
        "logistics.reception_difference_candidates.read",
    ],
)
_extend_role_permissions("LOGISTICS_VIEWER", ["logistics.inbound_receipts.read"])


_PHASE_040_CODES = [str(permission["code"]) for permission in PHASE_040_PERMISSIONS]
_PHASE_040_READ_CODES = [
    code
    for code in _PHASE_040_CODES
    if code.endswith(
        (
            ".read",
            ".read_all",
            ".read_history",
            ".read_integrity",
            ".preview",
            ".download",
            ".download_package",
        )
    )
]
_PHASE_040_CASE_CODES = [
    code for code in _PHASE_040_CODES if code.startswith("logistics.reception_differences.")
]
_PHASE_040_EVIDENCE_CODES = [
    code for code in _PHASE_040_CODES if code.startswith("logistics.reception_difference_evidence.")
]
_PHASE_040_RESPONSIBILITY_CODES = [
    code
    for code in _PHASE_040_CODES
    if code.startswith("logistics.reception_difference_responsibility.")
]
_PHASE_040_DOCUMENT_CODES = [
    code
    for code in _PHASE_040_CODES
    if code.startswith("logistics.reception_difference_documents.")
]
_extend_role_permissions("LOGISTICS_ADMIN", _PHASE_040_CODES)
_extend_role_permissions("LOGISTICS_MANAGER", _PHASE_040_CODES)
_extend_role_permissions(
    "RECEIVING",
    [
        *_PHASE_040_CASE_CODES,
        *_PHASE_040_EVIDENCE_CODES,
        *_PHASE_040_RESPONSIBILITY_CODES,
        "logistics.reception_difference_documents.preview",
        "logistics.reception_difference_documents.download",
        "logistics.reception_differences.read_quality_preparation",
        "logistics.reception_differences.read_quarantine_recommendations",
        "logistics.reception_differences.read_claim_preparation",
    ],
)
_extend_role_permissions(
    "WAREHOUSE_OPERATOR",
    [*_PHASE_040_CASE_CODES, *_PHASE_040_EVIDENCE_CODES, *_PHASE_040_RESPONSIBILITY_CODES],
)
_extend_role_permissions(
    "PURCHASING",
    [
        *_PHASE_040_READ_CODES,
        "logistics.reception_differences.read",
        "logistics.reception_difference_responsibility.read",
    ],
)
_extend_role_permissions(
    "QUALITY", [*_PHASE_040_READ_CODES, "logistics.reception_differences.read_quality_preparation"]
)
_extend_role_permissions("LOGISTICS_AUDITOR", _PHASE_040_READ_CODES)
_extend_role_permissions("LOGISTICS_VIEWER", _PHASE_040_READ_CODES)


_PHASE_041_CODES = [str(permission["code"]) for permission in PHASE_041_PERMISSIONS]
_PHASE_041_READ_CODES = [
    code
    for code in _PHASE_041_CODES
    if code.endswith((".read", ".read_history", ".read_integrity"))
]
_extend_role_permissions("LOGISTICS_ADMIN", _PHASE_041_CODES)
_extend_role_permissions("LOGISTICS_MANAGER", _PHASE_041_CODES)
_extend_role_permissions(
    "QUALITY",
    [
        code
        for code in _PHASE_041_CODES
        if not code.startswith("logistics.quality_plan.archive")
        and not code.startswith("logistics.quality_plan.delete")
    ],
)
_extend_role_permissions("RECEIVING", _PHASE_041_READ_CODES)
_extend_role_permissions("WAREHOUSE_OPERATOR", _PHASE_041_READ_CODES)
_extend_role_permissions("LOGISTICS_AUDITOR", _PHASE_041_READ_CODES)
_extend_role_permissions("LOGISTICS_VIEWER", _PHASE_041_READ_CODES)


_PHASE_042_CODES = [str(permission["code"]) for permission in PHASE_042_PERMISSIONS]
_PHASE_042_READ_CODES = [
    code
    for code in _PHASE_042_CODES
    if code.endswith(
        (
            ".read",
            ".read_all",
            ".read_history",
            ".read_integrity",
            ".preview",
            ".download",
        )
    )
]
_PHASE_042_DISPOSITION_CODES = [
    code
    for code in _PHASE_042_CODES
    if code.startswith("logistics.inbound_inventory_disposition.")
]
_extend_role_permissions("LOGISTICS_ADMIN", _PHASE_042_CODES)
_extend_role_permissions("LOGISTICS_MANAGER", _PHASE_042_CODES)
_extend_role_permissions(
    "QUALITY",
    [
        code
        for code in _PHASE_042_CODES
        if not code.startswith("logistics.inbound_inventory_disposition.")
        or code.endswith(".read")
    ],
)
_extend_role_permissions(
    "RECEIVING",
    [
        *_PHASE_042_READ_CODES,
        *_PHASE_042_DISPOSITION_CODES,
        "logistics.quality_quarantine.create",
        "logistics.quality_quarantine.activate",
        "logistics.quality_quarantine.confirm_placement",
    ],
)
_extend_role_permissions(
    "WAREHOUSE_OPERATOR",
    [
        *_PHASE_042_READ_CODES,
        "logistics.quality_quarantine.confirm_placement",
        "logistics.quality_quarantine.execute_release",
        "logistics.quality_quarantine.execute_rejection",
    ],
)
_extend_role_permissions("LOGISTICS_AUDITOR", _PHASE_042_READ_CODES)
_extend_role_permissions("LOGISTICS_VIEWER", _PHASE_042_READ_CODES)


# --- Phase 043: Putaway ---

PHASE_043_PERMISSIONS = [
    _phase_permission(
        "logistics.putaway.policies.read", PermissionCategory.INVENTORY, RiskLevel.LOW
    ),
    _phase_permission(
        "logistics.putaway.policies.create", PermissionCategory.INVENTORY, RiskLevel.MEDIUM
    ),
    _phase_permission(
        "logistics.putaway.policies.update",
        PermissionCategory.INVENTORY,
        RiskLevel.MEDIUM,
        is_sensitive=True,
    ),
    _phase_permission(
        "logistics.putaway.execute", PermissionCategory.INVENTORY, RiskLevel.HIGH, is_sensitive=True
    ),
    _phase_permission("logistics.putaway.read", PermissionCategory.INVENTORY, RiskLevel.LOW),
    _phase_permission("logistics.putaway.create", PermissionCategory.INVENTORY, RiskLevel.MEDIUM),
    _phase_permission("logistics.putaway.update", PermissionCategory.INVENTORY, RiskLevel.MEDIUM),
    _phase_permission("logistics.putaway.assign", PermissionCategory.INVENTORY, RiskLevel.MEDIUM),
    _phase_permission(
        "logistics.putaway.override",
        PermissionCategory.INVENTORY,
        RiskLevel.HIGH,
        is_sensitive=True,
        requires_reason=True,
    ),
    _phase_permission(
        "logistics.putaway.override.approve",
        PermissionCategory.INVENTORY,
        RiskLevel.CRITICAL,
        is_sensitive=True,
        requires_step_up=True,
    ),
    _phase_permission(
        "logistics.putaway.capacity.read", PermissionCategory.INVENTORY, RiskLevel.LOW
    ),
    _phase_permission(
        "logistics.putaway.capacity.create", PermissionCategory.INVENTORY, RiskLevel.MEDIUM
    ),
    _phase_permission(
        "logistics.putaway.proximity.read", PermissionCategory.INVENTORY, RiskLevel.LOW
    ),
    _phase_permission(
        "logistics.putaway.proximity.create", PermissionCategory.INVENTORY, RiskLevel.MEDIUM
    ),
    _phase_permission(
        "logistics.putaway.compatibility.read", PermissionCategory.INVENTORY, RiskLevel.LOW
    ),
    _phase_permission(
        "logistics.putaway.compatibility.create", PermissionCategory.INVENTORY, RiskLevel.MEDIUM
    ),
]

PERMISSIONS.extend(PHASE_043_PERMISSIONS)

_PHASE_043_CODES = [str(permission["code"]) for permission in PHASE_043_PERMISSIONS]
_PHASE_043_READ_CODES = [code for code in _PHASE_043_CODES if code.endswith((".read",))]
_PHASE_043_EXECUTE_CODES = [code for code in _PHASE_043_CODES if code.endswith((".execute",))]
_extend_role_permissions("LOGISTICS_ADMIN", _PHASE_043_CODES)
_extend_role_permissions("LOGISTICS_MANAGER", _PHASE_043_CODES)
_extend_role_permissions(
    "WAREHOUSE_OPERATOR",
    [
        *_PHASE_043_READ_CODES,
        *_PHASE_043_EXECUTE_CODES,
        "logistics.putaway.create",
        "logistics.putaway.update",
    ],
)
_extend_role_permissions("RECEIVING", _PHASE_043_READ_CODES)
_extend_role_permissions("QUALITY", _PHASE_043_READ_CODES)
_extend_role_permissions("LOGISTICS_AUDITOR", _PHASE_043_READ_CODES)
_extend_role_permissions("LOGISTICS_VIEWER", _PHASE_043_READ_CODES)


# --- Phase 044: Append-only inventory ledger ---

PHASE_044_PERMISSIONS = [
    _phase_permission("logistics.inventory_ledger.read", PermissionCategory.INVENTORY),
    _phase_permission("logistics.inventory_ledger.read_sources", PermissionCategory.INVENTORY),
    _phase_permission(
        "logistics.inventory_ledger.read_snapshots",
        PermissionCategory.INVENTORY,
        RiskLevel.MEDIUM,
        is_sensitive=True,
        requires_step_up=True,
    ),
    _phase_permission("logistics.inventory_ledger.read_history", PermissionCategory.INVENTORY),
    _phase_permission("logistics.inventory_ledger.read_integrity", PermissionCategory.INVENTORY),
    _phase_permission(
        "logistics.inventory_ledger.validate_prepared_event",
        PermissionCategory.INVENTORY,
        RiskLevel.MEDIUM,
        requires_step_up=True,
    ),
    _phase_permission(
        "logistics.inventory_ledger.post_prepared_event",
        PermissionCategory.INVENTORY,
        RiskLevel.HIGH,
        is_sensitive=True,
        requires_step_up=True,
    ),
    _phase_permission(
        "logistics.inventory_ledger.post_quality_events",
        PermissionCategory.INVENTORY,
        RiskLevel.HIGH,
        is_sensitive=True,
        requires_step_up=True,
    ),
    _phase_permission(
        "logistics.inventory_ledger.post_putaway_events",
        PermissionCategory.INVENTORY,
        RiskLevel.HIGH,
        is_sensitive=True,
        requires_step_up=True,
    ),
    _phase_permission(
        "logistics.inventory_ledger.retry_failed_posting",
        PermissionCategory.INVENTORY,
        RiskLevel.HIGH,
        is_sensitive=True,
        requires_step_up=True,
    ),
    _phase_permission(
        "logistics.inventory_ledger.request_compensation",
        PermissionCategory.INVENTORY,
        RiskLevel.HIGH,
        is_sensitive=True,
        requires_reason=True,
        requires_step_up=True,
    ),
    _phase_permission(
        "logistics.inventory_ledger.review_compensation",
        PermissionCategory.INVENTORY,
        RiskLevel.HIGH,
        is_sensitive=True,
        requires_step_up=True,
    ),
    _phase_permission(
        "logistics.inventory_ledger.approve_compensation",
        PermissionCategory.INVENTORY,
        RiskLevel.CRITICAL,
        is_sensitive=True,
        requires_reason=True,
        requires_step_up=True,
    ),
    _phase_permission(
        "logistics.inventory_ledger.execute_compensation",
        PermissionCategory.INVENTORY,
        RiskLevel.CRITICAL,
        is_sensitive=True,
        requires_step_up=True,
    ),
    _phase_permission(
        "logistics.inventory_ledger.verify",
        PermissionCategory.INVENTORY,
        RiskLevel.MEDIUM,
        requires_step_up=True,
    ),
    _phase_permission(
        "logistics.inventory_ledger.create_checkpoint",
        PermissionCategory.INVENTORY,
        RiskLevel.HIGH,
        is_sensitive=True,
        requires_step_up=True,
    ),
    _phase_permission(
        "logistics.inventory_ledger.reconcile",
        PermissionCategory.INVENTORY,
        RiskLevel.HIGH,
        is_sensitive=True,
        requires_step_up=True,
    ),
    _phase_permission(
        "logistics.inventory_ledger.read_balance_preparation", PermissionCategory.INVENTORY
    ),
    _phase_permission(
        "logistics.inventory_ledger.read_traceability_preparation", PermissionCategory.INVENTORY
    ),
    _phase_permission("logistics.inventory_kardex.read", PermissionCategory.INVENTORY),
    _phase_permission(
        "logistics.inventory_kardex.read_running_quantity",
        PermissionCategory.INVENTORY,
        RiskLevel.MEDIUM,
    ),
    _phase_permission(
        "logistics.inventory_kardex.export",
        PermissionCategory.INVENTORY,
        RiskLevel.MEDIUM,
        is_sensitive=True,
        requires_step_up=True,
    ),
]

PERMISSIONS.extend(PHASE_044_PERMISSIONS)

_PHASE_044_CODES = [str(permission["code"]) for permission in PHASE_044_PERMISSIONS]
_PHASE_044_READ_CODES = [
    code for code in _PHASE_044_CODES if ".read" in code or code.endswith((".verify", ".export"))
]
_PHASE_044_OPERATOR_CODES = [
    code
    for code in _PHASE_044_CODES
    if code.endswith(
        (
            ".validate_prepared_event",
            ".post_prepared_event",
            ".post_quality_events",
            ".post_putaway_events",
            ".retry_failed_posting",
        )
    )
]
_PHASE_044_AUDIT_CODES = [
    *_PHASE_044_READ_CODES,
    "logistics.inventory_ledger.create_checkpoint",
    "logistics.inventory_ledger.reconcile",
]

_extend_role_permissions("LOGISTICS_ADMIN", _PHASE_044_CODES)
_extend_role_permissions("LEDGER_ADMIN", _PHASE_044_CODES)
_extend_role_permissions("LOGISTICS_MANAGER", _PHASE_044_AUDIT_CODES)
_extend_role_permissions("WAREHOUSE_OPERATOR", [*_PHASE_044_READ_CODES, *_PHASE_044_OPERATOR_CODES])
_extend_role_permissions("INVENTORY_OPERATOR", [*_PHASE_044_READ_CODES, *_PHASE_044_OPERATOR_CODES])
_extend_role_permissions("SYSTEM_INTEGRATION_SERVICE", _PHASE_044_OPERATOR_CODES)
_extend_role_permissions("INVENTORY_CONTROLLER", _PHASE_044_CODES)
_extend_role_permissions("INVENTORY_AUDITOR", _PHASE_044_AUDIT_CODES)
_extend_role_permissions("LOGISTICS_AUDITOR", _PHASE_044_AUDIT_CODES)
_extend_role_permissions("LOGISTICS_VIEWER", _PHASE_044_READ_CODES)


# --- RBAC catalog gaps discovered while enabling existing logistics screens ---

LEGACY_WORKFLOW_PERMISSIONS = [
    # Phase 031: purchase requisitions
    _phase_permission("logistics.purchase_requisitions.read", PermissionCategory.PURCHASING),
    _phase_permission("logistics.purchase_requisitions.create", PermissionCategory.PURCHASING),
    _phase_permission("logistics.purchase_requisitions.edit", PermissionCategory.PURCHASING),
    _phase_permission("logistics.purchase_requisitions.submit", PermissionCategory.PURCHASING),
    _phase_permission("logistics.purchase_requisitions.review", PermissionCategory.PURCHASING),
    _phase_permission("logistics.purchase_requisitions.approve", PermissionCategory.PURCHASING),
    _phase_permission("logistics.purchase_requisitions.cancel", PermissionCategory.PURCHASING),
    _phase_permission("logistics.purchase_requisitions.comment", PermissionCategory.PURCHASING),
    _phase_permission("logistics.purchase_requisitions.issue", PermissionCategory.PURCHASING),
    # Phase 035: procurement approval pages
    _phase_permission("logistics.procurement_approvals.read", PermissionCategory.PURCHASING),
    _phase_permission("logistics.procurement_approvals.decide", PermissionCategory.PURCHASING),
    _phase_permission("logistics.procurement_approval_policies.read", PermissionCategory.PURCHASING),
    _phase_permission("logistics.procurement_approval_policies.create", PermissionCategory.PURCHASING),
    _phase_permission("logistics.procurement_approval_policies.update", PermissionCategory.PURCHASING),
    _phase_permission("logistics.procurement_approval_policies.activate", PermissionCategory.PURCHASING),
    # Phase 037: gate control
    _phase_permission("logistics.gate_check_ins.read", PermissionCategory.INBOUND),
    _phase_permission("logistics.gate_check_ins.read_all", PermissionCategory.INBOUND),
    _phase_permission("logistics.gate_check_ins.create", PermissionCategory.INBOUND),
    _phase_permission("logistics.gate_check_ins.walk_in", PermissionCategory.INBOUND),
    _phase_permission("logistics.gate_check_ins.start_verification", PermissionCategory.INBOUND),
    _phase_permission("logistics.gate_check_ins.hold", PermissionCategory.INBOUND),
    _phase_permission("logistics.gate_check_ins.resume", PermissionCategory.INBOUND),
    _phase_permission("logistics.gate_check_ins.complete", PermissionCategory.INBOUND),
    _phase_permission("logistics.gate_check_ins.cancel", PermissionCategory.INBOUND),
    _phase_permission("logistics.gate_check_ins.request_correction", PermissionCategory.INBOUND),
    _phase_permission("logistics.gate_check_ins.approve_correction", PermissionCategory.INBOUND),
    _phase_permission("logistics.gate_check_ins.read_history", PermissionCategory.INBOUND),
    _phase_permission("logistics.warehouse_gates.read", PermissionCategory.INBOUND),
    _phase_permission("logistics.warehouse_gates.manage", PermissionCategory.INBOUND),
    _phase_permission("logistics.warehouse_gates.activate", PermissionCategory.INBOUND),
    _phase_permission("logistics.gate_vehicle_inspections.manage", PermissionCategory.INBOUND),
    _phase_permission("logistics.gate_driver_inspections.manage", PermissionCategory.INBOUND),
    _phase_permission("logistics.gate_document_inspections.manage", PermissionCategory.INBOUND),
    _phase_permission("logistics.gate_seal_inspections.manage", PermissionCategory.INBOUND),
    _phase_permission("logistics.gate_photo_evidence.capture", PermissionCategory.INBOUND),
    _phase_permission("logistics.gate_photo_evidence.read", PermissionCategory.INBOUND),
    _phase_permission("logistics.gate_sensitive_evidence.read", PermissionCategory.INBOUND),
    _phase_permission("logistics.gate_exceptions.request", PermissionCategory.INBOUND),
    _phase_permission("logistics.gate_exceptions.approve", PermissionCategory.INBOUND),
    _phase_permission("logistics.gate_exceptions.reject", PermissionCategory.INBOUND),
    _phase_permission("logistics.gate_entry.supervise", PermissionCategory.INBOUND),
    _phase_permission("logistics.gate_entry.authorize", PermissionCategory.INBOUND),
    _phase_permission("logistics.gate_entry.authorize_with_observations", PermissionCategory.INBOUND),
    _phase_permission("logistics.gate_entry.deny", PermissionCategory.INBOUND),
    _phase_permission("logistics.gate_documents.preview", PermissionCategory.INBOUND),
    _phase_permission("logistics.gate_documents.issue", PermissionCategory.INBOUND),
    _phase_permission("logistics.gate_documents.download", PermissionCategory.INBOUND),
    _phase_permission("logistics.gate_documents.download_package", PermissionCategory.INBOUND),
    # Phase 040 router-level permission names used by the implemented endpoints
    _phase_permission("logistics.reception_difference_cases.read", PermissionCategory.INBOUND),
    _phase_permission("logistics.reception_difference_cases.create", PermissionCategory.INBOUND),
    _phase_permission("logistics.reception_difference_cases.update", PermissionCategory.INBOUND),
    _phase_permission("logistics.reception_difference_cases.submit", PermissionCategory.INBOUND),
    _phase_permission("logistics.reception_difference_cases.review", PermissionCategory.INBOUND),
    _phase_permission("logistics.reception_difference_cases.approve", PermissionCategory.INBOUND),
    _phase_permission("logistics.reception_difference_cases.cancel", PermissionCategory.INBOUND),
    _phase_permission("logistics.reception_difference_cases.close", PermissionCategory.INBOUND),
    _phase_permission("logistics.reception_difference_items.read", PermissionCategory.INBOUND),
    _phase_permission("logistics.reception_difference_items.create", PermissionCategory.INBOUND),
    _phase_permission("logistics.reception_difference_items.update", PermissionCategory.INBOUND),
    _phase_permission("logistics.reception_difference_items.dismiss", PermissionCategory.INBOUND),
    _phase_permission("logistics.reception_difference_evidence.create", PermissionCategory.INBOUND),
    _phase_permission("logistics.reception_difference_evidence.update", PermissionCategory.INBOUND),
    _phase_permission("logistics.reception_difference_responsibility.read", PermissionCategory.INBOUND),
    _phase_permission("logistics.reception_difference_responsibility.create", PermissionCategory.INBOUND),
    _phase_permission("logistics.reception_difference_responsibility.update", PermissionCategory.INBOUND),
    _phase_permission("logistics.reception_difference_reviews.read", PermissionCategory.INBOUND),
    _phase_permission("logistics.reception_difference_reviews.create", PermissionCategory.INBOUND),
    _phase_permission("logistics.reception_difference_reviews.update", PermissionCategory.INBOUND),
    _phase_permission("logistics.reception_difference_approvals.read", PermissionCategory.INBOUND),
    _phase_permission("logistics.reception_difference_acknowledgements.read", PermissionCategory.INBOUND),
    _phase_permission("logistics.reception_difference_acknowledgements.create", PermissionCategory.INBOUND),
    _phase_permission("logistics.reception_difference_acknowledgements.dispute", PermissionCategory.INBOUND),
    _phase_permission("logistics.reception_difference_documents.read", PermissionCategory.INBOUND),
    _phase_permission("logistics.reception_difference_documents.package", PermissionCategory.INBOUND),
]

PERMISSIONS.extend(LEGACY_WORKFLOW_PERMISSIONS)

_LEGACY_WORKFLOW_CODES = [
    str(permission["code"]) for permission in LEGACY_WORKFLOW_PERMISSIONS
]
_extend_role_permissions("LOGISTICS_ADMIN", _LEGACY_WORKFLOW_CODES)


# ---------------------------------------------------------------------------
# Fase 006 — permisos que el código exigía sin que existieran en el catálogo
# ---------------------------------------------------------------------------
#
# El módulo `procurement/evaluations` protegía sus endpoints con
# `require_permission(...)` sobre siete códigos que nunca se declararon aquí. Como
# el sembrado solo crea lo que está en el catálogo, esos permisos no existían en la
# base y ningún rol podía tenerlos: `require_permission` fallaba cerrado y dejaba el
# módulo entero inaccesible. Pasó desapercibido porque el bypass de administrador de
# plataforma se saltaba la comprobación, así que quien probaba era siempre admin.
#
# Se declaran con la semántica que ya usan sus endpoints. No se renombra ninguno en
# esta fase: cambiar el código obligaría a tocar el router, y aquí solo se cierra el
# agujero. La acción `manage` es deliberadamente vaga y queda anotada para F006 PR 2.
PHASE_006_EVALUATION_PERMISSIONS: list[dict[str, object]] = [
    {
        "code": "logistics.supplier_evaluation_templates.read",
        "resource": "supplier_evaluation_templates",
        "action": "read",
        "name": "Consultar plantillas de evaluación",
        "description": "Ver las plantillas de evaluación de proveedores y sus criterios",
        "category": "procurement",
        "risk_level": RiskLevel.LOW,
    },
    {
        "code": "logistics.supplier_evaluation_templates.manage",
        "resource": "supplier_evaluation_templates",
        "action": "manage",
        "name": "Administrar plantillas de evaluación",
        "description": "Crear y modificar plantillas de evaluación de proveedores y sus criterios",
        "category": "procurement",
        "risk_level": RiskLevel.HIGH,
        "is_sensitive": True,
    },
    {
        "code": "logistics.supplier_evaluation_templates.activate",
        "resource": "supplier_evaluation_templates",
        "action": "activate",
        "name": "Activar plantilla de evaluación",
        "description": "Poner en vigor una versión de plantilla de evaluación de proveedores",
        "category": "procurement",
        "risk_level": RiskLevel.HIGH,
        "is_sensitive": True,
        "requires_reason": True,
    },
    {
        "code": "logistics.quotation_evaluations.create",
        "resource": "quotation_evaluations",
        "action": "create",
        "name": "Crear evaluación de cotización",
        "description": "Abrir la evaluación de las cotizaciones recibidas para una compra",
        "category": "procurement",
        "risk_level": RiskLevel.MEDIUM,
    },
    {
        "code": "logistics.quotation_evaluations.calculate",
        "resource": "quotation_evaluations",
        "action": "calculate",
        "name": "Calcular evaluación de cotización",
        "description": "Ejecutar el cálculo de puntajes de una evaluación de cotizaciones",
        "category": "procurement",
        "risk_level": RiskLevel.MEDIUM,
    },
    {
        # Sobrescribir a mano un puntaje calculado permite dirigir el resultado de la
        # evaluación hacia un proveedor concreto. Es la operación más manipulable del
        # módulo, y por eso pide motivo y verificación reforzada.
        "code": "logistics.quotation_evaluation_scores.manual_create",
        "resource": "quotation_evaluation_scores",
        "action": "manual_create",
        "name": "Registrar puntaje manual",
        "description": "Asignar manualmente un puntaje de evaluación en lugar del calculado",
        "category": "procurement",
        "risk_level": RiskLevel.HIGH,
        "is_sensitive": True,
        "requires_reason": True,
        "requires_step_up": True,
    },
    {
        # Registrar la decisión es adjudicar: cierra el ciclo de selección de
        # proveedor. Se separa de quien origina y calcula la evaluación.
        "code": "logistics.quotation_evaluation_decisions.record",
        "resource": "quotation_evaluation_decisions",
        "action": "record",
        "name": "Registrar decisión de evaluación",
        "description": "Dejar constancia de la decisión de adjudicación de una evaluación",
        "category": "procurement",
        "risk_level": RiskLevel.CRITICAL,
        "is_sensitive": True,
        "requires_reason": True,
        "requires_step_up": True,
    },
]

PERMISSIONS.extend(PHASE_006_EVALUATION_PERMISSIONS)

_EVALUATION_READ = ["logistics.supplier_evaluation_templates.read"]
_EVALUATION_ORIGINATE = [
    "logistics.quotation_evaluations.create",
    "logistics.quotation_evaluations.calculate",
    "logistics.quotation_evaluation_scores.manual_create",
]
_EVALUATION_DECIDE = ["logistics.quotation_evaluation_decisions.record"]
_EVALUATION_ADMIN = [
    "logistics.supplier_evaluation_templates.manage",
    "logistics.supplier_evaluation_templates.activate",
]

# Quien origina y puntúa la evaluación no registra la decisión: es la misma
# separación originar/aprobar que ya rige para los pedidos de compra.
_extend_role_permissions("PURCHASING", _EVALUATION_READ + _EVALUATION_ORIGINATE)
_extend_role_permissions("PURCHASING_APPROVER", _EVALUATION_READ + _EVALUATION_DECIDE)
_extend_role_permissions("LOGISTICS_AUDITOR", _EVALUATION_READ)
_extend_role_permissions("LOGISTICS_MANAGER", _EVALUATION_READ + _EVALUATION_DECIDE)
_extend_role_permissions(
    "LOGISTICS_ADMIN",
    _EVALUATION_READ + _EVALUATION_ORIGINATE + _EVALUATION_DECIDE + _EVALUATION_ADMIN,
)


# ---------------------------------------------------------------------------
# Fase 006 — permisos que LOGISTICS_ADMIN solo alcanzaba por el bypass
# ---------------------------------------------------------------------------
#
# Estos cinco existen en el catálogo y los exige algún endpoint, pero no estaban en
# la matriz de LOGISTICS_ADMIN: hasta ahora llegaba a ellos porque el bypass de
# administrador de plataforma se saltaba la comprobación. Al retirar el bypass hay
# que concederlos por la vía normal o el rol pierde acceso.
#
# Se añaden solo estos cinco, medidos comparando lo que exigen los endpoints contra
# la matriz real. No se concede comodín ni acceso total.
_PHASE_006_ADMIN_GAP = [
    "logistics.documents.export",
    "logistics.integrations.configure",
    "logistics.inventory.rebuild",
    "logistics.role_permissions.update",
    "logistics.vehicles.create",
]
_extend_role_permissions("LOGISTICS_ADMIN", _PHASE_006_ADMIN_GAP)


# Scope rules: all permissions allow all scope types by default.
# Individual permissions can be restricted in future phases.
ALL_SCOPES = ["global", "organization", "branch", "warehouse"]
