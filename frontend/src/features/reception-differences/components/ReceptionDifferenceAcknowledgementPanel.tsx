import type { ReceptionDifferenceAcknowledgement } from '../types/reception-differences'

interface ReceptionDifferenceAcknowledgementPanelProps {
  acknowledgements: ReceptionDifferenceAcknowledgement[]
}

const ACK_TYPE_LABELS: Record<string, string> = {
  COPY_RECEIVED: 'Copia recibida',
  FACTS_ACKNOWLEDGED: 'Hechos reconocidos',
  RESPONSIBILITY_ACKNOWLEDGED: 'Responsabilidad reconocida',
}

export function ReceptionDifferenceAcknowledgementPanel({ acknowledgements }: ReceptionDifferenceAcknowledgementPanelProps) {
  return (
    <div className="space-y-3">
      <h3 className="text-sm font-bold text-slate-800">Reconocimientos</h3>

      {acknowledgements.length === 0 ? (
        <p className="text-xs text-slate-400">No hay reconocimientos registrados.</p>
      ) : (
        <div className="space-y-2">
          {acknowledgements.map((a) => (
            <div key={a.acknowledgement_id} className="rounded-lg border border-slate-200 p-3 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-slate-800">{ACK_TYPE_LABELS[a.acknowledgement_type]}</span>
                <span className="text-[10px] text-slate-400">{a.created_at}</span>
              </div>
              <p className="text-slate-500">{a.acknowledged_by.display_name} · {a.party_name}</p>
              {a.comment && <p className="mt-1 text-slate-600">{a.comment}</p>}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
