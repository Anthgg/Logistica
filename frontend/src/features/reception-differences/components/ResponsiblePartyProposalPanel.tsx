import type { ReceptionDifferenceResponsibleParty } from '../types/reception-differences'

interface ResponsiblePartyProposalPanelProps {
  parties: ReceptionDifferenceResponsibleParty[]
  canPropose?: boolean
  onPropose?: () => void
}

const PARTY_TYPE_LABELS: Record<string, string> = {
  SUPPLIER: 'Proveedor',
  CARRIER: 'Transportista',
  INTERNAL_RECEPTION: 'Recepción interna',
  GATE: 'Garita',
  DOCK: 'Muelle',
  PURCHASING: 'Compras',
  CONTRACTOR: 'Contratista',
  SHARED: 'Compartido',
  UNDETERMINED: 'Indeterminado',
  OTHER: 'Otro',
}

const STATUS_LABELS: Record<string, string> = {
  NONE: 'Sin asignar',
  PROPOSED: 'Propuesto',
  REVIEWED: 'Revisado',
  ACKNOWLEDGED: 'Reconocido',
  DISPUTED: 'Disputado',
  UNDETERMINED: 'Indeterminado',
}

const STATUS_COLORS: Record<string, string> = {
  NONE: 'bg-slate-100 text-slate-600',
  PROPOSED: 'bg-amber-100 text-amber-700',
  REVIEWED: 'bg-blue-100 text-blue-700',
  ACKNOWLEDGED: 'bg-emerald-100 text-emerald-700',
  DISPUTED: 'bg-rose-100 text-rose-700',
  UNDETERMINED: 'bg-slate-100 text-slate-500',
}

export function ResponsiblePartyProposalPanel({ parties, canPropose = false, onPropose }: ResponsiblePartyProposalPanelProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold text-slate-800">Responsables</h3>
        {canPropose && onPropose && (
          <button
            type="button"
            onClick={onPropose}
            className="rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#173a55]"
          >
            Proponer responsable
          </button>
        )}
      </div>

      {parties.length === 0 ? (
        <p className="text-xs text-slate-400">No hay responsables asignados.</p>
      ) : (
        <div className="space-y-2">
          {parties.map((p) => (
            <div key={p.responsibility_id} className="rounded-lg border border-slate-200 p-3 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-slate-800">{p.party_name}</span>
                <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${STATUS_COLORS[p.status]}`}>
                  {STATUS_LABELS[p.status]}
                </span>
              </div>
              <p className="text-slate-500">
                {PARTY_TYPE_LABELS[p.party_type]} · {p.role}
                {p.percentage && ` · ${p.percentage}%`}
              </p>
              {p.rationale && <p className="mt-1 text-slate-600">{p.rationale}</p>}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
