import { apiRequest, getCsrfToken } from '../../../api/api-client'
import type {
  ReceptionDifferenceReview,
  ReceptionDifferenceApproval,
  PaginatedResponse,
} from '../types/reception-differences'

const CASES_BASE = '/logistics/reception-difference-cases'
const REVIEWS_BASE = '/logistics/reception-difference-reviews'

function generateKey(): string {
  return typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

async function withCsrf(): Promise<Record<string, string>> {
  const token = await getCsrfToken()
  return { 'X-CSRF-Token': token }
}

export const receptionDifferenceReviewsApi = {
  // ── Reviews (6) ───────────────────────────────────────────────────────────────

  /** GET /reception-difference-cases/{case_id}/reviews */
  async listReviews(caseId: string): Promise<PaginatedResponse<ReceptionDifferenceReview>> {
    return apiRequest({ path: `${CASES_BASE}/${caseId}/reviews`, method: 'GET' })
  },

  /** POST /reception-difference-cases/{case_id}/reviews */
  async createReview(caseId: string): Promise<ReceptionDifferenceReview> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${CASES_BASE}/${caseId}/reviews`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: {},
    })
  },

  /** POST /reception-difference-reviews/{review_id}/start */
  async startReview(reviewId: string): Promise<ReceptionDifferenceReview> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${REVIEWS_BASE}/${reviewId}/start`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: {},
    })
  },

  /** POST /reception-difference-reviews/{review_id}/request-changes */
  async requestChanges(reviewId: string, data: { reason: string; sections?: string[]; items_affected?: string[]; evidence_missing?: string[]; responsible_missing?: boolean }): Promise<ReceptionDifferenceReview> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${REVIEWS_BASE}/${reviewId}/request-changes`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** POST /reception-difference-reviews/{review_id}/complete */
  async completeReview(reviewId: string): Promise<ReceptionDifferenceReview> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${REVIEWS_BASE}/${reviewId}/complete`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: {},
    })
  },

  // ── Approvals (1) ─────────────────────────────────────────────────────────────

  /** GET /reception-difference-cases/{case_id}/approvals */
  async listApprovals(caseId: string): Promise<PaginatedResponse<ReceptionDifferenceApproval>> {
    return apiRequest({ path: `${CASES_BASE}/${caseId}/approvals`, method: 'GET' })
  },
}
