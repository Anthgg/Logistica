import { clsx } from 'clsx'
import { useServerTime } from '../../utils/server-time'
import { formatServerDateTime, formatServerTime } from '../../utils/format'

export interface DockOperationsServerClockProps {
  serverTimeIso: string | null | undefined
  timezone: string | null | undefined
  className?: string
  showDate?: boolean
  label?: string
}

export function DockOperationsServerClock({
  serverTimeIso,
  timezone,
  className,
  showDate = true,
  label = 'Hora del servidor',
}: DockOperationsServerClockProps) {
  const { driftMs, lastSyncedAt } = useServerTime(serverTimeIso ?? null, timezone ?? null)
  const driftSeconds = Math.round(driftMs / 1000)
  const driftLabel =
    Math.abs(driftSeconds) < 2
      ? 'Sincronizado'
      : driftSeconds > 0
        ? `Servidor ${driftSeconds}s adelante`
        : `Servidor ${Math.abs(driftSeconds)}s atrás`
  return (
    <div
      className={clsx(
        'flex flex-col items-end gap-0.5 text-right text-[10px] text-slate-500',
        className,
      )}
      aria-live="polite"
    >
      <span className="font-semibold uppercase tracking-wider text-slate-500">
        {label}
      </span>
      <span className="font-mono text-sm font-bold text-slate-800">
        {serverTimeIso
          ? showDate
            ? formatServerDateTime(serverTimeIso, timezone)
            : formatServerTime(serverTimeIso, timezone)
          : '—'}
      </span>
      <span className="text-[10px] text-slate-400">
        {driftLabel}
        {lastSyncedAt ? ` · última sync ${formatServerTime(lastSyncedAt.toISOString(), null)}` : ''}
      </span>
    </div>
  )
}
