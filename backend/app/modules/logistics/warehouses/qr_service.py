"""Service for opaque QR version management, resolution and PNG rendering (Phase 022)."""

import hashlib
import io
from typing import Any
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

import qrcode

from app.database.base import utc_now
from app.modules.logistics.audit.service import audit_service, AuditEventCommand
from app.modules.logistics.warehouses.models import (
    WarehouseLocationModel,
    WarehouseLocationQRVersionModel,
)


class WarehouseLocationQRService:
    """Service for generating versioned opaque QR references and PNG images."""

    def __init__(self, db: Session):
        self.db = db

    def _write_audit(
        self, event_code: str, organization_id: UUID, actor_id: UUID | None, resource_id: Any, details: dict
    ):
        cmd = AuditEventCommand(
            event_code=event_code,
            actor_user_id=actor_id,
            organization_id=organization_id,
            resource_type="location_qr",
            resource_id=str(resource_id),
            new_data=details,
        )
        audit_service.write_event(self.db, cmd)

    def generate_or_get_qr(
        self, organization_id: UUID, location_id: UUID, actor_id: UUID | None = None
    ) -> WarehouseLocationQRVersionModel:
        loc = self.db.get(WarehouseLocationModel, location_id)
        if not loc or loc.organization_id != organization_id:
            raise HTTPException(status_code=404, detail="WarehouseLocation no encontrada.")

        active_qr = self.db.scalars(
            select(WarehouseLocationQRVersionModel).where(
                and_(
                    WarehouseLocationQRVersionModel.location_id == location_id,
                    WarehouseLocationQRVersionModel.status == "ACTIVE",
                )
            )
        ).first()

        if active_qr:
            return active_qr

        # Create new opaque public_ref
        public_ref = f"loc_{uuid4().hex[:16]}"
        payload_str = f"t1loc:v1:{public_ref}"
        payload_hash = hashlib.sha256(payload_str.encode()).hexdigest()

        latest = self.db.scalars(
            select(WarehouseLocationQRVersionModel)
            .where(WarehouseLocationQRVersionModel.location_id == location_id)
            .order_by(WarehouseLocationQRVersionModel.qr_version.desc())
        ).first()

        next_ver = (latest.qr_version + 1) if latest else 1

        qr_ver = WarehouseLocationQRVersionModel(
            location_id=location_id,
            qr_version=next_ver,
            public_reference=public_ref,
            payload_hash=payload_hash,
            status="ACTIVE",
            generated_by=actor_id,
        )
        self.db.add(qr_ver)
        self.db.flush()

        self._write_audit(
            event_code="logistics.warehouse_location.qr_generated",
            organization_id=organization_id,
            actor_id=actor_id,
            resource_id=qr_ver.id,
            details={"location_id": str(location_id), "public_ref": public_ref, "qr_version": next_ver},
        )

        return qr_ver

    def rotate_qr(
        self, organization_id: UUID, location_id: UUID, reason: str, actor_id: UUID | None = None
    ) -> WarehouseLocationQRVersionModel:
        """Revokes the current active QR and generates a new version."""
        loc = self.db.get(WarehouseLocationModel, location_id)
        if not loc or loc.organization_id != organization_id:
            raise HTTPException(status_code=404, detail="WarehouseLocation no encontrada.")

        active_qrs = self.db.scalars(
            select(WarehouseLocationQRVersionModel).where(
                and_(
                    WarehouseLocationQRVersionModel.location_id == location_id,
                    WarehouseLocationQRVersionModel.status == "ACTIVE",
                )
            )
        ).all()

        for q in active_qrs:
            q.status = "REVOKED"
            q.revoked_at = utc_now()
            q.revocation_reason = reason

        self.db.flush()

        new_qr = self.generate_or_get_qr(organization_id, location_id, actor_id=actor_id)

        self._write_audit(
            event_code="logistics.warehouse_location.qr_rotated",
            organization_id=organization_id,
            actor_id=actor_id,
            resource_id=new_qr.id,
            details={"location_id": str(location_id), "reason": reason, "new_public_ref": new_qr.public_reference},
        )

        return new_qr

    def resolve_public_qr(
        self, organization_id: UUID, public_reference: str
    ) -> dict[str, Any]:
        """Resolves an opaque public_ref to full location details for authenticated clients."""
        qr_ver = self.db.scalars(
            select(WarehouseLocationQRVersionModel).where(
                WarehouseLocationQRVersionModel.public_reference == public_reference
            )
        ).first()

        if not qr_ver:
            raise HTTPException(status_code=404, detail="Código QR no válido o no encontrado.")

        if qr_ver.status != "ACTIVE":
            raise HTTPException(status_code=410, detail=f"Código QR revocado. Motivo: {qr_ver.revocation_reason or 'No especificado'}")

        loc = self.db.get(WarehouseLocationModel, qr_ver.location_id)
        if not loc or loc.organization_id != organization_id:
            raise HTTPException(status_code=403, detail="No tiene permisos para acceder a esta ubicación.")

        return {
            "public_reference": public_reference,
            "qr_version": qr_ver.qr_version,
            "location_id": str(loc.id),
            "full_code": loc.full_code,
            "code": loc.code,
            "name": loc.name,
            "location_type": loc.location_type,
            "warehouse_id": str(loc.warehouse_id),
            "status": loc.status,
            "usage_type": loc.usage_type,
            "is_pickable": loc.is_pickable,
            "is_receivable": loc.is_receivable,
            "is_dispatchable": loc.is_dispatchable,
        }

    def render_qr_png(self, organization_id: UUID, location_id: UUID) -> bytes:
        qr_ver = self.generate_or_get_qr(organization_id, location_id)
        payload = f"t1loc:v1:{qr_ver.public_reference}"

        img = qrcode.make(payload)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
