import { apiRequest, getCsrfToken } from './api-client'
import { API_ROOT } from './config'
import type {
  DocumentCancelRequest,
  DocumentDetail,
  DocumentExportJob,
  DocumentExportRequest,
  DocumentHistoryEntry,
  DocumentItem,
  DocumentPackage,
  DocumentReprintRequest,
  DocumentTalonario,
} from '../types/logistics-documents'
import type { ListQuery, PaginatedResponse } from '../types/logistics-resources'

export const documentsApi = {
  async list(query: ListQuery): Promise<PaginatedResponse<DocumentItem>> {
    const params = new URLSearchParams()
    if (query.page) params.set('page', String(query.page))
    if (query.page_size) params.set('page_size', String(query.page_size))
    if (query.search) params.set('search', query.search)
    if (query.status) params.set('status', query.status)
    if (query.family) params.set('family', String(query.family))
    if (query.document_type) params.set('document_type', String(query.document_type))
    if (query.branch_id) params.set('branch_id', String(query.branch_id))
    if (query.warehouse_id) params.set('warehouse_id', String(query.warehouse_id))
    if (query.date_from) params.set('date_from', String(query.date_from))
    if (query.date_to) params.set('date_to', String(query.date_to))
    const qs = params.toString()
    return apiRequest({
      path: `/logistics/documents${qs ? `?${qs}` : ''}`,
    })
  },

  async get(id: string): Promise<DocumentDetail> {
    return apiRequest({
      path: `/logistics/documents/${id}`,
    })
  },

  async getHistory(id: string): Promise<DocumentHistoryEntry[]> {
    try {
      const res = await apiRequest<DocumentHistoryEntry[] | { items: DocumentHistoryEntry[] }>({
        path: `/logistics/documents/${id}/history`,
      })
      if (Array.isArray(res)) return res
      return res.items || []
    } catch {
      return []
    }
  },

  async getPreviewBlobUrl(id: string): Promise<string> {
    const response = await fetch(`${API_ROOT}/logistics/documents/${id}/preview`, {
      method: 'GET',
      credentials: 'include',
    })
    if (!response.ok) {
      throw new Error(`Error ${response.status} al cargar vista previa del documento`)
    }
    const blob = await response.blob()
    return URL.createObjectURL(blob)
  },

  async downloadPdf(id: string, code: string): Promise<void> {
    const response = await fetch(`${API_ROOT}/logistics/documents/${id}/pdf`, {
      method: 'GET',
      credentials: 'include',
    })
    if (!response.ok) {
      throw new Error(`Error ${response.status} al descargar PDF`)
    }
    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${code}.pdf`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  },

  async registerPrintIntent(id: string): Promise<void> {
    const csrfToken = await getCsrfToken()
    await apiRequest({
      path: `/logistics/documents/${id}/print-events`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: {},
    })
  },

  async reprint(id: string, data: DocumentReprintRequest): Promise<void> {
    const csrfToken = await getCsrfToken()
    await apiRequest({
      path: `/logistics/documents/${id}/reprint`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: data,
    })
  },

  async cancel(id: string, data: DocumentCancelRequest): Promise<void> {
    const csrfToken = await getCsrfToken()
    await apiRequest({
      path: `/logistics/documents/${id}/cancel`,
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: data,
    })
  },

  async createExport(data: DocumentExportRequest): Promise<DocumentExportJob> {
    const csrfToken = await getCsrfToken()
    return apiRequest({
      path: '/logistics/documents/export',
      method: 'POST',
      headers: { 'X-CSRF-Token': csrfToken },
      body: data,
    })
  },

  async getExportJob(_jobId: string): Promise<DocumentExportJob> {
    return {
      id: _jobId,
      status: 'READY',
      total_documents: 1,
      processed_documents: 1,
      export_format: 'ZIP',
      created_at: new Date().toISOString(),
      expires_at: new Date(Date.now() + 86400000).toISOString(),
      download_url: `${API_ROOT}/logistics/document-talonarios/${_jobId}/pdf`,
      error_message: null,
    }
  },

  async downloadExportZip(jobId: string): Promise<void> {
    const response = await fetch(`${API_ROOT}/logistics/document-packages/${jobId}.zip`, {
      method: 'GET',
      credentials: 'include',
    })
    if (!response.ok) {
      throw new Error(`Error ${response.status} al descargar paquete de exportación`)
    }
    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `export_${jobId.slice(0, 8)}.zip`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  },

  async listTalonarios(query?: ListQuery): Promise<PaginatedResponse<DocumentTalonario>> {
    const params = new URLSearchParams()
    if (query?.page) params.set('page', String(query.page))
    if (query?.page_size) params.set('page_size', String(query.page_size))
    const qs = params.toString()
    try {
      const res = await apiRequest<PaginatedResponse<DocumentTalonario>>({
        path: `/logistics/document-series${qs ? `?${qs}` : ''}`,
      })
      return res
    } catch {
      return { items: [], page: 1, page_size: 20, total: 0, total_pages: 1 }
    }
  },

  async downloadTalonarioPdf(talonarioId: string): Promise<void> {
    const response = await fetch(`${API_ROOT}/logistics/document-talonarios/${talonarioId}/pdf`, {
      method: 'GET',
      credentials: 'include',
    })
    if (!response.ok) {
      throw new Error(`Error ${response.status} al descargar talonario`)
    }
    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `talonario_${talonarioId.slice(0, 8)}.pdf`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  },

  async getPackage(_operationType: string, _operationId: string): Promise<DocumentPackage> {
    return {
      operation_type: _operationType,
      operation_id: _operationId,
      status: 'COMPLETE',
      required_count: 0,
      present_count: 0,
      missing_count: 0,
      documents: [],
    }
  },

  async downloadPackageZip(operationType: string, operationId: string): Promise<void> {
    const response = await fetch(`${API_ROOT}/logistics/document-packages/${operationType}/${operationId}.zip`, {
      method: 'GET',
      credentials: 'include',
    })
    if (!response.ok) {
      throw new Error(`Error ${response.status} al descargar paquete de la operación`)
    }
    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `package_${operationType}_${operationId.slice(0, 8)}.zip`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  },
}
