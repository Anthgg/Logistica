import { useState } from 'react'
import { gateDocumentsApi } from '../api/gateDocumentsApi'
import type { GateCheckInCapabilities, GateCpvDocumentResponse } from '../types/gate-control'
import { useSensitiveActionGuard } from '../../logistics-permissions/hooks/useSensitiveActionGuard'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { EmptyState, StatusPill } from './ui'

export function GateControlDocumentPanel({
  checkInId, cpvDocument, capabilities, onChanged,
}: {
  checkInId: string
  cpvDocument: GateCpvDocumentResponse | null
  capabilities: GateCheckInCapabilities | null
  onChanged: () => void
}) {
  const [submitting, setSubmitting] = useState<string | null>(null)

  const issueGuard = useSensitiveActionGuard({ permission: LOGISTICS_PERMISSIONS.gateControl.issueCPV })

  const handlePreview = async () => {
    setSubmitting('preview')
    try { await gateDocumentsApi.previewDocument(checkInId); onChanged() } catch (e) { alert(e instanceof Error ? e.message : 'No se pudo previsualizar.') } finally { setSubmitting(null) }
  }
  const handleIssue = async () => {
    setSubmitting('issue')
    try {
      const executed = await issueGuard.run(async () => { await gateDocumentsApi.issueDocument(checkInId) })
      if (executed) onChanged()
    } catch (e) { alert(e instanceof Error ? e.message : 'No se pudo emitir.') } finally { setSubmitting(null) }
  }
  const handleDownload = async () => {
    let url: string | null = null
    try {
      const blob = await gateDocumentsApi.downloadDocument(checkInId)
      url = URL.createObjectURL(blob)
      const a = globalThis.document.createElement('a')
      a.href = url; a.download = `${cpvDocument?.document_code ?? checkInId}.pdf`
      globalThis.document.body.appendChild(a); a.click(); globalThis.document.body.removeChild(a)
    } catch (e) { alert(e instanceof Error ? e.message : 'No se pudo descargar.') } finally {
      if (url) URL.revokeObjectURL(url)
    }
  }

  if (!cpvDocument) {
    return (
      <div className="space-y-3">
        {capabilities?.can_issue_CPV ? (
          <div className="rounded-xl border border-slate-200 bg-white p-3 text-xs">
            <EmptyState title="Sin acta CPV" />
            <div className="mt-3 flex flex-wrap gap-2">
              {capabilities.can_preview_CPV && (
                <button type="button" disabled={submitting === 'preview'} onClick={() => void handlePreview()} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50">
                  {submitting === 'preview' ? 'Generando…' : 'Previsualizar'}
                </button>
              )}
              <button type="button" disabled={submitting === 'issue' || issueGuard.isBlocked} onClick={() => void handleIssue()} className="rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#173a55] disabled:opacity-50">
                {submitting === 'issue' ? 'Emitiendo…' : 'Emitir CPV'}
              </button>
            </div>
          </div>
        ) : (
          <EmptyState title="Sin acta CPV" />
        )}
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <div className="rounded-xl border border-slate-200 bg-white p-3 text-xs">
        <div className="flex items-center justify-between">
          <span className="font-semibold">{cpvDocument.document_code ?? 'Sin código'}</span>
          <StatusPill tone={cpvDocument.status === 'ISSUED' ? 'success' : cpvDocument.status === 'VOID' ? 'danger' : 'warning'}>{cpvDocument.status}</StatusPill>
        </div>
        <dl className="mt-2 grid grid-cols-2 gap-1 md:grid-cols-3">
          <dt className="text-slate-500">Emitido:</dt><dd>{cpvDocument.issued_at ?? '—'}</dd>
          <dt className="text-slate-500">Hash:</dt><dd className="font-mono">{cpvDocument.snapshot_hash?.slice(0, 12) ?? '—'}</dd>
        </dl>
        <div className="mt-3 flex flex-wrap gap-2">
          {capabilities?.can_preview_CPV && (
            <button type="button" disabled={submitting === 'preview'} onClick={() => void handlePreview()} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50">{submitting === 'preview' ? 'Generando…' : 'Previsualizar'}</button>
          )}
          {capabilities?.can_issue_CPV && (
            <button type="button" disabled={submitting === 'issue' || issueGuard.isBlocked} onClick={() => void handleIssue()} className="rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#173a55] disabled:opacity-50">{submitting === 'issue' ? 'Emitiendo…' : 'Emitir CPV'}</button>
          )}
          {capabilities?.can_download_CPV && (
            <button type="button" onClick={() => void handleDownload()} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50">Descargar acta</button>
          )}
        </div>
      </div>
    </div>
  )
}
