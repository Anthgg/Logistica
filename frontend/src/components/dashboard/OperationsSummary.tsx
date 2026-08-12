import type { CSSProperties } from 'react'
import { LogisticsIcon } from '../common/LogisticsIcon'

interface Props {
  totalShipments: number
  inTransit: number
  pendingShipments: number
  deliveriesToday: number
  criticalIncidents: number
  deliveredShipments: number
  routesToday: number
}

export function OperationsSummary({
  totalShipments,
  inTransit,
  pendingShipments,
  deliveriesToday,
  criticalIncidents,
  deliveredShipments,
  routesToday,
}: Props) {
  const completionPct =
    totalShipments > 0
      ? Math.round((deliveredShipments / totalShipments) * 100)
      : 0

  const deg = completionPct * 3.6

  return (
    <div className="grid gap-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm lg:grid-cols-[minmax(0,1fr)_auto]">
      {/* Left zone */}
      <div className="min-w-0">
        <div className="flex items-center gap-1.5 mb-2">
          <span className="pulse-dot" aria-hidden="true" />
          <span className="text-[10px] font-bold uppercase tracking-widest text-slate-500 leading-none">
            Operación de hoy
          </span>
        </div>

        <h2 className="text-lg font-bold text-slate-900 leading-tight mb-1">
          Resumen de operaciones en curso
        </h2>

        <p className="text-xs text-slate-500 leading-snug mb-3">
          La red concentra{' '}
          <strong className="font-semibold text-slate-800">
            {(inTransit + pendingShipments).toLocaleString('es-PE')} envíos activos
          </strong>{' '}
          y{' '}
          <strong className="font-semibold text-slate-800">
            {routesToday}
          </strong>{' '}
          rutas programadas para hoy.
        </p>

        {/* Chips */}
        <div className="flex flex-wrap gap-2">
          <span className="inline-flex h-7 items-center gap-1.5 rounded-full border border-blue-200 bg-blue-50 px-2.5 text-[10px] font-medium text-blue-700">
            <LogisticsIcon name="truck" size={12} />
            <strong className="font-bold">{inTransit}</strong>
            En tránsito
          </span>
          <span className="inline-flex h-7 items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-2.5 text-[10px] font-medium text-emerald-700">
            <LogisticsIcon name="check" size={12} />
            <strong className="font-bold">{deliveriesToday}</strong>
            Entregas hoy
          </span>
          <span
            className={`inline-flex h-7 items-center gap-1.5 rounded-full border px-2.5 text-[10px] font-medium ${
              criticalIncidents > 0
                ? 'border-rose-200 bg-rose-50 text-rose-700'
                : 'border-slate-200 bg-slate-50 text-slate-600'
            }`}
          >
            <LogisticsIcon name="alert" size={12} />
            <strong className="font-bold">{criticalIncidents}</strong>
            Incidencias críticas
          </span>
        </div>
      </div>

      {/* Right zone — completion ring */}
      <div className="flex flex-col items-center justify-center gap-2 border-l border-slate-100 pl-5 shrink-0">
        <div
          className="completion-ring relative flex h-[84px] w-[84px] items-center justify-center rounded-full"
          style={{ '--deg': `${deg}deg` } as CSSProperties}
          aria-label={`${completionPct}% de envíos entregados`}
          role="img"
        >
          {/* Inner white circle */}
          <div className="absolute inset-[9px] rounded-full bg-white" />
          <div className="relative flex flex-col items-center leading-none">
            <span className="text-[18px] font-bold text-slate-900 tracking-tight">
              {completionPct}%
            </span>
            <span className="text-[9px] uppercase tracking-wider text-slate-400">
              completado
            </span>
          </div>
        </div>
        <p className="text-center text-[10px] text-slate-500 leading-snug">
          <span className="block font-semibold text-slate-700 text-xs">
            {deliveredShipments.toLocaleString('es-PE')} de {totalShipments.toLocaleString('es-PE')}
          </span>
          envíos entregados
        </p>
      </div>
    </div>
  )
}
