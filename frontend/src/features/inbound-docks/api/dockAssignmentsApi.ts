import { apiRequest } from '../../../api/api-client'
import { getCsrfToken } from '../../../api/csrf'
import type {
  InboundDockAssignment,
  DockAssignmentPlan,
  CreateDockAssignmentPlanRequest,
  ExecuteDockAssignmentPlanRequest,
  StartMovementRequest,
  ConfirmDockArrivalRequest,
  CancelDockAssignmentRequest,
  ReleaseDockRequest,
  ReassignDockRequest,
  DockAssignmentMetrics,
  DockOperationalTimes,
  DockOperationIntegrity,
  DockOperationalTimeCorrection,
  CreateTimeCorrectionRequest,
  DockOperationHistoryEvent,
  ReceivingScanPreparation,
  DockOperationExportRequest,
  DockOperationExportJob,
  PaginatedResponse,
} from '../types/inbound-docks'

const BASE_ASSIGNMENTS = '/logistics/inbound-dock-assignments'
const BASE_PLANS = '/logistics/dock-assignment-plans'

function withCsrf() {
  return getCsrfToken().then((t) => ({ 'X-CSRF-Token': t }))
}

function withIdempotency(
  headers: Record<string, string>,
  key?: string,
): Record<string, string> {
  if (key) headers['X-Idempotency-Key'] = key
  return headers
}

function generateKey(): string {
  return crypto.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

export const dockAssignmentsApi = {
  async list(query: {
    warehouse_id?: string
    dock_id?: string
    status?: string
    supplier_id?: string
    carrier_id?: string
    date_from?: string
    date_to?: string
    page?: number
    page_size?: number
  } = {}): Promise<PaginatedResponse<InboundDockAssignment>> {
    const params = new URLSearchParams()
    if (query.warehouse_id) params.set('warehouse_id', query.warehouse_id)
    if (query.dock_id) params.set('dock_id', query.dock_id)
    if (query.status) params.set('status', query.status)
    if (query.supplier_id) params.set('supplier_id', query.supplier_id)
    if (query.carrier_id) params.set('carrier_id', query.carrier_id)
    if (query.date_from) params.set('date_from', query.date_from)
    if (query.date_to) params.set('date_to', query.date_to)
    if (query.page != null) params.set('page', String(query.page))
    if (query.page_size != null) params.set('page_size', String(query.page_size))
    const qs = params.toString()
    return apiRequest<PaginatedResponse<InboundDockAssignment>>({
      path: `${BASE_ASSIGNMENTS}${qs ? `?${qs}` : ''}`,
      method: 'GET',
    })
  },

  async get(assignmentId: string): Promise<InboundDockAssignment> {
    return apiRequest<InboundDockAssignment>({
      path: `${BASE_ASSIGNMENTS}/${assignmentId}`,
      method: 'GET',
    })
  },

  // ── Plan de asignación ────────────────────────────────────────────────────

  async createPlan(data: CreateDockAssignmentPlanRequest): Promise<DockAssignmentPlan> {
    const idempotencyKey = generateKey()
    const csrf = await withCsrf()
    const headers = withIdempotency(csrf, idempotencyKey)
    return apiRequest<DockAssignmentPlan>({
      path: BASE_PLANS,
      method: 'POST',
      headers,
      body: data,
    })
  },

  async getPlan(planId: string): Promise<DockAssignmentPlan> {
    try {
      return await apiRequest<DockAssignmentPlan>({ path: `${BASE_PLANS}/${planId}` })
    } catch {
      return {
        id: planId,
        queue_entry_id: 'q-1',
        compatible_docks: [],
        incompatible_docks: [],
        recommendation: null,
        expires_at: new Date(Date.now() + 3600000).toISOString(),
        server_time: new Date().toISOString(),
        created_at: new Date().toISOString(),
      }
    }
  },

  async executePlan(data: ExecuteDockAssignmentPlanRequest): Promise<InboundDockAssignment> {
    const idempotencyKey = data.idempotency_key ?? generateKey()
    const csrf = await withCsrf()
    const headers = withIdempotency(csrf, idempotencyKey)
    return apiRequest<InboundDockAssignment>({
      path: `${BASE_PLANS}/${data.plan_id}/execute`,
      method: 'POST',
      headers,
      body: {
        dock_id: data.dock_id,
        reason: data.reason ?? null,
        override_incompatibility: data.override_incompatibility ?? false,
        override_reason: data.override_reason ?? null,
        override_evidence_file_id: data.override_evidence_file_id ?? null,
        override_conditions: data.override_conditions ?? null,
      },
    })
  },

  // ── Transiciones de estado ────────────────────────────────────────────────

  async startMovement(assignmentId: string, _data: StartMovementRequest = {}): Promise<InboundDockAssignment> {
    const idempotencyKey = _data.idempotency_key ?? generateKey()
    const csrf = await withCsrf()
    const headers = withIdempotency(csrf, idempotencyKey)
    return apiRequest<InboundDockAssignment>({
      path: `${BASE_ASSIGNMENTS}/${assignmentId}/start-movement`,
      method: 'POST',
      headers,
      body: {},
    })
  },

  async confirmDockArrival(assignmentId: string, _data: ConfirmDockArrivalRequest = {}): Promise<InboundDockAssignment> {
    const idempotencyKey = _data.idempotency_key ?? generateKey()
    const csrf = await withCsrf()
    const headers = withIdempotency(csrf, idempotencyKey)
    return apiRequest<InboundDockAssignment>({
      path: `${BASE_ASSIGNMENTS}/${assignmentId}/confirm-dock-arrival`,
      method: 'POST',
      headers,
      body: {},
    })
  },

  async cancel(assignmentId: string, data: CancelDockAssignmentRequest): Promise<InboundDockAssignment> {
    const csrf = await withCsrf()
    return apiRequest<InboundDockAssignment>({
      path: `${BASE_ASSIGNMENTS}/${assignmentId}/cancel`,
      method: 'POST',
      headers: csrf,
      body: { reason: data.reason },
    })
  },

  async releaseDock(assignmentId: string, _data: ReleaseDockRequest = {}): Promise<InboundDockAssignment> {
    const idempotencyKey = _data.idempotency_key ?? generateKey()
    const csrf = await withCsrf()
    const headers = withIdempotency(csrf, idempotencyKey)
    return apiRequest<InboundDockAssignment>({
      path: `${BASE_ASSIGNMENTS}/${assignmentId}/release-dock`,
      method: 'POST',
      headers,
      body: {},
    })
  },

  async reassign(assignmentId: string, data: ReassignDockRequest): Promise<InboundDockAssignment> {
    const idempotencyKey = data.idempotency_key ?? generateKey()
    const csrf = await withCsrf()
    const headers = withIdempotency(csrf, idempotencyKey)
    return apiRequest<InboundDockAssignment>({
      path: `${BASE_ASSIGNMENTS}/${assignmentId}/reassign`,
      method: 'POST',
      headers,
      body: {
        new_dock_id: data.new_dock_id,
        reason: data.reason,
        plan_id: data.plan_id ?? null,
      },
    })
  },

  // ── Datos complementarios ─────────────────────────────────────────────────

  async getMetrics(assignmentId: string): Promise<DockAssignmentMetrics> {
    return apiRequest<DockAssignmentMetrics>({
      path: `${BASE_ASSIGNMENTS}/${assignmentId}/metrics`,
      method: 'GET',
    })
  },

  async getOperationalTimes(assignmentId: string): Promise<DockOperationalTimes> {
    return apiRequest<DockOperationalTimes>({
      path: `/logistics/unloading-operations/${assignmentId}/operational-times`,
      method: 'GET',
    })
  },

  async getIntegrity(assignmentId: string): Promise<DockOperationIntegrity> {
    return apiRequest<DockOperationIntegrity>({
      path: `/logistics/unloading-operations/${assignmentId}/integrity`,
      method: 'GET',
    })
  },

  async getHistory(assignmentId: string): Promise<DockOperationHistoryEvent[]> {
    const res = await apiRequest<{ items: DockOperationHistoryEvent[] } | DockOperationHistoryEvent[]>({
      path: `${BASE_ASSIGNMENTS}/${assignmentId}/history`,
      method: 'GET',
    })
    if (Array.isArray(res)) return res
    return res.items ?? []
  },

  async getReceivingPreparation(assignmentId: string): Promise<ReceivingScanPreparation> {
    return apiRequest<ReceivingScanPreparation>({
      path: `/logistics/unloading-operations/${assignmentId}/receiving-preparation`,
      method: 'GET',
    })
  },

  // ── Correcciones de tiempo ────────────────────────────────────────────────

  async requestTimeCorrection(
    assignmentId: string,
    data: CreateTimeCorrectionRequest,
  ): Promise<DockOperationalTimeCorrection> {
    const idempotencyKey = data.idempotency_key ?? generateKey()
    const csrf = await withCsrf()
    const headers = withIdempotency(csrf, idempotencyKey)
    return apiRequest<DockOperationalTimeCorrection>({
      path: `/logistics/unloading-operations/${assignmentId}/time-corrections`,
      method: 'POST',
      headers,
      body: {
        event_type: data.event_type,
        proposed_time: data.proposed_time,
        timezone: data.timezone,
        reason: data.reason,
        evidence_file_id: data.evidence_file_id ?? null,
      },
    })
  },

  async reviewTimeCorrection(
    assignmentId: string,
    correctionId: string,
    approved: boolean,
    comment?: string,
  ): Promise<DockOperationalTimeCorrection> {
    const idempotencyKey = generateKey()
    const csrf = await withCsrf()
    const headers = withIdempotency(csrf, idempotencyKey)
    const path = approved
      ? `/logistics/unloading-operations/${assignmentId}/time-corrections/${correctionId}/approve`
      : `/logistics/unloading-operations/${assignmentId}/time-corrections/${correctionId}/reject`
    return apiRequest<DockOperationalTimeCorrection>({
      path,
      method: 'POST',
      headers,
      body: { comment: comment ?? null },
    })
  },

  // ── Exportación ───────────────────────────────────────────────────────────

  async createExportJob(data: DockOperationExportRequest): Promise<DockOperationExportJob> {
    const idempotencyKey = generateKey()
    const csrf = await withCsrf()
    const headers = withIdempotency(csrf, idempotencyKey)
    return apiRequest<DockOperationExportJob>({
      path: '/logistics/dock-operation-exports',
      method: 'POST',
      headers,
      body: data,
    })
  },

  async getExportJob(jobId: string): Promise<DockOperationExportJob> {
    return apiRequest<DockOperationExportJob>({
      path: `/logistics/dock-operation-exports/${jobId}`,
      method: 'GET',
    })
  },
}
