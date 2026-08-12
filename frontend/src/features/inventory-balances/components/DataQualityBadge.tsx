import type { InventoryBalanceDataQualityStatus } from '../types/inventory-balances'

const qualityLabels: Record<InventoryBalanceDataQualityStatus, string> = {
  VERIFIED: 'Verificado',
  RECONCILED: 'Reconciliado',
  CURRENT: 'Actual',
  LAGGING: 'Atrasado',
  PARTIAL_BASELINE: 'Baseline parcial',
  MISSING_BASELINE: 'Baseline faltante',
  INTEGRITY_FAILED: 'Integridad fallida',
  UNIT_CONFLICT: 'Conflicto de unidad',
  POSITION_CONFLICT: 'Conflicto de posición',
  NEGATIVE: 'Negativo',
  REBUILD_REQUIRED: 'Rebuild requerido',
  UNKNOWN: 'Desconocido',
}

const qualityColors: Record<InventoryBalanceDataQualityStatus, string> = {
  VERIFIED: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  RECONCILED: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  CURRENT: 'border-blue-200 bg-blue-50 text-blue-700',
  LAGGING: 'border-amber-200 bg-amber-50 text-amber-700',
  PARTIAL_BASELINE: 'border-amber-200 bg-amber-50 text-amber-700',
  MISSING_BASELINE: 'border-rose-200 bg-rose-50 text-rose-700',
  INTEGRITY_FAILED: 'border-rose-200 bg-rose-100 text-rose-800',
  UNIT_CONFLICT: 'border-rose-200 bg-rose-50 text-rose-700',
  POSITION_CONFLICT: 'border-rose-200 bg-rose-50 text-rose-700',
  NEGATIVE: 'border-rose-200 bg-rose-50 text-rose-700',
  REBUILD_REQUIRED: 'border-violet-200 bg-violet-50 text-violet-700',
  UNKNOWN: 'border-slate-200 bg-slate-50 text-slate-600',
}

const qualityDot: Record<InventoryBalanceDataQualityStatus, string> = {
  VERIFIED: 'bg-emerald-500',
  RECONCILED: 'bg-emerald-500',
  CURRENT: 'bg-blue-500',
  LAGGING: 'bg-amber-500',
  PARTIAL_BASELINE: 'bg-amber-500',
  MISSING_BASELINE: 'bg-rose-500',
  INTEGRITY_FAILED: 'bg-rose-600',
  UNIT_CONFLICT: 'bg-rose-500',
  POSITION_CONFLICT: 'bg-rose-500',
  NEGATIVE: 'bg-rose-500',
  REBUILD_REQUIRED: 'bg-violet-500',
  UNKNOWN: 'bg-slate-400',
}

export function DataQualityBadge({
  status,
  className,
}: {
  status: InventoryBalanceDataQualityStatus
  className?: string
}) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-medium leading-none ${qualityColors[status]} ${className ?? ''}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full shrink-0 ${qualityDot[status]}`} aria-hidden="true" />
      {qualityLabels[status]}
    </span>
  )
}
