import { LogisticsIcon } from '../common/LogisticsIcon'

interface SecuritySummaryProps {
  activeSessions: number
  recognizedDevices: number
  lastUpdated: string
}

export function SecuritySummary({
  activeSessions,
  recognizedDevices,
  lastUpdated,
}: SecuritySummaryProps) {
  const items = [
    {
      icon: 'sessions' as const,
      value: activeSessions,
      label: 'Sesiones activas',
    },
    {
      icon: 'shield' as const,
      value: recognizedDevices,
      label: 'Dispositivos reconocidos',
    },
    {
      icon: 'check' as const,
      value: null,
      label: lastUpdated,
    },
  ]

  return (
    <div className="grid grid-cols-3 gap-2.5">
      {items.map((item, index) => (
        <div
          key={`skeleton-${index}`}
          className="flex items-center gap-2.5 rounded-lg border border-border-subtle bg-white px-3 py-2.5"
        >
          <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-primary-xlight text-primary">
            <LogisticsIcon name={item.icon} size={15} />
          </span>
          <div className="min-w-0">
            {item.value !== null && (
              <span className="block text-sm font-bold text-ink leading-tight">
                {item.value}
              </span>
            )}
            <span className="block text-2xs text-muted leading-tight">
              {item.label}
            </span>
          </div>
        </div>
      ))}
    </div>
  )
}