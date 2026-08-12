import { useState } from 'react'
import { purchaseRequisitionsApi } from '../../api/purchase-requisitions-api'
import type { PurchaseRequisitionRevision } from '../../types/purchase-requisitions'

interface Props {
  requisitionId: string
  revisions: PurchaseRequisitionRevision[]
}

export function PurchaseRequisitionRevisionsPanel({ requisitionId, revisions }: Props) {
  const [selectedRevA, setSelectedRevA] = useState<number>(1)
  const [selectedRevB, setSelectedRevB] = useState<number>(revisions.length > 1 ? revisions.length : 1)
  const [diffs, setDiffs] = useState<Array<{ field_name: string; field_label: string; value_a: string; value_b: string; change_type: 'ADDED' | 'REMOVED' | 'MODIFIED' }> | null>(null)
  const [loadingDiff, setLoadingDiff] = useState(false)

  const handleCompare = async () => {
    setLoadingDiff(true)
    try {
      const res = await purchaseRequisitionsApi.compareRevisions(requisitionId, selectedRevA, selectedRevB)
      setDiffs(res.diffs || [])
    } catch {
      setDiffs([])
    } finally {
      setLoadingDiff(false)
    }
  }

  return (
    <div className="space-y-6 text-xs">
      <div className="flex items-center justify-between border-b border-slate-200 pb-3">
        <h4 className="font-bold uppercase tracking-wider text-slate-500 text-xs">
          Revisiones Inmutables ({revisions.length})
        </h4>
      </div>

      <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
        <table className="min-w-full divide-y divide-slate-200">
          <thead className="bg-slate-50 text-slate-600">
            <tr>
              <th className="px-4 py-3 text-left font-semibold">Revisión</th>
              <th className="px-4 py-3 text-left font-semibold">Estado</th>
              <th className="px-4 py-3 text-left font-semibold">Justificación Resumida</th>
              <th className="px-4 py-3 text-center font-semibold">Líneas</th>
              <th className="px-4 py-3 text-left font-semibold">Creado por</th>
              <th className="px-4 py-3 text-left font-semibold">Fecha</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 bg-white">
            {revisions.map((r) => (
              <tr key={r.id} className="hover:bg-slate-50">
                <td className="px-4 py-3 font-mono font-bold text-indigo-700">v{r.revision_number}</td>
                <td className="px-4 py-3">
                  <span className={`rounded px-2 py-0.5 text-[10px] font-bold ${r.is_current ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-600'}`}>
                    {r.status} {r.is_current ? '(Actual)' : ''}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-800 font-medium">{r.summary_justification}</td>
                <td className="px-4 py-3 text-center font-mono font-bold">{r.lines_count}</td>
                <td className="px-4 py-3 text-slate-600">{r.created_by_user_name}</td>
                <td className="px-4 py-3 text-slate-500 font-mono">{new Date(r.created_at).toLocaleString('es-PE')}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Revision Comparison */}
      {revisions.length > 1 && (
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs space-y-4">
          <h4 className="font-bold text-slate-800 text-sm border-b border-slate-100 pb-2">
            Comparador Side-by-Side de Revisiones
          </h4>

          <div className="flex items-center gap-3">
            <span>Comparar v</span>
            <select
              value={selectedRevA}
              onChange={(e) => setSelectedRevA(parseInt(e.target.value, 10))}
              className="rounded-lg border border-slate-300 px-2 py-1 bg-white font-mono"
            >
              {revisions.map((r) => <option key={r.id} value={r.revision_number}>v{r.revision_number}</option>)}
            </select>
            <span>con v</span>
            <select
              value={selectedRevB}
              onChange={(e) => setSelectedRevB(parseInt(e.target.value, 10))}
              className="rounded-lg border border-slate-300 px-2 py-1 bg-white font-mono"
            >
              {revisions.map((r) => <option key={r.id} value={r.revision_number}>v{r.revision_number}</option>)}
            </select>
            <button
              type="button"
              onClick={handleCompare}
              disabled={loadingDiff}
              className="rounded-lg bg-indigo-600 px-3 py-1 font-bold text-white hover:bg-indigo-700"
            >
              {loadingDiff ? 'Comparando...' : 'Comparar Cambios'}
            </button>
          </div>

          {diffs && (
            <div className="space-y-2">
              {diffs.length === 0 ? (
                <p className="text-slate-400">Sin diferencias encontradas entre las revisiones seleccionadas.</p>
              ) : (
                <div className="overflow-x-auto rounded-xl border border-slate-200">
                  <table className="min-w-full divide-y divide-slate-200">
                    <thead className="bg-slate-50 text-slate-600">
                      <tr>
                        <th className="px-3 py-2 text-left font-semibold">Campo / Atributo</th>
                        <th className="px-3 py-2 text-left font-semibold">Valor en v{selectedRevA}</th>
                        <th className="px-3 py-2 text-left font-semibold">Valor en v{selectedRevB}</th>
                        <th className="px-3 py-2 text-center font-semibold">Tipo Cambio</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 bg-white font-mono">
                      {diffs.map((d, idx) => (
                        <tr key={idx}>
                          <td className="px-3 py-2 font-sans font-bold text-slate-800">{d.field_label || d.field_name}</td>
                          <td className="px-3 py-2 text-slate-600">{d.value_a || '—'}</td>
                          <td className="px-3 py-2 font-bold text-indigo-700">{d.value_b || '—'}</td>
                          <td className="px-3 py-2 text-center">
                            <span className="rounded bg-indigo-100 px-2 py-0.5 font-sans font-bold text-[10px] text-indigo-800">
                              {d.change_type}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
