import type {
  EvaluationCapabilities,
  QuotationEvaluationCandidate,
} from '../types/evaluation'
import { formatMoney } from '../format'
import { StatusPill, EmptyState } from './ui/SharedState'

export function EvaluationCandidatesPanel({
  candidates,
  capabilities,
}: {
  evaluationId: string
  candidates: QuotationEvaluationCandidate[]
  capabilities: EvaluationCapabilities
}) {
  if (candidates.length === 0) return <EmptyState title="Sin candidatos" />
  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200">
      <table className="min-w-full divide-y divide-slate-200 text-xs">
        <thead className="bg-slate-50/60 font-semibold uppercase text-slate-500">
          <tr>
            <th className="px-3 py-2.5 text-left">Proveedor</th>
            <th className="px-3 py-2.5 text-left">Respuesta</th>
            <th className="px-3 py-2.5 text-left">Moneda</th>
            <th className="px-3 py-2.5 text-right">Total declarado</th>
            <th className="px-3 py-2.5 text-left">Completitud</th>
            <th className="px-3 py-2.5 text-center">Tardía</th>
            <th className="px-3 py-2.5 text-left">Elegibilidad</th>
            <th className="px-3 py-2.5 text-right">Documentos</th>
            <th className="px-3 py-2.5 text-right">Riesgos</th>
            <th className="px-3 py-2.5 text-left">Estado</th>
            <th className="px-3 py-2.5 text-left">Advertencias</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {candidates.map((c) => {
            const showPrice = capabilities.can_view_prices && c.can_view_prices
            const showRisk = capabilities.can_view_risk && c.can_view_risk
            return (
              <tr key={c.id} className="hover:bg-slate-50/60">
                <td className="px-3 py-2">
                  <div className="font-semibold">{c.supplier_name}</div>
                  <div className="font-mono text-[11px] text-slate-500">{c.supplier_code}</div>
                </td>
                <td className="px-3 py-2 font-mono">{c.response_number}</td>
                <td className="px-3 py-2">{c.currency}</td>
                <td className="px-3 py-2 text-right font-mono">
                  {showPrice ? formatMoney(c.total_declared, c.currency) : <span className="text-slate-400">Restringido</span>}
                </td>
                <td className="px-3 py-2 font-mono">{c.completeness ?? '—'}</td>
                <td className="px-3 py-2 text-center">{c.is_late_response ? 'Sí' : 'No'}</td>
                <td className="px-3 py-2">
                  {c.is_disqualified ? (
                    <StatusPill tone="danger">Descalificado</StatusPill>
                  ) : c.is_eligible ? (
                    <StatusPill tone="success">Elegible</StatusPill>
                  ) : (
                    <StatusPill tone="warning">Revisar</StatusPill>
                  )}
                </td>
                <td className="px-3 py-2 text-right font-mono">{c.documents_count}</td>
                <td className="px-3 py-2 text-right font-mono">
                  {showRisk ? c.risks_count : <span className="text-slate-400">—</span>}
                </td>
                <td className="px-3 py-2">
                  {c.disqualification_reason ? (
                    <span className="text-rose-600">{c.disqualification_reason}</span>
                  ) : '—'}
                </td>
                <td className="px-3 py-2">
                  {c.warnings.length > 0 ? (
                    <ul className="list-disc pl-3 text-[11px] text-amber-700">
                      {c.warnings.map((w) => <li key={w}>{w}</li>)}
                    </ul>
                  ) : '—'}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}