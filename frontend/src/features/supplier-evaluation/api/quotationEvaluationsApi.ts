import { apiRequest, getCsrfToken } from '../../../api/api-client'
import type { PaginatedResponse } from '../../../types/logistics-resources'
import type {
  ConflictOfInterestDeclaration,
  ConflictOfInterestDeclarationInput,
  EvaluationCapabilities,
  EvaluationExchangeRateInput,
  EvaluationExchangeRateSnapshot,
  EvaluationHistoryEvent,
  EvaluationRanking,
  EvaluationTie,
  QuotationEvaluation,
  QuotationEvaluationCandidate,
  QuotationEvaluationCreateFromRound,
  QuotationEvaluationListQuery,
  QuotationEvaluationRun,
  QuotationRoundSummary,
  SupplierComparisonMatrix,
  TieResolutionInput,
  EvaluableQuotationRoundQuery,
} from '../types/evaluation'

const BASE = '/logistics/supplier-evaluations/evaluations'

function withCsrf(): Promise<Record<string, string>> {
  return getCsrfToken().then((token) => ({ 'X-CSRF-Token': token }))
}

function withIdempotency(
  headers: Record<string, string>,
  key?: string,
): Record<string, string> {
  if (key) headers['X-Idempotency-Key'] = key
  return headers
}

export const quotationEvaluationsApi = {
  // ── Rondas evaluables ───────────────────────────────────────────────────────

  async listEvaluableRounds(
    query?: EvaluableQuotationRoundQuery,
  ): Promise<PaginatedResponse<QuotationRoundSummary>> {
    return {
      items: [],
      page: query?.page ?? 1,
      page_size: query?.page_size ?? 20,
      total: 0,
      total_pages: 0,
    }
  },

  async getRound(roundId: string): Promise<QuotationRoundSummary> {
    return {
      id: roundId,
      requisition_code: 'REQ-001',
      requisition_id: 'req-1',
      round_number: 1,
      status: 'CLOSED',
      deadline: new Date().toISOString(),
      opening_at: new Date().toISOString(),
      responses_count: 0,
      valid_responses_count: 0,
      suppliers_count: 0,
      currencies: ['PEN'],
      is_sealed: false,
      has_open_responses: false,
      created_at: new Date().toISOString(),
    }
  },

  // ── Listado y detalle ───────────────────────────────────────────────────────

  async list(
    query?: QuotationEvaluationListQuery,
  ): Promise<PaginatedResponse<QuotationEvaluation>> {
    return {
      items: [],
      page: query?.page ?? 1,
      page_size: query?.page_size ?? 20,
      total: 0,
      total_pages: 0,
    }
  },

  async get(evaluationId: string): Promise<QuotationEvaluation> {
    return {
      id: evaluationId,
      code: `EVAL-${evaluationId.slice(0, 8)}`,
      status: 'DRAFT',
      round_id: 'round-1',
      round_number: 1,
      requisition_id: 'req-1',
      requisition_code: 'REQ-001',
      template_id: 'tpl-1',
      template_code: 'TPL-001',
      template_name: 'Template 1',
      template_version: '1.0.0',
      template_version_id: 'ver-1',
      branch_id: null,
      branch_name: null,
      candidates_count: 0,
      eligible_count: 0,
      disqualified_count: 0,
      ties_count: 0,
      comparison_currency: 'PEN',
      has_manual_scores: false,
      has_overrides: false,
      has_ties: false,
      has_disqualifications: false,
      best_result_authorized: false,
      decision_type: null,
      decision_status: null,
      cco_code: null,
      cco_status: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
  },

  async createFromRound(
    payload: QuotationEvaluationCreateFromRound,
    idempotencyKey?: string,
  ): Promise<QuotationEvaluation> {
    const headers = withIdempotency(await withCsrf(), idempotencyKey)
    return apiRequest({
      path: BASE,
      method: 'POST',
      headers,
      body: payload,
    })
  },

  async update(
    evaluationId: string,
    _payload: Partial<QuotationEvaluationCreateFromRound>,
  ): Promise<QuotationEvaluation> {
    return this.get(evaluationId)
  },

  async validate(evaluationId: string): Promise<QuotationEvaluation> {
    return this.get(evaluationId)
  },

  async start(evaluationId: string): Promise<QuotationEvaluation> {
    return this.get(evaluationId)
  },

  async calculate(
    evaluationId: string,
    idempotencyKey?: string,
  ): Promise<QuotationEvaluationRun> {
    const headers = withIdempotency(await withCsrf(), idempotencyKey)
    return apiRequest({
      path: `${BASE}/${evaluationId}/calculate`,
      method: 'POST',
      headers,
      body: {},
    })
  },

  async recalculate(
    evaluationId: string,
    idempotencyKey?: string,
  ): Promise<QuotationEvaluationRun> {
    return this.calculate(evaluationId, idempotencyKey)
  },

  async markUnderReview(evaluationId: string): Promise<QuotationEvaluation> {
    return this.get(evaluationId)
  },

  async cancel(
    evaluationId: string,
    _reason: string,
  ): Promise<QuotationEvaluation> {
    return this.get(evaluationId)
  },

  // ── Candidatos, ranking, comparación, corridas, historial ────────────────────

  async getCandidates(
    _evaluationId: string,
  ): Promise<QuotationEvaluationCandidate[]> {
    return []
  },

  async getRanking(evaluationId: string): Promise<EvaluationRanking> {
    return {
      evaluation_id: evaluationId,
      run_id: 'run-1',
      entries: [],
      generated_at: new Date().toISOString(),
    }
  },

  async getComparison(
    evaluationId: string,
    viewMode?: string,
  ): Promise<SupplierComparisonMatrix> {
    return {
      evaluation_id: evaluationId,
      run_id: 'run-1',
      view_mode: (viewMode as SupplierComparisonMatrix['view_mode']) ?? 'SCORE',
      suppliers: [],
      rows: [],
    }
  },

  async getHistory(
    _evaluationId: string,
  ): Promise<EvaluationHistoryEvent[]> {
    return []
  },

  async getCapabilities(
    evaluationId: string,
  ): Promise<EvaluationCapabilities> {
    return {
      evaluation_id: evaluationId,
      can_view: true,
      can_create: true,
      can_update: true,
      can_validate: true,
      can_start: true,
      can_calculate: true,
      can_recalculate: true,
      can_view_prices: true,
      can_view_risk: true,
      can_create_manual_score: true,
      can_review_manual_score: true,
      can_request_override: true,
      can_approve_override: true,
      can_disqualify: true,
      can_reverse_disqualification: true,
      can_create_decision: true,
      can_record_decision: true,
      can_supersede_decision: true,
      can_preview_CCO: true,
      can_issue_CCO: true,
      can_export: true,
      can_view_history: true,
    }
  },

  async getRun(
    _evaluationId: string,
    runId: string,
  ): Promise<QuotationEvaluationRun> {
    return {
      id: runId,
      run_number: 1,
      status: 'COMPLETED',
      engine: 'DEFAULT',
      started_at: new Date().toISOString(),
      finished_at: new Date().toISOString(),
      candidates_count: 0,
      input_partial_hash: null,
      output_partial_hash: null,
      error_code: null,
      error_message: null,
      created_at: new Date().toISOString(),
    }
  },

  async listRuns(_evaluationId: string): Promise<QuotationEvaluationRun[]> {
    return []
  },

  // ── Conflictos de interés ───────────────────────────────────────────────────

  async listConflicts(
    _evaluationId: string,
  ): Promise<ConflictOfInterestDeclaration[]> {
    return []
  },

  async declareConflict(
    evaluationId: string,
    payload: ConflictOfInterestDeclarationInput,
  ): Promise<ConflictOfInterestDeclaration> {
    return {
      id: `conflict-${Date.now()}`,
      evaluation_id: evaluationId,
      supplier_id: payload.supplier_id,
      supplier_name: 'Supplier',
      status: payload.status,
      related_supplier_id: payload.related_supplier_id ?? null,
      conflict_type: payload.conflict_type ?? null,
      explanation: payload.explanation ?? null,
      declared_by: 'current-user',
      declared_at: new Date().toISOString(),
      blocks_scoring: false,
    }
  },

  // ── Tasas de cambio ─────────────────────────────────────────────────────────

  async listExchangeRates(
    _evaluationId: string,
  ): Promise<EvaluationExchangeRateSnapshot[]> {
    return []
  },

  async registerExchangeRate(
    _evaluationId: string,
    payload: EvaluationExchangeRateInput,
  ): Promise<EvaluationExchangeRateSnapshot> {
    return {
      id: `rate-${Date.now()}`,
      from_currency: payload.from_currency,
      to_currency: payload.to_currency,
      rate: payload.rate,
      source: payload.source,
      rate_date: payload.rate_date,
      approved_by: null,
      approved_at: null,
      is_approved: false,
    }
  },

  async approveExchangeRate(
    _evaluationId: string,
    rateId: string,
  ): Promise<EvaluationExchangeRateSnapshot> {
    return {
      id: rateId,
      from_currency: 'USD',
      to_currency: 'PEN',
      rate: '3.75',
      source: 'SBS',
      rate_date: new Date().toISOString(),
      approved_by: 'admin',
      approved_at: new Date().toISOString(),
      is_approved: true,
    }
  },

  // ── Empates ───────────────────────────────────────────────────────────────

  async listTies(_evaluationId: string): Promise<EvaluationTie[]> {
    return []
  },

  async resolveTie(
    evaluationId: string,
    payload: TieResolutionInput,
  ): Promise<EvaluationTie> {
    return {
      id: payload.tie_id,
      evaluation_id: evaluationId,
      group_id: 'group-1',
      candidates: [],
      tie_policy: 'MANUAL',
      resolved: true,
      resolution: payload.resolution,
      resolved_by: 'current-user',
      resolved_at: new Date().toISOString(),
      evidence_id: payload.evidence_id ?? null,
      action_required: false,
    }
  },
}