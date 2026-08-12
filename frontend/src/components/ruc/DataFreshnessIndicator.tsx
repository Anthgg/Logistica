import type { RucFreshnessStatus } from '../../types/ruc-integration'

interface Props {
  freshnessStatus: RucFreshnessStatus
  sourceDate: string // ISO date or datetime
  lookupDate?: string
  ageInDays?: number
  showAbsoluteDate?: boolean
}

const FRESHNESS_CONFIG: Record<RucFreshnessStatus, { label: string; className: string }> = {
  FRESH: {
    label: 'Actual',
    className: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  },
  AGING: {
    label: 'Envejeciendo',
    className: 'bg-yellow-50 text-yellow-800 border-yellow-200',
  },
  STALE: {
    label: 'Desactualizado',
    className: 'bg-orange-50 text-orange-800 border-orange-200',
  },
  CRITICAL: {
    label: 'Crítico',
    className: 'bg-red-50 text-red-800 border-red-200',
  },
  UNKNOWN: {
    label: 'Desconocido',
    className: 'bg-slate-50 text-slate-600 border-slate-200',
  },
}

export function DataFreshnessIndicator({
  freshnessStatus,
  sourceDate,
  ageInDays,
  showAbsoluteDate = true,
}: Props) {
  const cfg = FRESHNESS_CONFIG[freshnessStatus] ?? FRESHNESS_CONFIG.UNKNOWN

  const formattedDate = sourceDate
    ? new Date(sourceDate).toLocaleDateString('es-PE', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
      })
    : '—'

  return (
    <div className={`inline-flex items-center gap-2 rounded-lg border px-3 py-1.5 text-xs font-medium ${cfg.className}`}>
      <span className="font-semibold uppercase tracking-wider">{cfg.label}</span>
      {showAbsoluteDate && (
        <span className="border-l border-current/20 pl-2">
          Fecha fuente: {formattedDate}
          {typeof ageInDays === 'number' && ` (${ageInDays}d)`}
        </span>
      )}
    </div>
  )
}
