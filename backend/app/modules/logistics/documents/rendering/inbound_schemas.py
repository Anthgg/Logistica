"""Pydantic v2 schemas for Inbound & Quality Document contexts and Package Manifests (Phase 016)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


def mask_sensitive_id(val: str | None, visible_end: int = 2) -> str:
    """Utility to mask DNI or License strings for privacy protection."""
    if not val:
        return "******"
    clean = str(val).strip()
    if len(clean) <= visible_end:
        return "*" * len(clean)
    return "*" * (len(clean) - visible_end) + clean[-visible_end:]


class InboundItemSchema(BaseModel):
    line_number: int = 1
    sku: str | None = None
    description: str
    expected_quantity: Decimal = Field(Decimal("0.00"), ge=0)
    received_quantity: Decimal = Field(Decimal("0.00"), ge=0)
    accepted_quantity: Decimal = Field(Decimal("0.00"), ge=0)
    rejected_quantity: Decimal = Field(Decimal("0.00"), ge=0)
    unit: str = "UND"


class InboundCitContext(BaseModel):
    appointment_date: str | None = None
    appointment_window_start: str = "08:00"
    appointment_window_end: str = "10:00"
    warehouse: str = "Almacén Principal Sede Lima"
    dock: str = "Muelle 02"
    purchase_order_reference: str = "OC-LIM-2026-000001"
    operation_type: str = "RECEPCION_PROVEEDOR"
    supplier_name: str = "DISTRIBUIDORA INDUSTRIAL S.A.C."
    carrier_name: str = "TRANSPORTES EXPRESS S.A.C."
    expected_plate: str = "ABC-123"
    expected_driver_name: str = "Juan Pérez"
    expected_items: list[InboundItemSchema] = Field(default_factory=list)


class InboundCpvContext(BaseModel):
    gate_event_type: str = "INGRESO"
    arrival_at: str | None = None
    gate: str = "Puerta Principal 01"
    gate_operator: str = "Agente Vigilancia"
    access_decision: str = "AUTORIZADO"
    appointment_reference: str = "CIT-2026-000001"
    plate: str = "ABC-123"
    vehicle_type: str = "Camión Furgón 10T"
    driver_name: str = "Pedro Rodríguez"
    driver_dni_raw: str | None = "12345642"
    driver_license_raw: str | None = "Q49876521"
    carrier_name: str = "LOGISTICA RAPIDA S.A.C."
    seal_number: str = "SEAL-987654"
    seal_status: str = "COINCIDE"

    def get_masked_context(self) -> dict[str, Any]:
        data = self.model_dump()
        data["driver_dni_masked"] = mask_sensitive_id(self.driver_dni_raw, visible_end=2)
        data["driver_license_masked"] = mask_sensitive_id(self.driver_license_raw, visible_end=2)
        data.pop("driver_dni_raw", None)
        data.pop("driver_license_raw", None)
        return data


class InboundArecContext(BaseModel):
    reception_date: str | None = None
    warehouse: str = "Almacén Principal"
    dock: str = "Muelle 01"
    unloading_start: str = "08:15:00"
    unloading_end: str = "09:30:00"
    supplier_name: str = "DISTRIBUIDORA INDUSTRIAL S.A.C."
    purchase_order_reference: str = "OC-LIM-2026-000001"
    reception_result: str = "ACEPTADO"
    waybill_reference: str = "GR-001-98765"
    received_items: list[InboundItemSchema] = Field(default_factory=list)


class InboundNiContext(BaseModel):
    entry_date: str | None = None
    warehouse: str = "Almacén Principal Sede Lima"
    reception_reference: str = "AREC-LIM-2026-000001"
    quality_state: str = "APROBADO_SINO_INSPECCION"
    inventory_state: str = "PENDIENTE_PUTAWAY"
    responsible_user: str = "Jefe de Almacén"
    accepted_items: list[InboundItemSchema] = Field(default_factory=list)


class InboundDifContext(BaseModel):
    reception_reference: str = "AREC-LIM-2026-000001"
    report_date: str | None = None
    supplier_name: str = "DISTRIBUIDORA INDUSTRIAL S.A.C."
    carrier_name: str = "TRANSPORTES EXPRESS S.A.C."
    differences: list[dict[str, Any]] = Field(default_factory=list)
    immediate_action: str = "Registro de incidencia en el acta de recepción y emisión de reclamo formal"


class QualityNcContext(BaseModel):
    reception_reference: str = "AREC-LIM-2026-000001"
    detection_date: str | None = None
    non_conformity_type: str = "DANO_EMBALAJE_O_PRODUCTO"
    severity: str = "ALTA"
    supplier_name: str = "DISTRIBUIDORA INDUSTRIAL S.A.C."
    inspector_name: str = "Inspector Calidad"
    unfulfilled_requirement: str = "Empaque secundario roto e insumos dañados por humedad"
    description: str = "Se constató al abrir el furgón que la paleta 2 presentó cajas aplastadas"
    affected_items: list[dict[str, Any]] = Field(default_factory=list)


class ReceptionPackageManifestResponse(BaseModel):
    manifest_version: str = "1.0.0"
    package_mode: str = "PREVIEW"
    organization_name: str
    branch_name: str
    warehouse_name: str
    included_documents: list[str]
    missing_documents: list[str]
    warnings: list[str] = Field(default_factory=list)
