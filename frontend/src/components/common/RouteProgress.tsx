import { useTranslations } from '../../hooks/useTranslations'

export function RouteProgress({
  label,
  value,
  total,
}: {
  label: string
  value: number
  total: number
}) {
  const { language, translate } = useTranslations()
  const percentage = total > 0 ? Math.min(100, Math.round((value / total) * 100)) : 0
  const displayLabel = translate('status', label, label)

  return (
    <div className="flex flex-col gap-[5px] px-4 py-[11px] border-b border-[#EEF2F5] last:border-b-0">
      <div className="flex items-center justify-between">
        <span className="text-xs text-muted font-medium">{displayLabel}</span>
        <strong className="text-xs font-bold text-ink">{value.toLocaleString(language)}</strong>
      </div>
      <div
        className="h-[5px] bg-[#F0F4F7] rounded-full overflow-hidden border border-[#EEF2F5]"
        role="progressbar"
        aria-label={displayLabel}
        aria-valuemin={0}
        aria-valuemax={total}
        aria-valuenow={value}
      >
        <span
          className="block h-full bg-primary rounded-full transition-colors duration-500"
          style={{ width: `${percentage}%` }}
        />
      </div>
      <small className="text-[10px] text-faint">{percentage}% del total</small>
    </div>
  )
}
