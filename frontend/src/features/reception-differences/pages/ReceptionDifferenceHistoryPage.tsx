import { useParams } from 'react-router-dom'
import { useQuery } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import type { ReceptionDifferenceHistoryEvent } from '../types/reception-differences'

const EVENT_LABELS: Record<string, string> = {
  CASE_CREATED: 'Caso creado',
  CANDIDATE_FORMALIZED: 'Candidato formalizado',
  MANUAL_ITEM_CREATED: 'Ítem manual creado',
  EVIDENCE_ADDED: 'Evidencia añadida',
  PHOTO_ADDED: 'Fotografía añadida',
  RESPONSIBLE_PROPOSED: 'Responsable propuesto',
  RESPONSIBLE_REVIEWED: 'Responsable revisado',
  CASE_SUBMITTED: 'Caso enviado',
  REVIEW_STARTED: 'Revisión iniciada',
  CHANGES_REQUESTED: 'Cambios solicitados',
  CASE_READY: 'Caso listo',
  CASE_APPROVED: 'Caso aprobado',
  DIF_ISSUED: 'DIF emitido',
  COPY_DOWNLOADED: 'Copia descargada',
  COPY_ACKNOWLEDGED: 'Copia reconocida',
  FACTS_ACKNOWLEDGED: 'Hechos reconocidos',
  RESPONSIBILITY_ACKNOWLEDGED: 'Responsabilidad reconocida',
  FACTS_DISPUTED: 'Hechos disputados',
  RESPONSIBILITY_DISPUTED: 'Responsabilidad disputada',
  FOLLOW_UP_REQUIRED: 'Seguimiento requerido',
  DOCUMENT_CANCELLED: 'Acta anulada',
  CASE_CLOSED: 'Caso cerrado',
  INTEGRITY_FAILED: 'Integridad fallida',
}

export function ReceptionDifferenceHistoryPage() {
  const { caseId } = useParams<{ caseId: string }>()
  const auth = useLogisticsPermissions()

  const historyQuery = useQuery<ReceptionDifferenceHistoryEvent[]>(
    ['reception-difference-history', caseId],
    `/logistics/reception-difference-cases/${caseId}/history`,
    undefined,
    { enabled: !!caseId },
  )

  if (!auth.hasPermission(LOGISTICS_PERMISSIONS.receptionDifferences.viewHistory)) {
    return (
      <div className="page">
        <div className="panel p-6 text-center text-sm text-slate-500">
          No tienes permisos para ver el historial.
        </div>
      </div>
    )
  }

  const events = historyQuery.data ?? []

  return (
    <div className="page">
      <h1 className="mb-4 text-lg font-bold text-slate-800">Historial</h1>

      {historyQuery.isLoading ? (
        <div className="panel p-8 text-center text-sm text-slate-400">Cargando…</div>
      ) : events.length === 0 ? (
        <div className="panel p-8 text-center text-sm text-slate-400">
          No hay eventos registrados.
        </div>
      ) : (
        <div className="relative ml-3 border-l-2 border-slate-200 pl-6 space-y-4">
          {events.map((e) => (
            <div key={e.event_id} className="relative">
              <div className="absolute -left-8 top-1 h-3 w-3 rounded-full border-2 border-[#1F4E6D] bg-white" />
              <div className="text-xs">
                <p className="font-semibold text-slate-800">{EVENT_LABELS[e.event_type] ?? e.event_type}</p>
                <p className="text-slate-500">{e.actor.display_name} · {e.timestamp}</p>
                {e.reason && <p className="text-slate-500">Motivo: {e.reason}</p>}
                {e.previous_status && e.new_status && (
                  <p className="text-slate-500">{e.previous_status} → {e.new_status}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
