import { apiRequest } from '../../../api/api-client'
import { getCsrfToken } from '../../../api/csrf'
import type {
  UnloadingOperation,
  UnloadingReadinessCheck,
  UnloadingCompletionCheck,
  UnloadingExpectedLoad,
  UnloadingPause,
  UnloadingSealOpening,
  UnloadingResponsibleAssignment,
  UnloadingEquipmentAssignment,
  StartUnloadingRequest,
  CreatePauseRequest,
  ResumeUnloadingRequest,
  AbortUnloadingRequest,
  CompleteUnloadingRequest,
  CreateSealOpeningRequest,
  AssignResponsibleRequest,
  WarehouseDockReadinessOverrideRequest,
  ReceivingScanPreparation,
  PaginatedResponse,
} from '../types/inbound-docks'

const BASE = '/logistics/unloading-operations'

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

export const unloadingOperationsApi = {
  async list(query: {
    warehouse_id?: string
    dock_id?: string
    assignment_id?: string
    status?: string
    page?: number
    page_size?: number
  } = {}): Promise<PaginatedResponse<UnloadingOperation>> {
    const params = new URLSearchParams()
    if (query.warehouse_id) params.set('warehouse_id', query.warehouse_id)
    if (query.dock_id) params.set('dock_id', query.dock_id)
    if (query.assignment_id) params.set('assignment_id', query.assignment_id)
    if (query.status) params.set('status', query.status)
    if (query.page != null) params.set('page', String(query.page))
    if (query.page_size != null) params.set('page_size', String(query.page_size))
    const qs = params.toString()
    return apiRequest<PaginatedResponse<UnloadingOperation>>({
      path: `${BASE}${qs ? `?${qs}` : ''}`,
      method: 'GET',
    })
  },

  async get(operationId: string): Promise<UnloadingOperation> {
    return apiRequest<UnloadingOperation>({
      path: `${BASE}/${operationId}`,
      method: 'GET',
    })
  },

  // ── Transiciones de estado ────────────────────────────────────────────────

  async start(operationId: string, _data: StartUnloadingRequest = {}): Promise<UnloadingOperation> {
    const idempotencyKey = _data.idempotency_key ?? generateKey()
    const csrf = await withCsrf()
    const headers = withIdempotency(csrf, idempotencyKey)
    return apiRequest<UnloadingOperation>({
      path: `${BASE}/${operationId}/start`,
      method: 'POST',
      headers,
      body: {},
    })
  },

  async pause(operationId: string, data: CreatePauseRequest): Promise<UnloadingOperation> {
    const idempotencyKey = data.idempotency_key ?? generateKey()
    const csrf = await withCsrf()
    const headers = withIdempotency(csrf, idempotencyKey)
    return apiRequest<UnloadingOperation>({
      path: `${BASE}/${operationId}/pause`,
      method: 'POST',
      headers,
      body: {
        reason: data.reason,
        severity: data.severity,
        comment: data.comment ?? null,
        evidence_file_id: data.evidence_file_id ?? null,
        responsible_informed_user_id: data.responsible_informed_user_id ?? null,
      },
    })
  },

  async resume(operationId: string, data: ResumeUnloadingRequest): Promise<UnloadingOperation> {
    const idempotencyKey = data.idempotency_key ?? generateKey()
    const csrf = await withCsrf()
    const headers = withIdempotency(csrf, idempotencyKey)
    return apiRequest<UnloadingOperation>({
      path: `${BASE}/${operationId}/resume`,
      method: 'POST',
      headers,
      body: {
        condition_resolved: data.condition_resolved,
        evidence_file_id: data.evidence_file_id ?? null,
      },
    })
  },

  async abort(operationId: string, data: AbortUnloadingRequest): Promise<UnloadingOperation> {
    const idempotencyKey = data.idempotency_key ?? generateKey()
    const csrf = await withCsrf()
    const headers = withIdempotency(csrf, idempotencyKey)
    return apiRequest<UnloadingOperation>({
      path: `${BASE}/${operationId}/abort`,
      method: 'POST',
      headers,
      body: {
        reason: data.reason,
        category: data.category,
        risk_level: data.risk_level,
        evidence_file_id: data.evidence_file_id ?? null,
        supervisor_user_id: data.supervisor_user_id ?? null,
        next_action: data.next_action,
      },
    })
  },

  async complete(operationId: string, _data: CompleteUnloadingRequest = {}): Promise<UnloadingOperation> {
    const idempotencyKey = _data.idempotency_key ?? generateKey()
    const csrf = await withCsrf()
    const headers = withIdempotency(csrf, idempotencyKey)
    return apiRequest<UnloadingOperation>({
      path: `${BASE}/${operationId}/complete`,
      method: 'POST',
      headers,
      body: {},
    })
  },

  // ── Readiness checks ──────────────────────────────────────────────────────

  async getReadinessChecks(operationId: string): Promise<UnloadingReadinessCheck[]> {
    const res = await apiRequest<{ items: UnloadingReadinessCheck[] } | UnloadingReadinessCheck[]>({
      path: `${BASE}/${operationId}/readiness-checks`,
      method: 'GET',
    })
    if (Array.isArray(res)) return res
    return res.items ?? []
  },

  async updateReadinessCheck(
    operationId: string,
    checkId: string,
    result: 'PASS' | 'PASS_WITH_OBSERVATION' | 'FAIL' | 'NOT_APPLICABLE',
    observation?: string | null,
    evidenceFileId?: string | null,
  ): Promise<UnloadingReadinessCheck> {
    const csrf = await withCsrf()
    return apiRequest<UnloadingReadinessCheck>({
      path: `${BASE}/${operationId}/readiness-checks`,
      method: 'POST',
      headers: csrf,
      body: {
        check_id: checkId,
        result,
        observation: observation ?? null,
        evidence_file_id: evidenceFileId ?? null,
      },
    })
  },

  async requestReadinessOverride(
    operationId: string,
    data: WarehouseDockReadinessOverrideRequest,
  ): Promise<UnloadingReadinessCheck> {
    const idempotencyKey = data.idempotency_key ?? generateKey()
    const csrf = await withCsrf()
    const headers = withIdempotency(csrf, idempotencyKey)
    return apiRequest<UnloadingReadinessCheck>({
      path: `${BASE}/${operationId}/readiness-checks/${data.check_id}/request-override`,
      method: 'POST',
      headers,
      body: {
        reason: data.reason,
        evidence_file_id: data.evidence_file_id ?? null,
        conditions: data.conditions ?? null,
      },
    })
  },

  async reviewReadinessOverride(
    operationId: string,
    checkId: string,
    approved: boolean,
    comment?: string | null,
  ): Promise<UnloadingReadinessCheck> {
    const idempotencyKey = generateKey()
    const csrf = await withCsrf()
    const headers = withIdempotency(csrf, idempotencyKey)
    const path = approved
      ? `${BASE}/${operationId}/readiness-checks/${checkId}/approve-override`
      : `${BASE}/${operationId}/readiness-checks/${checkId}/reject-override`
    return apiRequest<UnloadingReadinessCheck>({
      path,
      method: 'POST',
      headers,
      body: { comment: comment ?? null },
    })
  },

  // ── Completion checks ─────────────────────────────────────────────────────

  async getCompletionChecks(operationId: string): Promise<UnloadingCompletionCheck[]> {
    const res = await apiRequest<{ items: UnloadingCompletionCheck[] } | UnloadingCompletionCheck[]>({
      path: `${BASE}/${operationId}/completion-checks`,
      method: 'GET',
    })
    if (Array.isArray(res)) return res
    return res.items ?? []
  },

  async updateCompletionCheck(
    operationId: string,
    checkId: string,
    result: 'PASS' | 'PASS_WITH_OBSERVATION' | 'FAIL' | 'NOT_APPLICABLE',
    observation?: string | null,
    evidenceFileId?: string | null,
  ): Promise<UnloadingCompletionCheck> {
    const csrf = await withCsrf()
    return apiRequest<UnloadingCompletionCheck>({
      path: `${BASE}/${operationId}/completion-checks`,
      method: 'POST',
      headers: csrf,
      body: {
        check_id: checkId,
        result,
        observation: observation ?? null,
        evidence_file_id: evidenceFileId ?? null,
      },
    })
  },

  // ── Apertura de sello ─────────────────────────────────────────────────────

  async recordSealOpening(
    operationId: string,
    data: CreateSealOpeningRequest,
  ): Promise<UnloadingSealOpening> {
    const idempotencyKey = data.idempotency_key ?? generateKey()
    const csrf = await withCsrf()
    const headers = withIdempotency(csrf, idempotencyKey)
    return apiRequest<UnloadingSealOpening>({
      path: `${BASE}/${operationId}/seal-opening`,
      method: 'POST',
      headers,
      body: {
        observed_seal_number: data.observed_seal_number ?? null,
        result: data.result,
        observation: data.observation ?? null,
        witness_user_id: data.witness_user_id ?? null,
        photo_before_file_id: data.photo_before_file_id ?? null,
        photo_after_file_id: data.photo_after_file_id ?? null,
      },
    })
  },

  async getSealOpening(operationId: string): Promise<UnloadingSealOpening | null> {
    return apiRequest<UnloadingSealOpening | null>({
      path: `${BASE}/${operationId}/seal-opening`,
      method: 'GET',
    })
  },

  // ── Pausas ────────────────────────────────────────────────────────────────

  async getPauses(operationId: string): Promise<UnloadingPause[]> {
    const res = await apiRequest<{ items: UnloadingPause[] } | UnloadingPause[]>({
      path: `${BASE}/${operationId}/pauses`,
      method: 'GET',
    })
    if (Array.isArray(res)) return res
    return res.items ?? []
  },

  // ── Responsables ──────────────────────────────────────────────────────────

  async getResponsibles(operationId: string): Promise<UnloadingResponsibleAssignment[]> {
    const res = await apiRequest<{ items: UnloadingResponsibleAssignment[] } | UnloadingResponsibleAssignment[]>({
      path: `${BASE}/${operationId}/responsibles`,
      method: 'GET',
    })
    if (Array.isArray(res)) return res
    return res.items ?? []
  },

  async assignResponsible(
    operationId: string,
    data: AssignResponsibleRequest,
  ): Promise<UnloadingResponsibleAssignment> {
    const idempotencyKey = data.idempotency_key ?? generateKey()
    const csrf = await withCsrf()
    const headers = withIdempotency(csrf, idempotencyKey)
    return apiRequest<UnloadingResponsibleAssignment>({
      path: `${BASE}/${operationId}/responsibles`,
      method: 'POST',
      headers,
      body: {
        responsibility_type: data.responsibility_type,
        user_id: data.user_id ?? null,
        team_id: data.team_id ?? null,
        contractor_id: data.contractor_id ?? null,
        valid_until: data.valid_until ?? null,
        comment: data.comment ?? null,
      },
    })
  },

  async releaseResponsible(
    operationId: string,
    responsibleId: string,
  ): Promise<UnloadingResponsibleAssignment> {
    const idempotencyKey = generateKey()
    const csrf = await withCsrf()
    const headers = withIdempotency(csrf, idempotencyKey)
    return apiRequest<UnloadingResponsibleAssignment>({
      path: `${BASE}/${operationId}/responsibles/${responsibleId}/release`,
      method: 'POST',
      headers,
      body: {},
    })
  },

  // ── Equipo ────────────────────────────────────────────────────────────────

  async getEquipment(operationId: string): Promise<UnloadingEquipmentAssignment[]> {
    const res = await apiRequest<{ items: UnloadingEquipmentAssignment[] } | UnloadingEquipmentAssignment[]>({
      path: `${BASE}/${operationId}/equipment`,
      method: 'GET',
    })
    if (Array.isArray(res)) return res
    return res.items ?? []
  },

  async assignEquipment(
    operationId: string,
    equipmentType: string,
    equipmentIdentifier?: string | null,
  ): Promise<UnloadingEquipmentAssignment> {
    const idempotencyKey = generateKey()
    const csrf = await withCsrf()
    const headers = withIdempotency(csrf, idempotencyKey)
    return apiRequest<UnloadingEquipmentAssignment>({
      path: `${BASE}/${operationId}/equipment`,
      method: 'POST',
      headers,
      body: {
        equipment_type: equipmentType,
        equipment_identifier: equipmentIdentifier ?? null,
      },
    })
  },

  async releaseEquipment(
    operationId: string,
    equipmentId: string,
  ): Promise<UnloadingEquipmentAssignment> {
    const idempotencyKey = generateKey()
    const csrf = await withCsrf()
    const headers = withIdempotency(csrf, idempotencyKey)
    return apiRequest<UnloadingEquipmentAssignment>({
      path: `${BASE}/${operationId}/equipment/${equipmentId}/release`,
      method: 'POST',
      headers,
      body: {},
    })
  },

  // ── Datos complementarios ─────────────────────────────────────────────────

  async getExpectedLoad(operationId: string): Promise<UnloadingExpectedLoad> {
    return apiRequest<UnloadingExpectedLoad>({
      path: `${BASE}/${operationId}/receiving-preparation`,
      method: 'GET',
    })
  },

  async getReceivingPreparation(operationId: string): Promise<ReceivingScanPreparation> {
    return apiRequest<ReceivingScanPreparation>({
      path: `${BASE}/${operationId}/receiving-preparation`,
      method: 'GET',
    })
  },
}
