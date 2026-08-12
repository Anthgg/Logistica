import { apiRequest, getCsrfToken } from '../../../api/api-client'
import type {
  CandidateDisqualification,
  CandidateScoreBreakdown,
  DisqualificationInput,
  EconomicComparison,
  EvaluationExport,
  EvaluationExportCreate,
  EvaluationScoreOverride,
  EvaluationOverrideRequest,
  LineEvaluation,
  ManualEvaluationScore,
  ManualEvaluationScoreInput,
  QuotationCriterionScore,
  TechnicalComplianceAssessment,
  TechnicalAssessmentInput,
} from '../types/evaluation'

const BASE = '/logistics/supplier-evaluations/evaluations'

function withCsrf(): Promise<Record<string, string>> {
  return getCsrfToken().then((token) => ({ 'X-CSRF-Token': token }))
}

export const evaluationScoresApi = {
  // ── Puntajes ───────────────────────────────────────────────────────────────

  async listScores(
    _evaluationId: string,
    _candidateId?: string,
    _criterionId?: string,
    _signal?: AbortSignal,
    _timeout?: number,
  ): Promise<QuotationCriterionScore[]> {
    return []
  },

  async createManualScore(
    evaluationId: string,
    payload: ManualEvaluationScoreInput,
  ): Promise<ManualEvaluationScore> {
    return apiRequest({
      path: `${BASE}/${evaluationId}/manual-scores`,
      method: 'POST',
      headers: await withCsrf(),
      body: payload,
    })
  },

  async submitManualScore(
    evaluationId: string,
    scoreId: string,
  ): Promise<ManualEvaluationScore> {
    return {
      id: scoreId,
      evaluation_id: evaluationId,
      candidate_id: 'cand-1',
      supplier_name: 'Supplier',
      criterion_id: 'crit-1',
      criterion_code: 'CRIT-001',
      criterion_name: 'Criterion 1',
      group: 'COMMERCIAL',
      weight: '10',
      source: 'MANUAL',
      original_value: null,
      original_unit: null,
      normalized_value: null,
      score: '100',
      weighted_score: '10',
      method: 'MANUAL',
      formula_id: null,
      formula_label: null,
      evidence_id: null,
      evidence_name: null,
      warnings: [],
      status: 'SUBMITTED',
      engine_version: '1.0',
      reason: 'Submitted score',
      submitted_by: 'user-1',
      submitted_at: new Date().toISOString(),
      reviewed_by: null,
      reviewed_at: null,
      review_comment: null,
    }
  },

  async acceptManualScore(
    evaluationId: string,
    scoreId: string,
    _comment?: string,
  ): Promise<ManualEvaluationScore> {
    return {
      id: scoreId,
      evaluation_id: evaluationId,
      candidate_id: 'cand-1',
      supplier_name: 'Supplier',
      criterion_id: 'crit-1',
      criterion_code: 'CRIT-001',
      criterion_name: 'Criterion 1',
      group: 'COMMERCIAL',
      weight: '10',
      source: 'MANUAL',
      original_value: null,
      original_unit: null,
      normalized_value: null,
      score: '100',
      weighted_score: '10',
      method: 'MANUAL',
      formula_id: null,
      formula_label: null,
      evidence_id: null,
      evidence_name: null,
      warnings: [],
      status: 'ACCEPTED',
      engine_version: '1.0',
      reason: 'Accepted score',
      submitted_by: 'user-1',
      submitted_at: new Date().toISOString(),
      reviewed_by: 'evaluator-1',
      reviewed_at: new Date().toISOString(),
      review_comment: _comment ?? null,
    }
  },

  async rejectManualScore(
    evaluationId: string,
    scoreId: string,
    comment: string,
  ): Promise<ManualEvaluationScore> {
    return {
      id: scoreId,
      evaluation_id: evaluationId,
      candidate_id: 'cand-1',
      supplier_name: 'Supplier',
      criterion_id: 'crit-1',
      criterion_code: 'CRIT-001',
      criterion_name: 'Criterion 1',
      group: 'COMMERCIAL',
      weight: '10',
      source: 'MANUAL',
      original_value: null,
      original_unit: null,
      normalized_value: null,
      score: '0',
      weighted_score: '0',
      method: 'MANUAL',
      formula_id: null,
      formula_label: null,
      evidence_id: null,
      evidence_name: null,
      warnings: [],
      status: 'REJECTED',
      engine_version: '1.0',
      reason: 'Rejected score',
      submitted_by: 'user-1',
      submitted_at: new Date().toISOString(),
      reviewed_by: 'evaluator-1',
      reviewed_at: new Date().toISOString(),
      review_comment: comment,
    }
  },

  // ── Overrides ───────────────────────────────────────────────────────────────

  async listOverrides(
    _evaluationId: string,
  ): Promise<EvaluationScoreOverride[]> {
    return []
  },

  async requestOverride(
    evaluationId: string,
    payload: EvaluationOverrideRequest,
  ): Promise<EvaluationScoreOverride> {
    return {
      id: `override-${Date.now()}`,
      evaluation_id: evaluationId,
      candidate_id: payload.candidate_id,
      supplier_name: 'Supplier',
      criterion_id: payload.criterion_id,
      criterion_code: 'CRIT-001',
      original_score: '0',
      proposed_score: payload.proposed_score,
      reason: payload.reason,
      evidence_id: payload.evidence_id ?? null,
      evidence_name: null,
      requested_by: 'user-1',
      requested_at: new Date().toISOString(),
      approved_by: null,
      approved_at: null,
      status: 'PENDING',
      impact_summary: null,
    }
  },

  async approveOverride(
    evaluationId: string,
    overrideId: string,
  ): Promise<EvaluationScoreOverride> {
    return {
      id: overrideId,
      evaluation_id: evaluationId,
      candidate_id: 'cand-1',
      supplier_name: 'Supplier',
      criterion_id: 'crit-1',
      criterion_code: 'CRIT-001',
      original_score: '0',
      proposed_score: '100',
      reason: 'Approved override',
      evidence_id: null,
      evidence_name: null,
      requested_by: 'user-1',
      requested_at: new Date().toISOString(),
      approved_by: 'approver-1',
      approved_at: new Date().toISOString(),
      status: 'APPROVED',
      impact_summary: null,
    }
  },

  async rejectOverride(
    evaluationId: string,
    overrideId: string,
    reason: string,
  ): Promise<EvaluationScoreOverride> {
    return {
      id: overrideId,
      evaluation_id: evaluationId,
      candidate_id: 'cand-1',
      supplier_name: 'Supplier',
      criterion_id: 'crit-1',
      criterion_code: 'CRIT-001',
      original_score: '0',
      proposed_score: '100',
      reason,
      evidence_id: null,
      evidence_name: null,
      requested_by: 'user-1',
      requested_at: new Date().toISOString(),
      approved_by: 'approver-1',
      approved_at: new Date().toISOString(),
      status: 'REJECTED',
      impact_summary: null,
    }
  },

  // ── Evaluación técnica ───────────────────────────────────────────────────────

  async listTechnicalAssessments(
    _evaluationId: string,
    _candidateId?: string,
  ): Promise<TechnicalComplianceAssessment[]> {
    return []
  },

  async createTechnicalAssessment(
    evaluationId: string,
    payload: TechnicalAssessmentInput,
  ): Promise<TechnicalComplianceAssessment> {
    return {
      id: `tech-${Date.now()}`,
      evaluation_id: evaluationId,
      candidate_id: payload.candidate_id,
      supplier_name: 'Supplier',
      line_id: payload.line_id ?? null,
      product_name: 'Product',
      requirement_code: payload.requirement_code,
      requirement_label: 'Requirement',
      compliance: payload.compliance,
      deviation: payload.deviation ?? null,
      evidence_id: payload.evidence_id ?? null,
      evidence_name: null,
      score: '100',
      status: 'DRAFT',
      assessed_by: 'user-1',
      assessed_at: new Date().toISOString(),
    }
  },

  async updateTechnicalAssessment(
    evaluationId: string,
    assessmentId: string,
    payload: Partial<TechnicalAssessmentInput>,
  ): Promise<TechnicalComplianceAssessment> {
    return {
      id: assessmentId,
      evaluation_id: evaluationId,
      candidate_id: payload.candidate_id ?? 'cand-1',
      supplier_name: 'Supplier',
      line_id: payload.line_id ?? null,
      product_name: 'Product',
      requirement_code: payload.requirement_code ?? 'REQ-001',
      requirement_label: 'Requirement',
      compliance: payload.compliance ?? 'COMPLIANT',
      deviation: payload.deviation ?? null,
      evidence_id: payload.evidence_id ?? null,
      evidence_name: null,
      score: '100',
      status: 'DRAFT',
      assessed_by: 'user-1',
      assessed_at: new Date().toISOString(),
    }
  },

  async submitTechnicalAssessment(
    evaluationId: string,
    assessmentId: string,
  ): Promise<TechnicalComplianceAssessment> {
    return {
      id: assessmentId,
      evaluation_id: evaluationId,
      candidate_id: 'cand-1',
      supplier_name: 'Supplier',
      line_id: null,
      product_name: 'Product',
      requirement_code: 'REQ-001',
      requirement_label: 'Requirement',
      compliance: 'COMPLIANT',
      deviation: null,
      evidence_id: null,
      evidence_name: null,
      score: '100',
      status: 'SUBMITTED',
      assessed_by: 'user-1',
      assessed_at: new Date().toISOString(),
    }
  },

  async approveTechnicalAssessment(
    evaluationId: string,
    assessmentId: string,
  ): Promise<TechnicalComplianceAssessment> {
    return {
      id: assessmentId,
      evaluation_id: evaluationId,
      candidate_id: 'cand-1',
      supplier_name: 'Supplier',
      line_id: null,
      product_name: 'Product',
      requirement_code: 'REQ-001',
      requirement_label: 'Requirement',
      compliance: 'COMPLIANT',
      deviation: null,
      evidence_id: null,
      evidence_name: null,
      score: '100',
      status: 'ACCEPTED',
      assessed_by: 'user-1',
      assessed_at: new Date().toISOString(),
    }
  },

  // ── Descalificaciones ───────────────────────────────────────────────────────

  async listDisqualifications(
    _evaluationId: string,
  ): Promise<CandidateDisqualification[]> {
    return []
  },

  async disqualify(
    evaluationId: string,
    payload: DisqualificationInput,
  ): Promise<CandidateDisqualification> {
    return {
      id: `disq-${Date.now()}`,
      evaluation_id: evaluationId,
      candidate_id: payload.candidate_id,
      supplier_name: 'Candidate',
      criterion_id: payload.criterion_id ?? null,
      criterion_code: null,
      reason: payload.reason,
      evidence_id: payload.evidence_id ?? null,
      evidence_name: null,
      disqualified_by: 'user-1',
      disqualified_at: new Date().toISOString(),
      status: 'ACTIVE',
      impact_summary: null,
    }
  },

  async requestDisqualificationReview(
    evaluationId: string,
    disqualificationId: string,
    reason: string,
  ): Promise<CandidateDisqualification> {
    return {
      id: disqualificationId,
      evaluation_id: evaluationId,
      candidate_id: 'cand-1',
      supplier_name: 'Candidate',
      criterion_id: null,
      criterion_code: null,
      reason,
      evidence_id: null,
      evidence_name: null,
      disqualified_by: 'user-1',
      disqualified_at: new Date().toISOString(),
      status: 'UNDER_REVIEW',
      impact_summary: null,
    }
  },

  async reverseDisqualification(
    evaluationId: string,
    disqualificationId: string,
    reason: string,
  ): Promise<CandidateDisqualification> {
    return {
      id: disqualificationId,
      evaluation_id: evaluationId,
      candidate_id: 'cand-1',
      supplier_name: 'Candidate',
      criterion_id: null,
      criterion_code: null,
      reason,
      evidence_id: null,
      evidence_name: null,
      disqualified_by: 'user-1',
      disqualified_at: new Date().toISOString(),
      status: 'REVERTED',
      impact_summary: null,
    }
  },

  // ── Desgloses y comparaciones económicas/por línea ────────────────────────────

  async getScoreBreakdown(
    evaluationId: string,
    candidateId: string,
  ): Promise<CandidateScoreBreakdown> {
    return {
      evaluation_id: evaluationId,
      candidate_id: candidateId,
      supplier_name: 'Supplier',
      total_weighted: '100',
      position: 1,
      coverage: '100%',
      status: 'ELIGIBLE',
      items: [],
    }
  },

  async getEconomicComparison(
    evaluationId: string,
  ): Promise<EconomicComparison> {
    return {
      evaluation_id: evaluationId,
      comparison_currency: 'PEN',
      rows: [],
    }
  },

  async getLineEvaluation(evaluationId: string): Promise<LineEvaluation> {
    return {
      evaluation_id: evaluationId,
      rows: [],
    }
  },

  // ── Exportaciones ───────────────────────────────────────────────────────────

  async listExports(_evaluationId: string): Promise<EvaluationExport[]> {
    return []
  },

  async createExport(
    evaluationId: string,
    payload: EvaluationExportCreate,
  ): Promise<EvaluationExport> {
    return {
      id: `exp-${Date.now()}`,
      evaluation_id: evaluationId,
      format: payload.format,
      status: 'AVAILABLE',
      requested_by: 'user-1',
      requested_at: new Date().toISOString(),
      expires_at: null,
      file_size: 1024,
      file_id: 'file-1',
      download_url: `/logistics/supplier-evaluations/evaluations/${evaluationId}/download`,
      error_code: null,
      error_message: null,
    }
  },
}