"""SQLAlchemy ORM models for Phase 024 — Units and Conversions Engine."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import relationship

from app.database.base import Base


class MeasurementDimensionModel(Base):
    __tablename__ = "measurement_dimensions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    code = Column(String(30), nullable=False, unique=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    canonical_unit_id = Column(PG_UUID(as_uuid=True), ForeignKey("units_of_measure.id", ondelete="SET NULL", use_alter=True, name="fk_dimensions_canonical_unit_id"), nullable=True)
    supports_fractional_quantities = Column(Boolean, nullable=False, default=True)
    default_precision = Column(Integer, nullable=False, default=4)
    status = Column(String(20), nullable=False, default="ACTIVE")
    system_defined = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    units = relationship("UnitOfMeasureModel", foreign_keys="[UnitOfMeasureModel.dimension_id]", back_populates="dimension")


class UnitOfMeasureModel(Base):
    __tablename__ = "units_of_measure"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PG_UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="RESTRICT"), nullable=True, index=True)
    dimension_id = Column(PG_UUID(as_uuid=True), ForeignKey("measurement_dimensions.id", ondelete="RESTRICT"), nullable=False, index=True)
    code = Column(String(30), nullable=False)
    normalized_code = Column(String(30), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    plural_name = Column(String(100), nullable=True)
    symbol = Column(String(20), nullable=False)
    unit_scope = Column(String(20), nullable=False, default="SYSTEM")
    unit_kind = Column(String(20), nullable=False, default="BASE")
    decimal_precision = Column(Integer, nullable=False, default=4)
    minimum_increment = Column(Numeric(38, 18), nullable=True)
    integer_only = Column(Boolean, nullable=False, default=False)
    is_canonical = Column(Boolean, nullable=False, default=False)
    status = Column(String(20), nullable=False, default="ACTIVE")
    system_defined = Column(Boolean, nullable=False, default=True)
    active_version_id = Column(PG_UUID(as_uuid=True), nullable=True)
    row_version = Column(Integer, nullable=False, default=1)
    created_by = Column(PG_UUID(as_uuid=True), nullable=True)
    updated_by = Column(PG_UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    dimension = relationship("MeasurementDimensionModel", foreign_keys=[dimension_id], back_populates="units")

    __table_args__ = (
        UniqueConstraint("organization_id", "normalized_code", name="uq_units_org_norm_code"),
    )


class UnitOfMeasureVersionModel(Base):
    __tablename__ = "unit_of_measure_versions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    unit_id = Column(PG_UUID(as_uuid=True), ForeignKey("units_of_measure.id", ondelete="CASCADE"), nullable=False)
    version = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default="ACTIVE")
    name = Column(String(100), nullable=False)
    symbol = Column(String(20), nullable=False)
    dimension_snapshot = Column(JSONB, nullable=False)
    precision = Column(Integer, nullable=False)
    content_hash = Column(String(64), nullable=False)
    effective_from = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    effective_to = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(PG_UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("unit_id", "version", name="uq_unit_versions_unit_version"),
    )


class UnitConversionRuleModel(Base):
    __tablename__ = "unit_conversion_rules"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PG_UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="RESTRICT"), nullable=True)
    product_id = Column(PG_UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=True, index=True)
    source_unit_id = Column(PG_UUID(as_uuid=True), ForeignKey("units_of_measure.id", ondelete="RESTRICT"), nullable=False, index=True)
    target_unit_id = Column(PG_UUID(as_uuid=True), ForeignKey("units_of_measure.id", ondelete="RESTRICT"), nullable=False, index=True)
    conversion_scope = Column(String(20), nullable=False, default="SYSTEM", index=True)
    multiplier = Column(Numeric(38, 18), nullable=False)
    multiplier_numerator = Column(Numeric(38, 18), nullable=True)
    multiplier_denominator = Column(Numeric(38, 18), nullable=True)
    allows_inverse = Column(Boolean, nullable=False, default=True)
    precision = Column(Integer, nullable=False, default=4)
    rounding_policy = Column(String(30), nullable=False, default="HALF_UP")
    status = Column(String(20), nullable=False, default="ACTIVE")
    version = Column(String(20), nullable=False, default="1.0.0")
    effective_from = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    effective_to = Column(DateTime(timezone=True), nullable=True)
    content_hash = Column(String(64), nullable=False)
    created_by = Column(PG_UUID(as_uuid=True), nullable=True)
    updated_by = Column(PG_UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    source_unit = relationship("UnitOfMeasureModel", foreign_keys=[source_unit_id])
    target_unit = relationship("UnitOfMeasureModel", foreign_keys=[target_unit_id])


class ProductUnitConfigurationModel(Base):
    __tablename__ = "product_unit_configurations"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    product_id = Column(PG_UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, unique=True)
    base_unit_id = Column(PG_UUID(as_uuid=True), ForeignKey("units_of_measure.id", ondelete="RESTRICT"), nullable=False)
    purchase_unit_id = Column(PG_UUID(as_uuid=True), ForeignKey("units_of_measure.id", ondelete="RESTRICT"), nullable=True)
    reception_unit_id = Column(PG_UUID(as_uuid=True), ForeignKey("units_of_measure.id", ondelete="RESTRICT"), nullable=True)
    storage_unit_id = Column(PG_UUID(as_uuid=True), ForeignKey("units_of_measure.id", ondelete="RESTRICT"), nullable=True)
    picking_unit_id = Column(PG_UUID(as_uuid=True), ForeignKey("units_of_measure.id", ondelete="RESTRICT"), nullable=True)
    dispatch_unit_id = Column(PG_UUID(as_uuid=True), ForeignKey("units_of_measure.id", ondelete="RESTRICT"), nullable=True)
    count_unit_id = Column(PG_UUID(as_uuid=True), ForeignKey("units_of_measure.id", ondelete="RESTRICT"), nullable=True)
    status = Column(String(20), nullable=False, default="ACTIVE")
    version = Column(String(20), nullable=False, default="1.0.0")
    effective_from = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    effective_to = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(PG_UUID(as_uuid=True), nullable=True)
    updated_by = Column(PG_UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    base_unit = relationship("UnitOfMeasureModel", foreign_keys=[base_unit_id])


class ProductPackagingDefinitionModel(Base):
    __tablename__ = "product_packaging_definitions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    product_id = Column(PG_UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    packaging_unit_id = Column(PG_UUID(as_uuid=True), ForeignKey("units_of_measure.id", ondelete="RESTRICT"), nullable=False)
    contained_unit_id = Column(PG_UUID(as_uuid=True), ForeignKey("units_of_measure.id", ondelete="RESTRICT"), nullable=False)
    contained_quantity = Column(Numeric(38, 18), nullable=False)
    level_order = Column(Integer, nullable=False)
    package_type = Column(String(30), nullable=False, default="BOX")
    gross_weight = Column(Numeric(14, 4), nullable=True)
    status = Column(String(20), nullable=False, default="ACTIVE")
    version = Column(String(20), nullable=False, default="1.0.0")
    effective_from = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    effective_to = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(PG_UUID(as_uuid=True), nullable=True)
    updated_by = Column(PG_UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    packaging_unit = relationship("UnitOfMeasureModel", foreign_keys=[packaging_unit_id])
    contained_unit = relationship("UnitOfMeasureModel", foreign_keys=[contained_unit_id])

    __table_args__ = (
        UniqueConstraint("product_id", "packaging_unit_id", name="uq_product_pkg_prod_unit"),
    )
