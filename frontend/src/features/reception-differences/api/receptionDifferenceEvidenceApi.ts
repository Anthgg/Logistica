import { apiRequest, getCsrfToken } from '../../../api/api-client'
import type {
  ReceptionDifferenceEvidence,
  LinkEvidenceToCaseRequest,
  CreatePhotoUploadSessionRequest,
  PaginatedResponse,
} from '../types/reception-differences'

const CASES_BASE = '/logistics/reception-difference-cases'
const EVIDENCE_BASE = '/logistics/reception-difference-evidence'

function generateKey(): string {
  return typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

async function withCsrf(): Promise<Record<string, string>> {
  const token = await getCsrfToken()
  return { 'X-CSRF-Token': token }
}

export const receptionDifferenceEvidenceApi = {
  // ── Evidence (5 case-level + 2 item-level) ────────────────────────────────────

  /** GET /reception-difference-cases/{case_id}/evidence */
  async list(caseId: string, page = 1, pageSize = 50): Promise<PaginatedResponse<ReceptionDifferenceEvidence>> {
    return apiRequest({ path: `${CASES_BASE}/${caseId}/evidence?page=${page}&page_size=${pageSize}`, method: 'GET' })
  },

  /** POST /reception-difference-cases/{case_id}/evidence-links */
  async link(caseId: string, data: LinkEvidenceToCaseRequest): Promise<ReceptionDifferenceEvidence> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${CASES_BASE}/${caseId}/evidence-links`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** POST /reception-difference-cases/{case_id}/photo-upload-sessions */
  async createPhotoSession(caseId: string, data: CreatePhotoUploadSessionRequest): Promise<{ upload_session_id: string; target_url: string; headers: Record<string, string>; method: string; expires_at: string }> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${CASES_BASE}/${caseId}/photo-upload-sessions`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** POST /reception-difference-items/{item_id}/photo-upload-sessions */
  async createItemPhotoSession(itemId: string, data: CreatePhotoUploadSessionRequest): Promise<{ upload_session_id: string; target_url: string; headers: Record<string, string>; method: string; expires_at: string }> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `/logistics/reception-difference-items/${itemId}/photo-upload-sessions`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** POST /reception-difference-evidence/{evidence_link_id}/archive */
  async archive(evidenceLinkId: string): Promise<void> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${EVIDENCE_BASE}/${evidenceLinkId}/archive`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: {},
    })
  },
}
