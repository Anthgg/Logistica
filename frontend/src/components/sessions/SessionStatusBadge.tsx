import { LogisticsIcon, type LogisticsIconName } from '../common/LogisticsIcon'

type SessionStatusType =
  | 'current'
  | 'trusted'
  | 'unknown'
  | 'expiring'
  | 'expired'

interface SessionStatusBadgeProps {
  type: SessionStatusType
  label: string
}

const styles: Record<SessionStatusType, { className: string; icon: LogisticsIconName | null }> = {
  current: {
    className: 'border-emerald-200 bg-emerald-50 text-emerald-700',
    icon: 'check',
  },
  trusted: {
    className: 'border-primary-light bg-primary-xlight text-primary',
    icon: 'shield',
  },
  unknown: {
    className: 'border-amber-200 bg-amber-xlight text-amber',
    icon: 'alert',
  },
  expiring: {
    className: 'border-orange-200 bg-orange-xlight text-orange',
    icon: 'alert',
  },
  expired: {
    className: 'border-slate-200 bg-slate-100 text-slate-500',
    icon: null,
  },
}

export function SessionStatusBadge({ type, label }: SessionStatusBadgeProps) {
  const style = styles[type]
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-2xs font-semibold ${style.className}`}
    >
      {style.icon && <LogisticsIcon name={style.icon} size={11} />}
      {label}
    </span>
  )
}