import type { QualityPlanHistoryEvent, QualityPlanEventType } from '../types/quality-inspection-plans'

interface QualityPlanHistoryTimelineProps {
  events: QualityPlanHistoryEvent[]
}

const EVENT_ICONS: Record<QualityPlanEventType, string> = {
  PLAN_CREATED: '📋',
  PLAN_UPDATED: '✏️',
  VERSION_CREATED: '📦',
  SCOPE_ADDED: '🎯',
  SCOPE_MODIFIED: '🎯',
  SCOPE_REMOVED: '🎯',
  CONTROL_ADDED: '✅',
  CONTROL_MODIFIED: '✅',
  CONTROL_REORDERED: '🔀',
  TOLERANCE_CREATED: '📏',
  SAMPLING_CREATED: '🎲',
  CERTIFICATE_ADDED: '📄',
  VALIDATION_FAILED: '❌',
  PLAN_VALIDATED: '✔️',
  CONFLICT_DETECTED: '⚠️',
  VERSION_ACTIVATED: '🚀',
  VERSION_RETIRED: '🔚',
  PREVIEW_GENERATED: '👁️',
  RESOLUTION_EXECUTED: '🔧',
  INTEGRITY_FAILED: '🛡️',
}

const EVENT_LABELS: Record<QualityPlanEventType, string> = {
  PLAN_CREATED: 'Plan creado',
  PLAN_UPDATED: 'Plan actualizado',
  VERSION_CREATED: 'Versión creada',
  SCOPE_ADDED: 'Ámbito agregado',
  SCOPE_MODIFIED: 'Ámbito modificado',
  SCOPE_REMOVED: 'Ámbito eliminado',
  CONTROL_ADDED: 'Control agregado',
  CONTROL_MODIFIED: 'Control modificado',
  CONTROL_REORDERED: 'Controles reordenados',
  TOLERANCE_CREATED: 'Tolerancia creada',
  SAMPLING_CREATED: 'Muestreo creado',
  CERTIFICATE_ADDED: 'Certificado agregado',
  VALIDATION_FAILED: 'Validación fallida',
  PLAN_VALIDATED: 'Plan validado',
  CONFLICT_DETECTED: 'Conflicto detectado',
  VERSION_ACTIVATED: 'Versión activada',
  VERSION_RETIRED: 'Versión retirada',
  PREVIEW_GENERATED: 'Vista previa generada',
  RESOLUTION_EXECUTED: 'Resolución ejecutada',
  INTEGRITY_FAILED: 'Integridad fallida',
}

export function QualityPlanHistoryTimeline({ events }: QualityPlanHistoryTimelineProps) {
  if (events.length === 0) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-4 text-xs">
        <h2 className="text-sm font-bold text-slate-800">Historial</h2>
        <p className="mt-2 text-slate-500">Sin eventos de historial.</p>
      </div>
    )
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 text-xs">
      <h2 className="mb-3 text-sm font-bold text-slate-800">Historial ({events.length})</h2>
      <ol className="space-y-2 border-l border-slate-200 pl-4">
        {events.map((e) => (
          <li key={e.event_id} className="relative">
            <span className="absolute -left-[21px] top-1 h-3 w-3 rounded-full border-2 border-[#1F4E6D] bg-white" />
            <div className="rounded-lg border border-slate-100 bg-white p-2.5 shadow-xs">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-slate-800">
                  <span className="mr-1">{EVENT_ICONS[e.event_type]}</span>
                  {EVENT_LABELS[e.event_type] ?? e.event_type}
                </span>
                <span className="text-[11px] text-slate-400">
                  {new Date(e.timestamp).toLocaleString('es-PE')}
                </span>
              </div>
              <dl className="mt-1 grid grid-cols-2 gap-x-2 gap-y-0.5 text-[11px] text-slate-500 md:grid-cols-4">
                <dt>Actor:</dt>
                <dd>{e.actor.display_name}</dd>
                <dt>Acción:</dt>
                <dd>{e.action}</dd>
                {e.version_id && (
                  <>
                    <dt>Versión:</dt>
                    <dd className="font-mono">{e.version_id.slice(0, 8)}</dd>
                  </>
                )}
                {e.previous_status && (
                  <>
                    <dt>Estado anterior:</dt>
                    <dd>{e.previous_status}</dd>
                  </>
                )}
                {e.new_status && (
                  <>
                    <dt>Estado nuevo:</dt>
                    <dd>{e.new_status}</dd>
                  </>
                )}
                {e.reason && (
                  <>
                    <dt>Motivo:</dt>
                    <dd>{e.reason}</dd>
                  </>
                )}
                {e.result && (
                  <>
                    <dt>Resultado:</dt>
                    <dd>{e.result}</dd>
                  </>
                )}
              </dl>
            </div>
          </li>
        ))}
      </ol>
    </div>
  )
}
