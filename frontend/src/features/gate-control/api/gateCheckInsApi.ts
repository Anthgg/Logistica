import { apiRequest, getCsrfToken } from '../../../api/api-client'
import type { PaginatedResponse } from '../../../types/logistics-resources'
import type {
  DockAssignmentPreparation,
  GateArrivalRecord,
  GateCheckIn,
  GateCheckInCapabilities,
  GateCheckInCreate,
  GateCheckInDetail,
  GateCheckInHistoryEvent,
  GateIntegrityStatus,
  GateCheckInListQuery,
  GateEntryDecisionValidation,
  GateResolveAppointmentRequest,
  ReceptionAppointmentSummary,
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

export const gateCheckInsApi = {
  // ── Resolución de cita ────────────────────────────────────────────────────────

  async resolveAppointment(payload: GateResolveAppointmentRequest): Promise<ReceptionAppointmentSummary | null> {
    const res = await apiRequest<{ item: ReceptionAppointmentSummary | null } | ReceptionAppointmentSummary>({
      path: '/logistics/gate-control/resolve-appointment',
      method: 'POST',
      headers: await withCsrf(),
      body: payload,
    })
    if (res && 'item' in res) return res.item ?? null
    return (res as ReceptionAppointmentSummary) ?? null
  },

  // ── Listado y detalle ─────────────────────────────────────────────────────────

  async list(query?: GateCheckInListQuery): Promise<PaginatedResponse<GateCheckIn>> {
    const params = new URLSearchParams()
    if (query?.search) params.set('search', query.search)
    if (query?.warehouse_id) params.set('warehouse_id', query.warehouse_id)
    if (query?.gate_id) params.set('gate_id', query.gate_id)
    if (query?.status) params.set('status', query.status)
    if (query?.decision_type) params.set('decision_type', query.decision_type)
    if (query?.supplier_id) params.set('supplier_id', query.supplier_id)
    if (query?.carrier_id) params.set('carrier_id', query.carrier_id)
    if (query?.plate) params.set('plate', query.plate)
    if (query?.date_from) params.set('date_from', query.date_from)
    if (query?.date_to) params.set('date_to', query.date_to)
    if (query?.with_failures) params.set('with_failures', 'true')
    if (query?.with_exceptions) params.set('with_exceptions', 'true')
    if (query?.with_broken_seal) params.set('with_broken_seal', 'true')
    if (query?.with_missing_documents) params.set('with_missing_documents', 'true')
    if (query?.walk_in_only) params.set('walk_in_only', 'true')
    if (query?.tab) params.set('tab', query.tab)
    if (query?.page) params.set('page', String(query.page))
    if (query?.page_size) params.set('page_size', String(query.page_size))
    const qs = params.toString()
    return apiRequest({ path: `${BASE}${qs ? `?${qs}` : ''}` })
  },

  async get(id: string): Promise<GateCheckInDetail> {
    return apiRequest({ path: `${BASE}/${id}` })
  },

  async create(payload: GateCheckInCreate): Promise<GateCheckIn> {
    return apiRequest({ path: BASE, method: 'POST', headers: withIdempotency(await withCsrf(), generateKey()), body: payload })
  },

  async createWalkIn(payload: { gate_id: string; plate?: string; carrier_id?: string }): Promise<GateCheckIn> {
    return apiRequest({ path: `${BASE}/walk-in`, method: 'POST', headers: withIdempotency(await withCsrf(), generateKey()), body: payload })
  },

  async recordArrival(id: string): Promise<GateArrivalRecord> {
    return apiRequest({ path: `${BASE}/${id}/record-arrival`, method: 'POST', headers: withIdempotency(await withCsrf(), generateKey()), body: {} })
  },

  async startVerification(id: string): Promise<GateCheckIn> {
    return apiRequest({ path: `${BASE}/${id}/start-verification`, method: 'POST', headers: await withCsrf(), body: {} })
  },

  async hold(id: string, reason: string, category?: string): Promise<GateCheckIn> {
    return apiRequest({ path: `${BASE}/${id}/hold`, method: 'POST', headers: await withCsrf(), body: { reason, category } })
  },

  async requestSupervisor(id: string, reason: string, urgency?: string): Promise<GateCheckIn> {
    return apiRequest({ path: `${BASE}/${id}/request-supervisor`, method: 'POST', headers: await withCsrf(), body: { reason, urgency } })
  },

  async resume(id: string): Promise<GateCheckIn> {
    return apiRequest({ path: `${BASE}/${id}/resume`, method: 'POST', headers: await withCsrf(), body: {} })
  },

  async cancel(id: string, reason: string): Promise<GateCheckIn> {
    return apiRequest({ path: `${BASE}/${id}/cancel`, method: 'POST', headers: await withCsrf(), body: { reason } })
  },

  async complete(id: string): Promise<GateCheckIn> {
    return apiRequest({ path: `${BASE}/${id}/complete`, method: 'POST', headers: withIdempotency(await withCsrf(), generateKey()), body: {} })
  },

  async getHistory(id: string): Promise<GateCheckInHistoryEvent[]> {
    const res = await apiRequest<{ items: GateCheckInHistoryEvent[] }>({ path: `${BASE}/${id}/history` })
    return res.items ?? []
  },

  async getCapabilities(id: string): Promise<GateCheckInCapabilities> {
    return apiRequest({ path: `${BASE}/${id}/capabilities` })
  },

  async getIntegrity(id: string): Promise<GateIntegrityStatus> {
    return apiRequest({ path: `${BASE}/${id}/integrity` })
  },

  async getDockAssignmentPreparation(id: string): Promise<DockAssignmentPreparation> {
    return apiRequest({ path: `${BASE}/${id}/dock-preparation` })
  },

  async validateEntryDecision(id: string): Promise<GateEntryDecisionValidation> {
    return apiRequest({ path: `${BASE}/${id}/validate-decision`, method: 'POST', headers: await withCsrf(), body: {} })
  },

  async authorizeEntry(id: string, idempotencyKey?: string): Promise<GateCheckIn> {
    return apiRequest({ path: `${BASE}/${id}/authorize-entry`, method: 'POST', headers: withIdempotency(await withCsrf(), idempotencyKey ?? generateKey()), body: {} })
  },

  async authorizeEntryWithObservations(id: string, payload: { conditions?: string; final_observation?: string }, idempotencyKey?: string): Promise<GateCheckIn> {
    return apiRequest({ path: `${BASE}/${id}/authorize-with-observations`, method: 'POST', headers: withIdempotency(await withCsrf(), idempotencyKey ?? generateKey()), body: payload })
  },

  async denyEntry(id: string, payload: { reason: string; reason_code?: string; instructions?: string }, idempotencyKey?: string): Promise<GateCheckIn> {
    return apiRequest({ path: `${BASE}/${id}/deny-entry`, method: 'POST', headers: withIdempotency(await withCsrf(), idempotencyKey ?? generateKey()), body: payload })
  },
}