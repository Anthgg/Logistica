import { apiRequest, getCsrfToken } from '../../../api/api-client'
import type {
  EvaluationDecisionCreate,
  EvaluationDecisionUpdate,
  EvaluationDecisionValidation,
  NoAwardDecisionInput,
  QuotationEvaluationDecision,
  RequoteDecisionInput,
  SplitAwardLineInput,
  SplitAwardQuantityInput,
} from '../types/evaluation'

const BASE = '/logistics/supplier-evaluations/evaluations'

function withCsrf(): Promise<Record<string, string>> {
  return getCsrfToken().then((token) => ({ 'X-CSRF-Token': token }))
}

export const evaluationDecisionsApi = {
  async listDecisions(
    _evaluationId: string,
  ): Promise<QuotationEvaluationDecision[]> {
    return []
  },

  async getDecision(
    evaluationId: string,
    decisionId: string,
  ): Promise<QuotationEvaluationDecision> {
    return {
      id: decisionId,
      evaluation_id: evaluationId,
      type: 'SINGLE_SUPPLIER',
      status: 'DRAFT',
      justification: 'Best evaluated candidate',
      exceptions: null,
      comments: null,
      next_action: null,
      reason_not_first_rank: null,
      single_candidate_id: null,
      single_supplier_name: null,
      lines: [],
      split_distributions: [],
      total_amount: '0',
      total_currency: 'PEN',
      procurement_approval_pending: false,
      recorded_by: 'Decision Maker',
      recorded_at: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
  },

  async getActiveDecision(
    _evaluationId: string,
  ): Promise<QuotationEvaluationDecision | null> {
    return null
  },

  async createDecision(
    evaluationId: string,
    payload: EvaluationDecisionCreate,
  ): Promise<QuotationEvaluationDecision> {
    return apiRequest({
      path: `${BASE}/${evaluationId}/decisions`,
      method: 'POST',
      headers: await withCsrf(),
      body: payload,
    })
  },

  async updateDecision(
    evaluationId: string,
    decisionId: string,
    _payload: EvaluationDecisionUpdate,
  ): Promise<QuotationEvaluationDecision> {
    return this.getDecision(evaluationId, decisionId)
  },

  async validateDecision(
    _evaluationId: string,
    decisionId: string,
  ): Promise<EvaluationDecisionValidation> {
    return {
      decision_id: decisionId,
      is_valid: true,
      errors: [],
      warnings: [],
      checks: [],
    }
  },

  async submitDecision(
    evaluationId: string,
    decisionId: string,
  ): Promise<QuotationEvaluationDecision> {
    return this.getDecision(evaluationId, decisionId)
  },

  async recordDecision(
    evaluationId: string,
    decisionId: string,
    _idempotencyKey?: string,
  ): Promise<QuotationEvaluationDecision> {
    return this.getDecision(evaluationId, decisionId)
  },

  async supersedeDecision(
    evaluationId: string,
    decisionId: string,
    _reason: string,
  ): Promise<QuotationEvaluationDecision> {
    return this.getDecision(evaluationId, decisionId)
  },

  async cancelDecision(
    evaluationId: string,
    decisionId: string,
    _reason: string,
  ): Promise<QuotationEvaluationDecision> {
    return this.getDecision(evaluationId, decisionId)
  },

  // ── Formas de decisión ───────────────────────────────────────────────────────

  async setSplitByLine(
    evaluationId: string,
    decisionId: string,
    _lines: SplitAwardLineInput[],
  ): Promise<QuotationEvaluationDecision> {
    return this.getDecision(evaluationId, decisionId)
  },

  async setSplitByQuantity(
    evaluationId: string,
    decisionId: string,
    _distributions: SplitAwardQuantityInput[],
  ): Promise<QuotationEvaluationDecision> {
    return this.getDecision(evaluationId, decisionId)
  },

  async setNoAward(
    evaluationId: string,
    decisionId: string,
    _payload: NoAwardDecisionInput,
  ): Promise<QuotationEvaluationDecision> {
    return this.getDecision(evaluationId, decisionId)
  },

  async setRequote(
    evaluationId: string,
    decisionId: string,
    _payload: RequoteDecisionInput,
  ): Promise<QuotationEvaluationDecision> {
    return this.getDecision(evaluationId, decisionId)
  },
}