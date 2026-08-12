// ── Fase 040 — Tipos de diferencias de recepción ───────────────────────────────

// ── Primitivos reutilizados ─────────────────────────────────────────────────────

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  has_next: boolean
  has_previous: boolean
  cursor?: string | null
}

export interface DecimalValue {
  value: string
  scale: number
}

export interface UserSummary {
  user_id: string
  display_name: string
  email?: string
}

export interface FileAssetSummary {
  file_id: string
  filename: string
  mime_type: string
  size_bytes: number
  upload_session_id?: string
  url?: string
}

export interface ApiError {
  code: string
  message: string
  details?: Record<string, unknown>
  status?: number
}

// ── Resúmenes de dominio ────────────────────────────────────────────────────────

export interface InboundReceiptSummary {
  receipt_id: string
  code: string
  cpv_code: string | null
  cit_code: string | null
  supplier_name: string
  warehouse_name: string
  status: string
  completion_classification: string | null
}

export type ReceptionDifferenceCandidateType =
  | 'SHORTAGE'
  | 'OVERAGE'
  | 'DAMAGE'
  | 'WRONG_PRODUCT'
  | 'MISSING_DOCUMENT'
  | 'BROKEN_SEAL'
  | 'OTHER'

export interface ReceptionDifferenceCandidate {
  candidate_id: string
  receipt_id: string
  type: ReceptionDifferenceCandidateType
  line_id: string | null
  product: ProductSummary | null
  expected_quantity: string | null
  observed_quantity: string | null
  unit: UnitOfMeasureSummary | null
  severity: ReceptionDifferenceSeverity
  evidence: FileAssetSummary[]
  status: string
  created_at: string
  updated_at: string
}

export interface PurchaseOrderSummary {
  purchase_order_id: string
  code: string
  supplier_name: string
  status: string
}

export interface ProductSummary {
  product_id: string
  sku: string
  name: string
  description?: string
  barcode?: string
  category?: string
}

export interface ProductTrackingPolicySummary {
  requires_lot: boolean
  requires_serial: boolean
  requires_expiration: boolean
  serial_uniqueness: 'GLOBAL' | 'PRODUCT' | 'INCONCLUSIVE'
  lot_format?: string
  serial_format?: string
}

export interface ProductPackagingSummary {
  packaging_id: string
  code: string
  name: string
  quantity: string
  unit_code: string
  factor: string
  version: number
}

export interface UnitOfMeasureSummary {
  unit_id: string
  code: string
  name: string
  symbol: string
  unit_type: string
}

export interface BusinessPartnerSummary {
  partner_id: string
  name: string
  trade_name?: string
  document_type: string
  document_number: string
  roles: string[]
}

export interface WarehouseSummary {
  warehouse_id: string
  name: string
  code: string
}

// ── Caso de diferencia ──────────────────────────────────────────────────────────

export type ReceptionDifferenceCaseStatus =
  | 'DRAFT'
  | 'EVIDENCE_PENDING'
  | 'RESPONSIBILITY_PENDING'
  | 'IN_REVIEW'
  | 'CHANGES_REQUESTED'
  | 'PENDING_APPROVAL'
  | 'ISSUED'
  | 'ACKNOWLEDGED'
  | 'DISPUTED'
  | 'FOLLOW_UP'
  | 'CLOSED'
  | 'CANCELLED'

export type ReceptionDifferenceSeverity =
  | 'LOW'
  | 'MEDIUM'
  | 'HIGH'
  | 'CRITICAL'

export type ReceptionDifferenceType =
  | 'SHORTAGE'
  | 'OVERAGE'
  | 'DAMAGE'
  | 'WRONG_PRODUCT'
  | 'MISSING_DOCUMENT'
  | 'BROKEN_SEAL'
  | 'OTHER'

export type ReceptionDifferenceCategory =
  | 'QUANTITY'
  | 'QUALITY'
  | 'DOCUMENTATION'
  | 'SECURITY'
  | 'PACKAGING'
  | 'OTHER'

export interface ReceptionDifferenceCase {
  case_id: string
  case_code: string | null
  receipt_id: string
  receipt_code: string
  cpv_code: string | null
  cit_code: string | null
  purchase_order_codes: string[]
  supplier_id: string
  supplier_name: string
  carrier_name: string | null
  warehouse_id: string
  warehouse_name: string
  status: ReceptionDifferenceCaseStatus
  severity: ReceptionDifferenceSeverity
  items_count: number
  critical_items_count: number
  evidence_count: number
  primary_responsible: ResponsiblePartySummary | null
  responsibility_status: ResponsibilityStatus | null
  has_disputes: boolean
  issued_at: string | null
  created_at: string
  updated_at: string
  created_by: UserSummary
}

export interface ReceptionDifferenceCaseSummary {
  open_cases: number
  critical_differences: number
  shortages: number
  overages: number
  damages: number
  wrong_products: number
  missing_documents: number
  observed_seals: number
  pending_evidence: number
  pending_responsibility: number
  disputed_cases: number
  pending_documents: number
}

export interface ReceptionDifferenceCaseDetail extends ReceptionDifferenceCase {
  items: ReceptionDifferenceItem[]
  purchase_orders: PurchaseOrderSummary[]
  warnings: string[]
  blocking_issues: string[]
  receiving_code?: string
  supplier?: { name?: string; id?: string }
  carrier?: { name?: string; id?: string }
  current_status_display?: string
  summary?: string
  evidence?: ReceptionDifferenceEvidence[]
  responsibility?: {
    proposed_parties?: ReceptionDifferenceResponsibleParty[]
  } | ResponsiblePartySummary[]
  documents?: {
    issued_documents?: ReceptionDifferenceDocument[]
    pending_documents?: ReceptionDifferenceDocument[]
  } | ReceptionDifferenceDocument[]
  history?: {
    history_id?: string
    event_display?: string
    event_description?: string
    actor_display_name?: string
    created_at?: string
  }[]
  future_preparation?: {
    quarantine_recommendations?: FutureQuarantineRecommendation[]
    claim_preparation?: FutureClaimPreparation
    quality_inspection_preparation?: QualityInspectionPreparation
  }
  reviews?: {
    reviews?: any[]
    approvals?: any[]
    acknowledgements?: any[]
    review_notes?: string
    reviewed_at?: string
    reviewer?: UserSummary
  }
  integrity_status?: string
  content_hash?: string
  integrity_checked_at?: string
  total_versions?: number
}

export interface ReceptionDifferenceCaseCapabilities {
  case_id: string
  can_view: boolean
  can_create: boolean
  can_update: boolean
  can_formalize_candidates: boolean
  can_create_manual_item: boolean
  can_upload_evidence: boolean
  can_view_sensitive_evidence: boolean
  can_propose_responsibility: boolean
  can_review_responsibility: boolean
  can_acknowledge_responsibility: boolean
  can_dispute_responsibility: boolean
  can_submit: boolean
  can_review: boolean
  can_request_changes: boolean
  can_mark_ready_for_approval: boolean
  can_approve: boolean
  can_preview_DIF: boolean
  can_issue_DIF: boolean
  can_download_DIF: boolean
  can_reprint_DIF: boolean
  can_cancel_DIF: boolean
  can_download_package: boolean
  can_close: boolean
  can_view_history: boolean
  can_view_integrity: boolean
  can_view_quality_preparation: boolean
  can_view_quarantine_recommendations: boolean
  can_view_claim_preparation: boolean
}

// ── Ítems de diferencia ─────────────────────────────────────────────────────────

export type ReceptionDifferenceItemStatus =
  | 'DRAFT'
  | 'PENDING_REVIEW'
  | 'UNDER_REVIEW'
  | 'CHANGES_REQUESTED'
  | 'APPROVED'
  | 'DISMISSED'
  | 'SUPERSEDED'

export type ResponsibilityStatus =
  | 'NONE'
  | 'PROPOSED'
  | 'REVIEWED'
  | 'ACKNOWLEDGED'
  | 'DISPUTED'
  | 'UNDETERMINED'

export interface ReceptionDifferenceItem {
  item_id: string
  case_id: string
  item_number: number
  type: ReceptionDifferenceType
  category: ReceptionDifferenceCategory
  severity: ReceptionDifferenceSeverity
  difficulty_level?: ReceptionDifferenceSeverity
  product: ProductSummary
  expected_quantity: string
  observed_quantity: string
  difference_quantity: string
  unit: UnitOfMeasureSummary
  description: string | null
  damage_detail: ReceptionDamageDetail | null
  document_detail: ReceptionDocumentDetail | null
  seal_detail: ReceptionSealDetail | null
  evidence: FileAssetSummary[]
  responsible_party: ResponsiblePartySummary | null
  responsibility_status: ResponsibilityStatus
  follow_up_recommendation: string | null
  status: ReceptionDifferenceItemStatus
  source_candidate_id: string | null
  is_manual: boolean
  created_at: string
  updated_at: string
}

export interface ReceptionDamageDetail {
  damage_scope: string | null
  damage_type: string | null
  affected_quantity: string
  functional_impact: string | null
  safety_risk: boolean
  possible_contamination: boolean
  temperature_concern: boolean
}

export interface ReceptionDocumentDetail {
  document_type: string | null
  requirement_source: string | null
  expected_document: string | null
  presentation_status: string | null
  upload_status: string | null
  comparison_status: string | null
  issuer: string | null
  reference: string | null
}

export interface ReceptionSealDetail {
  expected_seal_redacted: string | null
  observed_seal_redacted: string | null
  gate_status: string | null
  opening_status: string | null
  opening_time: string | null
  guard_name: string | null
  supervisor_name: string | null
}

// ── Evidencias ──────────────────────────────────────────────────────────────────

export type ReceptionDifferenceEvidenceType =
  | 'PRODUCT'
  | 'DAMAGE'
  | 'PACKAGING'
  | 'LABEL'
  | 'COUNT'
  | 'DOCUMENT'
  | 'SEAL'
  | 'VEHICLE'
  | 'OTHER'

export interface ReceptionDifferenceEvidence {
  evidence_id: string
  case_id: string
  item_id: string | null
  evidence_type: ReceptionDifferenceEvidenceType
  file: FileAssetSummary
  classification: string | null
  partial_hash: string | null
  anti_malware_status: string | null
  created_at: string
  created_by: UserSummary
}

// ── Responsables ────────────────────────────────────────────────────────────────

export type ReceptionDifferencePartyType =
  | 'SUPPLIER'
  | 'CARRIER'
  | 'INTERNAL_RECEPTION'
  | 'GATE'
  | 'DOCK'
  | 'PURCHASING'
  | 'CONTRACTOR'
  | 'SHARED'
  | 'UNDETERMINED'
  | 'OTHER'

export type ReceptionDifferenceResponsibilityRole =
  | 'PRIMARY'
  | 'SECONDARY'
  | 'SHARED'

export interface ResponsiblePartySummary {
  responsibility_id: string
  party_type: ReceptionDifferencePartyType
  party_name: string
  role: ReceptionDifferenceResponsibilityRole
  percentage: string | null
  status: ResponsibilityStatus
}

export interface ReceptionDifferenceResponsibleParty {
  responsibility_id: string
  case_id: string
  item_id: string | null
  party_type: ReceptionDifferencePartyType
  business_partner_id: string | null
  user_id: string | null
  party_name: string
  role: ReceptionDifferenceResponsibilityRole
  percentage: string | null
  rationale: string | null
  evidence: FileAssetSummary[]
  status: ResponsibilityStatus
  proposed_by: UserSummary
  reviewed_by: UserSummary | null
  acknowledged_at: string | null
  disputed_at: string | null
  dispute_reason: string | null
  created_at: string
  updated_at: string
}

// ── Revisiones ──────────────────────────────────────────────────────────────────

export type ReceptionDifferenceReviewStatus =
  | 'PENDING'
  | 'IN_PROGRESS'
  | 'COMPLETED'
  | 'CHANGES_REQUESTED'
  | 'REJECTED'

export interface ReceptionDifferenceReview {
  review_id: string
  case_id: string
  status: ReceptionDifferenceReviewStatus
  reviewer: UserSummary
  changes_requested: string | null
  items_affected: string[] | null
  evidence_missing: string[] | null
  responsible_missing: boolean | null
  started_at: string | null
  completed_at: string | null
  created_at: string
}

// ── Aprobaciones ────────────────────────────────────────────────────────────────

export type ReceptionDifferenceApprovalStatus =
  | 'PENDING'
  | 'APPROVED'
  | 'CHANGES_REQUESTED'
  | 'REVIEW_REQUIRED'
  | 'REJECTED'

export interface ReceptionDifferenceApproval {
  approval_id: string
  case_id: string
  review_id: string | null
  status: ReceptionDifferenceApprovalStatus
  decision_by: UserSummary
  comments: string | null
  created_at: string
}

// ── Reconocimientos ─────────────────────────────────────────────────────────────

export type ReceptionDifferenceAcknowledgementType =
  | 'COPY_RECEIVED'
  | 'FACTS_ACKNOWLEDGED'
  | 'RESPONSIBILITY_ACKNOWLEDGED'

export interface ReceptionDifferenceAcknowledgement {
  acknowledgement_id: string
  case_id: string
  acknowledgement_type: ReceptionDifferenceAcknowledgementType
  acknowledged_by: UserSummary
  party_type: ReceptionDifferencePartyType
  party_name: string
  comment: string | null
  created_at: string
}

// ── Documento DIF ───────────────────────────────────────────────────────────────

export type ReceptionDifferenceDocumentStatus =
  | 'NOT_ISSUED'
  | 'PREVIEW'
  | 'ISSUED'
  | 'CANCELLED'
  | 'SUPERSEDED'

export interface ReceptionDifferenceDocument {
  document_id: string
  case_id: string
  case_code: string
  status: ReceptionDifferenceDocumentStatus
  issued_at: string | null
  issued_by: UserSummary | null
  cancelled_at: string | null
  cancelled_by: UserSummary | null
  cancellation_reason: string | null
  pdf_url: string | null
  pdf_hash: string | null
  integrity_hash: string | null
  reprint_count: number
  last_reprint_at: string | null
  created_at: string
}

export interface ReceptionDifferencePackage {
  package_id: string
  case_id: string
  document_id: string | null
  status: 'PENDING' | 'PROCESSING' | 'READY' | 'EXPIRED' | 'FAILED'
  package_url: string | null
  size_bytes: number | null
  expires_at: string | null
  created_at: string
}

// ── Historial ───────────────────────────────────────────────────────────────────

export type ReceptionDifferenceEventType =
  | 'CASE_CREATED'
  | 'CANDIDATE_FORMALIZED'
  | 'MANUAL_ITEM_CREATED'
  | 'EVIDENCE_ADDED'
  | 'PHOTO_ADDED'
  | 'RESPONSIBLE_PROPOSED'
  | 'RESPONSIBLE_REVIEWED'
  | 'CASE_SUBMITTED'
  | 'REVIEW_STARTED'
  | 'CHANGES_REQUESTED'
  | 'CASE_READY'
  | 'CASE_APPROVED'
  | 'DIF_ISSUED'
  | 'COPY_DOWNLOADED'
  | 'COPY_ACKNOWLEDGED'
  | 'FACTS_ACKNOWLEDGED'
  | 'RESPONSIBILITY_ACKNOWLEDGED'
  | 'FACTS_DISPUTED'
  | 'RESPONSIBILITY_DISPUTED'
  | 'FOLLOW_UP_REQUIRED'
  | 'DOCUMENT_CANCELLED'
  | 'CASE_CLOSED'
  | 'INTEGRITY_FAILED'

export interface ReceptionDifferenceHistoryEvent {
  event_id: string
  case_id: string
  event_type: ReceptionDifferenceEventType
  timestamp: string
  actor: UserSummary
  action: string
  item_id: string | null
  previous_status: string | null
  new_status: string | null
  reason: string | null
  result: string | null
}

// ── Integridad ──────────────────────────────────────────────────────────────────

export interface ReceptionDifferenceIntegrity {
  case_id: string
  source_hash: string | null
  items_hash: string | null
  evidence_hash: string | null
  responsibilities_hash: string | null
  review_hash: string | null
  approval_hash: string | null
  acknowledgement_hash: string | null
  snapshot_hash: string | null
  pdf_hash: string | null
  algorithm: string
  last_verified_at: string | null
  status: 'VALID' | 'INVALID' | 'PENDING' | 'NOT_VERIFIED'
}

// ── Validación ──────────────────────────────────────────────────────────────────

export interface ReceptionDifferenceValidation {
  case_id: string
  receipt_valid: boolean
  items_valid: boolean
  types_valid: boolean
  quantities_valid: boolean
  units_valid: boolean
  evidence_sufficient: boolean
  photos_sufficient: boolean
  responsibilities_assigned: boolean
  reviews_complete: boolean
  approvals_complete: boolean
  duplicates_found: boolean
  files_unavailable: string[]
  errors: string[]
  warnings: string[]
  ready_for_issuance: boolean
}

// ── Preparación futura ──────────────────────────────────────────────────────────

export interface QualityInspectionPreparation {
  case_id: string
  products: {
    product: ProductSummary
    category: string
    quantity: string
    unit: UnitOfMeasureSummary
    damage_description: string | null
    expiration_date: string | null
    temperature_concern: boolean
    certificates_required: string[]
    recommended_controls: string[]
  }[]
  overall_severity: ReceptionDifferenceSeverity
  evidence_count: number
}

export interface FutureQuarantineRecommendation {
  recommendation_id: string
  case_id: string
  item_id: string
  product: ProductSummary
  quantity: string
  unit: UnitOfMeasureSummary
  reason: string
  severity: ReceptionDifferenceSeverity
  evidence: FileAssetSummary[]
  recommendation: string
  created_at: string
}

export interface FutureClaimPreparation {
  case_id: string
  supplier: BusinessPartnerSummary | null
  carrier: BusinessPartnerSummary | null
  responsible_parties: ResponsiblePartySummary[]
  differences: {
    item_id: string
    type: ReceptionDifferenceType
    quantity: string
    unit: UnitOfMeasureSummary
  }[]
  evidence_count: number
  acknowledgements: ReceptionDifferenceAcknowledgement[]
  disputes: ReceptionDifferenceAcknowledgement[]
  document: ReceptionDifferenceDocument | null
  integrity_hash: string | null
}

// ── Request/Query types ─────────────────────────────────────────────────────────

export interface ReceptionDifferenceCaseQuery {
  page?: number
  page_size?: number
  cursor?: string
  status?: ReceptionDifferenceCaseStatus | ReceptionDifferenceCaseStatus[]
  severity?: ReceptionDifferenceSeverity | ReceptionDifferenceSeverity[]
  type?: ReceptionDifferenceType | ReceptionDifferenceType[]
  category?: ReceptionDifferenceCategory | ReceptionDifferenceCategory[]
  warehouse_id?: string
  supplier_id?: string
  carrier_id?: string
  product_id?: string
  responsible_id?: string
  responsibility_status?: ResponsibilityStatus
  has_photos?: boolean
  has_pending_evidence?: boolean
  has_disputes?: boolean
  is_critical?: boolean
  requires_quality?: boolean
  recommends_quarantine?: boolean
  recommends_claim?: boolean
  date_from?: string
  date_to?: string
  search?: string
  my_cases?: boolean
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface CreateReceptionDifferenceCaseRequest {
  receipt_id: string
  candidate_ids?: string[]
  severity?: ReceptionDifferenceSeverity
  summary?: string
  items?: CreateManualDifferenceItemRequest[]
}

export interface CreateManualDifferenceItemRequest {
  type?: ReceptionDifferenceType
  category?: ReceptionDifferenceCategory
  difference_types?: string[]
  severity?: ReceptionDifferenceSeverity
  purchase_order_line_id?: string
  product_id: string
  expected_quantity?: string
  observed_quantity: string
  unit_id: string
  description?: string
  damage_detail?: Partial<ReceptionDamageDetail>
  document_detail?: Partial<ReceptionDocumentDetail>
  seal_detail?: Partial<ReceptionSealDetail>
}

export interface UpdateReceptionDifferenceCaseRequest {
  severity?: ReceptionDifferenceSeverity
}

export interface UpdateReceptionDifferenceItemRequest {
  type?: ReceptionDifferenceType
  category?: ReceptionDifferenceCategory
  severity?: ReceptionDifferenceSeverity
  description?: string
  damage_detail?: Partial<ReceptionDamageDetail>
  document_detail?: Partial<ReceptionDocumentDetail>
  seal_detail?: Partial<ReceptionSealDetail>
}

export interface FormalizeCandidatesRequest {
  candidate_ids: string[]
}

export interface CreateResponsiblePartyRequest {
  item_id?: string
  party_type: ReceptionDifferencePartyType
  business_partner_id?: string
  user_id?: string
  role: ReceptionDifferenceResponsibilityRole
  percentage?: string
  rationale?: string
  evidence_file_ids?: string[]
}

export interface UpdateResponsiblePartyRequest {
  role?: ReceptionDifferenceResponsibilityRole
  percentage?: string
  rationale?: string
  evidence_file_ids?: string[]
}

export interface ReviewResponsibilityRequest {
  approved: boolean
  comments?: string
}

export interface AcknowledgeResponsibilityRequest {
  acknowledgement_type: ReceptionDifferenceAcknowledgementType
  party_type: ReceptionDifferencePartyType
  comment?: string
}

export interface DisputeResponsibilityRequest {
  dispute_type: 'FACTS' | 'RESPONSIBILITY'
  reason: string
  items_affected?: string[]
  comment?: string
  evidence_file_ids?: string[]
}

export interface SubmitCaseRequest {
  confirmation: boolean
}

export interface RequestChangesRequest {
  reason: string
  sections?: string[]
  items_affected?: string[]
  evidence_missing?: string[]
  responsible_missing?: boolean
}

export interface ApproveCaseRequest {
  decision: 'APPROVE' | 'REQUEST_CHANGES' | 'REVIEW_REQUIRED' | 'REJECT'
  comments?: string
}

export interface IssueDocumentRequest {
  confirmation: boolean
}

export interface CancelDocumentRequest {
  reason: string
  evidence_file_ids?: string[]
}

export interface ReprintDocumentRequest {
  reason: string
  copies?: number
  destination?: string
}

export interface DismissItemRequest {
  reason: string
  evidence_file_ids?: string[]
}

export interface SupersedeItemRequest {
  replacement_type: ReceptionDifferenceType
  description?: string
  evidence_file_ids?: string[]
}

export interface LinkEvidenceToItemRequest {
  file_id: string
  evidence_type: ReceptionDifferenceEvidenceType
  classification?: string
}

export interface LinkEvidenceToCaseRequest {
  file_id: string
  item_id?: string
  evidence_type: ReceptionDifferenceEvidenceType
  classification?: string
}

export interface CreatePhotoUploadSessionRequest {
  filename: string
  mime_type: string
  size_bytes: number
  item_id?: string
  evidence_type: ReceptionDifferenceEvidenceType
}

export interface CreateAcknowledgementRequest {
  acknowledgement_type: ReceptionDifferenceAcknowledgementType
  party_type: ReceptionDifferencePartyType
  party_name: string
  comment?: string
}

export interface AcknowledgeCopyRequest {
  comment?: string
}

export interface AcknowledgeFactsRequest {
  comment?: string
}

export interface AcknowledgeResponsibilityAckRequest {
  comment?: string
}

export interface DisputeFactsRequest {
  reason: string
  evidence_file_ids?: string[]
}

export interface DisputeResponsibilityAckRequest {
  reason: string
  evidence_file_ids?: string[]
}

export interface AcknowledgeCandidateRequest {
  comment?: string
}

export interface DismissCandidateRequest {
  reason: string
}

export interface PrepareForPhase040Request {
  evidence_file_ids?: string[]
}

// ── Descarga elegible ───────────────────────────────────────────────────────────

export interface EligibleReceiptForDifference {
  receipt_id: string
  code: string
  cpv_code: string | null
  cit_code: string | null
  supplier_name: string
  warehouse_name: string
  status: string
  completion_classification: string | null
  open_candidates: number
  evidence_count: number
  created_at: string
  completed_at?: string
  items_count?: number
  operator: UserSummary | null
  units?: { unit_id: string; name?: string; code?: string }[]
  products?: { product_id: string; name?: string; sku?: string }[]
}
