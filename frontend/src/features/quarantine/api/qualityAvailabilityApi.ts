import { apiRequest } from '../../../api/api-client'
import type {
  QualityAvailabilityRecord,
} from '../types/quarantine'

function buildQuery(params: Record<string, unknown>): string {
  const entries: [string, string][] = []
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null) continue
    if (Array.isArray(v)) {
      for (const item of v) entries.push([k, String(item)])
    } else {
      entries.push([k, String(v)])
    }
  }
  return entries.length ? `?${new URLSearchParams(entries).toString()}` : ''
}

export const qualityAvailabilityApi = {
  /** GET /quality-availability */
  async list(query?: Record<string, unknown>): Promise<QualityAvailabilityRecord[]> {
    return apiRequest({ path: `/logistics/quality-availability${query ? buildQuery(query) : ''}`, method: 'GET' })
  },
}
