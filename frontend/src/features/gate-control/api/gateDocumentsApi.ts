import { apiRequest, getCsrfToken } from '../../../api/api-client'
import { API_ROOT } from '../../../api/config'
import type { GateCpvDocumentResponse, GatePreviewResponse, GateControlPackage } from '../types/gate-control'

const BASE = '/logistics/gate-check-ins'

function generateKey(): string {
  return typeof crypto !== 'undefined' && 'randomUUID' in crypto ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

export const gateDocumentsApi = {
  async getDocument(checkInId: string): Promise<GateCpvDocumentResponse | null> {
    try {
      return await apiRequest<GateCpvDocumentResponse>({ path: `${BASE}/${checkInId}/document`, method: 'GET' })
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'status' in err && (err as { status: number }).status === 404) {
        return null
      }
      throw err
    }
  },

  async previewDocument(checkInId: string): Promise<GatePreviewResponse> {
    return apiRequest({ path: `${BASE}/${checkInId}/preview`, method: 'GET' })
  },

  async issueDocument(checkInId: string): Promise<GateCpvDocumentResponse> {
    const csrfToken = await getCsrfToken()
    return apiRequest({
      path: `${BASE}/${checkInId}/issue-document`,
      method: 'POST',
      headers: {
        'X-CSRF-Token': csrfToken,
        'Idempotency-Key': generateKey(),
      },
      body: {},
    })
  },

  async downloadDocument(checkInId: string): Promise<Blob> {
    const res = await fetch(`${API_ROOT}${BASE}/${checkInId}/document/pdf`, {
      method: 'GET',
      credentials: 'include',
      headers: { Accept: 'application/pdf' },
    })
    if (!res.ok) throw new Error(`Error ${res.status} al descargar el acta CPV.`)
    const contentType = res.headers.get('content-type') ?? ''
    if (!contentType.includes('application/pdf')) {
      let detail = ''
      try { const body = await res.json(); detail = body?.message ?? JSON.stringify(body) } catch { /* ignore */ }
      throw new Error(`Se esperaba application/pdf pero se recibió ${contentType}. ${detail}`.trim())
    }
    return res.blob()
  },

  // ── Paquete documental ────────────────────────────────────────────────────────

  async createPackage(_checkInId: string): Promise<GateControlPackage> {
    return {
      id: `pkg-${Date.now()}`,
      check_in_id: _checkInId,
      status: 'AVAILABLE',
      includes_cpv: false,
      includes_cit: false,
      evidence_count: 0,
      document_count: 1,
      has_personal_photos: false,
      file: null,
      requested_at: new Date().toISOString(),
      expires_at: null,
      created_at: new Date().toISOString(),
    }
  },

  async getPackage(_checkInId: string): Promise<GateControlPackage | null> {
    return null
  },

  async downloadPackage(checkInId: string, _packageId: string): Promise<Blob> {
    return this.downloadDocument(checkInId)
  },
}
