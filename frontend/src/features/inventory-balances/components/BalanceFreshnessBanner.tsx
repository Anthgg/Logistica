import type {
  InventoryBalanceFreshnessState,
  InventoryBalanceFreshness,
} from '../types/inventory-balances'

const freshnessLabels: Record<InventoryBalanceFreshnessState, string> = {
  CURRENT: 'Actual',
  NEAR_REAL_TIME: 'Casi en tiempo real',
  LAGGING: 'Atrasado',
  OBSOLETE: 'Obsoleto',
  REBUILDING: 'Reconstruyendo',
  INTEGRITY_FAILED: 'Integridad fallida',
}

const freshnessColors: Record<InventoryBalanceFreshnessState, string> = {
  CURRENT: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  NEAR_REAL_TIME: 'border-blue-200 bg-blue-50 text-blue-700',
  LAGGING: 'border-amber-200 bg-amber-50 text-amber-700',
  OBSOLETE: 'border-rose-200 bg-rose-50 text-rose-700',
  REBUILDING: 'border-violet-200 bg-violet-50 text-violet-700',
  INTEGRITY_FAILED: 'border-rose-200 bg-rose-100 text-rose-800',
}

const freshnessDot: Record<InventoryBalanceFreshnessState, string> = {
  CURRENT: 'bg-emerald-500',
  NEAR_REAL_TIME: 'bg-blue-500',
  LAGGING: 'bg-amber-500',
  OBSOLETE: 'bg-rose-500',
  REBUILDING: 'bg-violet-500',
  INTEGRITY_FAILED: 'bg-rose-600',
}

export function BalanceFreshnessBanner({
  freshness,
}: {
  freshness: InventoryBalanceFreshness
}) {
  const state = freshness.state
  return (
    <div className={`flex items-center gap-3 rounded-lg border px-3 py-2 text-xs ${freshnessColors[state]}`}>
      <span className={`h-2 w-2 rounded-full shrink-0 ${freshnessDot[state]}`} aria-hidden="true" />
      <div className="flex-1 min-w-0">
        <span className="font-medium">{freshnessLabels[state]}</span>
        <span className="ml-2 text-muted">
          Secuencia {freshness.balance_sequence.toLocaleString('es-PE')}
          {freshness.lag_movements > 0 && (
            <> · {freshness.lag_movements.toLocaleString('es-PE')} movimientos pendientes</>
          )}
        </span>
      </div>
      {freshness.warehouse_name && (
        <span className="text-muted shrink-0">{freshness.warehouse_name}</span>
      )}
    </div>
  )
}
