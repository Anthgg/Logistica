import { useMemo } from 'react'
import { useQuery } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import type {
  QualityQuarantineHistoryEvent,
  QualityQuarantineEventType,
} from '../types/quarantine'

const EVENT_LABEL: Record<QualityQuarantineEventType, string> = {
  CASE_CREATED: 'Asignación creada',
  CASE_OPENED: 'Cuarentena requerida',
  CASE_LOCKED: 'Caso bloqueado',
  CASE_UNLOCKED: 'Caso desbloqueado',
  PLACEMENT_CONFIRMED: 'Ubicación confirmada',
  PLACEMENT_SUPERSEDED: 'Ubicación reemplazada',
  INSPECTION_ASSIGNED: 'Inspección asignada',
  INSPECTION_STARTED: 'Inspección iniciada',
  INSPECTION_PAUSED: 'Inspección pausada',
  INSPECTION_COMPLETED: 'Inspección completada',
  INSPECTION_CANCELLED: 'Inspección cancelada',
  CONTROL_COMPLETED: 'Control completado',
  MEASUREMENT_RECORDED: 'Medición registrada',
  EVIDENCE_UPLOADED: 'Evidencia cargada',
  CERTIFICATE_REVIEWED: 'Certificado revisado',
  DECISION_PROPOSED: 'Decisión propuesta',
  DECISION_SUBMITTED: 'Decisión enviada',
  DECISION_APPROVED: 'Decisión aprobada',
  DECISION_REJECTED: 'Decisión rechazada',
  DECISION_EXECUTED: 'Decisión ejecutada',
  RELEASE_REQUESTED: 'Liberación solicitada',
  RELEASE_APPROVED: 'Liberación aprobada',
  RELEASE_EXECUTED: 'Liberación ejecutada',
  RELEASE_CANCELLED: 'Liberación cancelada',
  REJECTION_REQUESTED: 'Rechazo solicitado',
  REJECTION_APPROVED: 'Rechazo aprobado',
  REJECTION_EXECUTED: 'Rechazo ejecutado',
  REJECTION_CANCELLED: 'Rechazo cancelado',
  REINSPECTION_REQUESTED: 'Reinspección solicitada',
  REINSPECTION_APPROVED: 'Reinspección aprobada',
  NON_CONFORMITY_EMITTED: 'NC emitida',
  NON_CONFORMITY_DOWNLOADED: 'NC descargada',
  NON_CONFORMITY_CANCELLED: 'NC cancelada',
  STATUS_CHANGED: 'Estado cambiado',
  PRIORITY_CHANGED: 'Prioridad cambiada',
  DUE_DATE_SET: 'Fecha límite establecida',
  CASE_CLOSED: 'Caso cerrado',
  CASE_CANCELLED: 'Caso cancelado',
  INTEGRITY_VERIFIED: 'Integridad verificada',
  INTEGRITY_FAILED: 'Integridad fallida',
}

const TIMELINE_DOT_CLASSES: Record<QualityQuarantineEventType, string> = {
  CASE_CREATED: 'bg-blue-500',
  CASE_OPENED: 'bg-amber-500',
  CASE_LOCKED: 'bg-slate-400',
  CASE_UNLOCKED: 'bg-slate-500',
  PLACEMENT_CONFIRMED: 'bg-indigo-500',
  PLACEMENT_SUPERSEDED: 'bg-indigo-400',
  INSPECTION_ASSIGNED: 'bg-violet-500',
  INSPECTION_STARTED: 'bg-violet-400',
  INSPECTION_PAUSED: 'bg-amber-400',
  INSPECTION_COMPLETED: 'bg-emerald-500',
  INSPECTION_CANCELLED: 'bg-rose-400',
  CONTROL_COMPLETED: 'bg-emerald-400',
  MEASUREMENT_RECORDED: 'bg-teal-500',
  EVIDENCE_UPLOADED: 'bg-cyan-500',
  CERTIFICATE_REVIEWED: 'bg-sky-500',
  DECISION_PROPOSED: 'bg-orange-500',
  DECISION_SUBMITTED: 'bg-orange-400',
  DECISION_APPROVED: 'bg-emerald-600',
  DECISION_REJECTED: 'bg-rose-600',
  DECISION_EXECUTED: 'bg-emerald-700',
  RELEASE_REQUESTED: 'bg-green-500',
  RELEASE_APPROVED: 'bg-green-600',
  RELEASE_EXECUTED: 'bg-green-700',
  RELEASE_CANCELLED: 'bg-green-400',
  REJECTION_REQUESTED: 'bg-red-500',
  REJECTION_APPROVED: 'bg-red-600',
  REJECTION_EXECUTED: 'bg-red-700',
  REJECTION_CANCELLED: 'bg-red-400',
  REINSPECTION_REQUESTED: 'bg-purple-500',
  REINSPECTION_APPROVED: 'bg-purple-600',
  NON_CONFORMITY_EMITTED: 'bg-rose-500',
  NON_CONFORMITY_DOWNLOADED: 'bg-rose-400',
  NON_CONFORMITY_CANCELLED: 'bg-rose-300',
  STATUS_CHANGED: 'bg-slate-500',
  PRIORITY_CHANGED: 'bg-amber-500',
  DUE_DATE_SET: 'bg-blue-400',
  CASE_CLOSED: 'bg-slate-700',
  CASE_CANCELLED: 'bg-slate-600',
  INTEGRITY_VERIFIED: 'bg-teal-600',
  INTEGRITY_FAILED: 'bg-red-600',
}

function formatDateTime(iso: string): string {
  try {
    return new Date(iso).toLocaleString('es-PE', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return iso
  }
}

function TimelineEventCard({ event }: { event: QualityQuarantineHistoryEvent }) {
  const label = EVENT_LABEL[event.event_type] ?? event.event_type
  const dotClass = TIMELINE_DOT_CLASSES[event.event_type] ?? 'bg-slate-400'

  return (
    <li className="relative flex gap-3 pb-4">
      <div className="absolute left-[11px] top-2 h-full w-px bg-slate-200" aria-hidden="true" />
      <div
        className={`relative z-10 mt-1.5 h-[9px] w-[9px] shrink-0 rounded-full ring-2 ring-white ${dotClass}`}
        aria-hidden="true"
      />
      <div className="flex-1 rounded-lg border border-slate-200 bg-white p-3 text-xs shadow-xs">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <p className="text-sm font-semibold text-slate-800">{label}</p>
          <p className="font-mono text-[11px] text-slate-500">
            {formatDateTime(event.timestamp)}
          </p>
        </div>
        <div className="mt-1.5 flex flex-wrap items-center gap-2 text-[11px] text-slate-600">
          <span className="font-medium text-slate-700">{event.actor?.display_name ?? '—'}</span>
          <span className="text-slate-400">·</span>
          <span>{event.action}</span>
        </div>
        <div className="mt-2 flex flex-wrap gap-2">
          {event.previous_status && event.new_status && (
            <span className="inline-flex items-center gap-1 rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-medium text-slate-600">
              {event.previous_status} → {event.new_status}
            </span>
          )}
          {event.metadata && typeof event.metadata === 'object' && 'quantity' in event.metadata && (
            <span className="inline-flex items-center gap-1 rounded bg-blue-50 px-1.5 py-0.5 text-[10px] font-medium text-blue-700">
              {(event.metadata as Record<string, unknown>).quantity as string}{' '}
              {(event.metadata as Record<string, unknown>).unit as string}
            </span>
          )}
        </div>
        {event.reason && (
          <p className="mt-1.5 text-[11px] text-slate-500">
            <span className="font-medium">Motivo:</span> {event.reason}
          </p>
        )}
        {event.result && (
          <p className="mt-1 text-[11px] text-slate-500">
            <span className="font-medium">Resultado:</span> {event.result}
          </p>
        )}
      </div>
    </li>
  )
}

export function QualityQuarantineHistoryTimeline({
  caseId,
}: {
  caseId: string
}) {
  const { hasPermission } = useLogisticsPermissions()
  const canViewHistory = hasPermission(LOGISTICS_PERMISSIONS.quarantine.viewHistory)

  const {
    data: events,
    isLoading,
    isError,
    error,
  } = useQuery<QualityQuarantineHistoryEvent[]>(
    ['quarantine-history', caseId],
    `/logistics/quality-quarantine/cases/${caseId}/history`,
    undefined,
    { enabled: canViewHistory },
  )

  const sortedEvents = useMemo(
    () =>
      events
        ? [...events].sort(
            (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime(),
          )
        : [],
    [events],
  )

  if (!canViewHistory) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
        <h2 className="text-sm font-bold text-slate-800">Historial de cuarentena</h2>
        <p className="mt-2 text-xs text-slate-500">No tiene permisos para ver el historial.</p>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
        <h2 className="text-sm font-bold text-slate-800">Historial de cuarentena</h2>
        <div className="mt-3 space-y-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-16 w-full animate-pulse rounded-lg bg-slate-100" />
          ))}
        </div>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
        <h2 className="text-sm font-bold text-slate-800">Historial de cuarentena</h2>
        <div className="mt-3 rounded-lg border border-rose-100 bg-rose-50/40 p-3 text-xs text-rose-700">
          {error ?? 'Error al cargar el historial.'}
        </div>
      </div>
    )
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
      <header className="mb-3 border-b border-slate-100 pb-2">
        <h2 className="text-sm font-bold text-slate-800">Historial de cuarentena</h2>
        <p className="mt-0.5 text-xs text-slate-500">
          Eventos registrados en la cadena de custody del caso.
        </p>
      </header>
      {sortedEvents.length === 0 ? (
        <div className="flex flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-slate-200 bg-slate-50/40 px-4 py-8 text-center text-xs text-slate-500">
          <p className="text-sm font-semibold text-slate-700">Sin eventos</p>
          <p className="max-w-md">Aún no se registran eventos para este caso.</p>
        </div>
      ) : (
        <ol className="space-y-0">
          {sortedEvents.map((event) => (
            <TimelineEventCard key={event.event_id} event={event} />
          ))}
        </ol>
      )}
    </div>
  )
}
