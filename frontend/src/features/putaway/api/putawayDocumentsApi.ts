import { apiRequest, getCsrfToken } from '../../../api/api-client'

function generateKey(): string {
  return typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

async function withCsrf(): Promise<Record<string, string>> {
  const token = await getCsrfToken()
  return { 'X-CSRF-Token': token }
}

export const putawayDocumentsApi = {
  async generateDocument(orderId: string, documentType: string, format: string): Promise<unknown> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `/logistics/putaway/orders/${orderId}/documents`,
      method: 'POST',
      headers: { ...csrf, 'Idempotency-Key': generateKey() },
      body: { document_type: documentType, format },
    })
  },

  async getDocument(documentId: string): Promise<unknown> {
    return apiRequest({ path: `/logistics/putaway/documents/${documentId}`, method: 'GET' })
  },

  async downloadDocument(documentId: string): Promise<Blob> {
    return apiRequest({ path: `/logistics/putaway/documents/${documentId}/download`, method: 'GET' })
  },

  async updateDocumentMetadata(documentId: string, metadata: Record<string, unknown>): Promise<unknown> {
    const csrf = await withCsrf()
    return apiRequest({
      path: `/logistics/putaway/documents/${documentId}`,
      method: 'PUT',
      headers: csrf,
      body: metadata,
    })
  },

  async confirmPlacement(data: { order_id: string; line_id: string; location_id: string; quantity: { value: string; scale: number }; lot_id?: string; serial_id?: string }): Promise<unknown> {
    return apiRequest({
      path: `/logistics/putaway/orders/${data.order_id}/lines/${data.line_id}/confirm`,
      method: 'POST',
      body: data,
    })
  },
}
