import { useEffect, useState } from 'react'
import { documentsApi } from '../../api/documents-api'
import { Button } from './Button'
import { StatusBadge } from './StatusBadge'
import type { DocumentExportJob } from '../../types/logistics-documents'
import { formatDateTime } from '../../utils/date'
import { getErrorMessage } from '../../utils/errors'

interface DocumentExportJobsPanelProps {
  isOpen: boolean
  activeJobId: string | null
  onClose: () => void
}

export function DocumentExportJobsPanel({
  isOpen,
  activeJobId,
  onClose,
}: DocumentExportJobsPanelProps) {
  const [job, setJob] = useState<DocumentExportJob | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!isOpen || !activeJobId) return undefined

    let active = true
    let timer: number | null = null

    const fetchStatus = async () => {
      try {
        const data = await documentsApi.getExportJob(activeJobId)
        if (!active) return
        setJob(data)
        setError(null)

        // Continuar polling mientras el estado sea activo
        if (['QUEUED', 'VALIDATING', 'PROCESSING'].includes(data.status)) {
          timer = window.setTimeout(() => void fetchStatus(), 3000)
        }
      } catch (err: unknown) {
        if (active) setError(getErrorMessage(err))
      } finally {
        if (active) setIsLoading(false)
      }
    }

    setIsLoading(true)
    void fetchStatus()

    return () => {
      active = false
      if (timer) window.clearTimeout(timer)
    }
  }, [activeJobId, isOpen])

  if (!isOpen) return null

  return (
    <div
      className="fixed inset-0 z-[80] flex items-center justify-center bg-slate-950/60 p-4 backdrop-blur-sm"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div className="w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-5 shadow-2xl space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <p className="text-[10px] font-bold text-blue-700 uppercase tracking-widest">
              Exportaciones en segundo plano
            </p>
            <h2 className="text-base font-bold text-slate-900">Estado del paquete documental</h2>
          </div>
          <button
            type="button"
            className="text-slate-400 hover:text-slate-700"
            onClick={onClose}
            aria-label="Cerrar panel"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" aria-hidden="true"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>

        {isLoading && !job && (
          <div className="loading-panel">
            <span className="spinner" />
            <p>Consultando estado de la exportación…</p>
          </div>
        )}

        {error && <p className="text-xs font-semibold text-rose-600">{error}</p>}

        {job && (
          <div className="space-y-4 text-xs">
            <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 p-3">
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase">Identificador de tarea</span>
                <p className="font-mono font-bold text-slate-900">{job.id.slice(0, 13)}…</p>
              </div>
              <StatusBadge value={job.status.toLowerCase()}>{job.status}</StatusBadge>
            </div>

            <div className="space-y-1">
              <div className="flex justify-between text-[11px] font-semibold text-slate-700">
                <span>Progreso de empaquetado</span>
                <span>
                  {job.processed_documents} / {job.total_documents} docs
                </span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
                <div
                  className="h-full bg-blue-700 transition-colors duration-300"
                  style={{
                    width: `${
                      job.total_documents > 0
                        ? Math.min((job.processed_documents / job.total_documents) * 100, 100)
                        : 0
                    }%`,
                  }}
                />
              </div>
            </div>

            <dl className="detail-list detail-list--compact">
              <div>
                <dt>Formato</dt>
                <dd>{job.export_format}</dd>
              </div>
              <div>
                <dt>Solicitado el</dt>
                <dd>{formatDateTime(job.created_at)}</dd>
              </div>
              <div>
                <dt>Vencimiento de la descarga</dt>
                <dd>{formatDateTime(job.expires_at)}</dd>
              </div>
            </dl>

            {job.status === 'READY' && (
              <div className="flex justify-end pt-2">
                <Button
                  onClick={() => {
                    void documentsApi.downloadExportZip(job.id)
                  }}
                >
                  Descargar ZIP de exportación
                </Button>
              </div>
            )}

            {job.status === 'FAILED' && (
              <p className="rounded-lg bg-rose-50 p-3 text-xs text-rose-700">
                Error en la exportación: {job.error_message || 'No se pudo completar el empaquetado.'}
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
