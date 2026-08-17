"""Audit event catalog — versioned, centralized event code definitions."""

from enum import StrEnum

CATALOG_VERSION = "1.0.0"


class EventCategory(StrEnum):
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    ORGANIZATION = "organization"
    SECURITY = "security"
    MASTER_DATA = "master_data"
    RBAC = "rbac"
    DOCUMENT = "document"
    INVENTORY = "inventory"
    TRANSPORT = "transport"
    DELIVERY = "delivery"
    INTEGRATION = "integration"
    SYSTEM = "system"
    RECEIVING = "receiving"


class EventResult(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    DENIED = "denied"
    PARTIAL = "partial"
    CANCELLED = "cancelled"
    ERROR = "error"
    PENDING = "pending"


class EventSeverity(StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActorType(StrEnum):
    USER = "user"
    SYSTEM = "system"
    INTEGRATION = "integration"
    SCHEDULED_TASK = "scheduled_task"
    DRIVER_APP = "driver_app"
    MIGRATION = "migration"
    ADMIN_SCRIPT = "admin_script"


# ---------------------------------------------------------------------------
# Event codes catalog
# ---------------------------------------------------------------------------

EVENT_CATALOG: list[dict[str, str]] = [
    # Organization
    {"event_code": "logistics.organization.created", "category": EventCategory.ORGANIZATION, "severity": EventSeverity.MEDIUM, "description": "Organización creada"},
    {"event_code": "logistics.organization.updated", "category": EventCategory.ORGANIZATION, "severity": EventSeverity.MEDIUM, "description": "Organización actualizada"},
    {"event_code": "logistics.organization.status_changed", "category": EventCategory.ORGANIZATION, "severity": EventSeverity.HIGH, "description": "Estado de organización cambiado"},
    # Branch
    {"event_code": "logistics.branch.created", "category": EventCategory.ORGANIZATION, "severity": EventSeverity.MEDIUM, "description": "Sede creada"},
    {"event_code": "logistics.branch.updated", "category": EventCategory.ORGANIZATION, "severity": EventSeverity.MEDIUM, "description": "Sede actualizada"},
    {"event_code": "logistics.branch.status_changed", "category": EventCategory.ORGANIZATION, "severity": EventSeverity.HIGH, "description": "Estado de sede cambiado"},
    # Warehouse
    {"event_code": "logistics.warehouse.created", "category": EventCategory.ORGANIZATION, "severity": EventSeverity.MEDIUM, "description": "Almacén creado"},
    {"event_code": "logistics.warehouse.updated", "category": EventCategory.ORGANIZATION, "severity": EventSeverity.MEDIUM, "description": "Almacén actualizado"},
    {"event_code": "logistics.warehouse.status_changed", "category": EventCategory.ORGANIZATION, "severity": EventSeverity.HIGH, "description": "Estado de almacén cambiado"},
    {"event_code": "logistics.warehouse.default_changed", "category": EventCategory.ORGANIZATION, "severity": EventSeverity.MEDIUM, "description": "Almacén predeterminado cambiado"},
    # RBAC
    {"event_code": "logistics.role.assignment_created", "category": EventCategory.RBAC, "severity": EventSeverity.HIGH, "description": "Rol asignado a usuario"},
    {"event_code": "logistics.role.assignment_revoked", "category": EventCategory.RBAC, "severity": EventSeverity.HIGH, "description": "Rol revocado"},
    {"event_code": "logistics.role.assignment_dates_updated", "category": EventCategory.RBAC, "severity": EventSeverity.MEDIUM, "description": "Fechas de asignación actualizadas"},
    {"event_code": "logistics.role.conflict_detected", "category": EventCategory.RBAC, "severity": EventSeverity.MEDIUM, "description": "Conflicto de roles detectado"},
    # Definición de roles (F005). Las asignaciones ya estaban catalogadas; lo que
    # faltaba era auditar la creación y edición del propio rol.
    {"event_code": "logistics.role.created", "category": EventCategory.RBAC, "severity": EventSeverity.HIGH, "description": "Rol personalizado creado"},
    {"event_code": "logistics.role.updated", "category": EventCategory.RBAC, "severity": EventSeverity.MEDIUM, "description": "Rol personalizado actualizado"},
    {"event_code": "logistics.role.activated", "category": EventCategory.RBAC, "severity": EventSeverity.HIGH, "description": "Rol personalizado activado"},
    {"event_code": "logistics.role.deactivated", "category": EventCategory.RBAC, "severity": EventSeverity.HIGH, "description": "Rol personalizado desactivado"},
    {"event_code": "logistics.role.permissions_updated", "category": EventCategory.RBAC, "severity": EventSeverity.HIGH, "description": "Permisos de rol actualizados"},
    {"event_code": "logistics.role.system_role_registered", "category": EventCategory.RBAC, "severity": EventSeverity.LOW, "description": "Rol de sistema registrado"},
    # Permissions
    {"event_code": "logistics.permission.authorization_allowed", "category": EventCategory.AUTHORIZATION, "severity": EventSeverity.INFO, "description": "Autorización permitida"},
    {"event_code": "logistics.permission.authorization_denied", "category": EventCategory.AUTHORIZATION, "severity": EventSeverity.MEDIUM, "description": "Autorización denegada"},
    {"event_code": "logistics.permission.catalog_seeded", "category": EventCategory.RBAC, "severity": EventSeverity.LOW, "description": "Catálogo de permisos sembrado"},
    {"event_code": "logistics.permission.role_permission_granted", "category": EventCategory.RBAC, "severity": EventSeverity.HIGH, "description": "Permiso concedido a rol"},
    {"event_code": "logistics.permission.role_permission_revoked", "category": EventCategory.RBAC, "severity": EventSeverity.HIGH, "description": "Permiso revocado de rol"},
    {"event_code": "logistics.permission.scope_denied", "category": EventCategory.AUTHORIZATION, "severity": EventSeverity.MEDIUM, "description": "Acceso denegado por alcance"},
    {"event_code": "logistics.permission.step_up_required", "category": EventCategory.AUTHORIZATION, "severity": EventSeverity.HIGH, "description": "Step-up requerido"},
    {"event_code": "logistics.permission.reason_missing", "category": EventCategory.AUTHORIZATION, "severity": EventSeverity.MEDIUM, "description": "Motivo requerido no proporcionado"},
    # Audit
    {"event_code": "logistics.audit.exported", "category": EventCategory.SECURITY, "severity": EventSeverity.HIGH, "description": "Auditoría exportada"},
    {"event_code": "logistics.audit.integrity_verified", "category": EventCategory.SECURITY, "severity": EventSeverity.LOW, "description": "Integridad verificada"},
    {"event_code": "logistics.audit.integrity_failed", "category": EventCategory.SECURITY, "severity": EventSeverity.CRITICAL, "description": "Verificación de integridad falló"},
    # Security
    {"event_code": "logistics.security.self_escalation_blocked", "category": EventCategory.SECURITY, "severity": EventSeverity.CRITICAL, "description": "Autoescalamiento bloqueado"},
    {"event_code": "logistics.security.cross_scope_access_denied", "category": EventCategory.SECURITY, "severity": EventSeverity.HIGH, "description": "Acceso entre alcances denegado"},
    # Document events (Fase 020)
    {"event_code": "logistics.document.draft_created", "category": EventCategory.DOCUMENT, "severity": EventSeverity.INFO, "description": "Borrador creado"},
    {"event_code": "logistics.document.draft_updated", "category": EventCategory.DOCUMENT, "severity": EventSeverity.INFO, "description": "Borrador actualizado"},
    {"event_code": "logistics.document.preview_rendered", "category": EventCategory.DOCUMENT, "severity": EventSeverity.INFO, "description": "Vista previa generada"},
    {"event_code": "logistics.document.issued", "category": EventCategory.DOCUMENT, "severity": EventSeverity.HIGH, "description": "Documento emitido"},
    {"event_code": "logistics.document.issue_failed", "category": EventCategory.DOCUMENT, "severity": EventSeverity.HIGH, "description": "Fallo al emitir documento"},
    {"event_code": "logistics.document.downloaded", "category": EventCategory.DOCUMENT, "severity": EventSeverity.LOW, "description": "Documento descargado"},
    {"event_code": "logistics.document.print_requested", "category": EventCategory.DOCUMENT, "severity": EventSeverity.LOW, "description": "Intención de impresión registrada"},
    {"event_code": "logistics.document.reprinted", "category": EventCategory.DOCUMENT, "severity": EventSeverity.CRITICAL, "description": "Documento reimpreso"},
    {"event_code": "logistics.document.reprint_failed", "category": EventCategory.DOCUMENT, "severity": EventSeverity.HIGH, "description": "Fallo al reimprimir documento"},
    {"event_code": "logistics.document.cancelled", "category": EventCategory.DOCUMENT, "severity": EventSeverity.CRITICAL, "description": "Documento anulado"},
    {"event_code": "logistics.document.cancel_failed", "category": EventCategory.DOCUMENT, "severity": EventSeverity.HIGH, "description": "Fallo al anular documento"},
    {"event_code": "logistics.document.original_accessed", "category": EventCategory.DOCUMENT, "severity": EventSeverity.HIGH, "description": "Original de anulado accedido"},
    {"event_code": "logistics.document.snapshot_created", "category": EventCategory.DOCUMENT, "severity": EventSeverity.LOW, "description": "Snapshot creado"},
    {"event_code": "logistics.document.artifact_created", "category": EventCategory.DOCUMENT, "severity": EventSeverity.LOW, "description": "Artefacto creado"},
    {"event_code": "logistics.document.artifact_hash_verified", "category": EventCategory.DOCUMENT, "severity": EventSeverity.LOW, "description": "Hash de artefacto verificado"},
    {"event_code": "logistics.document.talonario_rendered", "category": EventCategory.DOCUMENT, "severity": EventSeverity.MEDIUM, "description": "Talonario PDF renderizado"},
    {"event_code": "logistics.document.export_requested", "category": EventCategory.DOCUMENT, "severity": EventSeverity.MEDIUM, "description": "Exportación solicitada"},
    {"event_code": "logistics.document.export_ready", "category": EventCategory.DOCUMENT, "severity": EventSeverity.MEDIUM, "description": "Exportación lista"},
    {"event_code": "logistics.document.export_failed", "category": EventCategory.DOCUMENT, "severity": EventSeverity.HIGH, "description": "Exportación fallida"},
    {"event_code": "logistics.document.export_downloaded", "category": EventCategory.DOCUMENT, "severity": EventSeverity.LOW, "description": "Exportación descargada"},
    {"event_code": "logistics.document.package_generated", "category": EventCategory.DOCUMENT, "severity": EventSeverity.MEDIUM, "description": "Paquete por operación generado"},
    {"event_code": "logistics.document.permission_denied", "category": EventCategory.DOCUMENT, "severity": EventSeverity.HIGH, "description": "Acceso denegado a documento"},
    {"event_code": "logistics.document.step_up_required", "category": EventCategory.DOCUMENT, "severity": EventSeverity.HIGH, "description": "Step-up requerido para documento"},
    {"event_code": "logistics.document.integrity_failure", "category": EventCategory.DOCUMENT, "severity": EventSeverity.CRITICAL, "description": "Fallo de integridad en documento"},

    # Company Profile events (Fase 021)
    {"event_code": "logistics.company_profile.updated", "category": EventCategory.ORGANIZATION, "severity": EventSeverity.MEDIUM, "description": "Ficha institucional actualizada"},
    {"event_code": "logistics.company_profile.version_created", "category": EventCategory.ORGANIZATION, "severity": EventSeverity.MEDIUM, "description": "Versión borrador de ficha creada"},
    {"event_code": "logistics.company_profile.version_activated", "category": EventCategory.ORGANIZATION, "severity": EventSeverity.HIGH, "description": "Versión institucional activada"},
    {"event_code": "logistics.company_address.created", "category": EventCategory.ORGANIZATION, "severity": EventSeverity.LOW, "description": "Dirección institucional creada"},
    {"event_code": "logistics.company_address.updated", "category": EventCategory.ORGANIZATION, "severity": EventSeverity.LOW, "description": "Dirección institucional actualizada"},
    {"event_code": "logistics.company_address.primary_changed", "category": EventCategory.ORGANIZATION, "severity": EventSeverity.MEDIUM, "description": "Dirección principal cambiada"},
    {"event_code": "logistics.company_contact.created", "category": EventCategory.ORGANIZATION, "severity": EventSeverity.LOW, "description": "Contacto institucional creado"},
    {"event_code": "logistics.company_contact.updated", "category": EventCategory.ORGANIZATION, "severity": EventSeverity.LOW, "description": "Contacto institucional actualizado"},
    {"event_code": "logistics.company_asset.uploaded", "category": EventCategory.ORGANIZATION, "severity": EventSeverity.MEDIUM, "description": "Activo institucional cargado"},
    {"event_code": "logistics.company_asset.activated", "category": EventCategory.ORGANIZATION, "severity": EventSeverity.MEDIUM, "description": "Activo institucional activado"},
    {"event_code": "logistics.company_asset.revoked", "category": EventCategory.ORGANIZATION, "severity": EventSeverity.HIGH, "description": "Activo institucional me revocado"},
    {"event_code": "logistics.authorized_signer.created", "category": EventCategory.ORGANIZATION, "severity": EventSeverity.HIGH, "description": "Firmante autorizado creado"},
    {"event_code": "logistics.authorized_signer.updated", "category": EventCategory.ORGANIZATION, "severity": EventSeverity.MEDIUM, "description": "Firmante autorizado actualizado"},
    {"event_code": "logistics.authorized_signer.activated", "category": EventCategory.ORGANIZATION, "severity": EventSeverity.HIGH, "description": "Firmante autorizado activado"},
    {"event_code": "logistics.authorized_signer.suspended", "category": EventCategory.ORGANIZATION, "severity": EventSeverity.HIGH, "description": "Firmante autorizado suspendido"},
    {"event_code": "logistics.authorized_signer.revoked", "category": EventCategory.ORGANIZATION, "severity": EventSeverity.CRITICAL, "description": "Firmante autorizado revocado"},
    {"event_code": "logistics.numbering_policy.created", "category": EventCategory.DOCUMENT, "severity": EventSeverity.MEDIUM, "description": "Política de numeración creada"},
    {"event_code": "logistics.numbering_policy.updated", "category": EventCategory.DOCUMENT, "severity": EventSeverity.MEDIUM, "description": "Política de numeración actualizada"},

    # Phase 022 — Warehouses & Locations
    {"event_code": "logistics.warehouse.created", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Almacén creado"},
    {"event_code": "logistics.warehouse.updated", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Almacén actualizado"},
    {"event_code": "logistics.warehouse.activated", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.HIGH, "description": "Almacén activado"},
    {"event_code": "logistics.warehouse.deactivated", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.HIGH, "description": "Almacén desactivado"},
    {"event_code": "logistics.warehouse.archived", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.CRITICAL, "description": "Almacén archivado"},
    {"event_code": "logistics.warehouse_location.created", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.LOW, "description": "Ubicación de almacén creada"},
    {"event_code": "logistics.warehouse_location.updated", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.LOW, "description": "Ubicación de almacén actualizada"},
    {"event_code": "logistics.warehouse_location.moved", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.HIGH, "description": "Ubicación de almacén movida"},
    {"event_code": "logistics.warehouse_location.bulk_created", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.HIGH, "description": "Generación masiva de ubicaciones"},
    {"event_code": "logistics.warehouse_location.capacity_added", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.LOW, "description": "Capacidad agregada a ubicación"},
    {"event_code": "logistics.warehouse_location.restriction_added", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Restricción agregada a ubicación"},
    {"event_code": "logistics.warehouse_layout.version_created", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.LOW, "description": "Versión de layout creada"},
    {"event_code": "logistics.warehouse_layout.activated", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.HIGH, "description": "Versión de layout activada"},
    {"event_code": "logistics.warehouse_location.qr_generated", "category": EventCategory.SECURITY, "severity": EventSeverity.LOW, "description": "QR de ubicación generado"},
    {"event_code": "logistics.warehouse_location.qr_rotated", "category": EventCategory.SECURITY, "severity": EventSeverity.HIGH, "description": "QR de ubicación rotado"},
    {"event_code": "logistics.warehouse_location.label_downloaded", "category": EventCategory.DOCUMENT, "severity": EventSeverity.LOW, "description": "Etiqueta PDF descargada"},
    {"event_code": "logistics.warehouse_location.batch_labels_downloaded", "category": EventCategory.DOCUMENT, "severity": EventSeverity.LOW, "description": "Lote de etiquetas PDF descargado"},

    # Phase 023 — Product Catalog
    {"event_code": "logistics.product.created", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Producto creado"},
    {"event_code": "logistics.product.updated", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Producto actualizado"},
    {"event_code": "logistics.product.activated", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.HIGH, "description": "Producto activado"},
    {"event_code": "logistics.product.SKU_changed", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.CRITICAL, "description": "SKU de producto modificado"},
    {"event_code": "logistics.product_category.created", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Categoría de producto creada"},
    {"event_code": "logistics.product_brand.created", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Marca de producto creada"},
    {"event_code": "logistics.product_identifier.created", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Identificador de producto registrado"},
    {"event_code": "logistics.product_location_compatibility.evaluated", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.LOW, "description": "Compatibilidad producto-ubicación evaluada"},

    # Phase 024 — Units & Conversions
    {"event_code": "logistics.unit.created", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Unidad de medida creada"},
    {"event_code": "logistics.unit.activated", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.HIGH, "description": "Unidad de medida activada"},
    {"event_code": "logistics.unit_conversion_rule.activated", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.HIGH, "description": "Regla de conversión activada"},
    {"event_code": "logistics.unit_conversion_rule.ambiguity_detected", "category": EventCategory.SECURITY, "severity": EventSeverity.HIGH, "description": "Ambivalencia/Ambigüedad en conversión detectada"},
    {"event_code": "logistics.unit_conversion_rule.cycle_detected", "category": EventCategory.SECURITY, "severity": EventSeverity.HIGH, "description": "Ciclo en grafo de conversión detectado"},
    {"event_code": "logistics.product_unit_configuration.created", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Configuración de unidades de producto creada"},
    {"event_code": "logistics.product_unit_configuration.updated", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.HIGH, "description": "Configuración de unidades de producto actualizada"},
    {"event_code": "logistics.product_packaging.activated", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.HIGH, "description": "Empaque de producto activado"},
    {"event_code": "logistics.unit_conversion.evaluated", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.LOW, "description": "Conversión de unidad evaluada"},
    {"event_code": "logistics.unit_conversion.decomposed", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.LOW, "description": "Descomposición de empaque evaluada"},

    # Phase 025 — Business Partners
    {"event_code": "logistics.business_partner.created", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Socio de negocio creado"},
    {"event_code": "logistics.business_partner.updated", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Socio de negocio actualizado"},
    {"event_code": "logistics.business_partner.activated", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.HIGH, "description": "Socio de negocio activado"},
    {"event_code": "logistics.business_partner.deactivated", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.HIGH, "description": "Socio de negocio desactivado"},
    {"event_code": "logistics.business_partner.suspended", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.HIGH, "description": "Socio de negocio suspendido"},
    {"event_code": "logistics.business_partner.blocked", "category": EventCategory.SECURITY, "severity": EventSeverity.CRITICAL, "description": "Socio de negocio bloqueado"},
    {"event_code": "logistics.business_partner.unblocked", "category": EventCategory.SECURITY, "severity": EventSeverity.CRITICAL, "description": "Socio de negocio desbloqueado"},
    {"event_code": "logistics.business_partner.archived", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.HIGH, "description": "Socio de negocio archivado"},
    {"event_code": "logistics.business_partner.version_created", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Versión de socio creada"},
    {"event_code": "logistics.business_partner.version_activated", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.HIGH, "description": "Versión de socio activada"},
    {"event_code": "logistics.business_partner.duplicate_detected", "category": EventCategory.SECURITY, "severity": EventSeverity.HIGH, "description": "Duplicado de socio detectado"},
    {"event_code": "logistics.business_partner_role.created", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Rol de socio creado"},
    {"event_code": "logistics.business_partner_role.activated", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.HIGH, "description": "Rol de socio activado"},
    {"event_code": "logistics.business_partner_role.suspended", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.HIGH, "description": "Rol de socio suspendido"},
    {"event_code": "logistics.business_partner_role.archived", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.HIGH, "description": "Rol de socio archivado"},
    {"event_code": "logistics.business_partner_identifier.created", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Identificador de socio creado"},
    {"event_code": "logistics.business_partner_evaluation.approved", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.HIGH, "description": "Evaluación de socio aprobada"},
    {"event_code": "logistics.business_partner_document.created", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Documento de socio registrado"},

    # Phase 026 — RUC Lookup and SUNAT Reduced Registry Integration
    {"event_code": "logistics.ruc.lookup_performed", "category": EventCategory.INTEGRATION, "severity": EventSeverity.LOW, "description": "Consulta de RUC realizada"},
    {"event_code": "logistics.ruc.lookup_not_found", "category": EventCategory.INTEGRATION, "severity": EventSeverity.LOW, "description": "Consulta de RUC sin resultados"},
    {"event_code": "logistics.ruc.lookup_stale", "category": EventCategory.INTEGRATION, "severity": EventSeverity.MEDIUM, "description": "Consulta RUC con datos de antigüedad elevada"},
    {"event_code": "logistics.ruc.lookup_rate_limited", "category": EventCategory.SECURITY, "severity": EventSeverity.HIGH, "description": "Límite de tasa excedido en consultas RUC"},
    {"event_code": "logistics.ruc.provider_called", "category": EventCategory.INTEGRATION, "severity": EventSeverity.LOW, "description": "Invocación a proveedor autorizado RUC"},
    {"event_code": "logistics.ruc.provider_failed", "category": EventCategory.INTEGRATION, "severity": EventSeverity.HIGH, "description": "Fallo en proveedor autorizado RUC"},
    {"event_code": "logistics.ruc.conflict_detected", "category": EventCategory.SECURITY, "severity": EventSeverity.HIGH, "description": "Conflicto de datos RUC detectado"},
    {"event_code": "logistics.ruc.import_requested", "category": EventCategory.INTEGRATION, "severity": EventSeverity.MEDIUM, "description": "Importación de RUC solicitada"},
    {"event_code": "logistics.ruc.import_started", "category": EventCategory.INTEGRATION, "severity": EventSeverity.MEDIUM, "description": "Importación de RUC iniciada"},
    {"event_code": "logistics.ruc.import_completed", "category": EventCategory.INTEGRATION, "severity": EventSeverity.HIGH, "description": "Importación de RUC completada"},
    {"event_code": "logistics.ruc.import_failed", "category": EventCategory.INTEGRATION, "severity": EventSeverity.HIGH, "description": "Importación de RUC fallida"},
    {"event_code": "logistics.ruc.dataset_activated", "category": EventCategory.INTEGRATION, "severity": EventSeverity.HIGH, "description": "Dataset RUC activado atómicamente"},
    {"event_code": "logistics.ruc.dataset_rolled_back", "category": EventCategory.SECURITY, "severity": EventSeverity.CRITICAL, "description": "Rollback de dataset RUC realizado"},
    {"event_code": "logistics.ruc.assisted_verification_created", "category": EventCategory.INTEGRATION, "severity": EventSeverity.MEDIUM, "description": "Verificación asistida RUC registrada"},
    {"event_code": "logistics.ruc.assisted_verification_approved", "category": EventCategory.INTEGRATION, "severity": EventSeverity.HIGH, "description": "Verificación asistida RUC aprobada"},
    {"event_code": "logistics.business_partner.ruc_verified", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.HIGH, "description": "Verificación de RUC registrada en socio"},
    {"event_code": "logistics.business_partner.ruc_data_applied", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.HIGH, "description": "Campos verificados de RUC aplicados a socio"},
    {"event_code": "logistics.business_partner.ruc_conflict_detected", "category": EventCategory.SECURITY, "severity": EventSeverity.HIGH, "description": "Conflicto de RUC detectado en socio"},

    # Phase 027 — Vehicle Master Events
    {"event_code": "logistics.vehicle.created", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Vehículo registrado en Borrador"},
    {"event_code": "logistics.vehicle.updated", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.LOW, "description": "Datos generales de vehículo actualizados"},
    {"event_code": "logistics.vehicle.activated", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.HIGH, "description": "Vehículo activado"},
    {"event_code": "logistics.vehicle.suspended", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.HIGH, "description": "Vehículo suspendido"},
    {"event_code": "logistics.vehicle.blocked", "category": EventCategory.SECURITY, "severity": EventSeverity.CRITICAL, "description": "Vehículo bloqueado manualmente"},
    {"event_code": "logistics.vehicle.unblocked", "category": EventCategory.SECURITY, "severity": EventSeverity.CRITICAL, "description": "Vehículo desbloqueado"},
    {"event_code": "logistics.vehicle.retired", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.CRITICAL, "description": "Vehículo retirado permanentemente"},
    {"event_code": "logistics.vehicle.plate_changed", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.HIGH, "description": "Placa vehicular actualizada con alias"},
    {"event_code": "logistics.vehicle.capacity_profile_created", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Perfil de capacidad registrado"},
    {"event_code": "logistics.vehicle.owner_assigned", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Propietario asignado a vehículo"},
    {"event_code": "logistics.vehicle.carrier_assigned", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.HIGH, "description": "Transportista asignado a vehículo"},
    {"event_code": "logistics.vehicle.document_created", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Documento vehicular registrado"},
    {"event_code": "logistics.vehicle.document_reviewed", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Metadatos de documento vehicular revisados"},

    # Phase 028 — Vehicle Verification Events
    {"event_code": "logistics.vehicle_verification.requested", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Solicitud de verificación vehicular iniciada"},
    {"event_code": "logistics.vehicle_verification.completed", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.HIGH, "description": "Verificación vehicular completada exitosamente"},
    {"event_code": "logistics.vehicle_verification.failed", "category": EventCategory.SECURITY, "severity": EventSeverity.MEDIUM, "description": "Error o fallo en consulta de verificación vehicular"},
    {"event_code": "logistics.vehicle_verification.source_enabled", "category": EventCategory.SECURITY, "severity": EventSeverity.HIGH, "description": "Fuente de verificación vehicular habilitada"},
    {"event_code": "logistics.vehicle_verification.source_disabled", "category": EventCategory.SECURITY, "severity": EventSeverity.HIGH, "description": "Fuente de verificación vehicular deshabilitada"},
    {"event_code": "logistics.vehicle_verification.assisted_created", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Verificación vehicular asistida registrada"},
    {"event_code": "logistics.vehicle_verification.assisted_approved", "category": EventCategory.SECURITY, "severity": EventSeverity.HIGH, "description": "Verificación vehicular asistida aprobada"},
    {"event_code": "logistics.vehicle_verification.assisted_rejected", "category": EventCategory.SECURITY, "severity": EventSeverity.MEDIUM, "description": "Verificación vehicular asistida rechazada"},
    {"event_code": "logistics.vehicle_verification.data_applied", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.HIGH, "description": "Campos verificados aplicados a vehículo"},

    # Phase 029 — Driver Master Events
    {"event_code": "logistics.driver.created", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Conductor registrado"},
    {"event_code": "logistics.driver.updated", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Datos de conductor actualizados"},
    {"event_code": "logistics.driver.activated", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.HIGH, "description": "Conductor activado operacionalmente"},
    {"event_code": "logistics.driver.blocked", "category": EventCategory.SECURITY, "severity": EventSeverity.CRITICAL, "description": "Conductor bloqueado por sanción o seguridad"},
    {"event_code": "logistics.driver.unblocked", "category": EventCategory.SECURITY, "severity": EventSeverity.HIGH, "description": "Bloqueo de conductor retirado"},
    {"event_code": "logistics.driver.version_created", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Snapshot de versión de conductor generado"},
    {"event_code": "logistics.driver.identity_document_created", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Documento de identidad de conductor registrado"},
    {"event_code": "logistics.driver.license_created", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.HIGH, "description": "Licencia de conducir de conductor registrada"},
    {"event_code": "logistics.driver.license_category_assigned", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.HIGH, "description": "Categoría asignada a licencia de conducir"},
    {"event_code": "logistics.driver.carrier_assigned", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.HIGH, "description": "Conductor asignado a transportista"},
    {"event_code": "logistics.driver.contact_created", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.LOW, "description": "Contacto de conductor registrado"},
    {"event_code": "logistics.driver.photo_linked", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Fotografía de conductor vinculada mediante referencia"},
    {"event_code": "logistics.driver.document_created", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Documento adicional de conductor registrado"},
    {"event_code": "logistics.driver.restriction_created", "category": EventCategory.SECURITY, "severity": EventSeverity.HIGH, "description": "Restricción operativa aplicada a conductor"},
    {"event_code": "logistics.driver.restriction_revoked", "category": EventCategory.SECURITY, "severity": EventSeverity.HIGH, "description": "Restricción operativa de conductor revocada"},

    # Phase 030 — Files & Evidence Centralization Events
    {"event_code": "logistics.file.upload_session_created", "category": EventCategory.SYSTEM, "severity": EventSeverity.LOW, "description": "Sesión de carga de archivo creada"},
    {"event_code": "logistics.file.upload_completed", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Archivo subido, escaneado y promovido a almacenamiento disponible"},
    {"event_code": "logistics.file.metadata_updated", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.LOW, "description": "Metadatos de archivo actualizados"},
    {"event_code": "logistics.file.downloaded", "category": EventCategory.SECURITY, "severity": EventSeverity.MEDIUM, "description": "Archivo o URL firmada solicitada para descarga"},
    {"event_code": "logistics.file.previewed", "category": EventCategory.SECURITY, "severity": EventSeverity.LOW, "description": "Vista previa de archivo generada"},
    {"event_code": "logistics.file.associated", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Archivo vinculado a recurso de dominio"},
    {"event_code": "logistics.file.association_removed", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Vinculación de archivo removida de recurso"},
    {"event_code": "logistics.file.archived", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.HIGH, "description": "Archivo archivado"},
    {"event_code": "logistics.file.restored", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.HIGH, "description": "Archivo archivado restaurado"},
    {"event_code": "logistics.evidence.created", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.HIGH, "description": "Registro de evidencia formal creado"},
    {"event_code": "logistics.evidence.accepted", "category": EventCategory.SECURITY, "severity": EventSeverity.CRITICAL, "description": "Evidencia inmutable aceptada formalmente"},
    {"event_code": "logistics.evidence.revoked", "category": EventCategory.SECURITY, "severity": EventSeverity.CRITICAL, "description": "Evidencia previamente aceptada revocada"},
    {"event_code": "logistics.file.legal_hold_applied", "category": EventCategory.SECURITY, "severity": EventSeverity.CRITICAL, "description": "Retención legal (Legal Hold) aplicada a archivo"},
    {"event_code": "logistics.file.legal_hold_released", "category": EventCategory.SECURITY, "severity": EventSeverity.HIGH, "description": "Retención legal (Legal Hold) liberada"},
    {"event_code": "logistics.file.deletion_requested", "category": EventCategory.SECURITY, "severity": EventSeverity.HIGH, "description": "Solicitud de eliminación controlada creada"},
    {"event_code": "logistics.file.deletion_approved", "category": EventCategory.SECURITY, "severity": EventSeverity.CRITICAL, "description": "Solicitud de eliminación de archivo aprobada"},

    # Phase 031 — Purchase Requisitions & Cost Centers Events
    {"event_code": "logistics.cost_center.created", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Centro de costo creado"},
    {"event_code": "logistics.cost_center.updated", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.LOW, "description": "Centro de costo actualizado"},
    {"event_code": "logistics.purchase_requisition.created", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Solicitud de compra registrada en borrador"},
    {"event_code": "logistics.purchase_requisition.updated", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.LOW, "description": "Borrador de solicitud de compra actualizado"},
    {"event_code": "logistics.purchase_requisition.line_created", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.LOW, "description": "Línea agregada a revisión de solicitud de compra"},
    {"event_code": "logistics.purchase_requisition.line_updated", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.LOW, "description": "Línea de solicitud de compra actualizada"},
    {"event_code": "logistics.purchase_requisition.line_removed", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.LOW, "description": "Línea removida de revisión de solicitud"},
    {"event_code": "logistics.purchase_requisition.lines_reordered", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.LOW, "description": "Líneas de solicitud de compra reordenadas"},
    {"event_code": "logistics.purchase_requisition.submitted", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.HIGH, "description": "Solicitud de compra enviada para aprobación y congelada"},
    {"event_code": "logistics.purchase_requisition.review_started", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Revisión de solicitud de compra iniciada"},
    {"event_code": "logistics.purchase_requisition.approved", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.HIGH, "description": "Solicitud de compra aprobada formalmente"},
    {"event_code": "logistics.purchase_requisition.rejected", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.HIGH, "description": "Solicitud de compra rechazada"},
    {"event_code": "logistics.purchase_requisition.returned", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Solicitud de compra devuelta para correcciones con nueva revisión"},
    {"event_code": "logistics.purchase_requisition.withdrawn", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Solicitud de compra retirada por el solicitante"},
    {"event_code": "logistics.purchase_requisition.cancelled", "category": EventCategory.SECURITY, "severity": EventSeverity.HIGH, "description": "Solicitud de compra cancelada"},
    {"event_code": "logistics.purchase_requisition.comment_created", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.LOW, "description": "Comentario registrado en solicitud de compra"},
    {"event_code": "logistics.purchase_requisition.document_issued", "category": EventCategory.DOCUMENT, "severity": EventSeverity.HIGH, "description": "Documento oficial PDF de solicitud de compra emitido"},
    {"event_code": "logistics.purchase_requisition.document_downloaded", "category": EventCategory.DOCUMENT, "severity": EventSeverity.LOW, "description": "Documento PDF de solicitud descargado"},

    # Phase 033 — Supplier Evaluations Events
    {"event_code": "logistics.supplier_evaluation_template.created", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Plantilla de evaluación de proveedores creada"},
    {"event_code": "logistics.supplier_evaluation_template.version_created", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Versión de plantilla de evaluación creada con ponderaciones"},
    {"event_code": "logistics.supplier_evaluation_template.activated", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.HIGH, "description": "Versión inmutable de plantilla de evaluación activada"},
    {"event_code": "logistics.quotation_evaluation.created", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Evaluación de cotización registrada en borrador"},
    {"event_code": "logistics.quotation_evaluation.calculated", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.HIGH, "description": "Motor determinista de scoring ejecutado exitosamente"},
    {"event_code": "logistics.quotation_evaluation.manual_score_submitted", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Puntaje manual evidenciado registrado"},
    {"event_code": "logistics.quotation_evaluation.decision_recorded", "category": EventCategory.SECURITY, "severity": EventSeverity.CRITICAL, "description": "Decisión de adjudicación recomendada registrada de forma inmutable"},

    # Phase 034 — Purchase Orders Events
    {"event_code": "logistics.purchase_order.created_from_decision", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.HIGH, "description": "Orden de compra generada desde decisión de evaluación CCO"},
    {"event_code": "logistics.purchase_order.submitted_for_approval", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Orden de compra enviada a flujo de aprobación"},
    {"event_code": "logistics.purchase_order.approved", "category": EventCategory.SECURITY, "severity": EventSeverity.CRITICAL, "description": "Orden de compra aprobada con autenticación step-up"},
    {"event_code": "logistics.purchase_order.rejected", "category": EventCategory.SECURITY, "severity": EventSeverity.HIGH, "description": "Orden de compra rechazada en flujo de aprobación"},
    {"event_code": "logistics.purchase_order.returned_for_changes", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Orden de compra devuelta para modificaciones"},
    {"event_code": "logistics.purchase_order.cancelled", "category": EventCategory.SECURITY, "severity": EventSeverity.HIGH, "description": "Orden de compra cancelada de forma inmutable"},

    # Phase 035 — Procurement Approval Engine Events
    {"event_code": "logistics.procurement_approval_policy.created", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Política de aprobación de compras creada"},
    {"event_code": "logistics.procurement_approval_policy.activated", "category": EventCategory.SECURITY, "severity": EventSeverity.HIGH, "description": "Versión de política de aprobación activada"},
    {"event_code": "logistics.procurement_approval.request_created", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Solicitud de aprobación de compras registrada y cadena compilada"},
    {"event_code": "logistics.procurement_approval.approved", "category": EventCategory.SECURITY, "severity": EventSeverity.CRITICAL, "description": "Decisión de aprobación registrada con autenticación step-up"},
    {"event_code": "logistics.procurement_approval.rejected", "category": EventCategory.SECURITY, "severity": EventSeverity.HIGH, "description": "Decisión de rechazo de compras registrada"},
    {"event_code": "logistics.procurement_approval.returned", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Solicitud de compras devuelta para observaciones"},
    {"event_code": "logistics.procurement_approval.audit_seal_created", "category": EventCategory.SECURITY, "severity": EventSeverity.CRITICAL, "description": "Sello de auditoría criptográfico SHA-256 generado para la cadena completada"},
    {"event_code": "logistics.procurement_approval.audit_seal_verified", "category": EventCategory.SECURITY, "severity": EventSeverity.MEDIUM, "description": "Verificación de integridad del sello de auditoría realizada"},

    # Phase 036 — Arrival Notices & Reception Appointments
    {"event_code": "logistics.arrival_notice.created", "category": EventCategory.TRANSPORT, "severity": EventSeverity.MEDIUM, "description": "Aviso de llegada creado"},
    {"event_code": "logistics.arrival_notice.updated", "category": EventCategory.TRANSPORT, "severity": EventSeverity.LOW, "description": "Aviso de llegada actualizado"},
    {"event_code": "logistics.arrival_notice.revision_created", "category": EventCategory.TRANSPORT, "severity": EventSeverity.MEDIUM, "description": "Revisión de aviso creada"},
    {"event_code": "logistics.arrival_notice.line_created", "category": EventCategory.TRANSPORT, "severity": EventSeverity.MEDIUM, "description": "Línea esperada asignada a una OC"},
    {"event_code": "logistics.arrival_notice.submitted", "category": EventCategory.SECURITY, "severity": EventSeverity.HIGH, "description": "Aviso enviado y revisión congelada"},
    {"event_code": "logistics.arrival_notice.review_started", "category": EventCategory.TRANSPORT, "severity": EventSeverity.MEDIUM, "description": "Revisión de aviso iniciada"},
    {"event_code": "logistics.arrival_notice.changes_requested", "category": EventCategory.TRANSPORT, "severity": EventSeverity.MEDIUM, "description": "Cambios solicitados al aviso"},
    {"event_code": "logistics.arrival_notice.ready_for_scheduling", "category": EventCategory.TRANSPORT, "severity": EventSeverity.HIGH, "description": "Aviso listo para programación"},
    {"event_code": "logistics.arrival_notice.cancelled", "category": EventCategory.SECURITY, "severity": EventSeverity.HIGH, "description": "Aviso cancelado y allocations liberados"},
    {"event_code": "logistics.arrival_notice.vehicle_selected", "category": EventCategory.TRANSPORT, "severity": EventSeverity.MEDIUM, "description": "Vehículo maestro seleccionado"},
    {"event_code": "logistics.arrival_notice.vehicle_override", "category": EventCategory.SECURITY, "severity": EventSeverity.HIGH, "description": "Referencia manual de vehículo registrada"},
    {"event_code": "logistics.arrival_notice.driver_selected", "category": EventCategory.TRANSPORT, "severity": EventSeverity.MEDIUM, "description": "Conductor maestro seleccionado"},
    {"event_code": "logistics.arrival_notice.driver_override", "category": EventCategory.SECURITY, "severity": EventSeverity.HIGH, "description": "Referencia manual de conductor registrada"},
    {"event_code": "logistics.arrival_notice.transport_document_added", "category": EventCategory.DOCUMENT, "severity": EventSeverity.MEDIUM, "description": "Documento de transporte agregado"},
    {"event_code": "logistics.arrival_notice.guide_registered", "category": EventCategory.DOCUMENT, "severity": EventSeverity.MEDIUM, "description": "Guía de transporte registrada"},
    {"event_code": "logistics.arrival_notice.file_associated", "category": EventCategory.DOCUMENT, "severity": EventSeverity.MEDIUM, "description": "Archivo asociado a documento de transporte"},
    {"event_code": "logistics.reception_calendar.created", "category": EventCategory.ORGANIZATION, "severity": EventSeverity.MEDIUM, "description": "Calendario de recepción creado"},
    {"event_code": "logistics.reception_calendar.updated", "category": EventCategory.ORGANIZATION, "severity": EventSeverity.MEDIUM, "description": "Calendario de recepción actualizado"},
    {"event_code": "logistics.reception_calendar.active", "category": EventCategory.SECURITY, "severity": EventSeverity.HIGH, "description": "Calendario de recepción activado"},
    {"event_code": "logistics.reception_calendar.inactive", "category": EventCategory.SECURITY, "severity": EventSeverity.HIGH, "description": "Calendario de recepción desactivado"},
    {"event_code": "logistics.reception_calendar.archived", "category": EventCategory.SECURITY, "severity": EventSeverity.HIGH, "description": "Calendario de recepción archivado"},
    {"event_code": "logistics.reception_calendar.window_created", "category": EventCategory.ORGANIZATION, "severity": EventSeverity.MEDIUM, "description": "Horario operativo de recepción creado"},
    {"event_code": "logistics.reception_calendar.blackout_created", "category": EventCategory.SECURITY, "severity": EventSeverity.CRITICAL, "description": "Bloqueo de calendario creado"},
    {"event_code": "logistics.reception_calendar.capacity_override", "category": EventCategory.SECURITY, "severity": EventSeverity.CRITICAL, "description": "Capacidad de recepción sobrepasada con autorización"},
    {"event_code": "logistics.reception_appointment.hold_created", "category": EventCategory.TRANSPORT, "severity": EventSeverity.MEDIUM, "description": "Hold temporal de franja creado"},
    {"event_code": "logistics.reception_appointment.hold_cancelled", "category": EventCategory.TRANSPORT, "severity": EventSeverity.LOW, "description": "Hold temporal cancelado"},
    {"event_code": "logistics.reception_appointment.hold_refreshed", "category": EventCategory.SECURITY, "severity": EventSeverity.MEDIUM, "description": "Hold temporal renovado"},
    {"event_code": "logistics.reception_appointment.hold_expired", "category": EventCategory.SYSTEM, "severity": EventSeverity.LOW, "description": "Hold temporal expirado"},
    {"event_code": "logistics.reception_appointment.created", "category": EventCategory.TRANSPORT, "severity": EventSeverity.MEDIUM, "description": "Cita de recepción propuesta"},
    {"event_code": "logistics.reception_appointment.confirmed", "category": EventCategory.SECURITY, "severity": EventSeverity.HIGH, "description": "Cita de recepción confirmada"},
    {"event_code": "logistics.reception_appointment.rescheduled", "category": EventCategory.SECURITY, "severity": EventSeverity.HIGH, "description": "Cita de recepción reprogramada"},
    {"event_code": "logistics.reception_appointment.cancelled", "category": EventCategory.SECURITY, "severity": EventSeverity.HIGH, "description": "Cita de recepción cancelada"},
    {"event_code": "logistics.reception_appointment.window_elapsed", "category": EventCategory.SYSTEM, "severity": EventSeverity.LOW, "description": "Ventana de cita transcurrida sin registrar llegada"},
    {"event_code": "logistics.reception_appointment.CIT_issued", "category": EventCategory.DOCUMENT, "severity": EventSeverity.HIGH, "description": "CIT emitida por el motor documental"},
    {"event_code": "logistics.reception_appointment.document_downloaded", "category": EventCategory.DOCUMENT, "severity": EventSeverity.LOW, "description": "Documento de cita descargado"},

    # Phase 038 — Dock Operations & Unloading
    {"event_code": "logistics.warehouse_dock.created", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Maestro de muelle creado"},
    {"event_code": "logistics.warehouse_dock.updated", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Maestro de muelle actualizado"},
    {"event_code": "logistics.warehouse_dock.status_changed", "category": EventCategory.SECURITY, "severity": EventSeverity.HIGH, "description": "Estado de muelle modificado"},
    {"event_code": "logistics.warehouse_dock.capability_added", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Capacidad de muelle agregada"},
    {"event_code": "logistics.warehouse_dock.window_added", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Ventana operativa de muelle agregada"},
    {"event_code": "logistics.warehouse_dock.window_updated", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Ventana operativa de muelle actualizada"},
    {"event_code": "logistics.warehouse_dock.window_deactivated", "category": EventCategory.SECURITY, "severity": EventSeverity.HIGH, "description": "Ventana operativa de muelle desactivada"},
    {"event_code": "logistics.warehouse_dock.blackout_created", "category": EventCategory.SECURITY, "severity": EventSeverity.CRITICAL, "description": "Blackout de muelle creado"},
    {"event_code": "logistics.warehouse_dock.blackout_cancelled", "category": EventCategory.SECURITY, "severity": EventSeverity.HIGH, "description": "Blackout de muelle cancelado"},
    {"event_code": "logistics.inbound_dock_queue.created", "category": EventCategory.TRANSPORT, "severity": EventSeverity.MEDIUM, "description": "Ingreso agregado a cola interna de muelles"},
    {"event_code": "logistics.inbound_dock_queue.ready", "category": EventCategory.TRANSPORT, "severity": EventSeverity.MEDIUM, "description": "Ingreso listo para asignación de muelle"},
    {"event_code": "logistics.inbound_dock_queue.held", "category": EventCategory.TRANSPORT, "severity": EventSeverity.HIGH, "description": "Ingreso retenido en cola de muelles"},
    {"event_code": "logistics.inbound_dock_queue.priority_changed", "category": EventCategory.SECURITY, "severity": EventSeverity.HIGH, "description": "Prioridad de cola modificada con motivo"},
    {"event_code": "logistics.inbound_dock_assignment.planned", "category": EventCategory.TRANSPORT, "severity": EventSeverity.MEDIUM, "description": "Plan determinista de asignación generado"},
    {"event_code": "logistics.inbound_dock_assignment.created", "category": EventCategory.SECURITY, "severity": EventSeverity.HIGH, "description": "Muelle asignado al ingreso"},
    {"event_code": "logistics.inbound_dock_assignment.movement_started", "category": EventCategory.TRANSPORT, "severity": EventSeverity.MEDIUM, "description": "Movimiento al muelle iniciado"},
    {"event_code": "logistics.inbound_dock_assignment.arrived_at_dock", "category": EventCategory.TRANSPORT, "severity": EventSeverity.MEDIUM, "description": "Vehículo confirmado en muelle"},
    {"event_code": "logistics.inbound_dock_assignment.cancelled", "category": EventCategory.SECURITY, "severity": EventSeverity.HIGH, "description": "Asignación de muelle cancelada"},
    {"event_code": "logistics.inbound_dock_assignment.reassigned", "category": EventCategory.SECURITY, "severity": EventSeverity.HIGH, "description": "Asignación de muelle reemplazada"},
    {"event_code": "logistics.inbound_dock_assignment.released", "category": EventCategory.TRANSPORT, "severity": EventSeverity.MEDIUM, "description": "Ocupación de muelle liberada"},
    {"event_code": "logistics.unloading_operation.created", "category": EventCategory.TRANSPORT, "severity": EventSeverity.MEDIUM, "description": "Operación de descarga creada"},
    {"event_code": "logistics.unloading_operation.readiness_completed", "category": EventCategory.TRANSPORT, "severity": EventSeverity.MEDIUM, "description": "Readiness de descarga evaluado"},
    {"event_code": "logistics.unloading_operation.responsible_assigned", "category": EventCategory.SECURITY, "severity": EventSeverity.MEDIUM, "description": "Responsable de descarga asignado"},
    {"event_code": "logistics.unloading_operation.equipment_assigned", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.MEDIUM, "description": "Referencia controlada de equipo asignada"},
    {"event_code": "logistics.unloading_operation.equipment_released", "category": EventCategory.MASTER_DATA, "severity": EventSeverity.LOW, "description": "Referencia controlada de equipo liberada"},
    {"event_code": "logistics.unloading_operation.seal_opened", "category": EventCategory.SECURITY, "severity": EventSeverity.HIGH, "description": "Apertura de precinto registrada"},
    {"event_code": "logistics.unloading_operation.started", "category": EventCategory.SECURITY, "severity": EventSeverity.HIGH, "description": "Descarga iniciada con hora de servidor"},
    {"event_code": "logistics.unloading_operation.cancelled", "category": EventCategory.SECURITY, "severity": EventSeverity.HIGH, "description": "Operación de descarga cancelada antes del inicio"},
    {"event_code": "logistics.unloading_operation.paused", "category": EventCategory.TRANSPORT, "severity": EventSeverity.MEDIUM, "description": "Descarga pausada con motivo"},
    {"event_code": "logistics.unloading_operation.pause_cancelled", "category": EventCategory.SECURITY, "severity": EventSeverity.HIGH, "description": "Pausa operativa anulada con trazabilidad"},
    {"event_code": "logistics.unloading_operation.resumed", "category": EventCategory.TRANSPORT, "severity": EventSeverity.MEDIUM, "description": "Descarga reanudada"},
    {"event_code": "logistics.unloading_operation.aborted", "category": EventCategory.SECURITY, "severity": EventSeverity.CRITICAL, "description": "Descarga abortada"},
    {"event_code": "logistics.unloading_operation.completed", "category": EventCategory.SECURITY, "severity": EventSeverity.HIGH, "description": "Descarga finalizada con duraciones calculadas"},
    {"event_code": "logistics.unloading_operation.time_correction_requested", "category": EventCategory.SECURITY, "severity": EventSeverity.CRITICAL, "description": "Corrección de tiempo operativo solicitada"},
    {"event_code": "logistics.unloading_operation.time_correction_approved", "category": EventCategory.SECURITY, "severity": EventSeverity.CRITICAL, "description": "Corrección de tiempo operativo aprobada"},
    {"event_code": "logistics.dock_operation_export.requested", "category": EventCategory.DOCUMENT, "severity": EventSeverity.HIGH, "description": "Exportación operativa de muelles solicitada"},
    {"event_code": "logistics.dock_operation_export.ready", "category": EventCategory.DOCUMENT, "severity": EventSeverity.MEDIUM, "description": "Exportación operativa de muelles disponible"},
    {"event_code": "logistics.dock_operation_export.failed", "category": EventCategory.DOCUMENT, "severity": EventSeverity.HIGH, "description": "Exportación operativa de muelles fallida"},
    {"event_code": "logistics.dock_operation_export.downloaded", "category": EventCategory.DOCUMENT, "severity": EventSeverity.MEDIUM, "description": "Exportación operativa de muelles descargada"},

    # Phase 039 — receiving observations and future-difference candidates.
    *[
        {"event_code": code, "category": EventCategory.SECURITY if any(x in code for x in ("completed", "cancelled", "compensated", "integrity_failed")) else EventCategory.TRANSPORT, "severity": EventSeverity.HIGH if any(x in code for x in ("failed", "duplicate", "difference", "expired", "completed", "cancelled", "compensated")) else EventSeverity.MEDIUM, "description": "Evento auditable de recepción física Fase 039"}
        for code in (
            "logistics.inbound_receipt.created", "logistics.inbound_receipt.prepared", "logistics.inbound_receipt.started", "logistics.inbound_receipt.paused", "logistics.inbound_receipt.resumed", "logistics.inbound_receipt.validation_started", "logistics.inbound_receipt.validation_failed", "logistics.inbound_receipt.partially_received", "logistics.inbound_receipt.fully_received", "logistics.inbound_receipt.completed", "logistics.inbound_receipt.cancelled", "logistics.inbound_receipt.scan_session_started", "logistics.inbound_receipt.code_scanned", "logistics.inbound_receipt.code_resolved", "logistics.inbound_receipt.code_unresolved", "logistics.inbound_receipt.quantity_applied", "logistics.inbound_receipt.manual_entry", "logistics.inbound_receipt.scan_compensated", "logistics.inbound_receipt.lot_observed", "logistics.inbound_receipt.serial_observed", "logistics.inbound_receipt.duplicate_serial_detected", "logistics.inbound_receipt.expiration_observed", "logistics.inbound_receipt.expired_product_detected", "logistics.inbound_receipt.difference_candidate_created", "logistics.inbound_receipt.difference_candidate_acknowledged", "logistics.inbound_receipt.difference_handover_ready", "logistics.inbound_receipt.integrity_failed"
        )
    ],


    # Future events (defined but not yet emitted)
    {"event_code": "logistics.inventory.adjustment_created", "category": EventCategory.INVENTORY, "severity": EventSeverity.CRITICAL, "description": "Ajuste de inventario (futuro)"},
    {"event_code": "logistics.inventory.adjustment_approved", "category": EventCategory.INVENTORY, "severity": EventSeverity.CRITICAL, "description": "Ajuste aprobado (futuro)"},
    {"event_code": "logistics.trip.started", "category": EventCategory.TRANSPORT, "severity": EventSeverity.MEDIUM, "description": "Viaje iniciado (futuro)"},
    {"event_code": "logistics.delivery.confirmed", "category": EventCategory.DELIVERY, "severity": EventSeverity.HIGH, "description": "Entrega confirmada (futuro)"},

    # Phase 040 - Reception Differences (case status transitions)
    {"event_code": "logistics.reception_difference.case_created", "category": EventCategory.RECEIVING, "severity": EventSeverity.MEDIUM, "description": "Caso de diferencia de recepción creado"},
    {"event_code": "logistics.reception_difference.case_updated", "category": EventCategory.RECEIVING, "severity": EventSeverity.LOW, "description": "Caso de diferencia de recepción actualizado"},
    {"event_code": "logistics.reception_difference.case_draft", "category": EventCategory.RECEIVING, "severity": EventSeverity.LOW, "description": "Caso de diferencia en borrador"},
    {"event_code": "logistics.reception_difference.case_under_preparation", "category": EventCategory.RECEIVING, "severity": EventSeverity.LOW, "description": "Caso de diferencia en preparación"},
    {"event_code": "logistics.reception_difference.case_pending_evidence", "category": EventCategory.RECEIVING, "severity": EventSeverity.MEDIUM, "description": "Caso de diferencia pendiente de evidencia"},
    {"event_code": "logistics.reception_difference.case_pending_responsibility", "category": EventCategory.RECEIVING, "severity": EventSeverity.MEDIUM, "description": "Caso de diferencia pendiente de responsabilidad"},
    {"event_code": "logistics.reception_difference.case_submitted_for_review", "category": EventCategory.RECEIVING, "severity": EventSeverity.MEDIUM, "description": "Caso de diferencia enviado a revisión"},
    {"event_code": "logistics.reception_difference.case_under_review", "category": EventCategory.RECEIVING, "severity": EventSeverity.MEDIUM, "description": "Caso de diferencia en revisión"},
    {"event_code": "logistics.reception_difference.case_changes_requested", "category": EventCategory.RECEIVING, "severity": EventSeverity.MEDIUM, "description": "Cambios solicitados en caso de diferencia"},
    {"event_code": "logistics.reception_difference.case_ready_for_approval", "category": EventCategory.RECEIVING, "severity": EventSeverity.MEDIUM, "description": "Caso de diferencia listo para aprobación"},
    {"event_code": "logistics.reception_difference.case_approved", "category": EventCategory.RECEIVING, "severity": EventSeverity.HIGH, "description": "Caso de diferencia aprobado"},
    {"event_code": "logistics.reception_difference.case_issued", "category": EventCategory.RECEIVING, "severity": EventSeverity.HIGH, "description": "Documento de diferencia emitido"},
    {"event_code": "logistics.reception_difference.case_acknowledgement_pending", "category": EventCategory.RECEIVING, "severity": EventSeverity.MEDIUM, "description": "Caso de diferencia pendiente de acuse de recibo"},
    {"event_code": "logistics.reception_difference.case_acknowledged", "category": EventCategory.RECEIVING, "severity": EventSeverity.MEDIUM, "description": "Caso de diferencia acusado de recibo"},
    {"event_code": "logistics.reception_difference.case_disputed", "category": EventCategory.RECEIVING, "severity": EventSeverity.HIGH, "description": "Caso de diferencia disputado"},
    {"event_code": "logistics.reception_difference.case_follow_up_required", "category": EventCategory.RECEIVING, "severity": EventSeverity.MEDIUM, "description": "Caso de diferencia requiere seguimiento"},
    {"event_code": "logistics.reception_difference.case_closed", "category": EventCategory.RECEIVING, "severity": EventSeverity.MEDIUM, "description": "Caso de diferencia cerrado"},
    {"event_code": "logistics.reception_difference.case_cancelled", "category": EventCategory.RECEIVING, "severity": EventSeverity.MEDIUM, "description": "Caso de diferencia cancelado"},
    {"event_code": "logistics.reception_difference.case_superseded", "category": EventCategory.RECEIVING, "severity": EventSeverity.MEDIUM, "description": "Caso de diferencia suplantado"},
    # Phase 040 - Item events
    {"event_code": "logistics.reception_difference.item_created", "category": EventCategory.RECEIVING, "severity": EventSeverity.LOW, "description": "Item de diferencia creado"},
    {"event_code": "logistics.reception_difference.item_dismissed", "category": EventCategory.RECEIVING, "severity": EventSeverity.LOW, "description": "Item de diferencia descartado"},
    {"event_code": "logistics.reception_difference.item_superseded", "category": EventCategory.RECEIVING, "severity": EventSeverity.LOW, "description": "Item de diferencia suplantado"},
    # Phase 040 - Evidence events
    {"event_code": "logistics.reception_difference.evidence_linked", "category": EventCategory.RECEIVING, "severity": EventSeverity.LOW, "description": "Evidencia vinculada a diferencia"},
    # Phase 040 - Responsibility events
    {"event_code": "logistics.reception_difference.responsibility_proposed", "category": EventCategory.RECEIVING, "severity": EventSeverity.MEDIUM, "description": "Responsabilidad propuesta en diferencia"},
    {"event_code": "logistics.reception_difference.responsibility_reviewed", "category": EventCategory.RECEIVING, "severity": EventSeverity.MEDIUM, "description": "Responsabilidad revisada en diferencia"},
    {"event_code": "logistics.reception_difference.responsibility_acknowledged", "category": EventCategory.RECEIVING, "severity": EventSeverity.MEDIUM, "description": "Responsabilidad aceptada en diferencia"},
    {"event_code": "logistics.reception_difference.responsibility_disputed", "category": EventCategory.RECEIVING, "severity": EventSeverity.HIGH, "description": "Responsabilidad disputada en diferencia"},
    {"event_code": "logistics.reception_difference.responsibility_undetermined", "category": EventCategory.RECEIVING, "severity": EventSeverity.MEDIUM, "description": "Responsabilidad indeterminada en diferencia"},
    # Phase 040 - Review events
    {"event_code": "logistics.reception_difference.review_created", "category": EventCategory.RECEIVING, "severity": EventSeverity.LOW, "description": "Revisión de diferencia creada"},
    {"event_code": "logistics.reception_difference.review_started", "category": EventCategory.RECEIVING, "severity": EventSeverity.LOW, "description": "Revisión de diferencia iniciada"},
    {"event_code": "logistics.reception_difference.review_changes_requested", "category": EventCategory.RECEIVING, "severity": EventSeverity.MEDIUM, "description": "Cambios solicitados en revisión de diferencia"},
    {"event_code": "logistics.reception_difference.review_completed", "category": EventCategory.RECEIVING, "severity": EventSeverity.MEDIUM, "description": "Revisión de diferencia completada"},
    # Phase 040 - Approval events
    {"event_code": "logistics.reception_difference.approval_decision_created", "category": EventCategory.RECEIVING, "severity": EventSeverity.HIGH, "description": "Decisión de aprobación de diferencia creada"},
    # Phase 040 - Acknowledgement events
    {"event_code": "logistics.reception_difference.acknowledgement_created", "category": EventCategory.RECEIVING, "severity": EventSeverity.MEDIUM, "description": "Acuse de recibo de diferencia creado"},
    # Phase 040 - Document events
    {"event_code": "logistics.reception_difference.document_issued", "category": EventCategory.RECEIVING, "severity": EventSeverity.HIGH, "description": "Documento de diferencia (DIF) emitido"},
    {"event_code": "logistics.reception_difference.document_cancelled", "category": EventCategory.RECEIVING, "severity": EventSeverity.HIGH, "description": "Documento de diferencia (DIF) cancelado"},
    {"event_code": "logistics.reception_difference.document_reprinted", "category": EventCategory.RECEIVING, "severity": EventSeverity.MEDIUM, "description": "Documento de diferencia (DIF) reimpreso"},
    {"event_code": "logistics.reception_difference.document_package_created", "category": EventCategory.RECEIVING, "severity": EventSeverity.MEDIUM, "description": "Paquete documental de diferencia creado"},
    # Phase 040 - Formalization events
    {"event_code": "logistics.reception_difference.candidate_formalized", "category": EventCategory.RECEIVING, "severity": EventSeverity.MEDIUM, "description": "Candidato de recepción formalizado como diferencia"},

    # Phase 041 — Quality Inspection Plans
    {"event_code": "logistics.quality_plan.plan_created", "category": EventCategory.RECEIVING, "severity": EventSeverity.MEDIUM, "description": "Plan de inspección de calidad creado"},
    {"event_code": "logistics.quality_plan.plan_updated", "category": EventCategory.RECEIVING, "severity": EventSeverity.LOW, "description": "Plan de inspección de calidad actualizado"},
    {"event_code": "logistics.quality_plan.plan_deleted", "category": EventCategory.RECEIVING, "severity": EventSeverity.HIGH, "description": "Plan de inspección de calidad eliminado"},
    {"event_code": "logistics.quality_plan.plan_active", "category": EventCategory.RECEIVING, "severity": EventSeverity.HIGH, "description": "Plan de inspección de calidad activado"},
    {"event_code": "logistics.quality_plan.plan_inactive", "category": EventCategory.RECEIVING, "severity": EventSeverity.HIGH, "description": "Plan de inspección de calidad desactivado"},
    {"event_code": "logistics.quality_plan.plan_archived", "category": EventCategory.RECEIVING, "severity": EventSeverity.CRITICAL, "description": "Plan de inspección de calidad archivado"},
    {"event_code": "logistics.quality_plan.version_created", "category": EventCategory.RECEIVING, "severity": EventSeverity.MEDIUM, "description": "Versión de plan de calidad creada"},
    {"event_code": "logistics.quality_plan.version_activated", "category": EventCategory.RECEIVING, "severity": EventSeverity.HIGH, "description": "Versión de plan de calidad activada"},
    {"event_code": "logistics.quality_plan.version_retired", "category": EventCategory.RECEIVING, "severity": EventSeverity.HIGH, "description": "Versión de plan de calidad retirada"},
    {"event_code": "logistics.quality_plan.scope_created", "category": EventCategory.RECEIVING, "severity": EventSeverity.LOW, "description": "Ámbito de plan de calidad creado"},
    {"event_code": "logistics.quality_plan.scope_deleted", "category": EventCategory.RECEIVING, "severity": EventSeverity.LOW, "description": "Ámbito de plan de calidad eliminado"},
    {"event_code": "logistics.quality_plan.control_created", "category": EventCategory.RECEIVING, "severity": EventSeverity.LOW, "description": "Control de calidad creado en plan"},
    {"event_code": "logistics.quality_plan.control_updated", "category": EventCategory.RECEIVING, "severity": EventSeverity.LOW, "description": "Control de calidad actualizado en plan"},
    {"event_code": "logistics.quality_plan.control_deleted", "category": EventCategory.RECEIVING, "severity": EventSeverity.LOW, "description": "Control de calidad eliminado de plan"},
    {"event_code": "logistics.quality_plan.conflict_detected", "category": EventCategory.SECURITY, "severity": EventSeverity.HIGH, "description": "Conflicto de planes de calidad detectado"},
    {"event_code": "logistics.quality_plan.validation_executed", "category": EventCategory.RECEIVING, "severity": EventSeverity.MEDIUM, "description": "Validación de plan de calidad ejecutada"},
    {"event_code": "logistics.quality_plan.integrity_verified", "category": EventCategory.SECURITY, "severity": EventSeverity.LOW, "description": "Integridad de plan de calidad verificada"},
    {"event_code": "logistics.quality_plan.integrity_failed", "category": EventCategory.SECURITY, "severity": EventSeverity.CRITICAL, "description": "Verificación de integridad de plan de calidad falló"},
    {"event_code": "logistics.quality_plan.metrics_calculated", "category": EventCategory.RECEIVING, "severity": EventSeverity.LOW, "description": "Métricas de plan de calidad calculadas"},
    {"event_code": "logistics.quality_plan.snapshot_captured", "category": EventCategory.RECEIVING, "severity": EventSeverity.LOW, "description": "Snapshot de plan de calidad capturado"},
    {"event_code": "logistics.quality_plan.reference_file_linked", "category": EventCategory.RECEIVING, "severity": EventSeverity.LOW, "description": "Archivo de referencia vinculado a plan de calidad"},
    {"event_code": "logistics.quality_plan.reference_file_unlinked", "category": EventCategory.RECEIVING, "severity": EventSeverity.LOW, "description": "Archivo de referencia desvinculado de plan de calidad"},

    # Phase 042 — Quality Quarantine
    {"event_code": "logistics.quality.disposition_materialized", "category": EventCategory.RECEIVING, "severity": EventSeverity.INFO, "description": "Asignación de disposición materializada desde recepción"},
    {"event_code": "logistics.quality.disposition_split", "category": EventCategory.RECEIVING, "severity": EventSeverity.MEDIUM, "description": "Asignación de disposición dividida"},
    {"event_code": "logistics.quality.quarantine_required", "category": EventCategory.RECEIVING, "severity": EventSeverity.MEDIUM, "description": "Cuarentena requerida para asignación"},
    {"event_code": "logistics.quality.quarantine_created", "category": EventCategory.RECEIVING, "severity": EventSeverity.MEDIUM, "description": "Caso de cuarentena creado"},
    {"event_code": "logistics.quality.quarantine_activated", "category": EventCategory.RECEIVING, "severity": EventSeverity.MEDIUM, "description": "Caso de cuarentena activado"},
    {"event_code": "logistics.quality.quarantine_placement_confirmed", "category": EventCategory.RECEIVING, "severity": EventSeverity.INFO, "description": "Colocación física en zona de cuarentena confirmada"},
    {"event_code": "logistics.quality.inspection_materialized", "category": EventCategory.RECEIVING, "severity": EventSeverity.INFO, "description": "Inspección de calidad materializada"},
    {"event_code": "logistics.quality.inspection_started", "category": EventCategory.RECEIVING, "severity": EventSeverity.INFO, "description": "Inspección de calidad iniciada"},
    {"event_code": "logistics.quality.inspection_paused", "category": EventCategory.RECEIVING, "severity": EventSeverity.LOW, "description": "Inspección de calidad pausada"},
    {"event_code": "logistics.quality.inspection_resumed", "category": EventCategory.RECEIVING, "severity": EventSeverity.LOW, "description": "Inspección de calidad reanudada"},
    {"event_code": "logistics.quality.control_result_recorded", "category": EventCategory.RECEIVING, "severity": EventSeverity.INFO, "description": "Resultado de control registrado"},
    {"event_code": "logistics.quality.measurement_recorded", "category": EventCategory.RECEIVING, "severity": EventSeverity.INFO, "description": "Medición registrada"},
    {"event_code": "logistics.quality.sample_recorded", "category": EventCategory.RECEIVING, "severity": EventSeverity.INFO, "description": "Muestra registrada"},
    {"event_code": "logistics.quality.certificate_reviewed", "category": EventCategory.RECEIVING, "severity": EventSeverity.INFO, "description": "Certificado revisado"},
    {"event_code": "logistics.quality.evidence_linked", "category": EventCategory.RECEIVING, "severity": EventSeverity.INFO, "description": "Evidencia vinculada a inspección"},
    {"event_code": "logistics.quality.inspection_completed", "category": EventCategory.RECEIVING, "severity": EventSeverity.MEDIUM, "description": "Inspección de calidad completada"},
    {"event_code": "logistics.quality.decision_proposed", "category": EventCategory.RECEIVING, "severity": EventSeverity.MEDIUM, "description": "Decisión de disposición propuesta"},
    {"event_code": "logistics.quality.approved", "category": EventCategory.RECEIVING, "severity": EventSeverity.MEDIUM, "description": "Calidad aprobada"},
    {"event_code": "logistics.quality.keep_quarantined", "category": EventCategory.RECEIVING, "severity": EventSeverity.INFO, "description": "Mercancía mantenida en cuarentena"},
    {"event_code": "logistics.quality.reinspection_requested", "category": EventCategory.RECEIVING, "severity": EventSeverity.MEDIUM, "description": "Reinspección solicitada"},
    {"event_code": "logistics.quality.release_requested", "category": EventCategory.RECEIVING, "severity": EventSeverity.HIGH, "description": "Liberación solicitada"},
    {"event_code": "logistics.quality.release_approved", "category": EventCategory.RECEIVING, "severity": EventSeverity.HIGH, "description": "Liberación aprobada"},
    {"event_code": "logistics.quality.release_executed", "category": EventCategory.RECEIVING, "severity": EventSeverity.HIGH, "description": "Liberación ejecutada"},
    {"event_code": "logistics.quality.partial_release_executed", "category": EventCategory.RECEIVING, "severity": EventSeverity.HIGH, "description": "Liberación parcial ejecutada"},
    {"event_code": "logistics.quality.rejection_requested", "category": EventCategory.RECEIVING, "severity": EventSeverity.HIGH, "description": "Rechazo solicitado"},
    {"event_code": "logistics.quality.rejection_approved", "category": EventCategory.RECEIVING, "severity": EventSeverity.CRITICAL, "description": "Rechazo aprobado"},
    {"event_code": "logistics.quality.rejection_executed", "category": EventCategory.RECEIVING, "severity": EventSeverity.HIGH, "description": "Rechazo ejecutado"},
    {"event_code": "logistics.quality.partial_rejection_executed", "category": EventCategory.RECEIVING, "severity": EventSeverity.HIGH, "description": "Rechazo parcial ejecutado"},
    {"event_code": "logistics.quality.NC_issued", "category": EventCategory.RECEIVING, "severity": EventSeverity.HIGH, "description": "No conformidad emitida"},
    {"event_code": "logistics.quality.NC_cancelled", "category": EventCategory.RECEIVING, "severity": EventSeverity.CRITICAL, "description": "No conformidad anulada"},
    {"event_code": "logistics.quality.integrity_failed", "category": EventCategory.RECEIVING, "severity": EventSeverity.CRITICAL, "description": "Verificación de integridad fallida"},
    {"event_code": "logistics.quality.case_closed", "category": EventCategory.RECEIVING, "severity": EventSeverity.INFO, "description": "Caso de cuarentena cerrado"},

    # Phase 043: Putaway
    {"event_code": "logistics.putaway.policy_created", "category": EventCategory.INVENTORY, "severity": EventSeverity.MEDIUM, "description": "Politica de putaway creada"},
    {"event_code": "logistics.putaway.policy_activated", "category": EventCategory.INVENTORY, "severity": EventSeverity.MEDIUM, "description": "Politica de putaway activada"},
    {"event_code": "logistics.putaway.policy_version_created", "category": EventCategory.INVENTORY, "severity": EventSeverity.MEDIUM, "description": "Version de politica de putaway creada"},
    {"event_code": "logistics.putaway.policy_version_activated", "category": EventCategory.INVENTORY, "severity": EventSeverity.HIGH, "description": "Version de politica de putaway activada"},
    {"event_code": "logistics.putaway.recommendation_executed", "category": EventCategory.INVENTORY, "severity": EventSeverity.INFO, "description": "Motor de recomendaciones ejecutado"},
    {"event_code": "logistics.putaway.recommendation_failed", "category": EventCategory.INVENTORY, "severity": EventSeverity.HIGH, "description": "Motor de recomendaciones fallo"},
    {"event_code": "logistics.putaway.order_created", "category": EventCategory.INVENTORY, "severity": EventSeverity.INFO, "description": "Orden de putaway creada"},
    {"event_code": "logistics.putaway.order_issued", "category": EventCategory.INVENTORY, "severity": EventSeverity.HIGH, "description": "Orden de putaway emitida"},
    {"event_code": "logistics.putaway.order_completed", "category": EventCategory.INVENTORY, "severity": EventSeverity.MEDIUM, "description": "Orden de putaway completada"},
    {"event_code": "logistics.putaway.order_cancelled", "category": EventCategory.INVENTORY, "severity": EventSeverity.HIGH, "description": "Orden de putaway cancelada"},
    {"event_code": "logistics.putaway.task_created", "category": EventCategory.INVENTORY, "severity": EventSeverity.INFO, "description": "Tarea de putaway creada"},
    {"event_code": "logistics.putaway.task_assigned", "category": EventCategory.INVENTORY, "severity": EventSeverity.MEDIUM, "description": "Tarea de putaway asignada"},
    {"event_code": "logistics.putaway.task_started", "category": EventCategory.INVENTORY, "severity": EventSeverity.INFO, "description": "Tarea de putaway iniciada"},
    {"event_code": "logistics.putaway.task_paused", "category": EventCategory.INVENTORY, "severity": EventSeverity.LOW, "description": "Tarea de putaway pausada"},
    {"event_code": "logistics.putaway.task_resumed", "category": EventCategory.INVENTORY, "severity": EventSeverity.LOW, "description": "Tarea de putaway reanudada"},
    {"event_code": "logistics.putaway.task_completed", "category": EventCategory.INVENTORY, "severity": EventSeverity.MEDIUM, "description": "Tarea de putaway completada"},
    {"event_code": "logistics.putaway.scan_recorded", "category": EventCategory.INVENTORY, "severity": EventSeverity.INFO, "description": "Escaneo registrado"},
    {"event_code": "logistics.putaway.scan_validated", "category": EventCategory.INVENTORY, "severity": EventSeverity.INFO, "description": "Escaneo validado"},
    {"event_code": "logistics.putaway.scan_mismatch", "category": EventCategory.INVENTORY, "severity": EventSeverity.HIGH, "description": "Escaneo con discrepancia"},
    {"event_code": "logistics.putaway.placement_confirmed", "category": EventCategory.INVENTORY, "severity": EventSeverity.MEDIUM, "description": "Colocacion confirmada"},
    {"event_code": "logistics.putaway.placement_finalized", "category": EventCategory.INVENTORY, "severity": EventSeverity.HIGH, "description": "Colocacion finalizada"},
    {"event_code": "logistics.putaway.reservation_created", "category": EventCategory.INVENTORY, "severity": EventSeverity.INFO, "description": "Reservacion de ubicacion creada"},
    {"event_code": "logistics.putaway.reservation_released", "category": EventCategory.INVENTORY, "severity": EventSeverity.LOW, "description": "Reservacion de ubicacion liberada"},
    {"event_code": "logistics.putaway.reservation_expired", "category": EventCategory.INVENTORY, "severity": EventSeverity.MEDIUM, "description": "Reservacion de ubicacion expirada"},
    {"event_code": "logistics.putaway.reservation_consumed", "category": EventCategory.INVENTORY, "severity": EventSeverity.INFO, "description": "Reservacion de ubicacion consumida"},
    {"event_code": "logistics.putaway.override_requested", "category": EventCategory.INVENTORY, "severity": EventSeverity.HIGH, "description": "Override de ubicacion solicitado"},
    {"event_code": "logistics.putaway.override_approved", "category": EventCategory.INVENTORY, "severity": EventSeverity.CRITICAL, "description": "Override de ubicacion aprobado"},
    {"event_code": "logistics.putaway.exception_reported", "category": EventCategory.INVENTORY, "severity": EventSeverity.HIGH, "description": "Excepcion de putaway reportada"},
    {"event_code": "logistics.putaway.exception_resolved", "category": EventCategory.INVENTORY, "severity": EventSeverity.MEDIUM, "description": "Excepcion de putaway resuelta"},
    {"event_code": "logistics.putaway.capacity_profile_created", "category": EventCategory.INVENTORY, "severity": EventSeverity.INFO, "description": "Perfil de capacidad creado"},
    {"event_code": "logistics.putaway.proximity_profile_created", "category": EventCategory.INVENTORY, "severity": EventSeverity.INFO, "description": "Perfil de proximidad creado"},
    {"event_code": "logistics.putaway.compatibility_rule_created", "category": EventCategory.INVENTORY, "severity": EventSeverity.INFO, "description": "Regla de compatibilidad creada"},

]


# Lookup map
EVENT_CODE_MAP = {e["event_code"]: e for e in EVENT_CATALOG}


def get_event_def(event_code: str) -> dict[str, str] | None:
    return EVENT_CODE_MAP.get(event_code)


def is_valid_event_code(code: str) -> bool:
    return code in EVENT_CODE_MAP
