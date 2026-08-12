"""Idempotent seed script for Phase 024 UOM Engine."""

import hashlib
from decimal import Decimal
from typing import Dict, Any, List
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.logistics.units.models import (
    MeasurementDimensionModel,
    UnitConversionRuleModel,
    UnitOfMeasureModel,
)


def seed_units_and_conversions(db: Session) -> Dict[str, int]:
    """Populates system dimensions, system units, and physical conversion rules idempotently."""

    dim_data = [
        {"code": "COUNT", "name": "Conteo", "default_precision": 0, "supports_fractional": False},
        {"code": "MASS", "name": "Masa / Peso", "default_precision": 4, "supports_fractional": True},
        {"code": "LENGTH", "name": "Longitud / Distancia", "default_precision": 4, "supports_fractional": True},
        {"code": "AREA", "name": "Área / Superficie", "default_precision": 4, "supports_fractional": True},
        {"code": "VOLUME", "name": "Volumen / Capacidad", "default_precision": 6, "supports_fractional": True},
    ]

    dimensions: Dict[str, MeasurementDimensionModel] = {}
    dims_created = 0

    for d in dim_data:
        stmt = select(MeasurementDimensionModel).where(MeasurementDimensionModel.code == d["code"])
        dim = db.scalar(stmt)
        if not dim:
            dim = MeasurementDimensionModel(
                code=d["code"],
                name=d["name"],
                default_precision=d["default_precision"],
                supports_fractional_quantities=d["supports_fractional"],
                status="ACTIVE",
                system_defined=True,
            )
            db.add(dim)
            db.flush()
            dims_created += 1
        dimensions[d["code"]] = dim

    # System Units
    unit_data = [
        # COUNT
        {"code": "UND", "name": "Unidad", "symbol": "und", "dim": "COUNT", "kind": "BASE", "canonical": True, "integer": True},
        {"code": "PAR", "name": "Par", "symbol": "par", "dim": "COUNT", "kind": "DERIVED", "canonical": False, "integer": True},
        {"code": "DOCENA", "name": "Docena", "symbol": "doc", "dim": "COUNT", "kind": "DERIVED", "canonical": False, "integer": True},
        {"code": "CENTENA", "name": "Centena", "symbol": "cen", "dim": "COUNT", "kind": "DERIVED", "canonical": False, "integer": True},
        {"code": "MILLAR", "name": "Millar", "symbol": "mil", "dim": "COUNT", "kind": "DERIVED", "canonical": False, "integer": True},
        {"code": "PAQUETE", "name": "Paquete", "symbol": "pqt", "dim": "COUNT", "kind": "PACKAGING", "canonical": False, "integer": True},
        {"code": "CAJA", "name": "Caja", "symbol": "cja", "dim": "COUNT", "kind": "PACKAGING", "canonical": False, "integer": True},
        {"code": "PALLET", "name": "Pallet / Paleta", "symbol": "plt", "dim": "COUNT", "kind": "PACKAGING", "canonical": False, "integer": True},

        # MASS
        {"code": "KG", "name": "Kilogramo", "symbol": "kg", "dim": "MASS", "kind": "BASE", "canonical": True, "integer": False},
        {"code": "MG", "name": "Miligramo", "symbol": "mg", "dim": "MASS", "kind": "DERIVED", "canonical": False, "integer": False},
        {"code": "G", "name": "Gramo", "symbol": "g", "dim": "MASS", "kind": "DERIVED", "canonical": False, "integer": False},
        {"code": "T", "name": "Tonelada Métria", "symbol": "t", "dim": "MASS", "kind": "DERIVED", "canonical": False, "integer": False},

        # LENGTH
        {"code": "M", "name": "Metro", "symbol": "m", "dim": "LENGTH", "kind": "BASE", "canonical": True, "integer": False},
        {"code": "MM", "name": "Milímetro", "symbol": "mm", "dim": "LENGTH", "kind": "DERIVED", "canonical": False, "integer": False},
        {"code": "CM", "name": "Centímetro", "symbol": "cm", "dim": "LENGTH", "kind": "DERIVED", "canonical": False, "integer": False},
        {"code": "KM", "name": "Kilómetro", "symbol": "km", "dim": "LENGTH", "kind": "DERIVED", "canonical": False, "integer": False},

        # AREA
        {"code": "M2", "name": "Metro Cuadrado", "symbol": "m²", "dim": "AREA", "kind": "BASE", "canonical": True, "integer": False},
        {"code": "MM2", "name": "Milímetro Cuadrado", "symbol": "mm²", "dim": "AREA", "kind": "DERIVED", "canonical": False, "integer": False},
        {"code": "CM2", "name": "Centímetro Cuadrado", "symbol": "cm²", "dim": "AREA", "kind": "DERIVED", "canonical": False, "integer": False},

        # VOLUME
        {"code": "M3", "name": "Metro Cúbico", "symbol": "m³", "dim": "VOLUME", "kind": "BASE", "canonical": True, "integer": False},
        {"code": "ML", "name": "Mililitro", "symbol": "ml", "dim": "VOLUME", "kind": "DERIVED", "canonical": False, "integer": False},
        {"code": "L", "name": "Litro", "symbol": "l", "dim": "VOLUME", "kind": "DERIVED", "canonical": False, "integer": False},
        {"code": "CM3", "name": "Centímetro Cúbico", "symbol": "cm³", "dim": "VOLUME", "kind": "DERIVED", "canonical": False, "integer": False},
    ]

    units: Dict[str, UnitOfMeasureModel] = {}
    units_created = 0

    for u in unit_data:
        dim = dimensions[u["dim"]]
        stmt = select(UnitOfMeasureModel).where(
            UnitOfMeasureModel.organization_id == None,
            UnitOfMeasureModel.normalized_code == u["code"],
        )
        unit = db.scalar(stmt)
        if not unit:
            unit = UnitOfMeasureModel(
                organization_id=None,
                dimension_id=dim.id,
                code=u["code"],
                normalized_code=u["code"],
                name=u["name"],
                symbol=u["symbol"],
                unit_scope="SYSTEM",
                unit_kind=u["kind"],
                is_canonical=u["canonical"],
                integer_only=u["integer"],
                status="ACTIVE",
                system_defined=True,
            )
            db.add(unit)
            db.flush()
            units_created += 1

            if u["canonical"]:
                dim.canonical_unit_id = unit.id

        units[u["code"]] = unit

    # Physical Conversion Rules
    rule_data = [
        # COUNT
        {"src": "PAR", "tgt": "UND", "mult": "2"},
        {"src": "DOCENA", "tgt": "UND", "mult": "12"},
        {"src": "CENTENA", "tgt": "UND", "mult": "100"},
        {"src": "MILLAR", "tgt": "UND", "mult": "1000"},

        # MASS
        {"src": "KG", "tgt": "G", "mult": "1000"},
        {"src": "G", "tgt": "MG", "mult": "1000"},
        {"src": "T", "tgt": "KG", "mult": "1000"},

        # LENGTH
        {"src": "KM", "tgt": "M", "mult": "1000"},
        {"src": "M", "tgt": "CM", "mult": "100"},
        {"src": "CM", "tgt": "MM", "mult": "10"},

        # AREA
        {"src": "M2", "tgt": "CM2", "mult": "10000"},
        {"src": "CM2", "tgt": "MM2", "mult": "100"},

        # VOLUME
        {"src": "M3", "tgt": "L", "mult": "1000"},
        {"src": "L", "tgt": "ML", "mult": "1000"},
        {"src": "CM3", "tgt": "ML", "mult": "1"},
    ]

    rules_created = 0
    for r in rule_data:
        src_u = units[r["src"]]
        tgt_u = units[r["tgt"]]
        mult = Decimal(r["mult"])

        stmt = select(UnitConversionRuleModel).where(
            UnitConversionRuleModel.organization_id == None,
            UnitConversionRuleModel.product_id == None,
            UnitConversionRuleModel.source_unit_id == src_u.id,
            UnitConversionRuleModel.target_unit_id == tgt_u.id,
        )
        rule = db.scalar(stmt)
        if not rule:
            c_hash = hashlib.sha256(f"SYSTEM:None:{src_u.id}:{tgt_u.id}:{mult}".encode("utf-8")).hexdigest()
            rule = UnitConversionRuleModel(
                organization_id=None,
                product_id=None,
                source_unit_id=src_u.id,
                target_unit_id=tgt_u.id,
                conversion_scope="SYSTEM",
                multiplier=mult,
                allows_inverse=True,
                status="ACTIVE",
                content_hash=c_hash,
            )
            db.add(rule)
            rules_created += 1

    db.commit()
    return {
        "dimensions_created": dims_created,
        "units_created": units_created,
        "rules_created": rules_created,
    }
