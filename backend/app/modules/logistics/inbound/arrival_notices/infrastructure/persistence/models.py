"""SQLAlchemy models for expected inbound arrivals (Phase 036).

These tables intentionally contain no physical gate entry, dock, unloading,
receiving, pallet entity or inventory mutation fields.
"""

from __future__ import annotations

from uuid import uuid4

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
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

_QTY = dict(precision=28, scale=10)
_WEIGHT = dict(precision=28, scale=10)


class ArrivalNoticeModel(Base):
    __tablename__ = "arrival_notices"
    __allow_unmapped__ = True
    __table_args__ = (
        CheckConstraint("expected_pallet_count >= 0", name="ck_arrival_notice_pallets_non_negative"),
        CheckConstraint("expected_package_count >= 0", name="ck_arrival_notice_packages_non_negative"),
        CheckConstraint(
            "expected_loose_item_count IS NULL OR expected_loose_item_count >= 0",
            name="ck_arrival_notice_loose_non_negative",
        ),
        CheckConstraint("expected_gross_weight >= 0", name="ck_arrival_notice_weight_non_negative"),
        CheckConstraint("current_revision_number >= 1", name="ck_arrival_notice_revision_positive"),
        CheckConstraint("row_version >= 1", name="ck_arrival_notice_row_version_positive"),
        Index("ix_arrival_notices_org", "organization_id"),
        Index("ix_arrival_notices_warehouse", "warehouse_id"),
        Index("ix_arrival_notices_supplier", "supplier_business_partner_id"),
        Index("ix_arrival_notices_carrier", "carrier_business_partner_id"),
        Index("ix_arrival_notices_status", "status"),
        Index("ix_arrival_notices_expected_date", "expected_arrival_date"),
        Index("ix_arrival_notices_updated", "updated_at"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("logistics_organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    branch_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("logistics_branches.id", ondelete="RESTRICT"),
        nullable=False,
    )
    warehouse_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("warehouses.id", ondelete="RESTRICT"),
        nullable=False,
    )
    supplier_business_partner_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("business_partners.id", ondelete="RESTRICT"),
        nullable=False,
    )
    supplier_snapshot = Column(JSONB, nullable=False, default=dict)
    carrier_business_partner_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("business_partners.id", ondelete="RESTRICT"),
        nullable=True,
    )
    carrier_snapshot = Column(JSONB, nullable=True)
    submission_channel = Column(String(40), nullable=False, default="INTERNAL")
    external_reference = Column(String(160), nullable=True)
    status = Column(String(40), nullable=False, default="DRAFT")
    appointment_status = Column(String(40), nullable=False, default="PROPOSED")
    source_type = Column(String(40), nullable=False, default="PURCHASE_ORDER")
    current_revision_number = Column(Integer, nullable=False, default=1)
    active_revision_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "arrival_notice_revisions.id",
            name="fk_arrival_notice_active_revision",
            ondelete="RESTRICT",
            use_alter=True,
        ),
        nullable=True,
    )
    confirmed_revision_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "arrival_notice_revisions.id",
            name="fk_arrival_notice_confirmed_revision",
            ondelete="RESTRICT",
            use_alter=True,
        ),
        nullable=True,
    )
    appointment_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "reception_appointments.id",
            name="fk_arrival_notice_appointment",
            ondelete="RESTRICT",
            use_alter=True,
        ),
        nullable=True,
    )
    expected_arrival_date = Column(Date, nullable=False)
    expected_arrival_timezone = Column(String(64), nullable=False)
    total_purchase_orders = Column(Integer, nullable=False, default=0)
    total_lines = Column(Integer, nullable=False, default=0)
    expected_pallet_count = Column(Integer, nullable=False, default=0)
    expected_package_count = Column(Integer, nullable=False, default=0)
    expected_loose_item_count = Column(Integer, nullable=True)
    expected_gross_weight = Column(Numeric(**_WEIGHT), nullable=False, default=0)
    normalized_gross_weight = Column(Numeric(**_WEIGHT), nullable=True)
    weight_unit_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("units_of_measure.id", ondelete="RESTRICT"),
        nullable=False,
    )
    normalized_weight_unit_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("units_of_measure.id", ondelete="RESTRICT"),
        nullable=True,
    )
    transport_mode = Column(String(50), nullable=False, default="TO_BE_CONFIRMED")
    special_handling_summary = Column(JSONB, nullable=False, default=list)
    comments = Column(Text, nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    submitted_by = Column(PG_UUID(as_uuid=True), nullable=True)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    confirmed_by = Column(PG_UUID(as_uuid=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_by = Column(PG_UUID(as_uuid=True), nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    window_elapsed_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(PG_UUID(as_uuid=True), nullable=False)
    updated_by = Column(PG_UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    row_version = Column(Integer, nullable=False, default=1)

    revisions = relationship(
        "ArrivalNoticeRevisionModel",
        back_populates="arrival_notice",
        foreign_keys="[ArrivalNoticeRevisionModel.arrival_notice_id]",
        order_by="ArrivalNoticeRevisionModel.revision_number",
    )


class ArrivalNoticeRevisionModel(Base):
    __tablename__ = "arrival_notice_revisions"
    __allow_unmapped__ = True
    __table_args__ = (
        UniqueConstraint(
            "arrival_notice_id",
            "revision_number",
            name="uq_arrival_notice_revision_number",
        ),
        CheckConstraint("revision_number >= 1", name="ck_arrival_notice_revision_number_positive"),
        Index("ix_arrival_notice_revisions_notice", "arrival_notice_id"),
        Index("ix_arrival_notice_revisions_status", "status"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    arrival_notice_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("arrival_notices.id", ondelete="RESTRICT"),
        nullable=False,
    )
    revision_number = Column(Integer, nullable=False)
    status = Column(String(30), nullable=False, default="EDITABLE")
    supplier_snapshot = Column(JSONB, nullable=False, default=dict)
    carrier_snapshot = Column(JSONB, nullable=True)
    warehouse_snapshot = Column(JSONB, nullable=False, default=dict)
    purchase_order_snapshots = Column(JSONB, nullable=False, default=list)
    transport_snapshot = Column(JSONB, nullable=False, default=dict)
    document_references_snapshot = Column(JSONB, nullable=False, default=list)
    expected_load_summary = Column(JSONB, nullable=False, default=dict)
    proposed_window = Column(JSONB, nullable=True)
    special_requirements = Column(JSONB, nullable=False, default=list)
    comments = Column(Text, nullable=True)
    content_hash = Column(String(64), nullable=True)
    created_from_revision_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("arrival_notice_revisions.id", ondelete="RESTRICT"),
        nullable=True,
    )
    change_summary = Column(Text, nullable=True)
    created_by = Column(PG_UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    frozen_at = Column(DateTime(timezone=True), nullable=True)

    arrival_notice = relationship(
        "ArrivalNoticeModel",
        back_populates="revisions",
        foreign_keys=[arrival_notice_id],
    )
    purchase_orders = relationship(
        "ArrivalNoticePurchaseOrderReferenceModel",
        back_populates="revision",
        cascade="all, delete-orphan",
    )
    lines = relationship(
        "ArrivalNoticeExpectedLineModel",
        back_populates="revision",
        cascade="all, delete-orphan",
    )
    transport_documents = relationship(
        "ArrivalNoticeTransportDocumentModel",
        back_populates="revision",
        cascade="all, delete-orphan",
    )


class ArrivalNoticePurchaseOrderReferenceModel(Base):
    __tablename__ = "arrival_notice_purchase_order_references"
    __allow_unmapped__ = True
    __table_args__ = (
        UniqueConstraint(
            "arrival_notice_revision_id",
            "purchase_order_id",
            name="uq_arrival_notice_revision_po",
        ),
        Index("ix_arrival_notice_po_ref_po", "purchase_order_id"),
        Index("ix_arrival_notice_po_ref_revision", "arrival_notice_revision_id"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    arrival_notice_revision_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("arrival_notice_revisions.id", ondelete="CASCADE"),
        nullable=False,
    )
    purchase_order_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("po_purchase_orders.id", ondelete="RESTRICT"),
        nullable=False,
    )
    purchase_order_revision_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("po_purchase_order_revisions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    purchase_order_code = Column(String(60), nullable=False)
    supplier_business_partner_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("business_partners.id", ondelete="RESTRICT"),
        nullable=False,
    )
    currency_code = Column(String(3), nullable=False)
    source_snapshot_hash = Column(String(64), nullable=False)
    status = Column(String(30), nullable=False, default="ACTIVE")
    linked_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    revision = relationship("ArrivalNoticeRevisionModel", back_populates="purchase_orders")
    lines = relationship(
        "ArrivalNoticeExpectedLineModel",
        back_populates="purchase_order_reference",
    )


class ArrivalNoticeExpectedLineModel(Base):
    __tablename__ = "arrival_notice_expected_lines"
    __allow_unmapped__ = True
    __table_args__ = (
        UniqueConstraint(
            "arrival_notice_revision_id",
            "purchase_order_line_id",
            name="uq_arrival_notice_revision_po_line",
        ),
        CheckConstraint("expected_quantity > 0", name="ck_arrival_expected_line_qty_positive"),
        CheckConstraint("expected_base_quantity > 0", name="ck_arrival_expected_line_base_qty_positive"),
        CheckConstraint(
            "expected_package_count IS NULL OR expected_package_count >= 0",
            name="ck_arrival_expected_line_packages_non_negative",
        ),
        CheckConstraint(
            "expected_pallet_count IS NULL OR expected_pallet_count >= 0",
            name="ck_arrival_expected_line_pallets_non_negative",
        ),
        Index("ix_arrival_expected_line_po_line", "purchase_order_line_id"),
        Index("ix_arrival_expected_line_product", "product_id"),
        Index("ix_arrival_expected_line_revision", "arrival_notice_revision_id"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    arrival_notice_revision_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("arrival_notice_revisions.id", ondelete="CASCADE"),
        nullable=False,
    )
    purchase_order_reference_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("arrival_notice_purchase_order_references.id", ondelete="RESTRICT"),
        nullable=False,
    )
    purchase_order_line_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("po_purchase_order_lines.id", ondelete="RESTRICT"),
        nullable=False,
    )
    purchase_order_schedule_line_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("po_delivery_schedule_lines.id", ondelete="RESTRICT"),
        nullable=True,
    )
    line_number = Column(Integer, nullable=False)
    product_id = Column(PG_UUID(as_uuid=True), nullable=True)
    product_version_id = Column(PG_UUID(as_uuid=True), nullable=True)
    sku_snapshot = Column(String(120), nullable=True)
    product_name_snapshot = Column(String(500), nullable=False)
    expected_quantity = Column(Numeric(**_QTY), nullable=False)
    expected_unit_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("units_of_measure.id", ondelete="RESTRICT"),
        nullable=False,
    )
    expected_base_quantity = Column(Numeric(**_QTY), nullable=False)
    base_unit_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("units_of_measure.id", ondelete="RESTRICT"),
        nullable=False,
    )
    conversion_rule_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("unit_conversion_rules.id", ondelete="RESTRICT"),
        nullable=True,
    )
    conversion_factor_snapshot = Column(Numeric(**_QTY), nullable=True)
    expected_package_count = Column(Integer, nullable=True)
    expected_pallet_count = Column(Integer, nullable=True)
    supplier_lot_reference = Column(String(120), nullable=True)
    supplier_expiration_reference = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="EXPECTED")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    revision = relationship("ArrivalNoticeRevisionModel", back_populates="lines")
    purchase_order_reference = relationship(
        "ArrivalNoticePurchaseOrderReferenceModel",
        back_populates="lines",
    )


class InboundExpectedQuantityAllocationModel(Base):
    __tablename__ = "inbound_expected_quantity_allocations"
    __allow_unmapped__ = True
    __table_args__ = (
        UniqueConstraint("expected_line_id", name="uq_inbound_allocation_expected_line"),
        CheckConstraint("allocated_quantity > 0", name="ck_inbound_allocation_qty_positive"),
        CheckConstraint("allocated_base_quantity > 0", name="ck_inbound_allocation_base_qty_positive"),
        Index("ix_inbound_allocations_org", "organization_id"),
        Index("ix_inbound_allocations_notice", "arrival_notice_id"),
        Index("ix_inbound_allocations_po_line", "purchase_order_line_id"),
        Index("ix_inbound_allocations_status", "status"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("logistics_organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    arrival_notice_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("arrival_notices.id", ondelete="RESTRICT"),
        nullable=False,
    )
    expected_line_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("arrival_notice_expected_lines.id", ondelete="RESTRICT"),
        nullable=False,
    )
    purchase_order_line_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("po_purchase_order_lines.id", ondelete="RESTRICT"),
        nullable=False,
    )
    purchase_order_schedule_line_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("po_delivery_schedule_lines.id", ondelete="RESTRICT"),
        nullable=True,
    )
    allocated_quantity = Column(Numeric(**_QTY), nullable=False)
    allocated_unit_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("units_of_measure.id", ondelete="RESTRICT"),
        nullable=False,
    )
    allocated_base_quantity = Column(Numeric(**_QTY), nullable=False)
    status = Column(String(30), nullable=False, default="HELD")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    released_at = Column(DateTime(timezone=True), nullable=True)
    release_reason = Column(Text, nullable=True)


class ArrivalNoticeVehicleReferenceModel(Base):
    __tablename__ = "arrival_notice_vehicle_references"
    __allow_unmapped__ = True
    __table_args__ = (
        UniqueConstraint("revision_id", name="uq_arrival_notice_vehicle_revision"),
        Index("ix_arrival_notice_vehicle_plate", "normalized_plate"),
        Index("ix_arrival_notice_vehicle_id", "vehicle_id"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    revision_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("arrival_notice_revisions.id", ondelete="CASCADE"),
        nullable=False,
    )
    vehicle_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("vehicles.id", ondelete="RESTRICT"),
        nullable=True,
    )
    plate_snapshot = Column(String(20), nullable=False)
    normalized_plate = Column(String(20), nullable=False)
    vehicle_snapshot = Column(JSONB, nullable=True)
    source_type = Column(String(50), nullable=False)
    verification_summary = Column(JSONB, nullable=False, default=dict)
    verification_date = Column(DateTime(timezone=True), nullable=True)
    verification_expiration = Column(DateTime(timezone=True), nullable=True)
    exception_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ArrivalNoticeDriverReferenceModel(Base):
    __tablename__ = "arrival_notice_driver_references"
    __allow_unmapped__ = True
    __table_args__ = (
        UniqueConstraint("revision_id", name="uq_arrival_notice_driver_revision"),
        Index("ix_arrival_notice_driver_id", "driver_id"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    revision_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("arrival_notice_revisions.id", ondelete="CASCADE"),
        nullable=False,
    )
    driver_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("drivers.id", ondelete="RESTRICT"),
        nullable=True,
    )
    full_name_snapshot = Column(String(300), nullable=False)
    document_type_snapshot = Column(String(30), nullable=True)
    document_number_redacted_snapshot = Column(String(80), nullable=True)
    license_number_redacted_snapshot = Column(String(80), nullable=True)
    license_category_snapshot = Column(String(120), nullable=True)
    license_expiration_snapshot = Column(Date, nullable=True)
    contact_snapshot = Column(JSONB, nullable=True)
    source_type = Column(String(50), nullable=False)
    exception_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ArrivalNoticeTransportDocumentModel(Base):
    __tablename__ = "arrival_notice_transport_documents"
    __allow_unmapped__ = True
    __table_args__ = (
        UniqueConstraint(
            "revision_id",
            "document_kind",
            "normalized_reference",
            name="uq_arrival_transport_doc_reference",
        ),
        Index("ix_arrival_transport_docs_revision", "revision_id"),
        Index("ix_arrival_transport_docs_reference", "normalized_reference"),
        Index("ix_arrival_transport_docs_file", "file_asset_id"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    revision_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("arrival_notice_revisions.id", ondelete="CASCADE"),
        nullable=False,
    )
    document_kind = Column(String(50), nullable=False)
    issuer_business_partner_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("business_partners.id", ondelete="RESTRICT"),
        nullable=True,
    )
    issuer_tax_identifier_snapshot = Column(String(40), nullable=True)
    series = Column(String(40), nullable=True)
    number = Column(String(80), nullable=False)
    normalized_reference = Column(String(140), nullable=False)
    issue_date = Column(Date, nullable=True)
    document_date = Column(Date, nullable=True)
    transport_reference = Column(String(160), nullable=True)
    verification_status = Column(String(50), nullable=False, default="NOT_VERIFIED")
    verification_source = Column(String(80), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    file_asset_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("file_assets.id", ondelete="RESTRICT"),
        nullable=True,
    )
    notes = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="ACTIVE")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    revision = relationship("ArrivalNoticeRevisionModel", back_populates="transport_documents")


class ArrivalNoticeOutboxEventModel(Base):
    """Transactional outbox scoped to inbound until a generic outbox exists."""

    __tablename__ = "arrival_notice_outbox_events"
    __allow_unmapped__ = True
    __table_args__ = (
        UniqueConstraint("organization_id", "deduplication_key", name="uq_arrival_outbox_dedupe"),
        Index("ix_arrival_outbox_status_available", "status", "available_at"),
        Index("ix_arrival_outbox_aggregate", "aggregate_type", "aggregate_id"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("logistics_organizations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    aggregate_type = Column(String(60), nullable=False)
    aggregate_id = Column(PG_UUID(as_uuid=True), nullable=False)
    event_type = Column(String(120), nullable=False)
    payload = Column(JSONB, nullable=False, default=dict)
    deduplication_key = Column(String(180), nullable=False)
    status = Column(String(30), nullable=False, default="PENDING")
    attempt_count = Column(Integer, nullable=False, default=0)
    available_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
