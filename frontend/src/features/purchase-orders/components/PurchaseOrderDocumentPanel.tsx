import { useState } from 'react'
import { purchaseOrdersV2Api } from '../api/purchaseOrdersV2Api'
import type {
  PurchaseOrderCapabilities,
  PurchaseOrderDocument,
} from '../types/purchase-orders-v2'
import { generateIdempotencyKey } from '../format'
import { EmptyState, StatusPill } from './ui'

export function PurchaseOrderDocumentPanel({
  purchaseOrderId,
  document,
  capabilities,
}: {
  purchaseOrderId: string
  document: PurchaseOrderDocument | null
  capabilities: PurchaseOrderCapabilities
}) {
  const [submitting, setSubmitting] = useState<string | null>(null)

  const handlePreview = async () => {
    setSubmitting('preview')
    try { await purchaseOrdersV2Api.previewDocument(purchaseOrderId, generateIdempotencyKey()); void window.location.reload() } catch (e) { alert(e instanceof Error ? e.message : 'No se pudo previsualizar.') } finally { setSubmitting(null) }
  }
  const handleReprint = async () => {
    setSubmitting('reprint')
    try { await purchaseOrdersV2Api.reprintDocument(purchaseOrderId) } catch (e) { alert(e instanceof Error ? e.message : 'No se pudo reimprimir.') } finally { setSubmitting(null) }
  }
  const handleDownload = async () => {
    if (!document) return
    try {
      const blob = await purchaseOrdersV2Api.downloadDocument(purchaseOrderId, document.id)
      triggerDownload(blob, `${document.code}.pdf`)
    } catch (e) { alert(e instanceof Error ? e.message : 'No se pudo descargar.') }
  }

  if (!document) {
    return (
      <div className="space-y-3">
        {capabilities.can_preview ? (
          <div className="flex items-center justify-between">
            <p className="text-xs text-slate-500">Sin documento. Preview no asigna número oficial.</p>
            <button type="button" disabled={submitting === 'preview'} onClick={handlePreview} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50">{submitting === 'preview' ? 'Generando…' : 'Previsualizar'}</button>
          </div>
        ) : (
          <EmptyState title="Sin documento" />
        )}
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <div className="rounded-xl border border-slate-200 p-3 text-xs">
        <div className="flex items-center justify-between">
          <div>
            <span className="font-semibold">{document.code}</span>
            {document.status === 'PREVIEW' && <span className="ml-2 text-rose-600">NO OFICIAL</span>}
          </div>
          <StatusPill tone={document.status === 'ISSUED' ? 'success' : document.status === 'VOID' ? 'danger' : 'warning'}>{document.status}</StatusPill>
        </div>
        <dl className="mt-2 grid grid-cols-2 gap-1 md:grid-cols-3">
          <dt className="text-slate-500">Versión:</dt><dd>{document.version}</dd>
          <dt className="text-slate-500">Emitido:</dt><dd>{document.issued_at ?? '—'}</dd>
          <dt className="text-slate-500">Hash:</dt><dd className="font-mono">{document.partial_hash?.slice(0, 12) ?? '—'}</dd>
          <dt className="text-slate-500">Integridad:</dt><dd>{document.integrity_ok ? 'OK' : '—'}</dd>
          <dt className="text-slate-500">Reimpresiones:</dt><dd>{document.reprints}</dd>
        </dl>
        <div className="mt-3 flex flex-wrap gap-2">
          {capabilities.can_preview && document.can_preview && (
            <button type="button" disabled={submitting === 'preview'} onClick={handlePreview} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50">{submitting === 'preview' ? 'Generando…' : 'Previsualizar'}</button>
          )}
          {capabilities.can_download && document.can_download && (
            <button type="button" onClick={handleDownload} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50">Descargar PDF</button>
          )}
          {capabilities.can_reprint && document.can_reprint && (
            <button type="button" disabled={submitting === 'reprint'} onClick={handleReprint} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50">{submitting === 'reprint' ? 'Reimprimiendo…' : 'Reimprimir'}</button>
          )}
        </div>
        <p className="mt-2 text-[11px] text-slate-500">No se modifica el PDF emitido.</p>
      </div>
    </div>
  )
}

function triggerDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = filename
  document.body.appendChild(a); a.click(); document.body.removeChild(a)
  URL.revokeObjectURL(url)
}