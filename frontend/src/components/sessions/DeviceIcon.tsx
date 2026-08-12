import { LogisticsIcon, type LogisticsIconName } from '../common/LogisticsIcon'

interface DeviceIconProps {
  deviceType: string | null
  size?: number
  className?: string
}

function resolveIcon(deviceType: string | null): LogisticsIconName {
  if (!deviceType) return 'sessions'
  const normalized = deviceType.toLowerCase()
  if (normalized.includes('mobile') || normalized.includes('phone')) return 'sessions'
  if (normalized.includes('tablet')) return 'sessions'
  if (normalized.includes('laptop')) return 'sessions'
  if (normalized.includes('desktop') || normalized.includes('pc')) return 'sessions'
  return 'sessions'
}

export function DeviceIcon({ deviceType, size = 18, className = '' }: DeviceIconProps) {
  const iconName = resolveIcon(deviceType)
  const bgClass = !deviceType
    ? 'bg-slate-100 text-slate-400'
    : 'bg-primary-light text-primary'

  return (
    <span
      className={`inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${bgClass} ${className}`}
      aria-hidden="true"
    >
      <LogisticsIcon name={iconName} size={size} />
    </span>
  )
}