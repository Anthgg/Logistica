import { useCallback, useEffect, useState } from 'react'
import { evaluationDocumentsApi } from '../api/evaluationDocumentsApi'
import type { ComparativeDocument, EvaluationCapabilities } from '../types/evaluation'
import { comparativeDocumentStatusLabel, generateIdempotencyKey } from '../format'
import { ErrorState, StatusPill, TableSkeleton, EmptyState } from './ui/SharedState'
import { useSensitiveActionGuard } from '../../logistics-permissions/hooks/useSensitiveActionGuard'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'

export function ComparativeDocumentPanel({
  evaluationId,
  capabilities,
}: {
  evaluationId: string
  capabilities: EvaluationCapabilities
}) {
  const [doc, setDoc] = useState<ComparativeDocument | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isError, setIsError] = useState(false)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState<string | null>(null)

  const issueGuard = useSensitiveActionGuard({
    permission: LOGISTICS_PERMISSIONS.supplierEvaluations.issueCCO,
  })

  const load = useCallback(async () => {
    setIsLoading(true)
    setIsError(false)
    try {
      setDoc(await evaluationDocumentsApi.getComparativeDocument(evaluationId))
    } catch (err: unknown) {
      // 404 => sin documento
      setIsError(false)
      setDoc(null)
      setError(err instanceof Error ? err.message : '')
    } finally {
      setIsLoading(false)
    }
  }, [evaluationId])

  useEffect(() => { void load() }, [load])

  const handlePreview = async () => {
    setSubmitting('preview')
    try {
      await evaluationDocumentsApi.previewComparativeDocument(evaluationId, generateIdempotencyKey())
      await load()
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'No se pudo previsualizar.')
    } finally {
      setSubmitting(null)
    }
  }

  const handleIssue = async () => {
    setSubmitting('issue')
    try {
      const executed = await issueGuard.run(async () => {
        await evaluationDocumentsApi.issueComparativeDocument(evaluationId, generateIdempotencyKey())
      })
      if (executed) await load()
    } finally {
      setSubmitting(null)
    }
  }

  const handleDownload = async () => {
    if (!doc) return
    try {
      const blob = await evaluationDocumentsApi.downloadComparativeDocument(evaluationId, doc.id)
      triggerDownload(blob, `${doc.code}.pdf`)
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'No se pudo descargar.')
    }
  }

  if (isLoading) return <TableSkeleton />
  if (isError && error) return <ErrorState message={error} onRetry={() => void load()} />

  return (
    <div className="space-y-3">
      {!doc ? (
        <>
          {capabilities.can_preview_CCO ? (
            <div className="flex items-center justify-between">
              <p className="text-xs text-slate-500">No hay documento CCO. Genera una previsualización.</p>
              <button type="button" disabled={submitting === 'preview'} onClick={handlePreview} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50">
                {submitting === 'preview' ? 'Generando…' : 'Previsualizar'}
              </button>
            </div>
          ) : (
            <EmptyState title="Sin documento CCO" />
          )}
        </>
      ) : (
        <div className="rounded-xl border border-slate-200 p-3 text-xs">
          <div className="flex items-center justify-between">
            <div>
              <span className="font-semibold">{doc.code}</span>
              {doc.status === 'PREVIEW' && <span className="ml-2 text-rose-600">NO OFICIAL</span>}
            </div>
            <StatusPill tone={doc.status === 'ISSUED' ? 'success' : 'warning'}>{comparativeDocumentStatusLabel(doc.status)}</StatusPill>
          </div>
          <dl className="mt-2 grid grid-cols-2 gap-1 md:grid-cols-3">
            <dt className="text-slate-500">Versión:</dt><dd>{doc.version}</dd>
            <dt className="text-slate-500">Emitido:</dt><dd>{doc.issued_at ?? '—'}</dd>
            <dt className="text-slate-500">Hash:</dt><dd className="font-mono">{doc.partial_hash?.slice(0, 12) ?? '—'}</dd>
            <dt className="text-slate-500">Integridad:</dt><dd>{doc.integrity_ok ? 'OK' : '—'}</dd>
            <dt className="text-slate-500">Archivo:</dt><dd>{doc.file_name ?? '—'}</dd>
          </dl>
          <div className="mt-3 flex flex-wrap gap-2">
            {capabilities.can_preview_CCO && doc.can_preview && (
              <button type="button" disabled={submitting === 'preview'} onClick={handlePreview} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50">{submitting === 'preview' ? 'Generando…' : 'Previsualizar'}</button>
            )}
            {capabilities.can_issue_CCO && doc.can_issue && (
              <button type="button" disabled={submitting === 'issue' || issueGuard.isBlocked} onClick={handleIssue} className="rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#173a55] disabled:opacity-50">{submitting === 'issue' ? 'Emitiendo…' : 'Emitir'}</button>
            )}
            {capabilities.can_issue_CCO && doc.can_download && (
              <button type="button" onClick={handleDownload} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50">Descargar PDF</button>
            )}
          </div>
          <p className="mt-2 text-[11px] text-slate-500">No se modifica un CCO emitido.</p>
        </div>
      )}
    </div>
  )
}

function triggerDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}