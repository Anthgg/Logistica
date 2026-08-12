import { SectionPanel, EmptyPanel, ErrorPanel, SkeletonRows, StatusPill } from './ui/Primitives'
import { dataQualityLabel, dataQualityTone, formatServerDateTime } from '../utils/format'
import type { DockOperationHistoryEvent, DockOperationalEvent } from '../types/inbound-docks'

const EVENT_LABEL: Record<string, string> = {
  GATE_CLEARANCE: 'Autorización de garita',
  QUEUE_ENTRY: 'Entrada a cola',
  PRIORITY_CHANGED: 'Cambio de prioridad',
  PLAN_GENERATED: 'Plan generado',
  DOCK_ASSIGNED: 'Muelle asignado',
  MOVEMENT_STARTED: 'Movimiento iniciado',
  DOCK_ARRIVAL: 'Llegada al muelle',
  READINESS_UPDATED: 'Readiness actualizado',
  RESPONSIBLE_ASSIGNED: 'Responsable asignado',
  SEAL_OPENING_RECORDED: 'Apertura de precinto',
  UNLOADING_STARTED: 'Descarga iniciada',
  UNLOADING_PAUSED: 'Pausa',
  UNLOADING_RESUMED: 'Reanudación',
  UNLOADING_ABORTED: 'Aborto',
  UNLOADING_COMPLETED: 'Descarga finalizada',
  DOCK_RELEASED: 'Liberación',
  DOCK_REASSIGNED: 'Reasignación',
  TIME_CORRECTION_REQUESTED: 'Corrección solicitada',
  TIME_CORRECTION_APPROVED: 'Corrección aprobada',
  TIME_CORRECTION_REJECTED: 'Corrección rechazada',
  INTEGRITY_FAILED: 'Integridad fallida',
}

export function DockOperationTimeline({
  events,
  loading,
  error,
}: {
  events: DockOperationalEvent[] | DockOperationHistoryEvent[] | undefined
  loading: boolean
  error: string | null
}) {
  if (loading) {
    return (
      <SectionPanel title="Timeline operativo" description="Eventos registrados por el backend">
        <SkeletonRows rows={4} />
      </SectionPanel>
    )
  }
  if (error) {
    return (
      <SectionPanel title="Timeline operativo" description="Eventos registrados por el backend">
        <ErrorPanel message={error} />
      </SectionPanel>
    )
  }
  if (!events?.length) {
    return (
      <SectionPanel title="Timeline operativo" description="Eventos registrados por el backend">
        <EmptyPanel title="Sin eventos" description="Aún no se registran eventos para esta operación." />
      </SectionPanel>
    )
  }
  return (
    <SectionPanel title="Timeline operativo" description="Eventos registrados por el backend">
      <ol className="space-y-2">
        {events.map((e) => {
          const typed = e as DockOperationalEvent
          const quality = (typed as DockOperationalEvent).data_quality
          return (
            <li key={e.id} className="flex flex-col gap-1 rounded-lg border border-slate-200 bg-white p-3 text-xs">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="text-sm font-semibold text-slate-800">
                  {EVENT_LABEL[e.event_type] ?? e.event_type}
                </p>
                <p className="font-mono text-[11px] text-slate-500">
                  {formatServerDateTime(e.occurred_at)}
                </p>
              </div>
              <p className="text-[11px] text-slate-600">
                Estado anterior: {e.previous_status ?? '—'} → Estado nuevo: {e.new_status ?? '—'}
              </p>
              <p className="text-[11px] text-slate-600">Actor: {e.actor?.display_name ?? '—'}</p>
              {e.reason && <p className="text-[11px] text-slate-600">Motivo: {e.reason}</p>}
              {e.result && <p className="text-[11px] text-slate-600">Resultado: {e.result}</p>}
              {quality && (
                <StatusPill tone={dataQualityTone(quality)}>{dataQualityLabel(quality)}</StatusPill>
              )}
              {typed.partial_hash && (
                <p className="text-[10px] text-slate-500">Hash parcial: {typed.partial_hash}</p>
              )}
            </li>
          )
        })}
      </ol>
    </SectionPanel>
  )
}
