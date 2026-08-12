import { useCallback, useEffect, useState } from 'react'
import { evaluationExportsApi } from '../api/evaluationExportsApi'
import type { EvaluationCapabilities, EvaluationExport, ExportFormat } from '../types/evaluation'
import { exportStatusLabel } from '../format'
import { ErrorState, StatusPill, TableSkeleton, EmptyState } from './ui/SharedState'

export function EvaluationExportsPanel({
  evaluationId,
  capabilities,
}: {
  evaluationId: string
  capabilities: EvaluationCapabilities
}) {
  const [items, setItems] = useState<EvaluationExport[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isError, setIsError] = useState(false)
  const [error, setError] = useState('')
  const [requesting, setRequesting] = useState(false)

  const load = useCallback(async () => {
    setIsLoading(true)
    setIsError(false)
    try {
      setItems(await evaluationExportsApi.listExports(evaluationId))
    } catch (err: unknown) {
      setIsError(true)
      setError(err instanceof Error ? err.message : 'No se pudieron cargar las exportaciones.')
    } finally {
      setIsLoading(false)
    }
  }, [evaluationId])

  useEffect(() => { void load() }, [load])

  const handleRequest = async (format: ExportFormat) => {
    setRequesting(true)
    try {
      await evaluationExportsApi.requestExport(evaluationId, format)
      await load()
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'No se pudo solicitar la exportación.')
    } finally {
      setRequesting(false)
    }
  }

  const handleDownload = async (exp: EvaluationExport) => {
    try {
      const blob = await evaluationExportsApi.downloadExport(evaluationId, exp.id, exp.format)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${exp.id}.${exp.format.toLowerCase()}`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'No se pudo descargar.')
    }
  }

  if (isLoading) return <TableSkeleton />
  if (isError) return <ErrorState message={error} onRetry={() => void load()} />

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs text-slate-500">
          No se genera CSV/XLSX completamente en el navegador para datos sensibles.
        </p>
        {capabilities.can_export && (
          <div className="flex gap-1">
            {(['PDF', 'CSV', 'XLSX'] as ExportFormat[]).map((f) => (
              <button
                key={f}
                type="button"
                disabled={requesting}
                onClick={() => void handleRequest(f)}
                className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50"
              >
                Solicitar {f}
              </button>
            ))}
          </div>
        )}
      </div>

      {items.length === 0 ? (
        <EmptyState title="Sin exportaciones" />
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200">
          <table className="min-w-full divide-y divide-slate-200 text-xs">
            <thead className="bg-slate-50/60 font-semibold uppercase text-slate-500">
              <tr>
                <th className="px-3 py-2.5 text-left">Formato</th>
                <th className="px-3 py-2.5 text-left">Estado</th>
                <th className="px-3 py-2.5 text-left">Solicitado por</th>
                <th className="px-3 py-2.5 text-left">Fecha</th>
                <th className="px-3 py-2.5 text-left">Vencimiento</th>
                <th className="px-3 py-2.5 text-right">Tamaño</th>
                <th className="px-3 py-2.5 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {items.map((e) => (
                <tr key={e.id} className="hover:bg-slate-50/60">
                  <td className="px-3 py-2 font-mono">{e.format}</td>
                  <td className="px-3 py-2"><StatusPill tone={e.status === 'AVAILABLE' ? 'success' : e.status === 'FAILED' ? 'danger' : 'info'}>{exportStatusLabel(e.status)}</StatusPill></td>
                  <td className="px-3 py-2">{e.requested_by}</td>
                  <td className="px-3 py-2">{new Date(e.requested_at).toLocaleDateString('es-PE')}</td>
                  <td className="px-3 py-2">{e.expires_at ? new Date(e.expires_at).toLocaleDateString('es-PE') : '—'}</td>
                  <td className="px-3 py-2 text-right font-mono">{e.file_size ?? '—'}</td>
                  <td className="px-3 py-2 text-right">
                    {e.status === 'AVAILABLE' && (
                      <button type="button" onClick={() => void handleDownload(e)} className="rounded border border-slate-200 px-2 py-0.5 text-[11px] font-semibold hover:bg-slate-50">Descargar</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}