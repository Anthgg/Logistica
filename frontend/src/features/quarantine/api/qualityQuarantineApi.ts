import { apiRequest, getCsrfToken } from '../../../api/api-client'
import type {
  PutawayPreparation,
  FutureInventoryMovementPreparation,
  FutureInventoryBalancePreparation,
  FutureTraceabilityPreparation,
  CreateQuarantineCaseRequest,
  QualityReinspectionRequest,
  QuarantinePlacement,
} from '../types/quarantine'
import type {
  MaterializeQualityInspectionRequestApi,
  QualityDecisionApi,
  QualityDecisionRequestApi,
  QualityInspectionDetailApi,
  QualityIntegrityApi,
  QualityQuarantineCaseDetailApi,
  QualityQuarantineCaseSummaryApi,
  QualityRejectionApi,
  QualityRejectionRequestApi,
  QualityReleaseApi,
  QualityReleaseRequestApi,
} from '../types/phase042-api'

const BASE = '/logistics/quality-quarantine-cases'

function generateKey(): string {
  return typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

async function withCsrf(): Promise<Record<string, string>> {
  const token = await getCsrfToken()
  return { 'X-CSRF-Token': token }
}

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

export const qualityQuarantineApi = {
  /** GET /quality-quarantine-cases */
  async listCases(query?: Record<string, unknown>): Promise<QualityQuarantineCaseSummaryApi[]> {
    return apiRequest({ path: `${BASE}${query ? buildQuery(query) : ''}`, method: 'GET' })
  },

  /** POST /quality-quarantine-cases */
  async createCase(data: CreateQuarantineCaseRequest): Promise<QualityQuarantineCaseDetailApi> {
    const csrf = await withCsrf()
    return apiRequest({
      path: BASE,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** GET /quality-quarantine-cases/{caseId} */
  async getCase(caseId: string): Promise<QualityQuarantineCaseDetailApi> {
    return apiRequest({ path: `${BASE}/${caseId}`, method: 'GET' })
  },

  /** POST /quality-quarantine-cases/{caseId}/activate */
  async activateCase(caseId: string): Promise<{ case_id: string; status: string }> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${caseId}/activate`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: {},
    })
  },

  /** POST /quality-quarantine-cases/{caseId}/close */
  async closeCase(caseId: string): Promise<{ case_id: string; status: string }> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${caseId}/close`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: {},
    })
  },

  /** POST /quality-quarantine-cases/{caseId}/materialize-inspection */
  async materializeInspection(caseId: string, data: MaterializeQualityInspectionRequestApi): Promise<QualityInspectionDetailApi> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${caseId}/materialize-inspection`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** GET /quality-quarantine-cases/{caseId}/decisions */
  async listDecisions(caseId: string): Promise<QualityDecisionApi[]> {
    return apiRequest({ path: `${BASE}/${caseId}/decisions`, method: 'GET' })
  },

  /** POST /quality-quarantine-cases/{caseId}/decisions */
  async createDecision(caseId: string, data: QualityDecisionRequestApi): Promise<QualityDecisionApi> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${caseId}/decisions`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** POST /quality-disposition-decisions/{decisionId}/approve */
  async approveDecision(decisionId: string): Promise<{ decision_id: string; status: string }> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `/logistics/quality-disposition-decisions/${decisionId}/approve`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: {},
    })
  },

  /** POST /quarantine-release-authorizations/{releaseId}/execute */
  async executeRelease(releaseId: string): Promise<{ release_id: string; status: string }> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `/logistics/quarantine-release-authorizations/${releaseId}/execute`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: {},
    })
  },

  /** POST /quarantine-rejection-authorizations/{rejectionId}/execute */
  async executeRejection(rejectionId: string): Promise<{ rejection_id: string; status: string }> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `/logistics/quarantine-rejection-authorizations/${rejectionId}/execute`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: {},
    })
  },

  /** GET /quality-quarantine-cases/{caseId}/release-authorizations */
  async listReleaseAuthorizations(caseId: string): Promise<QualityReleaseApi[]> {
    return apiRequest({ path: `${BASE}/${caseId}/release-authorizations`, method: 'GET' })
  },

  /** POST /quality-quarantine-cases/{caseId}/release-authorizations */
  async createReleaseAuthorization(caseId: string, data: QualityReleaseRequestApi): Promise<QualityReleaseApi> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${caseId}/release-authorizations`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** GET /quality-quarantine-cases/{caseId}/rejection-authorizations */
  async listRejectionAuthorizations(caseId: string): Promise<QualityRejectionApi[]> {
    return apiRequest({ path: `${BASE}/${caseId}/rejection-authorizations`, method: 'GET' })
  },

  /** POST /quality-quarantine-cases/{caseId}/rejection-authorizations */
  async createRejectionAuthorization(caseId: string, data: QualityRejectionRequestApi): Promise<QualityRejectionApi> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${caseId}/rejection-authorizations`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** POST /quality-quarantine-placements/{placementId}/confirm */
  async confirmPlacement(placementId: string): Promise<QuarantinePlacement> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `/logistics/quality-quarantine/placements/${placementId}/confirm`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: {},
    })
  },

  /** POST /quality-quarantine-cases/{caseId}/request-reinspection */
  async requestReinspection(caseId: string, data?: Record<string, unknown>): Promise<QualityReinspectionRequest> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${caseId}/request-reinspection`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data ?? {},
    })
  },

  /** GET /quality-quarantine-cases/{caseId}/putaway-preparation */
  async getPutawayPreparation(caseId: string): Promise<PutawayPreparation> {
    return apiRequest({ path: `${BASE}/${caseId}/putaway-preparation`, method: 'GET' })
  },

  /** GET /quality-quarantine-cases/{caseId}/future-movement-preparation */
  async getFutureMovementPreparation(caseId: string): Promise<FutureInventoryMovementPreparation> {
    return apiRequest({ path: `${BASE}/${caseId}/future-movement-preparation`, method: 'GET' })
  },

  /** GET /quality-quarantine-cases/{caseId}/future-balance-preparation */
  async getFutureBalancePreparation(caseId: string): Promise<FutureInventoryBalancePreparation> {
    return apiRequest({ path: `${BASE}/${caseId}/future-balance-preparation`, method: 'GET' })
  },

  /** GET /quality-quarantine-cases/{caseId}/future-traceability-preparation */
  async getFutureTraceabilityPreparation(caseId: string): Promise<FutureTraceabilityPreparation> {
    return apiRequest({ path: `${BASE}/${caseId}/future-traceability-preparation`, method: 'GET' })
  },

  /** GET /quality-quarantine-cases/{caseId}/integrity */
  async getIntegrity(caseId: string): Promise<QualityIntegrityApi> {
    return apiRequest({ path: `${BASE}/${caseId}/integrity`, method: 'GET' })
  },
}
