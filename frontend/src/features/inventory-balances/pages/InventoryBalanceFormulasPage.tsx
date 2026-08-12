import { PageHeader } from '../../../components/common/PageHeader'
import { Alert } from '../../../components/common/Alert'
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton'
import { useQuery } from '../../inbound-docks/hooks/useQuery'
import { getErrorMessage } from '../../../utils/errors'
import type { InventoryBalanceFormula } from '../types/inventory-balances'

export function InventoryBalanceFormulasPage() {
  const formulas = useQuery<InventoryBalanceFormula[]>(
    ['inventory-balances', 'formulas'],
    '/logistics/inventory/balances/formulas',
  )

  return (
    <div className="space-y-6 pb-10">
      <PageHeader
        eyebrow="Fase 045"
        title="Fórmulas de saldo"
        description="Definiciones declarativas de cómo se calculan las métricas de saldo."
      />

      <Alert variant="info">
        Las fórmulas son definiciones legibles del backend. No se permiten ediciones mediante código libre.
      </Alert>

      {formulas.isLoading && <LoadingSkeleton rows={6} />}
      {formulas.isError && <Alert variant="error">{getErrorMessage(formulas.error)}</Alert>}

      {formulas.data && formulas.data.length === 0 && (
        <Alert variant="info">No hay fórmulas disponibles.</Alert>
      )}

      {formulas.data && formulas.data.length > 0 && (
        <div className="space-y-3">
          {formulas.data.map((f) => (
            <div key={f.formula_id} className="bg-white border border-[#DDE4E8] rounded-[10px] p-4">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-semibold text-ink">{f.metric_label}</h3>
                <span className={`text-[10px] px-2 py-0.5 rounded-full border ${f.status === 'ACTIVE' ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : 'border-slate-200 bg-slate-50 text-slate-600'}`}>
                  {f.status}
                </span>
              </div>
              <p className="text-xs text-muted mb-2">{f.description}</p>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                <div>Dimensión: <span className="text-ink">{f.dimension}</span></div>
                <div>Versión: <span className="text-ink">{f.version}</span></div>
                <div>Vigencia: <span className="text-ink">{new Date(f.effective_from).toLocaleDateString('es-PE')}</span></div>
                <div>Overlap: <span className="text-ink">{f.overlap_allowed ? 'Permitido' : 'No'}</span></div>
              </div>
              {f.mutually_exclusive_group && (
                <p className="text-[10px] text-muted mt-1">Grupo exclusivo: {f.mutually_exclusive_group}</p>
              )}
              <div className="mt-2 p-2 bg-slate-50 rounded text-xs font-mono text-muted break-all">
                {f.formula_expression}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
