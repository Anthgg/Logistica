"""Phase 039 persistence. Scan events and revisions are append-only by service policy."""

from uuid import uuid4

from sqlalchemy import Boolean, CheckConstraint, Column, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID

from app.database.base import Base

QTY = {"precision": 38, "scale": 18}
ACTIVE_RECEIPT_SQL = "status NOT IN ('COMPLETED','CANCELLED','SUPERSEDED','FAILED')"


class InboundReceiptModel(Base):
    __tablename__ = "inbound_receipts"
    __table_args__ = (
        UniqueConstraint("organization_id", "normalized_receipt_code", name="uq_inbound_receipt_org_code"),
        Index("uq_inbound_receipt_active_unloading", "unloading_operation_id", unique=True, postgresql_where=text(ACTIVE_RECEIPT_SQL), sqlite_where=text(ACTIVE_RECEIPT_SQL)),
        Index("ix_inbound_receipt_org", "organization_id"), Index("ix_inbound_receipt_warehouse", "warehouse_id"),
        Index("ix_inbound_receipt_supplier", "supplier_business_partner_id"), Index("ix_inbound_receipt_status", "status"),
        Index("ix_inbound_receipt_started", "started_at"), Index("ix_inbound_receipt_completed", "completed_at"),
        CheckConstraint("row_version >= 1", name="ck_inbound_receipt_row_version"),
    )
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id = Column(PG_UUID(as_uuid=True), ForeignKey("logistics_organizations.id", ondelete="RESTRICT"), nullable=False)
    branch_id = Column(PG_UUID(as_uuid=True), nullable=False)
    warehouse_id = Column(PG_UUID(as_uuid=True), ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False)
    receipt_code = Column(String(80), nullable=False); normalized_receipt_code = Column(String(80), nullable=False)
    unloading_operation_id = Column(PG_UUID(as_uuid=True), ForeignKey("unloading_operations.id", ondelete="RESTRICT"), nullable=False)
    dock_assignment_id = Column(PG_UUID(as_uuid=True), ForeignKey("inbound_dock_assignments.id", ondelete="RESTRICT"), nullable=False)
    gate_check_in_id = Column(PG_UUID(as_uuid=True), ForeignKey("gate_check_ins.id", ondelete="RESTRICT"), nullable=False)
    appointment_id = Column(PG_UUID(as_uuid=True), nullable=True); arrival_notice_id = Column(PG_UUID(as_uuid=True), nullable=True)
    supplier_business_partner_id = Column(PG_UUID(as_uuid=True), nullable=True)
    supplier_snapshot = Column(JSONB, nullable=False); carrier_snapshot = Column(JSONB, nullable=True)
    status = Column(String(40), nullable=False, default="CREATED"); receipt_type = Column(String(40), nullable=False, default="PURCHASE_ORDER_RECEIPT")
    scan_mode_policy = Column(JSONB, nullable=False, default=dict); active_revision_id = Column(PG_UUID(as_uuid=True), nullable=True)
    current_revision_number = Column(Integer, nullable=False, default=0)
    total_expected_lines = Column(Integer, nullable=False, default=0); total_received_lines = Column(Integer, nullable=False, default=0)
    total_unresolved_scans = Column(Integer, nullable=False, default=0); total_validation_errors = Column(Integer, nullable=False, default=0)
    total_difference_candidates = Column(Integer, nullable=False, default=0)
    started_at = Column(DateTime(timezone=True)); started_by_user_id = Column(PG_UUID(as_uuid=True)); started_by_snapshot = Column(JSONB)
    validation_started_at = Column(DateTime(timezone=True)); completed_at = Column(DateTime(timezone=True)); completed_by_user_id = Column(PG_UUID(as_uuid=True)); completed_by_snapshot = Column(JSONB)
    completion_classification = Column(String(50)); cancelled_at = Column(DateTime(timezone=True)); cancelled_by_user_id = Column(PG_UUID(as_uuid=True)); cancellation_reason = Column(Text)
    content_hash = Column(String(64)); created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now()); updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()); row_version = Column(Integer, nullable=False, server_default=text("1"))


class InboundReceiptRevisionModel(Base):
    __tablename__ = "inbound_receipt_revisions"
    __table_args__ = (UniqueConstraint("inbound_receipt_id", "revision_number", name="uq_inbound_receipt_revision_number"),)
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4); inbound_receipt_id = Column(PG_UUID(as_uuid=True), ForeignKey("inbound_receipts.id", ondelete="RESTRICT"), nullable=False, index=True)
    revision_number = Column(Integer, nullable=False); status = Column(String(30), nullable=False, default="EDITABLE")
    source_snapshot = Column(JSONB, nullable=False); expected_lines_snapshot = Column(JSONB); received_lines_snapshot = Column(JSONB); identifier_capture_snapshot = Column(JSONB); validation_snapshot = Column(JSONB); difference_candidate_snapshot = Column(JSONB); completion_snapshot = Column(JSONB)
    content_hash = Column(String(64)); created_from_revision_id = Column(PG_UUID(as_uuid=True)); change_reason = Column(Text); created_by = Column(PG_UUID(as_uuid=True), nullable=False); created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now()); frozen_at = Column(DateTime(timezone=True))


class InboundReceiptExpectedLineModel(Base):
    __tablename__ = "inbound_receipt_expected_lines"
    __table_args__ = (UniqueConstraint("receipt_revision_id", "purchase_order_line_id", name="uq_inbound_expected_revision_po_line"), Index("ix_inbound_expected_po", "purchase_order_id"), Index("ix_inbound_expected_product", "product_id"))
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4); receipt_revision_id = Column(PG_UUID(as_uuid=True), ForeignKey("inbound_receipt_revisions.id", ondelete="RESTRICT"), nullable=False, index=True)
    purchase_order_id = Column(PG_UUID(as_uuid=True), nullable=False); purchase_order_revision_id = Column(PG_UUID(as_uuid=True)); purchase_order_line_id = Column(PG_UUID(as_uuid=True), nullable=False); arrival_notice_expected_line_id = Column(PG_UUID(as_uuid=True))
    product_id = Column(PG_UUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT"), nullable=True); product_version_id = Column(PG_UUID(as_uuid=True)); line_number = Column(Integer, nullable=False); sku_snapshot = Column(String(120)); product_name_snapshot = Column(String(500), nullable=False)
    ordered_quantity = Column(Numeric(**QTY), nullable=False); ordered_unit_id = Column(PG_UUID(as_uuid=True), ForeignKey("units_of_measure.id", ondelete="RESTRICT"), nullable=False); ordered_base_quantity = Column(Numeric(**QTY), nullable=False)
    shipped_quantity = Column(Numeric(**QTY)); shipped_unit_id = Column(PG_UUID(as_uuid=True)); shipped_base_quantity = Column(Numeric(**QTY)); previously_received_quantity = Column(Numeric(**QTY), nullable=False, default=0); previously_received_base_quantity = Column(Numeric(**QTY), nullable=False, default=0); maximum_receivable_quantity = Column(Numeric(**QTY), nullable=False); maximum_receivable_base_quantity = Column(Numeric(**QTY), nullable=False)
    tracking_policy_snapshot = Column(JSONB, nullable=False, default=dict); packaging_snapshot = Column(JSONB, nullable=False, default=list); status = Column(String(30), nullable=False, default="OPEN"); created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class InboundReceivedLineModel(Base):
    __tablename__ = "inbound_received_lines"
    __table_args__ = (Index("ix_inbound_received_expected", "expected_line_id"), Index("ix_inbound_received_product", "product_id"), Index("ix_inbound_received_validation", "validation_status"), CheckConstraint("received_quantity >= 0 AND received_base_quantity >= 0", name="ck_inbound_received_nonnegative"), CheckConstraint("row_version >= 1", name="ck_inbound_received_row_version"))
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4); receipt_revision_id = Column(PG_UUID(as_uuid=True), ForeignKey("inbound_receipt_revisions.id", ondelete="RESTRICT"), nullable=False); expected_line_id = Column(PG_UUID(as_uuid=True), ForeignKey("inbound_receipt_expected_lines.id", ondelete="RESTRICT")); product_id = Column(PG_UUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT")); product_version_id = Column(PG_UUID(as_uuid=True)); resolution_status = Column(String(40), nullable=False)
    received_quantity = Column(Numeric(**QTY), nullable=False, default=0); received_unit_id = Column(PG_UUID(as_uuid=True), ForeignKey("units_of_measure.id", ondelete="RESTRICT"), nullable=False); received_base_quantity = Column(Numeric(**QTY), nullable=False, default=0); conversion_rule_id = Column(PG_UUID(as_uuid=True)); conversion_factor_snapshot = Column(Numeric(**QTY)); scan_count = Column(Integer, nullable=False, default=0); manual_entry_count = Column(Integer, nullable=False, default=0)
    lot_capture_required = Column(Boolean, nullable=False, default=False); serial_capture_required = Column(Boolean, nullable=False, default=False); expiration_capture_required = Column(Boolean, nullable=False, default=False); lot_capture_complete = Column(Boolean, nullable=False, default=False); serial_capture_complete = Column(Boolean, nullable=False, default=False); expiration_capture_complete = Column(Boolean, nullable=False, default=False)
    validation_status = Column(String(30), nullable=False, default="NOT_VALIDATED"); comparison_status = Column(String(30), nullable=False, default="NOT_COMPARED"); notes = Column(Text); observed_condition = Column(String(40)); created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now()); updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()); row_version = Column(Integer, nullable=False, server_default=text("1"))


class InboundScanSessionModel(Base):
    __tablename__ = "inbound_scan_sessions"
    __table_args__ = (Index("ix_inbound_scan_session_receipt", "inbound_receipt_id"), CheckConstraint("row_version >= 1", name="ck_inbound_scan_session_row_version"))
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4); organization_id = Column(PG_UUID(as_uuid=True), nullable=False); inbound_receipt_id = Column(PG_UUID(as_uuid=True), ForeignKey("inbound_receipts.id", ondelete="RESTRICT"), nullable=False); receipt_revision_id = Column(PG_UUID(as_uuid=True), ForeignKey("inbound_receipt_revisions.id", ondelete="RESTRICT"), nullable=False); warehouse_id = Column(PG_UUID(as_uuid=True), nullable=False); station_id = Column(PG_UUID(as_uuid=True)); device_reference_hash = Column(String(64)); scanner_type = Column(String(40), nullable=False); status = Column(String(30), nullable=False, default="ACTIVE"); operator_user_id = Column(PG_UUID(as_uuid=True), nullable=False); operator_snapshot = Column(JSONB, nullable=False); started_at = Column(DateTime(timezone=True), nullable=False); last_activity_at = Column(DateTime(timezone=True), nullable=False); completed_at = Column(DateTime(timezone=True)); cancelled_at = Column(DateTime(timezone=True)); client_session_reference = Column(String(120)); created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now()); row_version = Column(Integer, nullable=False, server_default=text("1"))


class InboundScanEventModel(Base):
    __tablename__ = "inbound_scan_events"
    __table_args__ = (UniqueConstraint("scan_session_id", "client_scan_id", name="uq_inbound_scan_session_client_scan"), Index("ix_inbound_scan_event_receipt", "inbound_receipt_id"), Index("ix_inbound_scan_event_code_hash", "code_hash"), Index("ix_inbound_scan_event_product", "resolved_product_id"), Index("ix_inbound_scan_event_received", "received_at"), Index("ix_inbound_scan_event_status", "status"))
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4); organization_id = Column(PG_UUID(as_uuid=True), nullable=False); inbound_receipt_id = Column(PG_UUID(as_uuid=True), ForeignKey("inbound_receipts.id", ondelete="RESTRICT"), nullable=False); receipt_revision_id = Column(PG_UUID(as_uuid=True), ForeignKey("inbound_receipt_revisions.id", ondelete="RESTRICT"), nullable=False); scan_session_id = Column(PG_UUID(as_uuid=True), ForeignKey("inbound_scan_sessions.id", ondelete="RESTRICT"), nullable=False); client_scan_id = Column(String(120), nullable=False); client_sequence = Column(Integer); server_sequence = Column(Integer, nullable=False)
    raw_code_encrypted = Column(Text); normalized_code = Column(String(512), nullable=False); code_hash = Column(String(64), nullable=False); symbology = Column(String(40), nullable=False); parser_code = Column(String(60), nullable=False); parser_version = Column(String(20), nullable=False); parse_status = Column(String(30), nullable=False); parsed_elements = Column(JSONB, nullable=False); resolution_status = Column(String(40), nullable=False); resolved_product_id = Column(PG_UUID(as_uuid=True)); resolved_product_version_id = Column(PG_UUID(as_uuid=True)); resolved_expected_line_id = Column(PG_UUID(as_uuid=True)); requested_quantity = Column(Numeric(**QTY), nullable=False); requested_unit_id = Column(PG_UUID(as_uuid=True)); accepted_quantity = Column(Numeric(**QTY), nullable=False, default=0); accepted_unit_id = Column(PG_UUID(as_uuid=True)); accepted_base_quantity = Column(Numeric(**QTY), nullable=False, default=0); scan_source = Column(String(40), nullable=False); client_captured_at = Column(DateTime(timezone=True)); received_at = Column(DateTime(timezone=True), nullable=False); processed_at = Column(DateTime(timezone=True), nullable=False); operator_user_id = Column(PG_UUID(as_uuid=True), nullable=False); validation_summary = Column(JSONB, nullable=False, default=dict); duplicate_of_event_id = Column(PG_UUID(as_uuid=True)); status = Column(String(30), nullable=False); created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class InboundScanCompensationEventModel(Base):
    __tablename__ = "inbound_scan_compensation_events"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4); original_scan_event_id = Column(PG_UUID(as_uuid=True), ForeignKey("inbound_scan_events.id", ondelete="RESTRICT"), nullable=False, unique=True); inbound_receipt_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True); reason_code = Column(String(40), nullable=False); reason = Column(Text, nullable=False); compensated_quantity = Column(Numeric(**QTY), nullable=False); unit_id = Column(PG_UUID(as_uuid=True), nullable=False); base_quantity = Column(Numeric(**QTY), nullable=False); requested_by = Column(PG_UUID(as_uuid=True), nullable=False); approved_by = Column(PG_UUID(as_uuid=True)); created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now()); status = Column(String(30), nullable=False, default="APPLIED")


class UnresolvedInboundScanModel(Base):
    __tablename__ = "unresolved_inbound_scans"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4); inbound_receipt_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True); scan_event_id = Column(PG_UUID(as_uuid=True), ForeignKey("inbound_scan_events.id", ondelete="RESTRICT"), nullable=False, unique=True); code_hash = Column(String(64), nullable=False); encrypted_code = Column(Text); candidate_product_ids = Column(JSONB, nullable=False, default=list); status = Column(String(30), nullable=False, default="OPEN"); resolution_type = Column(String(40)); resolved_product_id = Column(PG_UUID(as_uuid=True)); resolved_expected_line_id = Column(PG_UUID(as_uuid=True)); reason = Column(Text); resolved_by = Column(PG_UUID(as_uuid=True)); resolved_at = Column(DateTime(timezone=True)); created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class InboundLotObservationModel(Base):
    __tablename__ = "inbound_lot_observations"
    __table_args__ = (Index("ix_inbound_lot_product", "product_id"), Index("ix_inbound_lot_hash", "lot_hash"), Index("ix_inbound_lot_expiration", "expiration_date"), CheckConstraint("quantity > 0 AND base_quantity > 0", name="ck_inbound_lot_quantity_positive"))
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4); inbound_receipt_id = Column(PG_UUID(as_uuid=True), nullable=False); receipt_revision_id = Column(PG_UUID(as_uuid=True), nullable=False); received_line_id = Column(PG_UUID(as_uuid=True), ForeignKey("inbound_received_lines.id", ondelete="RESTRICT"), nullable=False); expected_line_id = Column(PG_UUID(as_uuid=True)); product_id = Column(PG_UUID(as_uuid=True), nullable=False); lot_value = Column(String(160), nullable=False); normalized_lot_value = Column(String(160), nullable=False); lot_hash = Column(String(64), nullable=False); supplier_lot_reference = Column(String(160)); manufacturer_lot_reference = Column(String(160)); quantity = Column(Numeric(**QTY), nullable=False); unit_id = Column(PG_UUID(as_uuid=True), nullable=False); base_quantity = Column(Numeric(**QTY), nullable=False); manufacturing_date = Column(Date); expiration_date = Column(Date); source = Column(String(40), nullable=False); validation_status = Column(String(40), nullable=False); captured_by = Column(PG_UUID(as_uuid=True), nullable=False); captured_at = Column(DateTime(timezone=True), nullable=False); created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class InboundSerialObservationModel(Base):
    __tablename__ = "inbound_serial_observations"
    __table_args__ = (Index("ix_inbound_serial_product", "product_id"), Index("ix_inbound_serial_hash", "serial_hash"), Index("ix_inbound_serial_duplicate", "duplicate_status"), Index("uq_inbound_serial_active_receipt", "inbound_receipt_id", "serial_hash", unique=True, postgresql_where=text("validation_status <> 'INVALIDATED'"), sqlite_where=text("validation_status <> 'INVALIDATED'")))
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4); inbound_receipt_id = Column(PG_UUID(as_uuid=True), nullable=False); receipt_revision_id = Column(PG_UUID(as_uuid=True), nullable=False); received_line_id = Column(PG_UUID(as_uuid=True), ForeignKey("inbound_received_lines.id", ondelete="RESTRICT"), nullable=False); expected_line_id = Column(PG_UUID(as_uuid=True)); product_id = Column(PG_UUID(as_uuid=True), nullable=False); serial_value_encrypted = Column(Text); normalized_serial_value = Column(String(200), nullable=False); serial_hash = Column(String(64), nullable=False); source = Column(String(40), nullable=False); validation_status = Column(String(40), nullable=False); duplicate_status = Column(String(50), nullable=False); captured_by = Column(PG_UUID(as_uuid=True), nullable=False); captured_at = Column(DateTime(timezone=True), nullable=False); scan_event_id = Column(PG_UUID(as_uuid=True)); created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class InboundExpirationObservationModel(Base):
    __tablename__ = "inbound_expiration_observations"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4); inbound_receipt_id = Column(PG_UUID(as_uuid=True), nullable=False); received_line_id = Column(PG_UUID(as_uuid=True), nullable=False); lot_observation_id = Column(PG_UUID(as_uuid=True)); product_id = Column(PG_UUID(as_uuid=True), nullable=False); manufacturing_date = Column(Date); expiration_date = Column(Date, nullable=False); source = Column(String(40), nullable=False); validation_status = Column(String(50), nullable=False); policy_snapshot = Column(JSONB, nullable=False); captured_by = Column(PG_UUID(as_uuid=True), nullable=False); captured_at = Column(DateTime(timezone=True), nullable=False); created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class InboundReceiptPauseModel(Base):
    __tablename__ = "inbound_receipt_pauses"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4); inbound_receipt_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True); reason_code = Column(String(40), nullable=False); reason = Column(Text, nullable=False); started_at = Column(DateTime(timezone=True), nullable=False); started_by = Column(PG_UUID(as_uuid=True), nullable=False); ended_at = Column(DateTime(timezone=True)); ended_by = Column(PG_UUID(as_uuid=True)); status = Column(String(30), nullable=False, default="ACTIVE"); created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ReceivingValidationResultModel(Base):
    __tablename__ = "receiving_validation_results"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4); inbound_receipt_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True); receipt_revision_id = Column(PG_UUID(as_uuid=True), nullable=False); validation_status = Column(String(40), nullable=False); result = Column(JSONB, nullable=False); validation_hash = Column(String(64), nullable=False); validated_by = Column(PG_UUID(as_uuid=True), nullable=False); created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ReceptionDifferenceCandidateModel(Base):
    __tablename__ = "reception_difference_candidates"
    __table_args__ = (Index("ix_reception_difference_receipt", "inbound_receipt_id"), Index("ix_reception_difference_type", "candidate_type"), Index("ix_reception_difference_status", "status"))
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4); organization_id = Column(PG_UUID(as_uuid=True), nullable=False); inbound_receipt_id = Column(PG_UUID(as_uuid=True), nullable=False); receipt_revision_id = Column(PG_UUID(as_uuid=True), nullable=False); expected_line_id = Column(PG_UUID(as_uuid=True)); received_line_id = Column(PG_UUID(as_uuid=True)); candidate_type = Column(String(60), nullable=False); severity = Column(String(20), nullable=False); expected_value = Column(JSONB); observed_value = Column(JSONB); variance_quantity = Column(Numeric(**QTY)); unit_id = Column(PG_UUID(as_uuid=True)); source_event_id = Column(PG_UUID(as_uuid=True)); evidence_file_ids = Column(JSONB, nullable=False, default=list); status = Column(String(40), nullable=False, default="OPEN"); detected_at = Column(DateTime(timezone=True), nullable=False); detected_by_service = Column(String(120), nullable=False); acknowledged_by = Column(PG_UUID(as_uuid=True)); acknowledged_at = Column(DateTime(timezone=True)); formal_difference_id = Column(PG_UUID(as_uuid=True)); dismissal_reason = Column(Text); created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class InboundReceiptProgressProjectionModel(Base):
    __tablename__ = "inbound_receipt_progress_projection"
    receipt_id = Column(PG_UUID(as_uuid=True), ForeignKey("inbound_receipts.id", ondelete="CASCADE"), primary_key=True); expected_line_count = Column(Integer, nullable=False, default=0); started_line_count = Column(Integer, nullable=False, default=0); completed_line_count = Column(Integer, nullable=False, default=0); ordered_base_total = Column(Numeric(**QTY), nullable=False, default=0); shipped_base_total = Column(Numeric(**QTY)); received_base_total = Column(Numeric(**QTY), nullable=False, default=0); unresolved_scan_count = Column(Integer, nullable=False, default=0); validation_error_count = Column(Integer, nullable=False, default=0); warning_count = Column(Integer, nullable=False, default=0); difference_candidate_count = Column(Integer, nullable=False, default=0); scan_event_count = Column(Integer, nullable=False, default=0); compensated_scan_count = Column(Integer, nullable=False, default=0); progress_percentage = Column(Numeric(7, 4), nullable=False, default=0); data_quality_status = Column(String(30), nullable=False, default="PARTIAL"); calculated_at = Column(DateTime(timezone=True), nullable=False); projection_version = Column(Integer, nullable=False, default=1)


class PurchaseOrderReceiptProgressModel(Base):
    __tablename__ = "purchase_order_receipt_progress"
    __table_args__ = (UniqueConstraint("organization_id", "purchase_order_line_id", name="uq_po_receipt_progress_line"),)
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4); organization_id = Column(PG_UUID(as_uuid=True), nullable=False); purchase_order_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True); purchase_order_line_id = Column(PG_UUID(as_uuid=True), nullable=False); ordered_quantity = Column(Numeric(**QTY), nullable=False); cumulative_received_quantity = Column(Numeric(**QTY), nullable=False, default=0); remaining_quantity = Column(Numeric(**QTY), nullable=False); receipt_count = Column(Integer, nullable=False, default=0); last_receipt_at = Column(DateTime(timezone=True)); fulfillment_status = Column(String(50), nullable=False, default="NOT_RECEIVED"); pending_difference_review = Column(Boolean, nullable=False, default=False); quality_status_future = Column(String(40), nullable=False, default="FUTURE_QUALITY_PENDING"); inventory_posting_status_future = Column(String(40), nullable=False, default="FUTURE_INVENTORY_PENDING")


class InboundReceiptExportJobModel(Base):
    __tablename__ = "inbound_receipt_export_jobs"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4); organization_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True); requested_by = Column(PG_UUID(as_uuid=True), nullable=False); filters = Column(JSONB, nullable=False); format = Column(String(20), nullable=False); status = Column(String(30), nullable=False, default="PENDING"); file_asset_id = Column(PG_UUID(as_uuid=True)); error_code = Column(String(80)); created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now()); completed_at = Column(DateTime(timezone=True))


class InboundReceiptPolicyModel(Base):
    __tablename__ = "inbound_receipt_policies"
    __table_args__ = (UniqueConstraint("organization_id", "warehouse_id", "version", name="uq_inbound_receipt_policy_version"),)
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4); organization_id = Column(PG_UUID(as_uuid=True), nullable=False); warehouse_id = Column(PG_UUID(as_uuid=True)); partial_receipt_allowed = Column(Boolean, nullable=False, default=True); over_receipt_allowed = Column(Boolean, nullable=False, default=False); over_receipt_tolerance_type = Column(String(40), nullable=False, default="NONE"); over_receipt_tolerance_value = Column(Numeric(**QTY)); under_receipt_allowed = Column(Boolean, nullable=False, default=True); unexpected_product_allowed = Column(Boolean, nullable=False, default=False); manual_entry_allowed = Column(Boolean, nullable=False, default=False); multiple_scan_sessions_allowed = Column(Boolean, nullable=False, default=True); blind_count = Column(Boolean, nullable=False, default=False); completion_with_difference_candidates_allowed = Column(Boolean, nullable=False, default=False); serial_duplicate_policy = Column(String(40), nullable=False, default="BLOCK"); expired_product_policy = Column(String(40), nullable=False, default="BLOCK"); minimum_shelf_life_policy = Column(JSONB, nullable=False, default=dict); document_requirement_policy = Column(JSONB, nullable=False, default=dict); evidence_requirement_policy = Column(JSONB, nullable=False, default=dict); version = Column(Integer, nullable=False); effective_from = Column(DateTime(timezone=True), nullable=False); effective_to = Column(DateTime(timezone=True))


PHASE_039_TABLES = (
    "inbound_receipts", "inbound_receipt_revisions", "inbound_receipt_expected_lines", "inbound_received_lines",
    "inbound_scan_sessions", "inbound_scan_events", "inbound_scan_compensation_events", "unresolved_inbound_scans",
    "inbound_lot_observations", "inbound_serial_observations", "inbound_expiration_observations", "inbound_receipt_pauses",
    "receiving_validation_results", "reception_difference_candidates", "inbound_receipt_progress_projection",
    "purchase_order_receipt_progress", "inbound_receipt_export_jobs", "inbound_receipt_policies",
)
