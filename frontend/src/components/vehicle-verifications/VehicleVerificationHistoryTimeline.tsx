import type { VehicleVerificationHistoryEvent } from '../../types/vehicle-verifications'

interface Props {
  history: VehicleVerificationHistoryEvent[]
}

const EVENT_LABELS: Record<string, string> = {
  REQUESTED: 'Solicitada',
  STARTED: 'Iniciada',
  COMPLETED: 'Completada',
  FAILED: 'Fallida',
  RETRIED: 'Reintentada',
  EXPIRED: 'Vencida',
  REPLACED: 'Reemplazada',
  REVOKED: 'Revocada',
  EVIDENCE_ASSOCIATED: 'Evidencia asociada',
  CONFLICT_DETECTED: 'Conflicto detectado',
  CONFLICT_RESOLVED: 'Conflicto resuelto',
  DATA_APPLIED: 'Datos aplicados al vehículo',
  ASSISTED_VALIDATION: 'Validación asistida registrada',
  PROVIDER_CALLED: 'Proveedor llamado',
  PROVIDER_DEGRADED: 'Proveedor degradado',
}

function eventTone(eventType: string): string {
  if (['COMPLETED', 'CONFLICT_RESOLVED', 'DATA_APPLIED'].includes(eventType)) return 'text-emerald-700'
  if (['FAILED', 'EXPIRED', 'REVOKED', 'CONFLICT_DETECTED', 'PROVIDER_DEGRADED'].includes(eventType)) return 'text-rose-700'
  if (['RETRIED', 'REPLACED'].includes(eventType)) return 'text-amber-700'
  return 'text-slate-700'
}

export function VehicleVerificationHistoryTimeline({ history }: Props) {
  if (!history || history.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-slate-200 p-4 text-center text-slate-400 text-xs">
        Sin eventos de historial registrados.
      </div>
    )
  }

  return (
    <div className="space-y-3 text-xs">
      <h4 className="font-bold uppercase tracking-wider text-slate-500 text-[11px]">
        Historial de Eventos de Verificación
      </h4>

      <ol className="relative border-l border-slate-200 ml-2 space-y-3">
        {history.map((evt) => {
          const label = EVENT_LABELS[evt.event_type] ?? evt.event_type
          return (
            <li key={evt.id} className="ml-4">
              <span
                className={`absolute -left-1.5 mt-1 h-3 w-3 rounded-full border-2 border-white ${
                  evt.event_type === 'FAILED' || evt.event_type === 'REVOKED'
                    ? 'bg-rose-500'
                    : evt.event_type === 'COMPLETED'
                      ? 'bg-emerald-500'
                      : 'bg-indigo-500'
                }`}
                aria-hidden
              />
              <div className="rounded-xl border border-slate-200 bg-white p-3 shadow-xs">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className={`font-bold ${eventTone(evt.event_type)}`}>{label}</span>
                  <time className="font-mono text-[10px] text-slate-400">
                    {new Date(evt.created_at).toLocaleString('es-PE')}
                  </time>
                </div>
                <div className="mt-1 space-y-0.5 text-[11px] text-slate-600">
                  {evt.user_name && <div>Usuario: <strong>{evt.user_name}</strong></div>}
                  {evt.source_name && <div>Fuente: <strong>{evt.source_name}</strong></div>}
                  {evt.domain_label && <div>Dominio: <strong>{evt.domain_label}</strong></div>}
                  {evt.result_status && <div>Resultado: <strong>{evt.result_status}</strong></div>}
                  {evt.reason && <div>Motivo: <span className="italic">"{evt.reason}"</span></div>}
                  {evt.vehicle_version !== null && evt.vehicle_version !== undefined && (
                    <div>Versión vehículo: <strong className="font-mono">v{evt.vehicle_version}</strong></div>
                  )}
                  {evt.correlation_id_prefix && (
                    <div className="font-mono text-[10px] text-slate-400">
                      Correlation: {evt.correlation_id_prefix}…
                    </div>
                  )}
                </div>
              </div>
            </li>
          )
        })}
      </ol>
    </div>
  )
}