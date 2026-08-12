import { useEffect, useState } from 'react'
import { documentsApi } from '../../api/documents-api'
import { Button } from './Button'
import { StatusBadge } from './StatusBadge'
import type { DocumentDetail, DocumentHistoryEntry } from '../../types/logistics-documents'
import { formatDateTime } from '../../utils/date'
import { getErrorMessage } from '../../utils/errors'

interface DocumentDetailPanelProps {
  documentId: string | null
  onClose: () => void
  onPreview?: (doc: DocumentDetail) => void
  onDownload?: (doc: DocumentDetail) => void
  onReprint?: (doc: DocumentDetail) => void
  onCancel?: (doc: DocumentDetail) => void
}

export function DocumentDetailPanel({
  documentId,
  onClose,
  onPreview,
  onDownload,
  onReprint,
  onCancel,
}: DocumentDetailPanelProps) {
  const [doc, setDoc] = useState<DocumentDetail | null>(null)
  const [history, setHistory] = useState<DocumentHistoryEntry[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!documentId) {
      setDoc(null)
      setHistory([])
      return undefined
    }

    let active = true
    setIsLoading(true)
    setError(null)

    Promise.all([documentsApi.get(documentId), documentsApi.getHistory(documentId)])
      .then(([detailData, historyData]) => {
        if (!active) return
        setDoc(detailData)
        setHistory(historyData)
      })
      .catch((err: unknown) => {
        if (active) setError(getErrorMessage(err))
      })
      .finally(() => {
        if (active) setIsLoading(false)
      })

    return () => {
      active = false
    }
  }, [documentId])

  if (!documentId) return null

  return (
    <div
      className="fixed inset-0 z-[70] flex justify-end bg-slate-950/40 backdrop-blur-xs"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div className="flex h-full w-full max-w-2xl flex-col bg-white shadow-2xl overflow-hidden border-l border-slate-200">
        {/* Encabezado del panel */}
        <div className="flex items-center justify-between border-b border-slate-200 bg-slate-50 px-5 py-4">
          <div>
            <p className="text-[10px] font-bold text-blue-700 uppercase tracking-wider">
              Detalle documental inmutable
            </p>
            <h2 className="text-lg font-bold text-slate-900">{doc?.code || 'Cargando…'}</h2>
          </div>
          <button
            type="button"
            className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 hover:bg-slate-200 hover:text-slate-700"
            onClick={onClose}
            aria-label="Cerrar panel"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" aria-hidden="true"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>

        {/* Contenido principal */}
        <div className="flex-1 overflow-y-auto p-5 space-y-6">
          {isLoading && (
            <div className="loading-panel">
              <span className="spinner" />
              <p>Consultando snapshot del documento…</p>
            </div>
          )}

          {error && <p className="text-xs font-semibold text-rose-600">{error}</p>}

          {doc && (
            <>
              {/* Acciones principales */}
              <div className="flex flex-wrap items-center gap-2 border-b border-slate-100 pb-4">
                {doc.capabilities.can_preview && onPreview && (
                  <Button size="small" variant="secondary" onClick={() => onPreview(doc)}>
                    Ver vista previa
                  </Button>
                )}
                {doc.capabilities.can_download && onDownload && (
                  <Button size="small" variant="ghost" onClick={() => onDownload(doc)}>
                    Descargar PDF
                  </Button>
                )}
                {doc.capabilities.can_reprint && onReprint && (
                  <Button size="small" variant="ghost" onClick={() => onReprint(doc)}>
                    Reimprimir
                  </Button>
                )}
                {doc.capabilities.can_cancel && doc.status !== 'CANCELLED' && onCancel && (
                  <Button size="small" variant="ghost" onClick={() => onCancel(doc)}>
                    Anular
                  </Button>
                )}
              </div>

              {/* Atributos del documento */}
              <section className="space-y-2">
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                  Metadatos principales
                </h3>
                <dl className="detail-list detail-list--compact">
                  <div>
                    <dt>Título</dt>
                    <dd>{doc.title}</dd>
                  </div>
                  <div>
                    <dt>Familia</dt>
                    <dd>{doc.family}</dd>
                  </div>
                  <div>
                    <dt>Estado</dt>
                    <dd>
                      <StatusBadge value={doc.status.toLowerCase()}>{doc.status}</StatusBadge>
                    </dd>
                  </div>
                  <div>
                    <dt>Emisor</dt>
                    <dd>{doc.issued_by_user_name || 'Sistema'}</dd>
                  </div>
                  <div>
                    <dt>Fecha de emisión</dt>
                    <dd>{formatDateTime(doc.issued_at)}</dd>
                  </div>
                  <div>
                    <dt>Reimpresiones</dt>
                    <dd>{doc.reprint_count}</dd>
                  </div>
                  <div>
                    <dt>Integridad (SHA-256)</dt>
                    <dd>
                      <code className="font-mono text-[10px] text-slate-600 bg-slate-100 px-1 py-0.5 rounded">
                        {doc.hash_sha256.slice(0, 16)}…
                      </code>
                    </dd>
                  </div>
                </dl>
              </section>

              {/* Snapshot inmutable de contenido */}
              <section className="space-y-2">
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                  Snapshot inmutable al emitir
                </h3>
                <pre className="max-h-48 overflow-auto rounded-xl border border-slate-200 bg-slate-900 p-3 font-mono text-[10px] text-blue-300">
                  {JSON.stringify(doc.content_snapshot, null, 2)}
                </pre>
              </section>

              {/* Línea temporal de eventos */}
              <section className="space-y-3">
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                  Historial de auditoría
                </h3>
                <ul className="timeline">
                  {history.map((entry) => (
                    <li key={entry.id}>
                      <span className="timeline__dot" />
                      <div>
                        <div className="timeline__title">
                          <strong className="text-xs font-bold text-slate-900">
                            {entry.event_type}
                          </strong>
                          <time>{formatDateTime(entry.created_at)}</time>
                        </div>
                        <p className="text-xs text-slate-600">{entry.description}</p>
                        {entry.user_name && (
                          <small className="text-[10px] text-slate-400">
                            Por: {entry.user_name}
                          </small>
                        )}
                        {entry.reason && (
                          <p className="mt-1 rounded bg-slate-50 p-2 text-[11px] font-medium text-slate-700 italic border border-slate-200">
                            «{entry.reason}»
                          </p>
                        )}
                      </div>
                    </li>
                  ))}
                </ul>
              </section>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
