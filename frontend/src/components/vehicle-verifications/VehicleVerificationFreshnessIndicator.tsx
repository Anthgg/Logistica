import type { VehicleVerificationFreshness } from '../../types/vehicle-verifications'

interface Props {
  freshness: VehicleVerificationFreshness
  sourceDate?: string | null
  expirationDate?: string | null
  daysUntilExpiration?: number | null
  size?: 'sm' | 'md'
}

const FRESHNESS_CONFIG: Record<
  VehicleVerificationFreshness,
  { label: string; className: string }
> = {
  FRESH: { label: 'Vigente', className: 'bg-emerald-100 text-emerald-800 border-emerald-300' },
  AGING: { label: 'Envejeciendo', className: 'bg-blue-100 text-blue-800 border-blue-300' },
  STALE: { label: 'Desactualizada', className: 'bg-amber-100 text-amber-800 border-amber-300' },
  CRITICAL: { label: 'Por Vencer (Crítica)', className: 'bg-orange-100 text-orange-800 border-orange-300' },
  EXPIRED: { label: 'Vencida', className: 'bg-rose-100 text-rose-800 border-rose-300' },
  UNKNOWN: { label: 'Desconocida', className: 'bg-slate-100 text-slate-600 border-slate-300' },
}

export function VehicleVerificationFreshnessIndicator({
  freshness,
  sourceDate,
  expirationDate,
  daysUntilExpiration,
  size = 'md',
}: Props) {
  const cfg = FRESHNESS_CONFIG[freshness] ?? {
    label: freshness,
    className: 'bg-slate-100 text-slate-600 border-slate-300',
  }
  const sizeClass = size === 'sm' ? 'text-[10px] px-2 py-0.5' : 'text-xs px-2.5 py-1'

  const formattedSourceDate = sourceDate
    ? new Date(sourceDate).toLocaleDateString('es-PE', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      })
    : null

  const formattedExpDate = expirationDate
    ? new Date(expirationDate).toLocaleDateString('es-PE', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      })
    : null

  return (
    <div className="inline-flex flex-col items-start gap-0.5 text-xs">
      <span className={`inline-flex items-center rounded-full font-bold border ${sizeClass} ${cfg.className}`}>
        {cfg.label}
      </span>

      {(formattedSourceDate || formattedExpDate) && (
        <div className="text-[10px] text-slate-500 font-mono space-y-0.5 pt-0.5">
          {formattedSourceDate && <div>Fuente: {formattedSourceDate}</div>}
          {formattedExpDate && (
            <div>
              Vence: {formattedExpDate}
              {daysUntilExpiration !== null && daysUntilExpiration !== undefined && (
                <span className={daysUntilExpiration < 0 ? 'text-rose-600 font-bold ml-1' : 'text-slate-600 ml-1'}>
                  ({daysUntilExpiration < 0 ? `hace ${Math.abs(daysUntilExpiration)} días` : `en ${daysUntilExpiration} días`})
                </span>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
