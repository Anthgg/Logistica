import type { ReactNode } from 'react'
import { LogisticsIcon, type LogisticsIconName } from '../common/LogisticsIcon'

type Tone = 'blue' | 'slate' | 'emerald' | 'amber' | 'rose' | 'orange'

const toneMap: Record<Tone, { icon: string; bar: string; text: string }> = {
  blue:    { icon: 'bg-blue-50 text-blue-600',    bar: 'bg-blue-600',    text: 'text-blue-700'    },
  slate:   { icon: 'bg-slate-100 text-slate-600',  bar: 'bg-slate-600',   text: 'text-slate-700'   },
  emerald: { icon: 'bg-emerald-50 text-emerald-600', bar: 'bg-emerald-600', text: 'text-emerald-700' },
  amber:   { icon: 'bg-amber-50 text-amber-600',   bar: 'bg-amber-500',   text: 'text-amber-700'   },
  rose:    { icon: 'bg-rose-50 text-rose-600',     bar: 'bg-rose-500',    text: 'text-rose-700'    },
  orange:  { icon: 'bg-orange-50 text-orange-600', bar: 'bg-orange-600',  text: 'text-orange-700'  },
}

interface KpiCardProps {
  icon: LogisticsIconName
  value: number
  label: string
  detail: string
  tone?: Tone
  action?: ReactNode
}

export function KpiCard({ icon, value, label, detail, tone = 'slate', action }: KpiCardProps) {
  const t = toneMap[tone]
  return (
    <article className="relative min-w-0 rounded-xl border border-slate-200 bg-white p-3 shadow-sm transition-colors duration-150 hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-md">
      {/* Top: icon + value */}
      <div className="flex items-start justify-between gap-2 mb-2">
        <span
          className={`flex h-8 w-8 items-center justify-center rounded-lg ${t.icon} shrink-0`}
          aria-hidden="true"
        >
          <LogisticsIcon name={icon} size={16} />
        </span>
        {action}
      </div>

      <div className={`text-2xl font-bold tracking-tight leading-none mb-1 ${t.text}`}>
        {value.toLocaleString('es-PE')}
      </div>
      <div className="text-xs font-semibold text-slate-700 leading-tight">{label}</div>
      <div className="text-[10px] text-slate-500 leading-snug mt-0.5 truncate">{detail}</div>
    </article>
  )
}
