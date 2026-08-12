"""SQLAlchemy ORM models for Phase 023 — Product Catalog."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
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


class ProductCategoryModel(Base):
    __tablename__ = "product_categories"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PG_UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="RESTRICT"), nullable=False, index=True)
    parent_category_id = Column(PG_UUID(as_uuid=True), ForeignKey("product_categories.id", ondelete="RESTRICT"), nullable=True, index=True)
    code = Column(String(50), nullable=False)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    hierarchy_path = Column(String(500), nullable=False, index=True)
    depth = Column(Integer, nullable=False, default=1)
    status = Column(String(20), nullable=False, default="ACTIVE")
    default_tracking_policy_id = Column(PG_UUID(as_uuid=True), nullable=True)
    default_storage_condition_id = Column(PG_UUID(as_uuid=True), nullable=True)
    created_by = Column(PG_UUID(as_uuid=True), nullable=True)
    updated_by = Column(PG_UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    parent = relationship("ProductCategoryModel", remote_side=[id], backref="children")

    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_product_categories_org_code"),
    )


class ProductBrandModel(Base):
    __tablename__ = "product_brands"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PG_UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="RESTRICT"), nullable=False, index=True)
    code = Column(String(50), nullable=False)
    name = Column(String(150), nullable=False)
    normalized_name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    manufacturer_name = Column(String(200), nullable=True)
    country_code = Column(String(2), nullable=True)
    status = Column(String(20), nullable=False, default="ACTIVE")
    created_by = Column(PG_UUID(as_uuid=True), nullable=True)
    updated_by = Column(PG_UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_product_brands_org_code"),
        UniqueConstraint("organization_id", "normalized_name", name="uq_product_brands_org_norm_name"),
    )


class ProductModel(Base):
    __tablename__ = "products"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PG_UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="RESTRICT"), nullable=False, index=True)
    sku = Column(String(50), nullable=False)
    normalized_sku = Column(String(50), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    short_name = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    category_id = Column(PG_UUID(as_uuid=True), ForeignKey("product_categories.id", ondelete="RESTRICT"), nullable=False, index=True)
    brand_id = Column(PG_UUID(as_uuid=True), ForeignKey("product_brands.id", ondelete="RESTRICT"), nullable=True, index=True)
    product_type = Column(String(30), nullable=False, default="PHYSICAL_GOOD")
    base_unit_code = Column(String(20), nullable=False, default="UND")
    status = Column(String(20), nullable=False, default="DRAFT", index=True)
    lifecycle_status = Column(String(20), nullable=False, default="ACTIVE")
    tracking_policy_id = Column(PG_UUID(as_uuid=True), nullable=True)
    physical_profile_id = Column(PG_UUID(as_uuid=True), nullable=True)
    default_storage_condition_id = Column(PG_UUID(as_uuid=True), nullable=True)
    tax_category_reference = Column(String(50), nullable=True)
    manufacturer_reference = Column(String(100), nullable=True)
    country_of_origin_code = Column(String(2), nullable=True)
    internal_notes = Column(Text, nullable=True)
    external_description = Column(Text, nullable=True)
    active_version_id = Column(PG_UUID(as_uuid=True), nullable=True)
    created_by = Column(PG_UUID(as_uuid=True), nullable=True)
    updated_by = Column(PG_UUID(as_uuid=True), nullable=True)
    archived_by = Column(PG_UUID(as_uuid=True), nullable=True)
    archive_reason = Column(Text, nullable=True)
    archived_at = Column(DateTime(timezone=True), nullable=True)
    row_version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    category = relationship("ProductCategoryModel", foreign_keys=[category_id])
    brand = relationship("ProductBrandModel", foreign_keys=[brand_id])
    sku_aliases = relationship("ProductSKUAliasModel", back_populates="product", cascade="all, delete-orphan")
    versions = relationship("ProductVersionModel", back_populates="product", cascade="all, delete-orphan", foreign_keys="ProductVersionModel.product_id")
    identifiers = relationship("ProductIdentifierModel", back_populates="product", cascade="all, delete-orphan")
    physical_profile = relationship("ProductPhysicalProfileModel", back_populates="product", uselist=False, cascade="all, delete-orphan")
    tracking_policy = relationship("ProductTrackingPolicyModel", back_populates="product", uselist=False, cascade="all, delete-orphan")
    storage_conditions = relationship("ProductStorageConditionModel", back_populates="product", cascade="all, delete-orphan")
    handling_conditions = relationship("ProductHandlingConditionModel", back_populates="product", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("organization_id", "normalized_sku", name="uq_products_org_normalized_sku"),
    )


class ProductSKUAliasModel(Base):
    __tablename__ = "product_sku_aliases"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    product_id = Column(PG_UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(PG_UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="RESTRICT"), nullable=False)
    previous_sku = Column(String(50), nullable=False, index=True)
    current_sku = Column(String(50), nullable=False)
    reason = Column(Text, nullable=False)
    valid_from = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    valid_until = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(PG_UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    product = relationship("ProductModel", back_populates="sku_aliases")


class ProductVersionModel(Base):
    __tablename__ = "product_versions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    product_id = Column(PG_UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default="DRAFT")
    sku_snapshot = Column(String(50), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category_snapshot = Column(JSONB, nullable=False)
    brand_snapshot = Column(JSONB, nullable=True)
    product_type = Column(String(30), nullable=False)
    base_unit_code = Column(String(20), nullable=False)
    tracking_policy_snapshot = Column(JSONB, nullable=True)
    physical_profile_snapshot = Column(JSONB, nullable=True)
    storage_conditions_snapshot = Column(JSONB, nullable=True)
    handling_conditions_snapshot = Column(JSONB, nullable=True)
    identifiers_snapshot = Column(JSONB, nullable=True)
    content_hash = Column(String(64), nullable=False)
    effective_from = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    effective_to = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(PG_UUID(as_uuid=True), nullable=True)
    approved_by = Column(PG_UUID(as_uuid=True), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    product = relationship("ProductModel", back_populates="versions", foreign_keys=[product_id])

    __table_args__ = (
        UniqueConstraint("product_id", "version", name="uq_product_versions_product_version"),
    )


class ProductIdentifierModel(Base):
    __tablename__ = "product_identifiers"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PG_UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="RESTRICT"), nullable=False, index=True)
    product_id = Column(PG_UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    identifier_type = Column(String(30), nullable=False)
    value = Column(String(100), nullable=False)
    normalized_value = Column(String(100), nullable=False, index=True)
    symbology = Column(String(30), nullable=True)
    issuer = Column(String(100), nullable=True)
    is_primary = Column(Boolean, nullable=False, default=False)
    status = Column(String(20), nullable=False, default="ACTIVE")
    valid_from = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    valid_until = Column(DateTime(timezone=True), nullable=True)
    verified_status = Column(String(30), nullable=False, default="NOT_VERIFIED")
    created_by = Column(PG_UUID(as_uuid=True), nullable=True)
    updated_by = Column(PG_UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    product = relationship("ProductModel", back_populates="identifiers")

    __table_args__ = (
        UniqueConstraint("organization_id", "normalized_value", name="uq_product_identifiers_org_norm_val"),
    )


class ProductPhysicalProfileModel(Base):
    __tablename__ = "product_physical_profiles"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    product_id = Column(PG_UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, unique=True)
    net_weight_value = Column(Numeric(14, 4), nullable=True)
    net_weight_unit = Column(String(20), nullable=True)
    gross_weight_value = Column(Numeric(14, 4), nullable=True)
    gross_weight_unit = Column(String(20), nullable=True)
    length_value = Column(Numeric(14, 4), nullable=True)
    width_value = Column(Numeric(14, 4), nullable=True)
    height_value = Column(Numeric(14, 4), nullable=True)
    dimension_unit = Column(String(20), nullable=True)
    volume_value = Column(Numeric(14, 4), nullable=True)
    volume_unit = Column(String(20), nullable=True)
    density_value = Column(Numeric(14, 4), nullable=True)
    density_unit = Column(String(20), nullable=True)
    measurement_source = Column(String(30), nullable=False, default="MANUAL")
    measured_at = Column(DateTime(timezone=True), nullable=True)
    verified_by = Column(PG_UUID(as_uuid=True), nullable=True)
    status = Column(String(20), nullable=False, default="ACTIVE")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    product = relationship("ProductModel", back_populates="physical_profile")


class ProductTrackingPolicyModel(Base):
    __tablename__ = "product_tracking_policies"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    product_id = Column(PG_UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, unique=True)
    tracking_type = Column(String(30), nullable=False, default="NONE")
    lot_control = Column(Boolean, nullable=False, default=False)
    serial_control = Column(Boolean, nullable=False, default=False)
    expiration_control = Column(String(30), nullable=False, default="NONE")
    manufacturing_date_control = Column(Boolean, nullable=False, default=False)
    best_before_control = Column(Boolean, nullable=False, default=False)
    minimum_shelf_life_days = Column(Integer, nullable=True)
    total_shelf_life_days = Column(Integer, nullable=True)
    serial_quantity_rule = Column(String(40), nullable=False, default="NOT_APPLICABLE")
    lot_uniqueness_scope = Column(String(30), nullable=False, default="PRODUCT")
    allow_mixed_lots = Column(Boolean, nullable=False, default=True)
    allow_mixed_expiration_dates = Column(Boolean, nullable=False, default=False)
    require_supplier_lot = Column(Boolean, nullable=False, default=False)
    require_manufacturer_serial = Column(Boolean, nullable=False, default=False)
    status = Column(String(20), nullable=False, default="ACTIVE")
    effective_from = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    effective_to = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(PG_UUID(as_uuid=True), nullable=True)
    updated_by = Column(PG_UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    product = relationship("ProductModel", back_populates="tracking_policy")


class ProductStorageConditionModel(Base):
    __tablename__ = "product_storage_conditions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    product_id = Column(PG_UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    condition_type = Column(String(40), nullable=False)
    minimum_value = Column(Numeric(10, 2), nullable=True)
    maximum_value = Column(Numeric(10, 2), nullable=True)
    unit_code = Column(String(20), nullable=True)
    required = Column(Boolean, nullable=False, default=True)
    severity = Column(String(20), nullable=False, default="HARD_BLOCK")
    handling_instruction = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="ACTIVE")
    effective_from = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    effective_to = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(PG_UUID(as_uuid=True), nullable=True)
    updated_by = Column(PG_UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    product = relationship("ProductModel", back_populates="storage_conditions")


class ProductHandlingConditionModel(Base):
    __tablename__ = "product_handling_conditions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    product_id = Column(PG_UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    condition_type = Column(String(40), nullable=False)
    instruction = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False, default="WARNING_ONLY")
    required_equipment = Column(String(100), nullable=True)
    status = Column(String(20), nullable=False, default="ACTIVE")
    effective_from = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    effective_to = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(PG_UUID(as_uuid=True), nullable=True)
    updated_by = Column(PG_UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    product = relationship("ProductModel", back_populates="handling_conditions")
