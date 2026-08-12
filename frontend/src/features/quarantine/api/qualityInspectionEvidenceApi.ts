import { apiRequest, getCsrfToken } from '../../../api/api-client'
import type {
  QualityInspectionEvidence,
} from '../types/quarantine'

function generateKey(): string {
  return typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

async function withCsrf(): Promise<Record<string, string>> {
  const token = await getCsrfToken()
  return { 'X-CSRF-Token': token }
}

export const qualityInspectionEvidenceApi = {
  /** POST /quality-inspections/{inspectionId}/evidence-links */
  async createLink(inspectionId: string, data: Record<string, unknown>): Promise<QualityInspectionEvidence> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `/logistics/quality-inspections/${inspectionId}/evidence-links`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** POST /quality-inspections/{inspectionId}/upload-session */
  async createUploadSession(inspectionId: string, data: Record<string, unknown>): Promise<{ upload_url?: string; file_id?: string; storage_key?: string } & Record<string, unknown>> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `/logistics/quality-inspections/${inspectionId}/upload-session`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** POST /quality-inspection-evidence/{evidenceId}/archive */
  async archive(evidenceId: string): Promise<QualityInspectionEvidence> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `/logistics/quality-inspection-evidence/${evidenceId}/archive`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: {},
    })
  },
}
