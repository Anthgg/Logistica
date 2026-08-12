import { apiRequest, getCsrfToken } from '../../../api/api-client'
import { API_ROOT } from '../../../api/config'
import { filesApi } from '../../../api/files-api'
import type { FileUploadSession } from '../../../types/files'
import type { GatePhotoEvidence, GatePhotoEvidenceType } from '../types/gate-control'

const BASE = '/logistics/gate-check-ins'

function withCsrf(): Promise<Record<string, string>> {
  return getCsrfToken().then((t) => ({ 'X-CSRF-Token': t }))
}

export const gateEvidenceApi = {
  /**
   * Crea una sesión de upload usando el sistema de archivos existente.
   * No guarda base64 ni localStorage; sube el Blob al target firmado.
   */
  async createPhotoUploadSession(
    checkInId: string,
    payload: { filename: string; size_bytes: number; mime_type: string; classification: string; evidence_type: GatePhotoEvidenceType },
  ): Promise<FileUploadSession> {
    return filesApi.createUploadSession({
      filename: payload.filename,
      size_bytes: payload.size_bytes,
      declared_mime_type: payload.mime_type,
      asset_type: 'IMAGE',
      classification: payload.classification as never,
      resource_type: 'gate_check_in',
      resource_id: checkInId,
      association_type: payload.evidence_type,
      metadata: { evidence_type: payload.evidence_type },
    })
  },

  async uploadPhoto(
    session: FileUploadSession,
    blob: Blob,
    onProgress?: (loaded: number, total: number) => void,
    signal?: AbortSignal,
  ): Promise<void> {
    const file = blob instanceof File ? blob : new File([blob], session.id, { type: blob.type })
    await filesApi.uploadToSignedTarget(session.upload_target_url, session.upload_headers, session.method, file, onProgress, signal)
  },

  async finalizeUpload(sessionId: string): Promise<FileUploadSession> {
    return filesApi.finalizeUploadSession(sessionId)
  },

  async abortUpload(sessionId: string): Promise<void> {
    return filesApi.abortUploadSession(sessionId)
  },

  async listPhotos(checkInId: string): Promise<GatePhotoEvidence[]> {
    const res = await apiRequest<{ items: GatePhotoEvidence[] }>({ path: `${BASE}/${checkInId}/photos` })
    return res.items ?? []
  },

  async associatePhoto(checkInId: string, payload: { file_id: string; evidence_type: GatePhotoEvidenceType; classification?: string }): Promise<GatePhotoEvidence> {
    return apiRequest({ path: `${BASE}/${checkInId}/photos/associate`, method: 'POST', headers: await withCsrf(), body: payload })
  },

  async viewPhoto(checkInId: string, _photoId: string): Promise<{ url: string; expires_at: string }> {
    return {
      url: `${API_ROOT}${BASE}/${checkInId}/photos`,
      expires_at: new Date(Date.now() + 3600000).toISOString(),
    }
  },
}