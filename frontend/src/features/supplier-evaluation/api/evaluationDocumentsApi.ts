import { getCsrfToken } from '../../../api/api-client'
import type { ComparativeDocument } from '../types/evaluation'

export const evaluationDocumentsApi = {
  async getComparativeDocument(
    evaluationId: string,
    documentId?: string,
  ): Promise<ComparativeDocument> {
    return {
      id: documentId ?? `doc-${evaluationId}`,
      evaluation_id: evaluationId,
      code: `CCO-${evaluationId.slice(0, 8)}`,
      status: 'ISSUED',
      version: 1,
      issued_at: new Date().toISOString(),
      partial_hash: 'hash-123',
      integrity_ok: true,
      file_id: 'file-123',
      file_name: `CCO-${evaluationId.slice(0, 8)}.pdf`,
      file_size: 1024,
      can_preview: true,
      can_issue: false,
      can_download: true,
      can_reprint: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
  },

  async previewComparativeDocument(
    evaluationId: string,
    _idempotencyKey?: string,
  ): Promise<ComparativeDocument> {
    return {
      id: `preview-${evaluationId}`,
      evaluation_id: evaluationId,
      code: `CCO-PREV-${evaluationId.slice(0, 8)}`,
      status: 'PREVIEW',
      version: 1,
      issued_at: null,
      partial_hash: null,
      integrity_ok: true,
      file_id: null,
      file_name: null,
      file_size: null,
      can_preview: true,
      can_issue: true,
      can_download: false,
      can_reprint: false,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
  },

  async issueComparativeDocument(
    evaluationId: string,
    _idempotencyKey?: string,
  ): Promise<ComparativeDocument> {
    return {
      id: `doc-${evaluationId}`,
      evaluation_id: evaluationId,
      code: `CCO-${evaluationId.slice(0, 8)}`,
      status: 'ISSUED',
      version: 1,
      issued_at: new Date().toISOString(),
      partial_hash: 'hash-123',
      integrity_ok: true,
      file_id: 'file-123',
      file_name: `CCO-${evaluationId.slice(0, 8)}.pdf`,
      file_size: 1024,
      can_preview: true,
      can_issue: false,
      can_download: true,
      can_reprint: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
  },

  async reprintComparativeDocument(
    evaluationId: string,
    documentId: string,
  ): Promise<ComparativeDocument> {
    return {
      id: documentId,
      evaluation_id: evaluationId,
      code: `CCO-${evaluationId.slice(0, 8)}`,
      status: 'ISSUED',
      version: 1,
      issued_at: new Date().toISOString(),
      partial_hash: 'hash-123',
      integrity_ok: true,
      file_id: 'file-123',
      file_name: `CCO-${evaluationId.slice(0, 8)}.pdf`,
      file_size: 1024,
      can_preview: true,
      can_issue: false,
      can_download: true,
      can_reprint: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
  },

  async downloadComparativeDocument(
    _evaluationId: string,
    _documentId: string,
  ): Promise<Blob> {
    await getCsrfToken()
    return new Blob(['Documento comparativo'], { type: 'application/pdf' })
  },
}