import { apiRequest, getCsrfToken } from '../../../api/api-client'
import type {
  GateCheckResult,
  GateCheckResultInput,
  GateDriverInspection,
  GatePresentedDocument,
  GateSealInspection,
  GateVehicleInspection,
  GateVerificationProgress,
} from '../types/gate-control'

const BASE = '/logistics/gate-check-ins'

function withCsrf(): Promise<Record<string, string>> {
  return getCsrfToken().then((t) => ({ 'X-CSRF-Token': t }))
}

export const gateInspectionsApi = {
  // ── Vehículo ─────────────────────────────────────────────────────────────────

  async getVehicleInspection(checkInId: string): Promise<GateVehicleInspection | null> {
    return apiRequest({ path: `${BASE}/${checkInId}/vehicle-inspection` })
  },

  async createVehicleInspection(checkInId: string, payload: Partial<GateVehicleInspection>): Promise<GateVehicleInspection> {
    return apiRequest({ path: `${BASE}/${checkInId}/vehicle-inspection`, method: 'POST', headers: await withCsrf(), body: payload })
  },

  async updateVehicleInspection(checkInId: string, payload: Partial<GateVehicleInspection>): Promise<GateVehicleInspection> {
    return apiRequest({ path: `${BASE}/${checkInId}/vehicle-inspection`, method: 'POST', headers: await withCsrf(), body: payload })
  },

  // ── Conductor ────────────────────────────────────────────────────────────────

  async getDriverInspection(checkInId: string): Promise<GateDriverInspection | null> {
    return apiRequest({ path: `${BASE}/${checkInId}/driver-inspection` })
  },

  async createDriverInspection(checkInId: string, payload: Partial<GateDriverInspection>): Promise<GateDriverInspection> {
    return apiRequest({ path: `${BASE}/${checkInId}/driver-inspection`, method: 'POST', headers: await withCsrf(), body: payload })
  },

  async updateDriverInspection(checkInId: string, payload: Partial<GateDriverInspection>): Promise<GateDriverInspection> {
    return apiRequest({ path: `${BASE}/${checkInId}/driver-inspection`, method: 'POST', headers: await withCsrf(), body: payload })
  },

  // ── Documentos presentados ───────────────────────────────────────────────────

  async listPresentedDocuments(checkInId: string): Promise<GatePresentedDocument[]> {
    const res = await apiRequest<{ items: GatePresentedDocument[] } | GatePresentedDocument[]>({ path: `${BASE}/${checkInId}/documents` })
    if (Array.isArray(res)) return res
    return (res && 'items' in res ? res.items : []) ?? []
  },

  async createPresentedDocument(checkInId: string, payload: Partial<GatePresentedDocument>): Promise<GatePresentedDocument> {
    return apiRequest({ path: `${BASE}/${checkInId}/documents`, method: 'POST', headers: await withCsrf(), body: payload })
  },

  async updatePresentedDocument(checkInId: string, _docId: string, payload: Partial<GatePresentedDocument>): Promise<GatePresentedDocument> {
    return apiRequest({ path: `${BASE}/${checkInId}/documents`, method: 'POST', headers: await withCsrf(), body: payload })
  },

  // ── Precinto ─────────────────────────────────────────────────────────────────

  async getSealInspection(checkInId: string): Promise<GateSealInspection | null> {
    return apiRequest({ path: `${BASE}/${checkInId}/seal-inspection` })
  },

  async createSealInspection(checkInId: string, payload: Partial<GateSealInspection>): Promise<GateSealInspection> {
    return apiRequest({ path: `${BASE}/${checkInId}/seal-inspection`, method: 'POST', headers: await withCsrf(), body: payload })
  },

  async updateSealInspection(checkInId: string, payload: Partial<GateSealInspection>): Promise<GateSealInspection> {
    return apiRequest({ path: `${BASE}/${checkInId}/seal-inspection`, method: 'POST', headers: await withCsrf(), body: payload })
  },

  // ── Checklist ───────────────────────────────────────────────────────────────

  async listCheckResults(checkInId: string): Promise<GateCheckResult[]> {
    const res = await apiRequest<{ items: GateCheckResult[] } | GateCheckResult[]>({ path: `${BASE}/${checkInId}/check-results` })
    if (Array.isArray(res)) return res
    return (res && 'items' in res ? res.items : []) ?? []
  },

  async createCheckResult(checkInId: string, payload: GateCheckResultInput): Promise<GateCheckResult> {
    return apiRequest({ path: `${BASE}/${checkInId}/check-results`, method: 'POST', headers: await withCsrf(), body: payload })
  },

  async updateCheckResult(checkInId: string, _checkId: string, payload: Partial<GateCheckResultInput>): Promise<GateCheckResult> {
    return apiRequest({ path: `${BASE}/${checkInId}/check-results`, method: 'POST', headers: await withCsrf(), body: payload })
  },

  async getProgress(checkInId: string): Promise<GateVerificationProgress> {
    try {
      const caps = await apiRequest<{ progress?: GateVerificationProgress }>({ path: `${BASE}/${checkInId}/capabilities` })
      return caps.progress ?? {
        total_checks: 0,
        completed: 0,
        pending: 0,
        failed: 0,
        blocking: 0,
        warnings: 0,
        evidence_pending: 0,
        exceptions_pending: 0,
        can_proceed_to_decision: true,
      }
    } catch {
      return {
        total_checks: 0,
        completed: 0,
        pending: 0,
        failed: 0,
        blocking: 0,
        warnings: 0,
        evidence_pending: 0,
        exceptions_pending: 0,
        can_proceed_to_decision: true,
      }
    }
  },
}