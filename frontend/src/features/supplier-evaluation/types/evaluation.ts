/**
 * Tipos del dominio de evaluación de proveedores (Fase 033).
 *
 * Reglas de modelado:
 * - Montos, cantidades, pesos y puntajes se representan como `string`
 *   decimal. No se usa `number` para valores de negocio autoritativos.
 * - No se declara `weighted_score`, `ranking`, `organization_id` ni campos
 *   de decisión en el payload enviado al backend (esos solo se consumen).
 * - No se usa `any`.
 */

export interface MoneyValue {
  amount: string
  currency: string
}

export interface DecimalValue {
  value: string
  scale: number
}

export interface PaginatedResponse<T> {
  items: T[]
  page: number
  page_size: number
  total: number
  total_pages: number
}

export interface ApiError {
  code: string
  message: string
  status: number | null
  details?: unknown
}

// ── Catálogos base ──────────────────────────────────────────────────────────

export type EvaluationScoringMethod =
  | 'PRICE'
  | 'TECHNICAL'
  | 'MANUAL'
  | 'COMPLIANCE'
  | 'RISK'
  | 'QUALITY'
  | 'DELIVERY'
  | 'DOCUMENTATION'
  | 'FORMULA'

export type EvaluationCriterionGroup =
  | 'ECONOMIC'
  | 'TECHNICAL'
  | 'COMMERCIAL'
  | 'RISK'
  | 'QUALITY'
  | 'COMPLIANCE'
  | 'OTHER'

export type MissingDataPolicy =
  | 'ZERO'
  | 'EXCLUDE'
  | 'MINIMUM'
  | 'REQUIRE'
  | 'PENALTY'

export type TiePolicy =
  | 'HIGHEST_TECHNICAL'
  | 'LOWEST_PRICE'
  | 'LOWEST_RISK'
  | 'SHORTEST_DELIVERY'
  | 'MANUAL'
  | 'REQUOTE'

export type AwardPolicy = 'SINGLE' | 'SPLIT_BY_LINE' | 'SPLIT_BY_QUANTITY' | 'NO_AWARD' | 'REQUOTE'

export type RubricScale = 'BINARY' | 'ORDINAL_3' | 'ORDINAL_4' | 'ORDINAL_5' | 'POINTS_100'

export type CriterionSourceType =
  | 'RESPONSE_FIELD'
  | 'RESPONSE_LINE'
  | 'MANUAL'
  | 'TECHNICAL_ASSESSMENT'
  | 'COMPLIANCE'
  | 'RISK_SNAPSHOT'
  | 'QUALITY_SNAPSHOT'

// ── Plantillas y versiones ──────────────────────────────────────────────────

export interface EvaluationRubricLevel {
  code: string
  label: string
  description: string
  score: string
  expected_evidence: string | null
}

export interface EvaluationRubric {
  id: string
  code: string
  name: string
  scale: RubricScale
  levels: EvaluationRubricLevel[]
  evidence_required: boolean
  version: string
  status: 'DRAFT' | 'ACTIVE' | 'RETIRED' | 'ARCHIVED'
  created_at: string
  updated_at: string
}

export interface EvaluationCriterionDefinition {
  id: string
  order: number
  code: string
  name: string
  group: EvaluationCriterionGroup
  method: EvaluationScoringMethod
  weight: string
  is_required: boolean
  is_eliminator: boolean
  min_score: string | null
  source_type: CriterionSourceType
  source_field: string | null
  evidence_required: boolean
  rubric_id: string | null
  rubric: EvaluationRubric | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface SupplierEvaluationTemplateVersion {
  id: string
  template_id: string
  version: string
  status: 'DRAFT' | 'VALIDATED' | 'ACTIVE' | 'RETIRED' | 'ARCHIVED'
  scale: string
  min_total_score: string | null
  missing_data_policy: MissingDataPolicy
  tie_policy: TiePolicy
  award_policy: AwardPolicy
  comparison_currency: string | null
  engine: string
  partial_hash: string
  effective_from: string | null
  effective_to: string | null
  criteria: EvaluationCriterionDefinition[]
  created_at: string
  updated_at: string
}

export interface SupplierEvaluationTemplate {
  id: string
  code: string
  name: string
  description: string | null
  scope: 'QUOTATION' | 'SUPPLIER' | 'PRODUCT' | 'GENERAL'
  active_version_id: string | null
  active_version: SupplierEvaluationTemplateVersion | null
  versions_count: number
  criteria_count: number
  status: 'DRAFT' | 'ACTIVE' | 'INACTIVE' | 'ARCHIVED'
  effective_from: string | null
  effective_to: string | null
  created_at: string
  updated_at: string
}

export interface SupplierEvaluationTemplateCreate {
  code: string
  name: string
  description?: string | null
  scope: SupplierEvaluationTemplate['scope']
}

export interface SupplierEvaluationTemplateUpdate {
  name?: string
  description?: string | null
}

export interface EvaluationTemplateVersionCreate {
  version: string
  scale: string
  min_total_score?: string | null
  missing_data_policy?: MissingDataPolicy
  tie_policy?: TiePolicy
  award_policy?: AwardPolicy
  comparison_currency?: string | null
}

export interface EvaluationTemplateVersionUpdate {
  min_total_score?: string | null
  missing_data_policy?: MissingDataPolicy
  tie_policy?: TiePolicy
  award_policy?: AwardPolicy
  comparison_currency?: string | null
}

export interface EvaluationCriterionCreate {
  code: string
  name: string
  group: EvaluationCriterionGroup
  method: EvaluationScoringMethod
  weight: string
  is_required?: boolean
  is_eliminator?: boolean
  min_score?: string | null
  source_type?: CriterionSourceType
  source_field?: string | null
  evidence_required?: boolean
  rubric_id?: string | null
}

export interface EvaluationCriterionUpdate {
  code?: string
  name?: string
  group?: EvaluationCriterionGroup
  method?: EvaluationScoringMethod
  weight?: string
  is_required?: boolean
  is_eliminator?: boolean
  min_score?: string | null
  source_type?: CriterionSourceType
  source_field?: string | null
  evidence_required?: boolean
  rubric_id?: string | null
}

export interface EvaluationWeightsValidationRequest {
  weights: Record<string, string>
}

export interface EvaluationWeightsValidation {
  total: string
  target: string
  difference: string
  is_valid: boolean
  issues: Array<{
    criterion_id: string
    code: string
    message: string
  }>
}

// ── Rondas de cotización (vista de solo lectura) ───────────────────────────

export type QuotationRoundStatus =
  | 'DRAFT'
  | 'OPEN'
  | 'OPEN_INTERNAL_REVIEW'
  | 'CLOSED'
  | 'CANCELLED'
  | 'ARCHIVED'

export interface QuotationRoundSummary {
  id: string
  requisition_code: string
  requisition_id: string
  round_number: number
  status: QuotationRoundStatus
  deadline: string | null
  opening_at: string | null
  responses_count: number
  valid_responses_count: number
  suppliers_count: number
  currencies: string[]
  is_sealed: boolean
  has_open_responses: boolean
  created_at: string
}

export interface EvaluableQuotationRoundQuery {
  search?: string
  page?: number
  page_size?: number
}

// ── Evaluación de cotización ────────────────────────────────────────────────

export type QuotationEvaluationStatus =
  | 'DRAFT'
  | 'READY'
  | 'IN_PROGRESS'
  | 'CALCULATED'
  | 'UNDER_REVIEW'
  | 'DECISION_RECORDED'
  | 'SUPERSEDED'
  | 'CANCELLED'
  | 'ARCHIVED'

export interface ConflictOfInterestDeclaration {
  id: string
  evaluation_id: string
  supplier_id: string
  supplier_name: string
  status: 'NONE' | 'POSSIBLE' | 'CONFIRMED' | 'CANNOT_DECLARE'
  related_supplier_id: string | null
  conflict_type: string | null
  explanation: string | null
  declared_by: string
  declared_at: string
  blocks_scoring: boolean
}

export interface ConflictOfInterestDeclarationInput {
  supplier_id: string
  status: ConflictOfInterestDeclaration['status']
  related_supplier_id?: string | null
  conflict_type?: string | null
  explanation?: string | null
}

export interface EvaluationExchangeRateSnapshot {
  id: string
  from_currency: string
  to_currency: string
  rate: string
  source: string
  rate_date: string
  approved_by: string | null
  approved_at: string | null
  is_approved: boolean
}

export interface EvaluationExchangeRateInput {
  from_currency: string
  to_currency: string
  rate: string
  source: string
  rate_date: string
}

export interface QuotationEvaluationCandidate {
  id: string
  evaluation_id: string
  supplier_id: string
  supplier_name: string
  supplier_code: string
  response_id: string
  response_number: string
  currency: string
  total_declared: string | null
  is_late_response: boolean
  completeness: string | null
  is_eligible: boolean
  is_disqualified: boolean
  disqualification_reason: string | null
  documents_count: number
  risks_count: number
  warnings: string[]
  can_view_prices: boolean
  can_view_risk: boolean
}

export interface QuotationEvaluationRun {
  id: string
  run_number: number
  status: 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'SUPERSEDED'
  engine: string
  started_at: string | null
  finished_at: string | null
  candidates_count: number
  input_partial_hash: string | null
  output_partial_hash: string | null
  error_code: string | null
  error_message: string | null
  created_at: string
}

export type ScoreSource = 'RESPONSE' | 'MANUAL' | 'TECHNICAL' | 'COMPLIANCE' | 'RISK' | 'QUALITY'

export type ScoreStatus = 'DRAFT' | 'SUBMITTED' | 'ACCEPTED' | 'REJECTED' | 'SUPERSEDED'

export interface QuotationCriterionScore {
  id: string
  evaluation_id: string
  candidate_id: string
  supplier_name: string
  criterion_id: string
  criterion_code: string
  criterion_name: string
  group: EvaluationCriterionGroup
  weight: string
  source: ScoreSource
  original_value: string | null
  original_unit: string | null
  normalized_value: string | null
  score: string | null
  weighted_score: string | null
  method: EvaluationScoringMethod
  formula_id: string | null
  formula_label: string | null
  evidence_id: string | null
  evidence_name: string | null
  warnings: string[]
  status: ScoreStatus
  engine_version: string | null
}

export interface ManualEvaluationScoreInput {
  candidate_id: string
  criterion_id: string
  raw_value: string
  rubric_level_code?: string | null
  evidence_id?: string | null
  evidence_required: boolean
  reason: string | null
  conflict_of_interest_declared: boolean
}

export interface ManualEvaluationScore extends QuotationCriterionScore {
  reason: string | null
  submitted_by: string | null
  submitted_at: string | null
  reviewed_by: string | null
  reviewed_at: string | null
  review_comment: string | null
}

export type OverrideStatus = 'PENDING' | 'APPROVED' | 'REJECTED' | 'SUPERSEDED'

export interface EvaluationScoreOverride {
  id: string
  evaluation_id: string
  candidate_id: string
  supplier_name: string
  criterion_id: string
  criterion_code: string
  original_score: string
  proposed_score: string
  reason: string
  evidence_id: string | null
  evidence_name: string | null
  requested_by: string
  requested_at: string
  approved_by: string | null
  approved_at: string | null
  status: OverrideStatus
  impact_summary: string | null
}

export interface EvaluationOverrideRequest {
  candidate_id: string
  criterion_id: string
  proposed_score: string
  reason: string
  evidence_id?: string | null
}

// ── Evaluación técnica ─────────────────────────────────────────────────────

export type TechnicalCompliance =
  | 'COMPLIANT'
  | 'PARTIALLY_COMPLIANT'
  | 'NON_COMPLIANT'
  | 'ALTERNATIVE_REVIEW'
  | 'NOT_EVALUATED'

export interface TechnicalComplianceAssessment {
  id: string
  evaluation_id: string
  candidate_id: string
  supplier_name: string
  line_id: string | null
  product_name: string | null
  requirement_code: string
  requirement_label: string
  compliance: TechnicalCompliance
  deviation: string | null
  evidence_id: string | null
  evidence_name: string | null
  score: string | null
  status: ScoreStatus
  assessed_by: string | null
  assessed_at: string | null
}

export interface TechnicalAssessmentInput {
  candidate_id: string
  line_id?: string | null
  requirement_code: string
  compliance: TechnicalCompliance
  deviation?: string | null
  evidence_id?: string | null
}

export interface SupplierQualitySnapshot {
  supplier_id: string
  supplier_name: string
  quality_score: string | null
  on_time_rate: string | null
  non_conformities_count: number
  last_assessment_at: string | null
}

export interface SupplierRiskSnapshot {
  supplier_id: string
  supplier_name: string
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | 'UNKNOWN'
  risk_score: string | null
  open_issues: number
  assessed_at: string | null
  can_view: boolean
}

// ── Ranking, empates, descalificaciones ────────────────────────────────────

export interface EvaluationRankingEntry {
  position: number
  candidate_id: string
  supplier_name: string
  total_score: string
  coverage: string
  comparable_price: string | null
  delivery_days: number | null
  risk_level: SupplierRiskSnapshot['risk_level']
  status: 'ELIGIBLE' | 'DISQUALIFIED' | 'TIED'
  is_tied: boolean
  tie_group_id: string | null
}

export interface EvaluationRanking {
  evaluation_id: string
  run_id: string
  entries: EvaluationRankingEntry[]
  generated_at: string
}

export interface EvaluationTie {
  id: string
  evaluation_id: string
  group_id: string
  candidates: Array<{
    candidate_id: string
    supplier_name: string
    total_score: string
  }>
  tie_policy: TiePolicy
  resolved: boolean
  resolution: string | null
  resolved_by: string | null
  resolved_at: string | null
  evidence_id: string | null
  action_required: boolean
}

export interface TieResolutionInput {
  tie_id: string
  resolution: TiePolicy | 'MANUAL'
  reason?: string | null
  evidence_id?: string | null
  winner_candidate_id?: string | null
}

export interface CandidateDisqualification {
  id: string
  evaluation_id: string
  candidate_id: string
  supplier_name: string
  criterion_id: string | null
  criterion_code: string | null
  reason: string
  evidence_id: string | null
  evidence_name: string | null
  disqualified_by: string
  disqualified_at: string
  status: 'ACTIVE' | 'REVERTED' | 'UNDER_REVIEW'
  impact_summary: string | null
}

export interface DisqualificationInput {
  candidate_id: string
  criterion_id?: string | null
  reason: string
  evidence_id?: string | null
}

// ── Comparación ────────────────────────────────────────────────────────────

export type ComparisonViewMode = 'ORIGINAL' | 'NORMALIZED' | 'SCORE' | 'WEIGHTED'

export interface ComparisonRow {
  code: string
  label: string
  group: EvaluationCriterionGroup
  weight: string
  cells: Array<{
    candidate_id: string
    supplier_name: string
    value: string | null
    source: ScoreSource | null
    formula_id: string | null
    formula_label: string | null
    evidence_id: string | null
    evidence_name: string | null
    warnings: string[]
    explanation: string | null
  }>
}

export interface SupplierComparisonMatrix {
  evaluation_id: string
  run_id: string
  view_mode: ComparisonViewMode
  suppliers: Array<{
    candidate_id: string
    supplier_name: string
    is_disqualified: boolean
    is_tied: boolean
  }>
  rows: ComparisonRow[]
}

export interface EconomicComparisonRow {
  candidate_id: string
  supplier_name: string
  currency: string
  subtotal: string | null
  discount: string | null
  tax: string | null
  freight: string | null
  other_charges: string | null
  total_declared: string | null
  total_comparable: string | null
  rate: string | null
  rate_source: string | null
  rate_date: string | null
  price_score: string | null
  arithmetic_warnings: string[]
}

export interface EconomicComparison {
  evaluation_id: string
  comparison_currency: string
  rows: EconomicComparisonRow[]
}

export interface LineEvaluationRow {
  line_id: string
  product_name: string
  requested_quantity: string
  unit: string
  cells: Array<{
    candidate_id: string
    supplier_name: string
    quoted_quantity: string | null
    unit: string | null
    unit_price: string | null
    currency: string
    delivery_days: number | null
    compliance: TechnicalCompliance
    is_alternative: boolean
    line_score: string | null
    line_rank: number | null
    warnings: string[]
  }>
}

export interface LineEvaluation {
  evaluation_id: string
  rows: LineEvaluationRow[]
}

export interface CandidateScoreBreakdown {
  evaluation_id: string
  candidate_id: string
  supplier_name: string
  total_weighted: string
  position: number | null
  coverage: string
  status: 'ELIGIBLE' | 'DISQUALIFIED' | 'TIED'
  items: Array<{
    criterion_id: string
    criterion_code: string
    criterion_name: string
    weight: string
    original_value: string | null
    normalized_value: string | null
    score: string | null
    weighted_score: string | null
    source: ScoreSource
    method: EvaluationScoringMethod
    formula_label: string | null
    evidence_name: string | null
    warnings: string[]
  }>
}

// ── Decisiones ─────────────────────────────────────────────────────────────

export type EvaluationDecisionType =
  | 'SINGLE_SUPPLIER'
  | 'SPLIT_BY_LINE'
  | 'SPLIT_BY_QUANTITY'
  | 'NO_AWARD'
  | 'REQUOTE'
  | 'CLARIFICATION'
  | 'MANUAL_EXCEPTION'

export type DecisionStatus =
  | 'DRAFT'
  | 'VALIDATED'
  | 'SUBMITTED'
  | 'RECORDED'
  | 'SUPERSEDED'
  | 'CANCELLED'

export interface QuotationEvaluationDecisionLine {
  line_id: string
  product_name: string
  requested_quantity: string
  unit: string
  awarded_candidate_id: string | null
  awarded_supplier_name: string | null
  awarded_quantity: string | null
  awarded_unit_price: string | null
  awarded_currency: string | null
  awarded_total: string | null
  reason: string | null
}

export interface QuotationEvaluationDecision {
  id: string
  evaluation_id: string
  type: EvaluationDecisionType
  status: DecisionStatus
  justification: string | null
  exceptions: string | null
  comments: string | null
  next_action: string | null
  reason_not_first_rank: string | null
  single_candidate_id: string | null
  single_supplier_name: string | null
  lines: QuotationEvaluationDecisionLine[]
  split_distributions: Array<{
    line_id: string
    candidate_id: string
    supplier_name: string
    quantity: string
    percentage: string
    unit_price: string
    currency: string
  }>
  total_amount: string | null
  total_currency: string | null
  procurement_approval_pending: boolean
  recorded_by: string | null
  recorded_at: string | null
  created_at: string
  updated_at: string
}

export interface EvaluationDecisionCreate {
  type: EvaluationDecisionType
  justification?: string | null
  exceptions?: string | null
  comments?: string | null
  next_action?: string | null
  reason_not_first_rank?: string | null
  single_candidate_id?: string | null
  lines?: QuotationEvaluationDecisionLine[]
  split_distributions?: QuotationEvaluationDecision['split_distributions']
}

export interface EvaluationDecisionUpdate extends Partial<EvaluationDecisionCreate> {}

export interface SplitAwardLineInput {
  line_id: string
  awarded_candidate_id: string
  awarded_quantity: string
  reason?: string | null
}

export interface SplitAwardQuantityInput {
  line_id: string
  distributions: Array<{
    candidate_id: string
    quantity: string
  }>
}

export interface NoAwardDecisionInput {
  reason: string
  unsatisfied_criteria: string[]
  comments?: string | null
  next_action?: string | null
  evidence_id?: string | null
}

export interface RequoteDecisionInput {
  reason: string
  comments?: string | null
  next_action?: string | null
}

export interface EvaluationDecisionValidation {
  decision_id: string
  is_valid: boolean
  errors: Array<{ code: string; message: string; field: string | null }>
  warnings: Array<{ code: string; message: string }>
  checks: Array<{
    code: string
    label: string
    status: 'PASS' | 'FAIL' | 'WARN'
    detail: string | null
  }>
}

// ── Documento CCO y exportaciones ───────────────────────────────────────────

export type ComparativeDocumentStatus = 'DRAFT' | 'PREVIEW' | 'ISSUED' | 'VOID' | 'SUPERSEDED'

export interface ComparativeDocument {
  id: string
  evaluation_id: string
  code: string
  status: ComparativeDocumentStatus
  version: number
  issued_at: string | null
  partial_hash: string | null
  integrity_ok: boolean
  file_id: string | null
  file_name: string | null
  file_size: number | null
  can_preview: boolean
  can_issue: boolean
  can_download: boolean
  can_reprint: boolean
  created_at: string
  updated_at: string
}

export type ExportFormat = 'PDF' | 'CSV' | 'XLSX'

export type ExportStatus = 'QUEUED' | 'GENERATING' | 'AVAILABLE' | 'FAILED' | 'EXPIRED'

export interface EvaluationExport {
  id: string
  evaluation_id: string
  format: ExportFormat
  status: ExportStatus
  requested_by: string
  requested_at: string
  expires_at: string | null
  file_size: number | null
  file_id: string | null
  download_url: string | null
  error_code: string | null
  error_message: string | null
}

export interface EvaluationExportCreate {
  format: ExportFormat
}

// ── Historial ──────────────────────────────────────────────────────────────

export interface EvaluationHistoryEvent {
  id: string
  evaluation_id: string
  action: string
  resource_type: string | null
  resource_id: string | null
  result: string
  actor_display_name: string | null
  reason: string | null
  run_id: string | null
  version: string | null
  occurred_at: string
}

// ── Evidencias (integración Fase 030) ──────────────────────────────────────

export type EvaluationEvidenceType =
  | 'TECHNICAL_SHEET'
  | 'CERTIFICATE'
  | 'HISTORY'
  | 'NON_CONFORMITY'
  | 'TECHNICAL_REPORT'
  | 'QUALITY_ASSESSMENT'
  | 'RISK_EVIDENCE'
  | 'OVERRIDE_JUSTIFICATION'

export interface EvaluationEvidence {
  id: string
  evaluation_id: string
  file_id: string
  file_name: string
  evidence_type: EvaluationEvidenceType
  version: number
  partial_hash: string
  status: 'PENDING' | 'ACCEPTED' | 'REJECTED' | 'QUARANTINE'
  source: string
  associated_to: string | null
  associated_label: string | null
  created_at: string
}

// ── Capabilities ────────────────────────────────────────────────────────────

export interface EvaluationCapabilities {
  evaluation_id: string
  can_view: boolean
  can_create: boolean
  can_update: boolean
  can_validate: boolean
  can_start: boolean
  can_calculate: boolean
  can_recalculate: boolean
  can_view_prices: boolean
  can_view_risk: boolean
  can_create_manual_score: boolean
  can_review_manual_score: boolean
  can_request_override: boolean
  can_approve_override: boolean
  can_disqualify: boolean
  can_reverse_disqualification: boolean
  can_create_decision: boolean
  can_record_decision: boolean
  can_supersede_decision: boolean
  can_preview_CCO: boolean
  can_issue_CCO: boolean
  can_export: boolean
  can_view_history: boolean
}

// ── Evaluación raíz ─────────────────────────────────────────────────────────

export interface QuotationEvaluation {
  id: string
  code: string
  status: QuotationEvaluationStatus
  round_id: string
  round_number: number
  requisition_id: string
  requisition_code: string
  template_id: string
  template_code: string
  template_name: string
  template_version: string
  template_version_id: string
  branch_id: string | null
  branch_name: string | null
  candidates_count: number
  eligible_count: number
  disqualified_count: number
  ties_count: number
  comparison_currency: string | null
  has_manual_scores: boolean
  has_overrides: boolean
  has_ties: boolean
  has_disqualifications: boolean
  best_result_authorized: boolean
  decision_type: EvaluationDecisionType | null
  decision_status: DecisionStatus | null
  cco_code: string | null
  cco_status: ComparativeDocumentStatus | null
  created_at: string
  updated_at: string
}

export interface QuotationEvaluationSummary extends QuotationEvaluation {}

export interface QuotationEvaluationCreateFromRound {
  round_id: string
  template_version_id: string
  branch_id?: string | null
  comparison_currency?: string | null
  exchange_rates?: EvaluationExchangeRateInput[]
}

export interface QuotationEvaluationListQuery {
  page?: number
  page_size?: number
  search?: string
  status?: QuotationEvaluationStatus | null
  template_id?: string | null
  branch_id?: string | null
  supplier_id?: string | null
  decision_type?: EvaluationDecisionType | null
  date_from?: string | null
  date_to?: string | null
  with_ties?: boolean
  with_disqualified?: boolean
  with_manual_scores?: boolean
  with_overrides?: boolean
  currency?: string | null
  pending_my_evaluation?: boolean
  tab?: 'drafts' | 'in_progress' | 'calculated' | 'decided' | null
}