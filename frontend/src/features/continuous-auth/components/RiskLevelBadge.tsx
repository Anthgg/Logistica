import { useTranslations } from '../../../hooks/useTranslations'
import type { RiskLevel } from '../types/continuous-auth'
import { LogisticsIcon } from '../../../components/common/LogisticsIcon'

const styles: Record<RiskLevel, string> = {
  low: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  medium: 'border-amber-200 bg-amber-50 text-amber-800',
  high: 'border-orange-200 bg-orange-50 text-orange-800',
  critical: 'border-rose-200 bg-rose-50 text-rose-800',
  unknown: 'border-slate-200 bg-slate-50 text-slate-600',
}

function RiskSymbol({ level }: { level: RiskLevel }) {
  if (level === 'low') return <LogisticsIcon name="check" size={12} aria-hidden />
  if (level === 'critical') return <LogisticsIcon name="x" size={12} aria-hidden />
  if (level === 'medium' || level === 'high') return <LogisticsIcon name="alert" size={12} aria-hidden />
  return null
}

export function RiskLevelBadge({ level }: { level: RiskLevel }) {
  const { translate } = useTranslations()
  const label = translate('risk', level, level)
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold ${styles[level]}`}
      aria-label={label}
    >
      <RiskSymbol level={level} />
      {label}
    </span>
  )
}
