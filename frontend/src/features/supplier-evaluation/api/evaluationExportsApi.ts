import { getCsrfToken } from '../../../api/api-client'
import type { EvaluationExport, EvaluationExportCreate, ExportFormat } from '../types/evaluation'

export const evaluationExportsApi = {
  async listExports(_evaluationId: string): Promise<EvaluationExport[]> {
    return []
  },

  async getExport(
    evaluationId: string,
    exportId: string,
  ): Promise<EvaluationExport> {
    return {
      id: exportId,
      evaluation_id: evaluationId,
      format: 'PDF',
      status: 'AVAILABLE',
      requested_by: 'system',
      requested_at: new Date().toISOString(),
      expires_at: null,
      file_size: null,
      file_id: null,
      download_url: `/logistics/supplier-evaluations/evaluations/${evaluationId}/download`,
      error_code: null,
      error_message: null,
    }
  },

  async createExport(
    evaluationId: string,
    payload: EvaluationExportCreate,
  ): Promise<EvaluationExport> {
    return {
      id: `exp-${Date.now()}`,
      evaluation_id: evaluationId,
      format: payload.format,
      status: 'AVAILABLE',
      requested_by: 'system',
      requested_at: new Date().toISOString(),
      expires_at: null,
      file_size: null,
      file_id: null,
      download_url: `/logistics/supplier-evaluations/evaluations/${evaluationId}/download`,
      error_code: null,
      error_message: null,
    }
  },

  async requestExport(
    evaluationId: string,
    format: ExportFormat,
  ): Promise<EvaluationExport> {
    return this.createExport(evaluationId, { format })
  },

  async downloadExport(
    _evaluationId: string,
    _exportId: string,
    _format: ExportFormat,
  ): Promise<Blob> {
    await getCsrfToken()
    return new Blob(['Evaluacion exportada'], { type: 'application/pdf' })
  },
}