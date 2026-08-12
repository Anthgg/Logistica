import { Link } from 'react-router-dom'
import { LogisticsIcon, type LogisticsIconName } from '../common/LogisticsIcon'
import type { ActivityItem } from '../../types/operations'
import { formatDateTime } from '../../utils/date'
import { useTranslations } from '../../hooks/useTranslations'

const MAX_VISIBLE = 5

const eventIcons: Record<string, { icon: LogisticsIconName; color: string }> = {
  shipment_created:    { icon: 'package',  color: 'bg-blue-50 text-blue-600'    },
  shipment_updated:    { icon: 'truck',    color: 'bg-blue-50 text-blue-500'    },
  shipment_delivered:  { icon: 'check',    color: 'bg-emerald-50 text-emerald-600' },
  route_started:       { icon: 'route',    color: 'bg-indigo-50 text-indigo-600'  },
  incident_opened:     { icon: 'alert',    color: 'bg-rose-50 text-rose-600'    },
  incident_resolved:   { icon: 'shield',   color: 'bg-emerald-50 text-emerald-600' },
  session_started:     { icon: 'sessions', color: 'bg-slate-100 text-slate-600'  },
  facial_capture:      { icon: 'research', color: 'bg-purple-50 text-purple-600'  },
  behavior_batch:      { icon: 'activity', color: 'bg-slate-100 text-slate-500'  },
}

function getEventMeta(eventType: string) {
  const key = eventType.toLowerCase()
  for (const [k, v] of Object.entries(eventIcons)) {
    if (key.includes(k.split('_')[0] ?? '')) return v
  }
  return { icon: 'activity' as LogisticsIconName, color: 'bg-slate-100 text-slate-500' }
}

interface Props {
  activities: ActivityItem[]
}

export function RecentActivity({ activities }: Props) {
  const { translate } = useTranslations()
  const visible = activities.slice(0, MAX_VISIBLE)

  return (
    <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      {/* Header */}
      <div className="flex h-12 items-center justify-between border-b border-slate-200 px-4">
        <div className="flex items-center gap-2">
          <span className="flex h-6 w-6 items-center justify-center rounded-md bg-emerald-50 text-emerald-600" aria-hidden="true">
            <LogisticsIcon name="activity" size={14} />
          </span>
          <div>
            <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400 leading-none">Trazabilidad</p>
            <h2 className="text-sm font-semibold text-slate-800 leading-tight">Actividad reciente</h2>
          </div>
        </div>
        <span className="flex items-center gap-1.5 text-[10px] font-semibold text-emerald-600 uppercase tracking-wide" aria-live="polite">
          <span className="pulse-dot" aria-hidden="true" />
          En vivo
        </span>
      </div>

      {/* List — max 5 items, fixed height */}
      {visible.length === 0 ? (
        <div className="flex flex-col items-center gap-2 py-8 text-center text-slate-400">
          <LogisticsIcon name="activity" size={24} />
          <p className="text-xs">Sin actividad reciente</p>
        </div>
      ) : (
        <ol
          className="max-h-[290px] overflow-y-auto overscroll-contain scrollbar-thin"
          aria-label="Eventos recientes"
        >
          {visible.map((item, i) => {
            const { icon, color } = getEventMeta(item.event_type)
            return (
              <li
                key={`${item.created_at}-${item.resource_id ?? i}`}
                className="flex items-start gap-3 border-b border-slate-100 px-3 py-2.5 last:border-b-0"
              >
                <span
                  className={`mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-md ${color}`}
                  aria-hidden="true"
                >
                  <LogisticsIcon name={icon} size={13} />
                </span>
                <div className="min-w-0 flex-1">
                  <p className="text-xs font-medium text-slate-800 leading-snug truncate">
                    {item.event_type_label || translate('event', item.event_type, item.event_type)}
                  </p>
                  <p className="text-[10px] text-slate-500 leading-snug">
                    {item.resource_type_label ?? (item.resource_type ? translate('resource', item.resource_type, item.resource_type) : translate('resource', 'system', 'sistema'))} · {formatDateTime(item.created_at)}
                  </p>
                </div>
                <LogisticsIcon name="chevron" size={12} className="shrink-0 text-slate-300 mt-1" />
              </li>
            )
          })}
        </ol>
      )}

      {/* Footer */}
      <div className="border-t border-slate-100 px-4 py-2.5">
        <Link
          to="/sessions"
          className="text-[10px] font-semibold text-blue-600 hover:text-blue-700 transition-colors"
        >
          Ver toda la actividad →
        </Link>
      </div>
    </div>
  )
}
