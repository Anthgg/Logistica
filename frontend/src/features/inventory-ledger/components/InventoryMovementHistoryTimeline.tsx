import type { InventoryMovementHistoryEvent } from '../types/inventory-ledger'
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton'

interface Props {
  events: InventoryMovementHistoryEvent[]
  loading: boolean
}

const RESULT_COLORS: Record<string, string> = {
  SUCCESS: 'text-green-600',
  FAILED: 'text-red-600',
  WARNING: 'text-yellow-600',
}

const TYPE_LABELS: Record<string, string> = {
  POSTING_REQUESTED: 'Posting solicitado',
  SOURCE_VALIDATED: 'Fuente validada',
  MOVEMENT_POSTED: 'MOV publicado',
  DUPLICATE_DETECTED: 'Duplicado detectado',
  POSTING_FAILED: 'Publicación fallida',
  COMPENSATION_REQUESTED: 'Compensación solicitada',
  COMPENSATION_REVIEWED: 'Compensación revisada',
  COMPENSATION_APPROVED: 'Compensación aprobada',
  COMPENSATION_EXECUTED: 'Compensación ejecutada',
  VERIFICATION_STARTED: 'Verificación iniciada',
  INTEGRITY_OK: 'Integridad válida',
  INTEGRITY_FAILED: 'Integridad fallida',
  CHECKPOINT_CREATED: 'Checkpoint creado',
  RECONCILIATION_STARTED: 'Reconciliación iniciada',
  EXPORT_REQUESTED: 'Exportación solicitada',
  EXPORT_DOWNLOADED: 'Exportación descargada',
}

export function InventoryMovementHistoryTimeline({ events, loading }: Props) {
  if (loading) return <LoadingSkeleton rows={4} />

  if (events.length === 0) {
    return (
      <div className="bg-white p-8 rounded-lg border text-center text-gray-500">
        Sin eventos de historial.
      </div>
    )
  }

  return (
    <ol className="bg-white p-4 rounded-lg border space-y-3" aria-label="Historial del movimiento">
      {events.map((event) => (
        <li key={event.event_id} className="border-l-2 border-gray-200 pl-4 space-y-1">
          <div className="flex items-center justify-between">
            <span className="font-medium">{TYPE_LABELS[event.event_type] ?? event.event_type}</span>
            <span className={`text-sm font-medium ${RESULT_COLORS[event.result]}`}>
              {event.result}
            </span>
          </div>
          <div className="text-sm text-gray-600">{event.action}</div>
          <div className="text-xs text-gray-500">
            {new Date(event.occurred_at).toLocaleString()} · {event.actor?.display_name ?? '—'}
            {event.correlation_id && (
              <span className="ml-2 font-mono">corr={event.correlation_id}</span>
            )}
          </div>
          {event.previous_state && event.new_state && (
            <div className="text-xs text-gray-500">
              {event.previous_state} → {event.new_state}
            </div>
          )}
          {event.reason && <div className="text-xs text-gray-500">Razón: {event.reason}</div>}
        </li>
      ))}
    </ol>
  )
}
