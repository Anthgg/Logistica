import { LogisticsIcon, type LogisticsIconName } from './LogisticsIcon'

const toneMap = {
  primary: {
    bar:   'bg-primary',
    icon:  'bg-primary-xlight text-primary',
  },
  success: {
    bar:   'bg-emerald',
    icon:  'bg-emerald-xlight text-emerald',
  },
  warning: {
    bar:   'bg-amber',
    icon:  'bg-amber-xlight text-amber',
  },
  danger: {
    bar:   'bg-danger',
    icon:  'bg-[#FFF5F5] text-danger',
  },
  neutral: {
    bar:   'bg-primary-sec',
    icon:  'bg-primary-xlight text-primary-sec',
  },
}

export function MetricCard({
  label,
  value,
  detail,
  icon,
  tone = 'primary',
}: {
  label: string
  value: number
  detail: string
  icon: LogisticsIconName
  tone?: 'primary' | 'success' | 'warning' | 'danger' | 'neutral'
}) {
  const t = toneMap[tone]
  return (
    <article className="relative bg-white border border-[#DDE4E8] rounded-[10px] px-4 pt-3.5 pb-3 flex flex-col gap-1.5 shadow-xs hover:shadow-sm hover:border-[#C8D4DC] hover:-translate-y-px transition-colors duration-150 overflow-hidden">
      {/* Left accent bar */}
      <span className={`absolute left-0 top-0 bottom-0 w-[3px] ${t.bar} rounded-none`} aria-hidden="true" />

      {/* Top line: icon + signal */}
      <div className="flex items-center justify-between">
        <span className={`w-[30px] h-[30px] rounded-[6px] flex items-center justify-center shrink-0 ${t.icon}`} aria-hidden="true">
          <LogisticsIcon name={icon} size={16} />
        </span>
        <span className="text-[10px] font-medium text-faint uppercase tracking-wide">Actual</span>
      </div>

      {/* Value */}
      <div className="text-[clamp(22px,2vw,26px)] font-bold text-ink tracking-tight leading-none">
        {value.toLocaleString('es-PE')}
      </div>

      {/* Label + detail */}
      <div>
        <h3 className="text-xs font-semibold text-ink leading-tight">{label}</h3>
        <p className="text-[11px] text-muted leading-tight mt-0.5">{detail}</p>
      </div>
    </article>
  )
}
