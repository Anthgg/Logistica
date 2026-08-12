import { apiRequest, getCsrfToken } from '../../../api/api-client'
import type {
  QualityInspection,
  QualityInspectionControl,
  QualityMeasurement,
  QualityInspectionSampleSet,
  QualityCertificateReview,
  QualityInspectionEvidence,
} from '../types/quarantine'

const BASE = '/logistics/quality-inspections'
const CONTROLS_BASE = '/logistics/quality-inspection-controls'

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

export const qualityInspectionsApi = {
  /** GET /quality-inspections */
  async list(query?: Record<string, unknown>): Promise<QualityInspection[]> {
    return apiRequest({ path: `${BASE}${query ? buildQuery(query) : ''}`, method: 'GET' })
  },

  /** GET /quality-inspections/{inspectionId} */
  async get(inspectionId: string): Promise<QualityInspection> {
    return apiRequest({ path: `${BASE}/${inspectionId}`, method: 'GET' })
  },

  /** POST /quality-inspections/{inspectionId}/start */
  async start(inspectionId: string): Promise<QualityInspection> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${inspectionId}/start`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: {},
    })
  },

  /** POST /quality-inspections/{inspectionId}/pause */
  async pause(inspectionId: string, data?: { reason?: string }): Promise<QualityInspection> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${inspectionId}/pause`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data ?? {},
    })
  },

  /** POST /quality-inspections/{inspectionId}/resume */
  async resume(inspectionId: string, data?: { reason?: string }): Promise<QualityInspection> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${inspectionId}/resume`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data ?? {},
    })
  },

  /** POST /quality-inspections/{inspectionId}/complete */
  async complete(inspectionId: string, data?: { overall_result?: string; summary?: string }): Promise<QualityInspection> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${inspectionId}/complete`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data ?? {},
    })
  },

  /** GET /quality-inspections/{inspectionId}/controls */
  async listControls(inspectionId: string): Promise<QualityInspectionControl[]> {
    return apiRequest({ path: `${BASE}/${inspectionId}/controls`, method: 'GET' })
  },

  /** POST /quality-inspection-controls/{controlId}/results */
  async recordControlResult(controlId: string, data: Record<string, unknown>): Promise<QualityInspectionControl> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${CONTROLS_BASE}/${controlId}/results`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** POST /quality-inspection-controls/{controlId}/corrections */
  async requestControlResultCorrection(controlId: string, data: Record<string, unknown>): Promise<QualityInspectionControl> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${CONTROLS_BASE}/${controlId}/corrections`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** POST /quality-inspection-controls/{controlId}/start */
  async startControl(controlId: string): Promise<QualityInspectionControl> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${CONTROLS_BASE}/${controlId}/start`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: {},
    })
  },

  /** POST /quality-inspection-controls/{controlId}/not-applicable */
  async markControlNotApplicable(controlId: string): Promise<QualityInspectionControl> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${CONTROLS_BASE}/${controlId}/not-applicable`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: {},
    })
  },

  /** GET /quality-inspections/{inspectionId}/measurements */
  async listMeasurements(inspectionId: string): Promise<QualityMeasurement[]> {
    return apiRequest({ path: `${BASE}/${inspectionId}/measurements`, method: 'GET' })
  },

  /** POST /quality-inspections/{inspectionId}/measurements */
  async createMeasurement(inspectionId: string, data: Record<string, unknown>): Promise<QualityMeasurement> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${inspectionId}/measurements`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },

  /** GET /quality-inspections/{inspectionId}/sample-sets */
  async listSampleSets(inspectionId: string): Promise<QualityInspectionSampleSet[]> {
    return apiRequest({ path: `${BASE}/${inspectionId}/sample-sets`, method: 'GET' })
  },

  /** GET /quality-inspections/{inspectionId}/certificate-reviews */
  async listCertificateReviews(inspectionId: string): Promise<QualityCertificateReview[]> {
    return apiRequest({ path: `${BASE}/${inspectionId}/certificate-reviews`, method: 'GET' })
  },

  /** GET /quality-inspections/{inspectionId}/evidence */
  async listEvidence(inspectionId: string): Promise<QualityInspectionEvidence[]> {
    return apiRequest({ path: `${BASE}/${inspectionId}/evidence`, method: 'GET' })
  },

  /** POST /quality-inspections/{inspectionId}/evidence-links */
  async createEvidenceLink(inspectionId: string, data: Record<string, unknown>): Promise<QualityInspectionEvidence> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `${BASE}/${inspectionId}/evidence-links`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: data,
    })
  },
}
