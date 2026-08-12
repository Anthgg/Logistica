import { apiRequest, getCsrfToken } from '../../../api/api-client'
import type {
  QualityMeasurement,
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

export const qualityMeasurementsApi = {
  /** POST /quality-inspections/{inspectionId}/measurements */
  async create(inspectionId: string, data: Record<string, unknown>): Promise<QualityMeasurement> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `/logistics/quality-inspections/${inspectionId}/measurements`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },
}
