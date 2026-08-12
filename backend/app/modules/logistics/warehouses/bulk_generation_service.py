"""Service for bulk location preview and generation with idempotency (Phase 022)."""

import hashlib
import json
from typing import Any
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.warehouse import Warehouse
from app.modules.logistics.audit.service import audit_service, AuditEventCommand
from app.modules.logistics.documents.series.series_models import IdempotencyRecordModel
from app.modules.logistics.warehouses.code_service import WarehouseLocationCodeService
from app.modules.logistics.warehouses.hierarchy_policy import WarehouseLocationHierarchyPolicy
from app.modules.logistics.warehouses.models import WarehouseLocationModel
from app.modules.logistics.warehouses.schemas import (
    WarehouseLocationBulkExecuteRequest,
    WarehouseLocationBulkPreviewRequest,
)

WAREHOUSE_LOCATION_BULK_MAX_NODES = 1000


class WarehouseLocationBulkService:
    """Service to preview and transactionally execute bulk location generation."""

    def __init__(self, db: Session):
        self.db = db

    def _write_audit(
        self, event_code: str, organization_id: UUID, actor_id: UUID | None, resource_id: Any, details: dict
    ):
        cmd = AuditEventCommand(
            event_code=event_code,
            actor_user_id=actor_id,
            organization_id=organization_id,
            resource_type="warehouse_location_bulk",
            resource_id=str(resource_id),
            new_data=details,
        )
        audit_service.write_event(self.db, cmd)

    def _compute_request_hash(self, req: WarehouseLocationBulkPreviewRequest) -> str:
        data = req.model_dump(mode="json")
        canonical = json.dumps(data, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()

    def generate_preview(
        self, organization_id: UUID, req: WarehouseLocationBulkPreviewRequest
    ) -> dict[str, Any]:
        wh = self.db.get(Warehouse, req.warehouse_id)
        if not wh or wh.organization_id != organization_id:
            raise HTTPException(status_code=404, detail="Warehouse no encontrado.")

        parent = None
        if req.parent_location_id:
            parent = self.db.get(WarehouseLocationModel, req.parent_location_id)
            if not parent or parent.warehouse_id != req.warehouse_id:
                raise HTTPException(status_code=400, detail="Ubicación padre inválida.")

        # Calculate combinations: Aisles x Racks x Levels x Positions
        aisles = range(req.aisle_start, req.aisle_end + 1) if req.aisle_count else [0]
        racks = range(req.rack_start, req.rack_end + 1) if req.rack_count else [0]
        levels = range(req.level_start, req.level_end + 1) if req.level_count else [0]
        positions = range(req.position_start, req.position_end + 1) if req.position_count else [0]

        total_nodes = len(aisles) * len(racks) * len(levels) * len(positions)
        if total_nodes > WAREHOUSE_LOCATION_BULK_MAX_NODES:
            raise HTTPException(
                status_code=422,
                detail=f"La generación masiva solicita {total_nodes} nodos, excediendo el límite máximo de {WAREHOUSE_LOCATION_BULK_MAX_NODES}.",
            )

        sample_codes = []
        conflicts = []

        # Check existing full_codes
        existing_codes = set(
            self.db.scalars(
                select(WarehouseLocationModel.full_code).where(
                    WarehouseLocationModel.organization_id == organization_id
                )
            ).all()
        )

        zone_code = req.zone_code.strip().upper() if req.zone_code else ""
        parent_fc = parent.full_code if parent else None

        for a in aisles:
            a_code = f"A{str(a).zfill(req.padding_length)}" if req.aisle_count else ""
            for r in racks:
                r_code = f"R{str(r).zfill(req.padding_length)}" if req.rack_count else ""
                for l in levels:
                    l_code = f"N{str(l).zfill(req.padding_length)}" if req.level_count else ""
                    for p in positions:
                        p_code = f"P{str(p).zfill(req.padding_length)}" if req.position_count else ""

                        # Build hierarchical full code
                        segments = [s for s in [zone_code, a_code, r_code, l_code, p_code] if s]
                        segment_code = "-".join(segments)
                        full_code = WarehouseLocationCodeService.build_full_code(wh.code, parent_fc, segment_code)

                        if full_code in existing_codes:
                            conflicts.append(full_code)

                        if len(sample_codes) < 10:
                            sample_codes.append(full_code)

        request_hash = self._compute_request_hash(req)

        return {
            "total_nodes": total_nodes,
            "sample_codes": sample_codes,
            "conflict_count": len(conflicts),
            "conflicts": conflicts[:10],
            "request_hash": request_hash,
            "allowed": len(conflicts) == 0,
        }

    def execute_bulk(
        self, organization_id: UUID, req: WarehouseLocationBulkExecuteRequest, actor_id: UUID | None = None
    ) -> dict[str, Any]:
        # Check idempotency
        idempotency_key = req.idempotency_key
        existing_idempotency = self.db.scalars(
            select(IdempotencyRecordModel).where(
                and_(
                    IdempotencyRecordModel.organization_id == organization_id,
                    IdempotencyRecordModel.idempotency_key == idempotency_key,
                )
            )
        ).first()

        if existing_idempotency:
            return json.loads(existing_idempotency.response_payload)

        # Generate preview & verify request_hash
        preview = self.generate_preview(organization_id, req.preview_request)
        if preview["request_hash"] != req.request_hash:
            raise HTTPException(
                status_code=400, detail="El hash de la solicitud no coincide con la vista previa enviada."
            )

        if preview["conflict_count"] > 0:
            raise HTTPException(
                status_code=400, detail=f"Existen {preview['conflict_count']} códigos en conflicto. Resuelva los duplicados antes de ejecutar."
            )

        # Execute creation
        preview_req = req.preview_request
        wh = self.db.get(Warehouse, preview_req.warehouse_id)
        parent = self.db.get(WarehouseLocationModel, preview_req.parent_location_id) if preview_req.parent_location_id else None

        aisles = range(preview_req.aisle_start, preview_req.aisle_end + 1) if preview_req.aisle_count else [0]
        racks = range(preview_req.rack_start, preview_req.rack_end + 1) if preview_req.rack_count else [0]
        levels = range(preview_req.level_start, preview_req.level_end + 1) if preview_req.level_count else [0]
        positions = range(preview_req.position_start, preview_req.position_end + 1) if preview_req.position_count else [0]

        created_locations = []
        zone_code = preview_req.zone_code.strip().upper() if preview_req.zone_code else ""
        parent_fc = parent.full_code if parent else None

        for a in aisles:
            a_code = f"A{str(a).zfill(preview_req.padding_length)}" if preview_req.aisle_count else ""
            for r in racks:
                r_code = f"R{str(r).zfill(preview_req.padding_length)}" if preview_req.rack_count else ""
                for l in levels:
                    l_code = f"N{str(l).zfill(preview_req.padding_length)}" if preview_req.level_count else ""
                    for p in positions:
                        p_code = f"P{str(p).zfill(preview_req.padding_length)}" if preview_req.position_count else ""

                        segments = [s for s in [zone_code, a_code, r_code, l_code, p_code] if s]
                        leaf_code = segments[-1] if segments else "POS"
                        full_code = WarehouseLocationCodeService.build_full_code(wh.code, parent_fc, "-".join(segments))

                        loc = WarehouseLocationModel(
                            organization_id=organization_id,
                            branch_id=wh.branch_id,
                            warehouse_id=wh.id,
                            parent_location_id=parent.id if parent else None,
                            location_type="POSITION" if preview_req.position_count else "ZONE",
                            code=leaf_code,
                            full_code=full_code,
                            name=f"Ubicación Masiva {full_code}",
                            hierarchy_path=f"{parent.hierarchy_path}/{parent.id}" if parent else str(wh.id),
                            depth=(parent.depth + 1) if parent else 1,
                            status="ACTIVE",
                            usage_type="GENERAL_STORAGE",
                            created_by=actor_id,
                        )
                        self.db.add(loc)
                        created_locations.append(loc)

        self.db.flush()

        res_payload = {
            "status": "SUCCESS",
            "created_count": len(created_locations),
            "warehouse_id": str(wh.id),
        }

        # Save idempotency record
        idempotency_rec = IdempotencyRecordModel(
            organization_id=organization_id,
            idempotency_key=idempotency_key,
            request_hash=req.request_hash,
            response_status_code=200,
            response_payload=json.dumps(res_payload),
            created_by=actor_id,
        )
        self.db.add(idempotency_rec)
        self.db.flush()

        self._write_audit(
            event_code="logistics.warehouse_location.bulk_created",
            organization_id=organization_id,
            actor_id=actor_id,
            resource_id=wh.id,
            details={"created_count": len(created_locations), "idempotency_key": idempotency_key},
        )

        return res_payload
