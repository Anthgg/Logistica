import { Link } from 'react-router-dom'
import { LogisticsIcon } from '../common/LogisticsIcon'
import { useTranslations } from '../../hooks/useTranslations'

const barColors: Record<string, string> = {
  delivered: 'bg-emerald-500', in_transit: 'bg-blue-500', out_for_delivery: 'bg-blue-400',
  pending: 'bg-amber-400', pending_pickup: 'bg-amber-400', registered: 'bg-slate-400',
  delayed: 'bg-rose-500', cancelled: 'bg-rose-400', returned: 'bg-rose-300',
  warehouse_received: 'bg-indigo-400', picked_up: 'bg-indigo-300',
}

interface Props {
  statusMap: Record<string, number>
  total: number
}

const MAX_VISIBLE = 5

export function StatusDistribution({ statusMap, total }: Props) {
  const { language, translate } = useTranslations()
  const sorted = Object.entries(statusMap).sort(([, a], [, b]) => b - a)
  const visible = sorted.slice(0, MAX_VISIBLE)
  const hasMore = sorted.length > MAX_VISIBLE

  return (
    <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      {/* Header */}
      <div className="flex h-12 items-center justify-between border-b border-slate-200 px-4">
        <div className="flex items-center gap-2">
          <span className="flex h-6 w-6 items-center justify-center rounded-md bg-blue-50 text-blue-600" aria-hidden="true">
            <LogisticsIcon name="reports" size={14} />
          </span>
          <div>
            <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400 leading-none">Distribución</p>
            <h2 className="text-sm font-semibold text-slate-800 leading-tight">Por estado</h2>
          </div>
        </div>
        <button
          type="button"
          className="flex h-6 w-6 items-center justify-center rounded-md text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-colors"
          aria-label="Exportar distribución"
        >
          <LogisticsIcon name="archive" size={13} />
        </button>
      </div>

      {/* Rows */}
      <div className="divide-y divide-slate-50 px-4 py-1">
        {visible.map(([status, count]) => {
          const pct = total > 0 ? Math.round((count / total) * 100) : 0
          const barColor = barColors[status] ?? 'bg-slate-400'
          const label = translate('status', status, status)
          return (
            <div key={status} className="py-2">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-slate-600 truncate">{label}</span>
                <span className="flex items-center gap-2 shrink-0 ml-2">
                  <span className="text-xs font-semibold text-slate-800">{count}</span>
                  <span className="w-9 text-right text-[10px] text-slate-400">{pct}%</span>
                </span>
              </div>
              <div
                className="h-1.5 overflow-hidden rounded-full bg-slate-100"
                role="progressbar"
                aria-label={label}
                aria-valuenow={count}
                aria-valuemin={0}
                aria-valuemax={total}
              >
                <div
                  className={`h-full rounded-full transition-colors duration-500 ${barColor}`}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          )
        })}

        {/* Total row */}
        <div className="flex items-center justify-between py-2 text-xs text-slate-500">
          <span>Total de envíos</span>
          <span className="font-bold text-slate-800">{total.toLocaleString(language)}</span>
        </div>
      </div>

      {/* Footer */}
      {hasMore && (
        <div className="border-t border-slate-100 px-4 py-2">
          <Link
            to="/shipments"
            className="text-[10px] font-semibold text-blue-600 hover:text-blue-700 transition-colors"
          >
            Ver todos los estados →
          </Link>
        </div>
      )}
    </div>
  )
}
