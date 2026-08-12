import { apiRequest, getCsrfToken } from '../../../api/api-client'

const BASE = '/logistics/quality-inspection-plans'

function generateKey(): string {
  return typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

async function withCsrf(): Promise<Record<string, string>> {
  const token = await getCsrfToken()
  return { 'X-CSRF-Token': token }
}

export interface QualityPlanReferenceFile {
  reference_file_id: string
  plan_id: string
  filename: string
  content_type: string
  size_bytes: number
  purpose: string
  description: string | null
  uploaded_by: string
  created_at: string
}

export interface CreateQualityPlanReferenceFileRequest {
  filename: string
  content_type: string
  purpose: string
  description?: string
}

export const qualityReferenceFilesApi = {
  /** GET /quality-inspection-plans/{planId}/reference-files */
  async list(planId: string): Promise<QualityPlanReferenceFile[]> {
    return apiRequest({ path: `${BASE}/${planId}/reference-files`, method: 'GET' })
  },

  /** POST /quality-inspection-plans/{planId}/reference-files */
  async create(planId: string, data: CreateQualityPlanReferenceFileRequest): Promise<QualityPlanReferenceFile> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${planId}/reference-files`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** DELETE /quality-inspection-plans/reference-files/{referenceFileId} */
  async delete(referenceFileId: string): Promise<void> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/reference-files/${referenceFileId}`,
      method: 'DELETE',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
    })
  },
}
