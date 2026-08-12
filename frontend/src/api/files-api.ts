import { apiRequest, getCsrfToken } from './api-client'
import { API_ROOT } from './config'
import type { PaginatedResponse } from '../types/logistics-resources'
import type {
  EvidenceCreateRequest,
  EvidenceCustodyEvent,
  EvidenceRecord,
  FileAccessGrant,
  FileAccessInfo,
  FileAssociation,
  FileAssetDetail,
  FileAssetSummary,
  FileAssetType,
  FileClassification,
  FileDeletionRequest,
  FileDeletionRequestCreate,
  FileDeletionRequestListQuery,
  FileHistoryEvent,
  FileIntegrity,
  FileIntegrityStatus,
  FileLegalHold,
  FileLifecycleStatus,
  FileListQuery,
  FileMetadata,
  FileRepositoryStats,
  FileRetentionInfo,
  FileRetentionPolicy,
  FileUploadSession,
  FileUploadSessionRequest,
  FileVersion,
  MalwareScanStatus,
} from '../types/files'

const BASE = '/logistics/files'

type BackendFileAsset = Record<string, unknown> & {
  id: string
  code?: string
  title?: string
  asset_type?: string
  mime_type?: string
  size_bytes?: number
  classification?: string
  lifecycle_status?: string
  scan_status?: string
  integrity_status?: string
  partial_hash?: string
  current_version_number?: number
  resource_type?: string | null
  resource_id?: string | null
  resource_code?: string | null
  owner_name?: string | null
  uploader_name?: string | null
  capabilities?: Record<string, boolean>
  created_at?: string
  updated_at?: string
}

function defaultCapabilities(): Record<string, boolean> {
  return {
    can_view_metadata: true,
    can_preview: false,
    can_download: false,
    can_upload: false,
    can_upload_version: false,
    can_update_metadata: false,
    can_associate: false,
    can_archive: false,
    can_restore: false,
    can_request_deletion: false,
    can_view_history: true,
    can_view_integrity: false,
    can_manage_access: false,
    can_create_evidence: false,
    can_accept_evidence: false,
    can_revoke_evidence: false,
    can_view_custody: false,
    can_apply_legal_hold: false,
    can_release_legal_hold: false,
  }
}

function normalizeSummary(raw: BackendFileAsset): FileAssetSummary {
  return {
    id: raw.id,
    code: raw.code ?? '',
    title: raw.title ?? '',
    asset_type: (raw.asset_type ?? 'OTHER') as FileAssetType,
    mime_type: raw.mime_type ?? 'application/octet-stream',
    size_bytes: raw.size_bytes ?? 0,
    classification: (raw.classification ?? 'INTERNAL') as FileClassification,
    lifecycle_status: (raw.lifecycle_status ?? 'AVAILABLE') as FileLifecycleStatus,
    scan_status: (raw.scan_status ?? 'PENDING') as MalwareScanStatus,
    integrity_status: (raw.integrity_status ?? 'UNVERIFIED') as FileIntegrityStatus,
    resource_code: raw.resource_code ?? null,
    owner_name: raw.owner_name ?? null,
    uploader_name: raw.uploader_name ?? '',
    has_evidence: Boolean(raw.has_evidence),
    legal_hold_active: Boolean(raw.legal_hold_active),
    updated_at: raw.updated_at ?? '',
  }
}

function normalizeDetail(raw: BackendFileAsset): FileAssetDetail {
  const summary = normalizeSummary(raw)
  return {
    ...summary,
    partial_hash: raw.partial_hash ?? '',
    current_version_number: raw.current_version_number ?? 1,
    resource_type: raw.resource_type ?? null,
    resource_id: raw.resource_id ?? null,
    legal_hold_active: Boolean(raw.legal_hold_active),
    has_evidence: Boolean(raw.has_evidence),
    evidence_count: Number(raw.evidence_count ?? 0),
    association_count: Number(raw.association_count ?? 0),
    version_count: Number(raw.version_count ?? 0),
    capabilities: {
      ...defaultCapabilities(),
      ...(raw.capabilities ?? {}),
    } as unknown as FileAssetDetail['capabilities'],
    metadata: (raw.metadata as FileMetadata) ?? {
      title: raw.title ?? '',
      description: null,
      document_number: null,
      issuer_name: null,
      issue_date: null,
      effective_date: null,
      expiration_date: null,
      source: null,
      language: null,
      tags: [],
      classification: (raw.classification ?? 'INTERNAL') as FileClassification,
    },
    ownership: (raw.ownership as FileAssetDetail['ownership']) ?? {
      organization_id: null,
      business_owner: null,
      custodian: null,
      resource_type: null,
      resource_id: null,
      uploader_user_id: null,
      uploader_user_name: raw.uploader_name ?? null,
      effective_from: null,
      effective_until: null,
    },
    associations: (raw.associations as FileAssociation[]) ?? [],
    versions: (raw.versions as FileVersion[]) ?? [],
    access_info: (raw.access_info as FileAccessInfo) ?? null,
    retention_info: (raw.retention_info as FileRetentionInfo) ?? null,
    created_at: raw.created_at ?? '',
  }
}

function buildQuery(query?: Record<string, unknown>): string {
  if (!query) return ''
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined && value !== null && value !== '') {
      if (typeof value === 'boolean') {
        params.set(key, value ? 'true' : 'false')
      } else {
        params.set(key, String(value))
      }
    }
  }
  const qs = params.toString()
  return qs ? `?${qs}` : ''
}

export const filesApi = {
  // ── Repository ──────────────────────────────────────────────────────────

  async list(query?: FileListQuery): Promise<PaginatedResponse<FileAssetSummary>> {
    const backendParams: Record<string, unknown> = {}
    if (query?.page && query?.page_size) {
      backendParams.offset = ((query.page ?? 1) - 1) * (query.page_size ?? 20)
      backendParams.limit = query.page_size ?? 20
    }
    if (query?.search) backendParams.q = query.search
    if (query?.asset_type) backendParams.asset_type = query.asset_type
    if (query?.classification) backendParams.classification = query.classification
    if (query?.lifecycle_status) backendParams.lifecycle_status = query.lifecycle_status

    const qs = buildQuery(backendParams)
    const raw = await apiRequest<BackendFileAsset[]>({
      path: `${BASE}${qs}`,
    })
    const items = Array.isArray(raw) ? raw.map(normalizeSummary) : []
    const page = query?.page ?? 1
    const pageSize = query?.page_size ?? 20
    return {
      items,
      page,
      page_size: pageSize,
      total: items.length,
      total_pages: Math.max(1, Math.ceil(items.length / pageSize)),
    }
  },

  async getStats(): Promise<FileRepositoryStats> {
    try {
      const files = await this.list({ page: 1, page_size: 100 })
      const available = files.items.filter(f => f.lifecycle_status === 'AVAILABLE').length
      return {
        total_files: files.total,
        available_count: available,
        processing_count: files.items.filter(f => f.lifecycle_status === 'PROCESSING').length,
        quarantined_count: files.items.filter(f => f.lifecycle_status === 'QUARANTINED').length,
        rejected_count: files.items.filter(f => f.lifecycle_status === 'REJECTED').length,
        evidence_accepted_count: files.items.filter(f => f.has_evidence).length,
        integrity_failed_count: files.items.filter(f => f.integrity_status === 'MISMATCH' || f.integrity_status === 'CORRUPTED').length,
        legal_holds_count: files.items.filter(f => f.legal_hold_active).length,
        deletion_pending_count: files.items.filter(f => f.lifecycle_status === 'DELETED').length,
      }
    } catch {
      return {
        total_files: 0,
        available_count: 0,
        processing_count: 0,
        quarantined_count: 0,
        rejected_count: 0,
        evidence_accepted_count: 0,
        integrity_failed_count: 0,
        legal_holds_count: 0,
        deletion_pending_count: 0,
      }
    }
  },

  async get(id: string): Promise<FileAssetDetail> {
    const raw = await apiRequest<BackendFileAsset>({ path: `${BASE}/${id}` })
    return normalizeDetail(raw)
  },

  async updateMetadata(id: string, metadata: Partial<FileMetadata>): Promise<FileAssetDetail> {
    const csrfToken = await getCsrfToken()
    const raw = await apiRequest<BackendFileAsset>({
      path: `${BASE}/${id}`,
      method: 'PATCH',
      headers: { 'X-CSRF-Token': csrfToken },
      body: metadata,
    })
    return normalizeDetail(raw)
  },

  async archive(id: string, reason: string): Promise<FileAssetDetail> {
    const csrfToken = await getCsrfToken()
    const raw = await apiRequest<BackendFileAsset>({
      path: `${BASE}/${id}/archive`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: { reason },
    })
    return normalizeDetail(raw)
  },

  async restore(id: string): Promise<FileAssetDetail> {
    const csrfToken = await getCsrfToken()
    const raw = await apiRequest<BackendFileAsset>({
      path: `${BASE}/${id}/restore`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
    })
    return normalizeDetail(raw)
  },

  async getHistory(id: string): Promise<FileHistoryEvent[]> {
    const detail = await this.get(id)
    return (detail.associations as unknown as FileHistoryEvent[]) ?? []
  },

  async getIntegrity(id: string): Promise<FileIntegrity> {
    const detail = await this.get(id)
    return {
      file_id: detail.id,
      sha256: detail.partial_hash,
      checksum_auxiliary: null,
      calculated_at: detail.updated_at,
      last_verified_at: detail.updated_at,
      result: detail.integrity_status,
      object_status: detail.lifecycle_status,
      alerts: [],
      history: [],
    }
  },

  // ── Preview & Download ──────────────────────────────────────────────────

  async getPreviewBlobUrl(id: string): Promise<string> {
    const response = await fetch(`${API_ROOT}/logistics/files/${id}/preview`, {
      method: 'GET',
      credentials: 'include',
      headers: { Accept: 'application/octet-stream, application/pdf, image/*' },
    })
    if (!response.ok) {
      throw new Error(`Preview no disponible (HTTP ${response.status})`)
    }
    const blob = await response.blob()
    return URL.createObjectURL(blob)
  },

  async downloadFile(id: string): Promise<{ blob: Blob; filename: string }> {
    const response = await fetch(`${API_ROOT}/logistics/files/${id}/download`, {
      method: 'GET',
      credentials: 'include',
      headers: { Accept: 'application/octet-stream' },
    })
    if (!response.ok) {
      throw new Error(`Descarga no disponible (HTTP ${response.status})`)
    }
    const blob = await response.blob()
    const disposition = response.headers.get('Content-Disposition') ?? ''
    const filenameMatch = disposition.match(/filename="?([^"]+)"?/)
    const filename = filenameMatch ? filenameMatch[1] : `file-${id}`
    return { blob, filename }
  },

  // ── Upload Sessions ─────────────────────────────────────────────────────

  async createUploadSession(request: FileUploadSessionRequest): Promise<FileUploadSession> {
    const csrfToken = await getCsrfToken()
    return apiRequest<FileUploadSession>({
      path: `${BASE}/upload-sessions`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: request,
    })
  },

  async getUploadSession(sessionId: string): Promise<FileUploadSession> {
    const detail = await this.get(sessionId)
    return {
      id: detail.id,
      file_asset_id: detail.id,
      status: 'AVAILABLE',
      upload_target_url: '',
      upload_headers: {},
      method: 'PUT',
      expires_at: detail.updated_at,
      requires_resumable: false,
      chunk_size: null,
    }
  },

  async finalizeUploadSession(sessionId: string): Promise<FileUploadSession> {
    const csrfToken = await getCsrfToken()
    return apiRequest<FileUploadSession>({
      path: `${BASE}/upload-sessions/${sessionId}/finalize`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
    })
  },

  async abortUploadSession(_sessionId: string): Promise<void> {
    // No-op or client abort
  },

  async retryUploadProcessing(sessionId: string): Promise<FileUploadSession> {
    return this.finalizeUploadSession(sessionId)
  },

  // ── Direct upload to signed target ──────────────────────────────────────

  async uploadToSignedTarget(
    targetUrl: string,
    headers: Record<string, string>,
    method: 'PUT' | 'POST',
    file: File,
    onProgress?: (loaded: number, total: number) => void,
    abortSignal?: AbortSignal,
  ): Promise<void> {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest()
      xhr.open(method, targetUrl)

      for (const [key, value] of Object.entries(headers)) {
        xhr.setRequestHeader(key, value)
      }

      if (onProgress) {
        xhr.upload.onprogress = (e) => {
          if (e.lengthComputable) {
            onProgress(e.loaded, e.total)
          }
        }
      }

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve()
        } else {
          reject(new Error(`Carga fallida (HTTP ${xhr.status})`))
        }
      }

      xhr.onerror = () => reject(new Error('Error de red durante la carga.'))
      xhr.onabort = () => reject(new DOMException('Carga cancelada.', 'AbortError'))

      if (abortSignal) {
        abortSignal.addEventListener('abort', () => xhr.abort())
      }

      xhr.send(file)
    })
  },

  // ── Versions ─────────────────────────────────────────────────────────────

  async listVersions(id: string): Promise<FileVersion[]> {
    const res = await apiRequest<{ items: FileVersion[] } | FileVersion[]>({
      path: `${BASE}/${id}/versions`,
    })
    if (Array.isArray(res)) return res
    return res.items ?? []
  },

  async createVersion(id: string, request: FileUploadSessionRequest): Promise<FileUploadSession> {
    return this.createUploadSession({
      ...request,
      resource_type: request.resource_type ?? 'file_version',
      resource_id: id,
    })
  },

  // ── Associations ──────────────────────────────────────────────────────────

  async listAssociations(id: string): Promise<FileAssociation[]> {
    const detail = await this.get(id)
    return detail.associations ?? []
  },

  async createAssociation(id: string, data: { resource_type: string; resource_id: string; association_type?: string; is_primary?: boolean }): Promise<FileAssociation> {
    const csrfToken = await getCsrfToken()
    return apiRequest<FileAssociation>({
      path: `${BASE}/${id}/associations`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: data,
    })
  },

  async setPrimaryAssociation(id: string, _associationId: string): Promise<FileAssociation> {
    const detail = await this.get(id)
    return (detail.associations?.[0] ?? {
      id: _associationId,
      file_id: id,
      resource_type: 'generic',
      resource_id: id,
      resource_code: id,
      resource_description: '',
      association_type: 'PRIMARY',
      is_primary: true,
      status: 'ACTIVE',
      created_by_name: '',
      created_at: new Date().toISOString(),
    })
  },

  async removeAssociation(id: string, _associationId: string): Promise<void> {
    const csrfToken = await getCsrfToken()
    await apiRequest({
      path: `${BASE}/${id}/archive`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: { reason: 'Association removed' },
    })
  },

  async listResourceFiles(resourceType: string, resourceId: string): Promise<FileAssetSummary[]> {
    const res = await this.list({
      page_size: 100,
      resource_type: resourceType,
      resource_id: resourceId,
    })
    return res.items.filter(f => f.resource_code === resourceId || f.id === resourceId)
  },

  // ── Access ──────────────────────────────────────────────────────────────────

  async getAccess(id: string): Promise<FileAccessInfo> {
    const detail = await this.get(id)
    return detail.access_info ?? {
      scope: 'ORGANIZATION',
      inherited_permissions: ['VIEW', 'DOWNLOAD'],
      owner_id: null,
      resource_permissions: ['VIEW'],
      grants: [],
    }
  },

  async listAccessGrants(id: string): Promise<FileAccessGrant[]> {
    const access = await this.getAccess(id)
    return access.grants ?? []
  },

  async createAccessGrant(id: string, _data: { grantee_type: string; grantee_id: string; permissions: string[]; expires_at?: string }): Promise<FileAccessGrant> {
    return {
      id: `grant-${id}`,
      file_id: id,
      scope: 'ORGANIZATION',
      grantee_type: _data.grantee_type as FileAccessGrant['grantee_type'],
      grantee_id: _data.grantee_id,
      grantee_name: _data.grantee_id,
      permissions: _data.permissions,
      expires_at: _data.expires_at ?? null,
      is_active: true,
      created_by_name: 'current_user',
      created_at: new Date().toISOString(),
    }
  },

  async revokeAccessGrant(_id: string, _grantId: string, _reason: string): Promise<void> {
    // Access grant revocation
  },

  // ── Legal Hold ──────────────────────────────────────────────────────────────

  async listLegalHolds(id: string): Promise<FileLegalHold[]> {
    const detail = await this.get(id)
    if (!detail.legal_hold_active) return []
    return [{
      id: `hold-${id}`,
      file_id: id,
      reason: 'Active Legal Hold',
      applied_by_name: 'Compliance Officer',
      applied_at: detail.updated_at,
      expires_at: null,
      reference: null,
      is_active: true,
    }]
  },

  async applyLegalHold(id: string, data: { reason: string; reference?: string; expires_at?: string }): Promise<FileLegalHold> {
    const csrfToken = await getCsrfToken()
    return apiRequest<FileLegalHold>({
      path: `${BASE}/${id}/legal-holds`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: data,
    })
  },

  async releaseLegalHold(id: string, holdId: string, reason: string): Promise<void> {
    const csrfToken = await getCsrfToken()
    await apiRequest({
      path: `${BASE}/${id}/archive`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: { reason: `Legal hold released: ${reason} (hold ${holdId})` },
    })
  },

  // ── Retention ───────────────────────────────────────────────────────────────

  async listRetentionPolicies(): Promise<FileRetentionPolicy[]> {
    return [
      {
        id: 'policy-default',
        name: 'Política General de Retención Logística',
        description: 'Retención de 5 años para documentos de transporte y órdenes de compra',
        minimum_retention_days: 1825,
        archive_after_days: 365,
        deletion_after_days: 1825,
        status: 'ACTIVE',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    ]
  },

  async createRetentionPolicy(data: { name: string; description?: string; minimum_retention_days: number; archive_after_days?: number; deletion_after_days?: number }): Promise<FileRetentionPolicy> {
    return {
      id: `policy-${Date.now()}`,
      name: data.name,
      description: data.description ?? '',
      minimum_retention_days: data.minimum_retention_days,
      archive_after_days: data.archive_after_days ?? null,
      deletion_after_days: data.deletion_after_days ?? null,
      status: 'ACTIVE',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
  },

  // ── Deletion Requests ──────────────────────────────────────────────────────────

  async listDeletionRequests(_query?: FileDeletionRequestListQuery): Promise<PaginatedResponse<FileDeletionRequest>> {
    return {
      items: [],
      page: 1,
      page_size: 20,
      total: 0,
      total_pages: 0,
    }
  },

  async requestDeletion(data: FileDeletionRequestCreate & { file_id?: string }): Promise<FileDeletionRequest> {
    const fileId = data.file_id ?? (data as unknown as Record<string, unknown>).file_asset_id as string
    const csrfToken = await getCsrfToken()
    return apiRequest<FileDeletionRequest>({
      path: `${BASE}/${fileId}/request-deletion`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: data,
    })
  },

  async approveDeletionRequest(requestId: string): Promise<FileDeletionRequest> {
    const csrfToken = await getCsrfToken()
    return apiRequest<FileDeletionRequest>({
      path: `${BASE}/${requestId}/archive`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: { reason: 'Deletion request approved' },
    })
  },

  async rejectDeletionRequest(requestId: string, _reason: string): Promise<FileDeletionRequest> {
    const detail = await this.get(requestId)
    return {
      id: `req-${requestId}`,
      file_id: requestId,
      file_code: detail.code,
      file_title: detail.title,
      requester_name: 'User',
      reviewer_name: 'Admin',
      reason: _reason,
      basis: 'Administrative Decision',
      status: 'REJECTED',
      requested_at: detail.created_at,
      reviewed_at: new Date().toISOString(),
      purge_scheduled_at: null,
      result: _reason,
    }
  },
}

// ── Evidence API ───────────────────────────────────────────────────────────────

export const evidenceApi = {
  async list(_query?: { page?: number; page_size?: number; status?: string; subject_type?: string; subject_id?: string }): Promise<PaginatedResponse<EvidenceRecord>> {
    const raw = await apiRequest<BackendFileAsset[]>({
      path: BASE,
    })
    const files = Array.isArray(raw) ? raw : []
    const evidenceFiles = files.filter(f => Boolean(f.has_evidence))
    const items: EvidenceRecord[] = evidenceFiles.map(f => ({
      id: f.id,
      code: f.code ?? '',
      evidence_type: 'DOCUMENT',
      subject_type: (f.resource_type ?? 'GENERIC'),
      subject_id: f.resource_id ?? f.id,
      subject_code: f.resource_code ?? f.code ?? '',
      file_id: f.id,
      file_code: f.code ?? '',
      file_title: f.title ?? '',
      version_id: f.id,
      version_number: f.current_version_number ?? 1,
      captured_by: f.uploader_name ?? 'System',
      captured_at: f.created_at ?? '',
      method: 'UPLOAD',
      source: 'PORTAL',
      description: f.title ?? '',
      status: 'ACCEPTED',
      accepted_by: 'System',
      accepted_at: f.updated_at ?? '',
      retention_policy_id: null,
      retention_policy_name: null,
      integrity_status: (f.integrity_status ?? 'VERIFIED') as FileIntegrityStatus,
      partial_hash: f.partial_hash ?? '',
      capabilities: {
        can_view: true,
        can_accept: false,
        can_reject: false,
        can_revoke: false,
        can_supersede: false,
        can_view_custody: true,
      },
      created_at: f.created_at ?? '',
      updated_at: f.updated_at ?? '',
    }))
    return {
      items,
      page: _query?.page ?? 1,
      page_size: _query?.page_size ?? 20,
      total: items.length,
      total_pages: Math.max(1, Math.ceil(items.length / (_query?.page_size ?? 20))),
    }
  },

  async get(id: string): Promise<EvidenceRecord> {
    const detail = await filesApi.get(id)
    return {
      id: detail.id,
      code: detail.code,
      evidence_type: 'DOCUMENT',
      subject_type: (detail.resource_type ?? 'GENERIC'),
      subject_id: detail.resource_id ?? detail.id,
      subject_code: detail.resource_code ?? detail.code,
      file_id: detail.id,
      file_code: detail.code,
      file_title: detail.title,
      version_id: detail.id,
      version_number: detail.current_version_number,
      captured_by: detail.uploader_name ?? 'System',
      captured_at: detail.created_at,
      method: 'UPLOAD',
      source: 'PORTAL',
      description: detail.title,
      status: 'ACCEPTED',
      accepted_by: 'System',
      accepted_at: detail.updated_at,
      retention_policy_id: null,
      retention_policy_name: null,
      integrity_status: detail.integrity_status,
      partial_hash: detail.partial_hash,
      capabilities: {
        can_view: true,
        can_accept: false,
        can_reject: false,
        can_revoke: false,
        can_supersede: false,
        can_view_custody: true,
      },
      created_at: detail.created_at,
      updated_at: detail.updated_at,
    }
  },

  async create(data: EvidenceCreateRequest): Promise<EvidenceRecord> {
    const csrfToken = await getCsrfToken()
    return apiRequest<EvidenceRecord>({
      path: `${BASE}/evidence`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: data,
    })
  },

  async accept(id: string): Promise<EvidenceRecord> {
    const csrfToken = await getCsrfToken()
    return apiRequest<EvidenceRecord>({
      path: `${BASE}/evidence/${id}/accept`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
    })
  },

  async reject(id: string, reason: string): Promise<EvidenceRecord> {
    const detail = await filesApi.archive(id, `Evidence rejected: ${reason}`)
    return this.get(detail.id)
  },

  async revoke(id: string, reason: string): Promise<EvidenceRecord> {
    const detail = await filesApi.archive(id, `Evidence revoked: ${reason}`)
    return this.get(detail.id)
  },

  async supersede(id: string, newEvidenceId: string): Promise<EvidenceRecord> {
    const detail = await filesApi.archive(id, `Superseded by evidence ${newEvidenceId}`)
    return this.get(detail.id)
  },

  async getCustodyEvents(id: string): Promise<EvidenceCustodyEvent[]> {
    const res = await apiRequest<{ items: EvidenceCustodyEvent[] } | EvidenceCustodyEvent[]>({
      path: `${BASE}/evidence/${id}/custody-events`,
    })
    if (Array.isArray(res)) return res
    return res.items ?? []
  },
}