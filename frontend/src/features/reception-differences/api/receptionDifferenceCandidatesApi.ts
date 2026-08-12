import { apiRequest, getCsrfToken } from '../../../api/api-client'
import type {
  ReceptionDifferenceCandidate,
  AcknowledgeCandidateRequest,
  DismissCandidateRequest,
  PrepareForPhase040Request,
  FormalizeCandidatesRequest,
  ReceptionDifferenceItem,
} from '../types/reception-differences'

const CASES_BASE = '/logistics/reception-difference-cases'
const CANDIDATES_BASE = '/logistics/reception-difference-candidates'

function generateKey(): string {
  return typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

async function withCsrf(): Promise<Record<string, string>> {
  const token = await getCsrfToken()
  return { 'X-CSRF-Token': token }
}

export const receptionDifferenceCandidatesApi = {
  // ── Candidate Management (4) ──────────────────────────────────────────────────

  /** GET /reception-difference-candidates/{candidate_id} */
  async get(candidateId: string): Promise<ReceptionDifferenceCandidate> {
    return apiRequest({ path: `${CANDIDATES_BASE}/${candidateId}`, method: 'GET' })
  },

  /** POST /reception-difference-candidates/{candidate_id}/acknowledge */
  async acknowledge(candidateId: string, data?: AcknowledgeCandidateRequest): Promise<ReceptionDifferenceCandidate> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${CANDIDATES_BASE}/${candidateId}/acknowledge`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data ?? {},
    })
  },

  /** POST /reception-difference-candidates/{candidate_id}/dismiss */
  async dismiss(candidateId: string, data: DismissCandidateRequest): Promise<ReceptionDifferenceCandidate> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${CANDIDATES_BASE}/${candidateId}/dismiss`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** POST /reception-difference-candidates/{candidate_id}/prepare-for-phase-040 */
  async prepareForPhase040(candidateId: string, data?: PrepareForPhase040Request): Promise<ReceptionDifferenceCandidate> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${CANDIDATES_BASE}/${candidateId}/prepare-for-phase-040`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data ?? {},
    })
  },

  // ── Formalization (2) ─────────────────────────────────────────────────────────

  /** POST /reception-difference-cases/{case_id}/formalize-candidates */
  async formalizeCandidates(caseId: string, data: FormalizeCandidatesRequest): Promise<ReceptionDifferenceItem[]> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${CASES_BASE}/${caseId}/formalize-candidates`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** POST /reception-difference-candidates/{candidate_id}/formalize */
  async formalize(candidateId: string): Promise<ReceptionDifferenceItem> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${CANDIDATES_BASE}/${candidateId}/formalize`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: {},
    })
  },
}
