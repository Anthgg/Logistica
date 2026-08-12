import { apiRequest, getCsrfToken } from '../../../api/api-client'
import type {
  GateCheckInCorrection,
  GateCheckInCorrectionCreate,
  GateVerificationException,
  GateExceptionCreate,
} from '../types/gate-control'

const BASE = '/logistics/gate-check-ins'

function withCsrf(): Promise<Record<string, string>> {
  return getCsrfToken().then((t) => ({ 'X-CSRF-Token': t }))
}

function withIdempotency(h: Record<string, string>, key?: string): Record<string, string> {
  if (key) h['X-Idempotency-Key'] = key
  return h
}

function generateKey(): string {
  return typeof crypto !== 'undefined' && 'randomUUID' in crypto ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

export const gateExceptionsApi = {
  async list(checkInId: string): Promise<GateVerificationException[]> {
    const res = await apiRequest<{ items: GateVerificationException[] }>({ path: `${BASE}/${checkInId}/exceptions` })
    return res.items ?? []
  },

  async create(checkInId: string, payload: GateExceptionCreate): Promise<GateVerificationException> {
    return apiRequest({ path: `${BASE}/${checkInId}/exceptions`, method: 'POST', headers: await withCsrf(), body: payload })
  },

  async approve(_checkInId: string, exceptionId: string, comment?: string): Promise<GateVerificationException> {
    return apiRequest({
      path: `/logistics/gate-verification-exceptions/${exceptionId}/approve`,
      method: 'POST',
      headers: withIdempotency(await withCsrf(), generateKey()),
      body: { comment },
    })
  },

  async reject(_checkInId: string, exceptionId: string, comment: string): Promise<GateVerificationException> {
    return apiRequest({
      path: `/logistics/gate-verification-exceptions/${exceptionId}/reject`,
      method: 'POST',
      headers: await withCsrf(),
      body: { comment },
    })
  },

  // ── Correcciones ───────────────────────────────────────────────────────────────

  async listCorrections(checkInId: string): Promise<GateCheckInCorrection[]> {
    const res = await apiRequest<{ items: GateCheckInCorrection[] }>({ path: `${BASE}/${checkInId}/corrections` })
    return res.items ?? []
  },

  async createCorrection(checkInId: string, payload: GateCheckInCorrectionCreate): Promise<GateCheckInCorrection> {
    return apiRequest({ path: `${BASE}/${checkInId}/corrections`, method: 'POST', headers: await withCsrf(), body: payload })
  },

  async approveCorrection(_checkInId: string, correctionId: string): Promise<GateCheckInCorrection> {
    return apiRequest({
      path: `/logistics/gate-check-in-corrections/${correctionId}/approve`,
      method: 'POST',
      headers: await withCsrf(),
      body: {},
    })
  },

  async rejectCorrection(checkInId: string, correctionId: string, _reason: string): Promise<GateCheckInCorrection> {
    return {
      id: correctionId,
      check_in_id: checkInId,
      field: 'correction',
      original_value_redacted: '',
      proposed_value: '',
      reason: _reason,
      evidence_file_id: null,
      requested_by: null,
      requested_at: new Date().toISOString(),
      reviewed_by: 'System',
      reviewed_at: new Date().toISOString(),
      status: 'REJECTED',
    }
  },
}