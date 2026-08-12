import { useEffect, useState } from 'react'
import { clsx } from 'clsx'
import { formatApproxSeconds, useServerTime } from '../../utils/server-time'
import { formatSecondsApprox } from '../../utils/format'

export interface ServerBasedOperationTimerProps {
  serverTimeIso: string | null | undefined
  startedAt: string | null | undefined
  activePauseStartedAt: string | null | undefined
  accumulatedPauseSeconds: number
  status: string
  officialDurationSeconds?: number | null
  className?: string
  showNet?: boolean
  compact?: boolean
}

export function ServerBasedOperationTimer({
  serverTimeIso,
  startedAt,
  activePauseStartedAt,
  accumulatedPauseSeconds,
  status,
  officialDurationSeconds,
  className,
  showNet = true,
  compact = false,
}: ServerBasedOperationTimerProps) {
  const { serverTimeIso: syncedTime, forceResync } = useServerTime(
    serverTimeIso ?? null,
    null,
  )
  const [tick, setTick] = useState(0)
  const isRunning = status === 'ACTIVE' || status === 'UNLOADING_ACTIVE'
  const isPaused = status === 'PAUSED' || status === 'UNLOADING_PAUSED'
  const isCompleted = status === 'COMPLETED' || status === 'UNLOADING_COMPLETED'

  useEffect(() => {
    if (!isRunning) return
    const id = window.setInterval(() => setTick((t) => t + 1), 1000)
    return () => window.clearInterval(id)
  }, [isRunning])

  const approx = formatApproxSeconds(
    syncedTime ?? serverTimeIso ?? null,
    startedAt ?? null,
    activePauseStartedAt ?? null,
    accumulatedPauseSeconds,
    status,
  )

  return (
    <div
      className={clsx(
        'flex flex-col gap-0.5 rounded-lg border border-slate-200 bg-slate-50/60 px-3 py-2',
        compact ? 'text-[10px]' : 'text-xs',
        className,
      )}
      role="status"
      aria-live={isRunning ? 'off' : 'polite'}
      aria-atomic="true"
    >
      <div className="flex items-center justify-between gap-2">
        <span className="font-semibold text-slate-500">Cronómetro operativo</span>
        <span
          className={clsx(
            'rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase',
            isRunning
              ? 'bg-emerald-100 text-emerald-700'
              : isPaused
                ? 'bg-amber-100 text-amber-700'
                : isCompleted
                  ? 'bg-slate-200 text-slate-700'
                  : 'bg-slate-100 text-slate-500',
          )}
        >
          {isRunning ? 'En curso' : isPaused ? 'Pausado' : isCompleted ? 'Finalizado' : 'Inactivo'}
        </span>
      </div>
      <div className="flex flex-wrap items-baseline gap-3 font-mono">
        <div>
          <span className="block text-[10px] font-semibold text-slate-500">Bruto (aprox.)</span>
          <span className="text-base font-bold text-slate-900" aria-hidden={tick < 0}>
            {formatSecondsApprox(approx.grossSeconds)}
          </span>
        </div>
        {showNet && (
          <div>
            <span className="block text-[10px] font-semibold text-slate-500">Neto (aprox.)</span>
            <span className="text-base font-bold text-slate-900">
              {formatSecondsApprox(approx.netSeconds)}
            </span>
          </div>
        )}
        <div>
          <span className="block text-[10px] font-semibold text-slate-500">Pausado (aprox.)</span>
          <span className="text-base font-bold text-slate-900">
            {formatSecondsApprox(approx.pausedSeconds)}
          </span>
        </div>
      </div>
      <p className="text-[10px] text-slate-500">
        {isCompleted && officialDurationSeconds != null
          ? `Duración oficial: ${formatSecondsApprox(officialDurationSeconds)}`
          : isCompleted
            ? 'Duración oficial pendiente de registrar.'
            : 'Valores aproximados. La duración oficial la calcula el servidor.'}
      </p>
      {!isCompleted && (
        <button
          type="button"
          onClick={forceResync}
          className="self-start text-[10px] font-semibold text-[#1F4E6D] hover:underline"
        >
          Sincronizar ahora
        </button>
      )}
    </div>
  )
}
