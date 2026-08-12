import { useCallback, useEffect, useState } from 'react'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../../components/ui/select'
import { LogisticsIcon } from '../../../components/common/LogisticsIcon'
import { quotationEvaluationsApi } from '../api/quotationEvaluationsApi'
import type {
  ComparisonViewMode,
  EvaluationCapabilities,
  SupplierComparisonMatrix,
} from '../types/evaluation'
import { comparisonViewModeLabel } from '../format'
import { ErrorState, TableSkeleton } from './ui/SharedState'

export function SupplierComparisonMatrixPanel({
  evaluationId,
  capabilities,
}: {
  evaluationId: string
  capabilities: EvaluationCapabilities
}) {
  const [view, setView] = useState<ComparisonViewMode>('WEIGHTED')
  const [matrix, setMatrix] = useState<SupplierComparisonMatrix | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isError, setIsError] = useState(false)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    setIsLoading(true)
    setIsError(false)
    try {
      setMatrix(await quotationEvaluationsApi.getComparison(evaluationId, view))
    } catch (err: unknown) {
      setIsError(true)
      setError(err instanceof Error ? err.message : 'No se pudo cargar la comparación.')
    } finally {
      setIsLoading(false)
    }
  }, [evaluationId, view])

  useEffect(() => { void load() }, [load])

  if (isLoading) return <TableSkeleton />
  if (isError) return <ErrorState message={error} onRetry={() => void load()} />
  if (!matrix) return <p className="text-xs text-slate-500">Sin comparación disponible.</p>

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-xs text-slate-500">
          Encabezado fijo y primera columna fija. No se usan colores como única señal.
          {capabilities.can_view_prices ? '' : ' Precios restringidos por permiso.'}
        </p>
        <Select value={view} onValueChange={(v) => setView(v as ComparisonViewMode)}>
          <SelectTrigger className="w-[200px]"><SelectValue /></SelectTrigger>
          <SelectContent>
            {(['ORIGINAL', 'NORMALIZED', 'SCORE', 'WEIGHTED'] as ComparisonViewMode[]).map((m) => (
              <SelectItem key={m} value={m}>{comparisonViewModeLabel(m)}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="overflow-auto rounded-xl border border-slate-200" style={{ maxHeight: '70vh' }}>
        <table className="min-w-full border-collapse text-xs">
          <thead className="sticky top-0 z-10 bg-slate-50/95 backdrop-blur">
            <tr>
              <th scope="col" className="sticky left-0 z-20 bg-slate-50/95 px-3 py-2.5 text-left font-semibold uppercase text-slate-500">
                Criterio
              </th>
              {matrix.suppliers.map((s) => (
                <th key={s.candidate_id} scope="col" className="px-3 py-2.5 text-left font-semibold uppercase text-slate-500">
                  <span>{s.supplier_name}</span>
                  {s.is_disqualified && <span className="ml-1 text-rose-600">(desc.)</span>}
                  {s.is_tied && <span className="ml-1 text-amber-600">(empate)</span>}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {matrix.rows.map((row) => (
              <tr key={row.code} className="hover:bg-slate-50/40">
                <th scope="row" className="sticky left-0 z-10 bg-white px-3 py-2 text-left font-medium text-slate-700">
                  <span className="font-mono">{row.code}</span> · {row.label}
                  <span className="ml-1 text-[10px] text-slate-400">(w {row.weight})</span>
                </th>
                {row.cells.map((cell) => (
                  <td key={cell.candidate_id} className="px-3 py-2 font-mono">
                    {cell.value ?? '—'}
                    {cell.warnings.length > 0 && (
                      <span className="ml-1 text-amber-600" title={cell.warnings.join('; ')}><LogisticsIcon name="alert" size={14} aria-hidden /></span>
                    )}
                    {cell.explanation && (
                      <span className="ml-1 text-slate-400" title={cell.explanation}>ⓘ</span>
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}