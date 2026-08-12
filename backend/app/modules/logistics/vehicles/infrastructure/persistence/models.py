"""SQLAlchemy 2.0 ORM Models for Phase 027 (Vehicles Module)."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, Integer, JSON, Numeric, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB, UUID as PG_UUID

JSONB = PG_JSONB().with_variant(JSON, "sqlite")
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class VehicleMakeModel(Base):
    __tablename__ = "vehicle_makes"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="CASCADE"), nullable=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    country_code: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="ACTIVE")
    system_defined: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    created_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    updated_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    models = relationship("VehicleModelModel", back_populates="make", cascade="all, delete-orphan")


class VehicleModelModel(Base):
    __tablename__ = "vehicle_models"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    make_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("vehicle_makes.id", ondelete="CASCADE"), nullable=False)
    organization_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="CASCADE"), nullable=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    vehicle_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    body_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    production_start_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    production_end_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="ACTIVE")
    system_defined: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    created_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    updated_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    make = relationship("VehicleMakeModel", back_populates="models")


class VehicleModel(Base):
    __tablename__ = "vehicles"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="CASCADE"), nullable=False)
    vehicle_code: Mapped[str] = mapped_column(String(50), nullable=False)
    normalized_vehicle_code: Mapped[str] = mapped_column(String(50), nullable=False)
    display_plate: Mapped[str] = mapped_column(String(20), nullable=False)
    normalized_plate: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    vin: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    normalized_vin: Mapped[Optional[str]] = mapped_column(String(30), nullable=True, index=True)
    chassis_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    engine_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    make_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("vehicle_makes.id", ondelete="RESTRICT"), nullable=False)
    model_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("vehicle_models.id", ondelete="RESTRICT"), nullable=False)
    manufacturing_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    model_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    vehicle_type: Mapped[str] = mapped_column(String(50), nullable=False, server_default="HEAVY_TRUCK")
    body_type: Mapped[str] = mapped_column(String(50), nullable=False, server_default="CLOSED_BOX")
    configuration_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    fuel_type: Mapped[Optional[str]] = mapped_column(String(30), nullable=True, server_default="DIESEL")
    transmission_type: Mapped[Optional[str]] = mapped_column(String(30), nullable=True, server_default="MANUAL")
    axle_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    wheel_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    country_of_registration_code: Mapped[str] = mapped_column(String(3), nullable=False, server_default="PE")
    registration_jurisdiction: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    lifecycle_status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="DRAFT")
    operational_status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="UNAVAILABLE")
    compliance_status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="PENDING_REVIEW")
    ownership_type: Mapped[str] = mapped_column(String(30), nullable=False, server_default="OWNED")
    current_owner_assignment_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    current_carrier_assignment_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    active_capacity_profile_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    active_version_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    updated_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    suspended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    suspended_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    suspension_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retired_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    retired_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    retirement_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    archive_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    row_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))

    make = relationship("VehicleMakeModel")
    model = relationship("VehicleModelModel")


class VehicleVersionModel(Base):
    __tablename__ = "vehicle_versions"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    vehicle_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="ACTIVE")
    vehicle_code: Mapped[str] = mapped_column(String(50), nullable=False)
    plate_snapshot: Mapped[str] = mapped_column(String(20), nullable=False)
    vin_snapshot: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    make_snapshot: Mapped[str] = mapped_column(String(100), nullable=False)
    model_snapshot: Mapped[str] = mapped_column(String(100), nullable=False)
    vehicle_type: Mapped[str] = mapped_column(String(50), nullable=False)
    body_type: Mapped[str] = mapped_column(String(50), nullable=False)
    capacity_snapshot: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    dimensions_snapshot: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    ownership_snapshot: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    carrier_snapshot: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    document_compliance_snapshot: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    effective_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    approved_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class VehicleAliasModel(Base):
    __tablename__ = "vehicle_aliases"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    vehicle_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    alias_type: Mapped[str] = mapped_column(String(30), nullable=False)
    previous_value: Mapped[str] = mapped_column(String(100), nullable=False)
    current_value: Mapped[str] = mapped_column(String(100), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class VehiclePlateAssignmentModel(Base):
    __tablename__ = "vehicle_plate_assignments"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    vehicle_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    display_plate: Mapped[str] = mapped_column(String(20), nullable=False)
    normalized_plate: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    country_code: Mapped[str] = mapped_column(String(3), nullable=False, server_default="PE")
    jurisdiction: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    assignment_type: Mapped[str] = mapped_column(String(30), nullable=False, server_default="INITIAL")
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="CURRENT")
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(String(30), nullable=False, server_default="DECLARED")
    created_by: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    approved_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class VehicleCapacityProfileModel(Base):
    __tablename__ = "vehicle_capacity_profiles"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    vehicle_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="ACTIVE")
    maximum_gross_weight_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 4), nullable=True)
    maximum_gross_weight_unit_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("units_of_measure.id", ondelete="RESTRICT"), nullable=True)
    tare_weight_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 4), nullable=True)
    tare_weight_unit_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("units_of_measure.id", ondelete="RESTRICT"), nullable=True)
    maximum_payload_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 4), nullable=True)
    maximum_payload_unit_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("units_of_measure.id", ondelete="RESTRICT"), nullable=True)
    maximum_volume_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 4), nullable=True)
    maximum_volume_unit_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("units_of_measure.id", ondelete="RESTRICT"), nullable=True)
    pallet_position_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    maximum_unit_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    passenger_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    axle_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source_type: Mapped[str] = mapped_column(String(30), nullable=False, server_default="DECLARED")
    source_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    verified_status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="NOT_VERIFIED")
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    effective_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    approved_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class VehicleDimensionsModel(Base):
    __tablename__ = "vehicle_dimensions"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    vehicle_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    external_length_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    external_width_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    external_height_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    internal_length_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    internal_width_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    internal_height_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    dimension_unit_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("units_of_measure.id", ondelete="RESTRICT"), nullable=False)
    calculated_internal_volume: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 4), nullable=True)
    reported_internal_volume: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 4), nullable=True)
    source_type: Mapped[str] = mapped_column(String(30), nullable=False, server_default="DECLARED")
    measured_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="NOT_VERIFIED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class VehicleOwnershipAssignmentModel(Base):
    __tablename__ = "vehicle_ownership_assignments"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    vehicle_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    owner_type: Mapped[str] = mapped_column(String(30), nullable=False)
    owner_organization_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="SET NULL"), nullable=True)
    owner_business_partner_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("business_partners.id", ondelete="SET NULL"), nullable=True)
    ownership_type: Mapped[str] = mapped_column(String(30), nullable=False, server_default="OWNED")
    contract_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="CURRENT")
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    approved_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class VehicleCarrierAssignmentModel(Base):
    __tablename__ = "vehicle_carrier_assignments"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    vehicle_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    carrier_business_partner_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("business_partners.id", ondelete="RESTRICT"), nullable=False)
    carrier_role_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("business_partner_roles.id", ondelete="RESTRICT"), nullable=False)
    assignment_type: Mapped[str] = mapped_column(String(30), nullable=False, server_default="OWN_FLEET")
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="CURRENT")
    authorization_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    approved_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class VehicleDocumentModel(Base):
    __tablename__ = "vehicle_documents"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    vehicle_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    document_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    issuer: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    issued_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    verification_status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="NOT_VERIFIED")
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="ACTIVE")
    file_reference_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_type: Mapped[str] = mapped_column(String(30), nullable=False, server_default="DECLARED")
    source_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    reviewed_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class VehicleDocumentRequirementModel(Base):
    __tablename__ = "vehicle_document_requirements"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="CASCADE"), nullable=False)
    vehicle_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    body_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ownership_type: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    blocking: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    requires_expiration: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    warning_days_before_expiration: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("30"))
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="ACTIVE")
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    effective_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    approved_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class VehicleOperationalRestrictionModel(Base):
    __tablename__ = "vehicle_operational_restrictions"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    vehicle_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    restriction_type: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    estimated_end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="ACTIVE")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    resolved_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
