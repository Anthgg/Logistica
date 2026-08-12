"""Multi-hop conversion graph path resolver for Phase 024."""

from decimal import Decimal
from typing import Dict, Any, List, Optional, Set, Tuple
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.logistics.units.models import (
    ProductPackagingDefinitionModel,
    UnitConversionRuleModel,
    UnitOfMeasureModel,
)


class ConversionPathResolver:
    """Resolves conversion paths through graph traversal with cycle and ambiguity checks."""

    MAX_HOPS = 5

    def __init__(self, db: Session):
        self.db = db

    def resolve_path(
        self,
        source_unit_id: UUID,
        target_unit_id: UUID,
        organization_id: Optional[UUID] = None,
        product_id: Optional[UUID] = None,
    ) -> Tuple[Decimal, List[str], List[Dict[str, Any]]]:
        """Resolves conversion factor and path from source_unit_id to target_unit_id.

        Returns (effective_factor, path_unit_codes, applied_rules).
        """
        if source_unit_id == target_unit_id:
            src = self.db.get(UnitOfMeasureModel, source_unit_id)
            code = src.code if src else str(source_unit_id)
            return Decimal("1.0"), [code], []

        src_unit = self.db.get(UnitOfMeasureModel, source_unit_id)
        tgt_unit = self.db.get(UnitOfMeasureModel, target_unit_id)

        if not src_unit or not tgt_unit:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source or target unit not found.")

        # Check dimension match
        if src_unit.dimension_id != tgt_unit.dimension_id and src_unit.unit_kind != "PACKAGING" and tgt_unit.unit_kind != "PACKAGING":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot convert between incompatible dimensions ('{src_unit.dimension.code if src_unit.dimension else 'SRC'}' vs '{tgt_unit.dimension.code if tgt_unit.dimension else 'TGT'}').",
            )

        # Build adjacency graph
        # 1. Product packaging definitions if product_id provided
        adj: Dict[UUID, List[Dict[str, Any]]] = {}

        if product_id:
            stmt_pkg = select(ProductPackagingDefinitionModel).where(
                ProductPackagingDefinitionModel.product_id == product_id,
                ProductPackagingDefinitionModel.status == "ACTIVE",
            )
            pkgs = list(self.db.scalars(stmt_pkg).all())
            for pkg in pkgs:
                # 1 packaging_unit = contained_quantity contained_units
                # Direct: packaging_unit -> contained_unit (multiplier = contained_quantity)
                adj.setdefault(pkg.packaging_unit_id, []).append({
                    "target_id": pkg.contained_unit_id,
                    "multiplier": Decimal(str(pkg.contained_quantity)),
                    "rule_type": "PRODUCT_PACKAGING",
                    "rule_id": str(pkg.id),
                })
                # Inverse: contained_unit -> packaging_unit (multiplier = 1 / contained_quantity)
                if pkg.contained_quantity > 0:
                    adj.setdefault(pkg.contained_unit_id, []).append({
                        "target_id": pkg.packaging_unit_id,
                        "multiplier": Decimal("1.0") / Decimal(str(pkg.contained_quantity)),
                        "rule_type": "PRODUCT_PACKAGING_INVERSE",
                        "rule_id": str(pkg.id),
                    })

        # 2. System and Organization conversion rules
        stmt_rules = select(UnitConversionRuleModel).where(UnitConversionRuleModel.status == "ACTIVE")
        if organization_id:
            stmt_rules = stmt_rules.where(
                (UnitConversionRuleModel.organization_id == None) | (UnitConversionRuleModel.organization_id == organization_id)
            )
        else:
            stmt_rules = stmt_rules.where(UnitConversionRuleModel.organization_id == None)

        rules = list(self.db.scalars(stmt_rules).all())
        for r in rules:
            mult = Decimal(str(r.multiplier))
            adj.setdefault(r.source_unit_id, []).append({
                "target_id": r.target_unit_id,
                "multiplier": mult,
                "rule_type": f"{r.conversion_scope}_RULE",
                "rule_id": str(r.id),
            })
            if r.allows_inverse and mult > 0:
                adj.setdefault(r.target_unit_id, []).append({
                    "target_id": r.source_unit_id,
                    "multiplier": Decimal("1.0") / mult,
                    "rule_type": f"{r.conversion_scope}_INVERSE_RULE",
                    "rule_id": str(r.id),
                })

        # BFS Graph Search
        found_paths: List[Tuple[Decimal, List[UUID], List[Dict[str, Any]]]] = []
        queue = [(source_unit_id, Decimal("1.0"), [source_unit_id], [])]

        while queue:
            curr_id, curr_factor, path_nodes, applied_rules = queue.pop(0)

            if len(path_nodes) > self.MAX_HOPS + 1:
                continue

            if curr_id == target_unit_id:
                found_paths.append((curr_factor, path_nodes, applied_rules))
                continue

            for edge in adj.get(curr_id, []):
                next_id = edge["target_id"]
                if next_id in path_nodes:
                    continue  # Cycle prevention
                queue.append((
                    next_id,
                    curr_factor * edge["multiplier"],
                    path_nodes + [next_id],
                    applied_rules + [edge],
                ))

        if not found_paths:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No valid conversion path found from '{src_unit.code}' to '{tgt_unit.code}'.",
            )

        # Ambiguity check: if multiple paths exist, verify factors match
        first_factor = found_paths[0][0]
        for f, p, r in found_paths[1:]:
            diff = abs(f - first_factor)
            if diff > Decimal("0.000001"):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Ambiguous conversion path detected between '{src_unit.code}' and '{tgt_unit.code}' with conflicting factors.",
                )

        selected_factor, selected_nodes, selected_rules = found_paths[0]

        # Convert node UUIDs to unit codes
        path_codes = []
        for n_id in selected_nodes:
            u = self.db.get(UnitOfMeasureModel, n_id)
            path_codes.append(u.code if u else str(n_id))

        return selected_factor, path_codes, selected_rules
