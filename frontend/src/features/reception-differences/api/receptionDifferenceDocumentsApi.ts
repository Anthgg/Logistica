import { apiRequest, getCsrfToken } from '../../../api/api-client'
import type {
  ReceptionDifferenceDocument,
  ReceptionDifferencePackage,
  IssueDocumentRequest,
  CancelDocumentRequest,
  ReprintDocumentRequest,
} from '../types/reception-differences'

const CASES_BASE = '/logistics/reception-difference-cases'
const PACKAGES_BASE = '/logistics/reception-difference-packages'

function generateKey(): string {
  return typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

async function withCsrf(): Promise<Record<string, string>> {
  const token = await getCsrfToken()
  return { 'X-CSRF-Token': token }
}

export const receptionDifferenceDocumentsApi = {
  // ── Documents (8) ─────────────────────────────────────────────────────────────

  /** GET /reception-difference-cases/{case_id}/preview */
  async preview(caseId: string): Promise<{ pdf_url: string; content: string }> {
    return apiRequest({ path: `${CASES_BASE}/${caseId}/preview`, method: 'GET' })
  },

  /** POST /reception-difference-cases/{case_id}/issue-document */
  async issue(caseId: string, data: IssueDocumentRequest): Promise<ReceptionDifferenceDocument> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${CASES_BASE}/${caseId}/issue-document`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** GET /reception-difference-cases/{case_id}/document */
  async getDocument(caseId: string): Promise<ReceptionDifferenceDocument> {
    return apiRequest({ path: `${CASES_BASE}/${caseId}/document`, method: 'GET' })
  },

  /** POST /reception-difference-cases/{case_id}/cancel-document */
  async cancel(caseId: string, data: CancelDocumentRequest): Promise<ReceptionDifferenceDocument> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${CASES_BASE}/${caseId}/cancel-document`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** POST /reception-difference-cases/{case_id}/reprint */
  async reprint(caseId: string, data: ReprintDocumentRequest): Promise<{ reprint_id: string; pdf_url: string }> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${CASES_BASE}/${caseId}/reprint`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** POST /reception-difference-cases/{case_id}/package */
  async createPackage(caseId: string): Promise<ReceptionDifferencePackage> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${CASES_BASE}/${caseId}/package`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: {},
    })
  },

  /** GET /reception-difference-packages/{package_id} */
  async getPackage(packageId: string): Promise<ReceptionDifferencePackage> {
    return apiRequest({ path: `${PACKAGES_BASE}/${packageId}`, method: 'GET' })
  },

  /** GET /reception-difference-packages/{package_id}/download */
  async downloadPackage(packageId: string): Promise<{ download_url: string; expires_at: string }> {
    return apiRequest({ path: `${PACKAGES_BASE}/${packageId}/download`, method: 'GET' })
  },
}
