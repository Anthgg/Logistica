import { useState } from 'react'
import type { ReceptionDifferenceResponsibleParty } from '../types/reception-differences'

interface SharedResponsibilityEditorProps {
  parties: ReceptionDifferenceResponsibleParty[]
  onChange: (parties: Partial<ReceptionDifferenceResponsibleParty>[]) => void
  readonly?: boolean
}

interface PartyDraft {
  party_name: string
  party_type: string
  role: string
  percentage: string
  rationale: string
}

const PARTY_TYPES = [
  { value: 'SUPPLIER', label: 'Proveedor' },
  { value: 'CARRIER', label: 'Transportista' },
  { value: 'INTERNAL_RECEPTION', label: 'Recepción interna' },
  { value: 'GATE', label: 'Garita' },
  { value: 'DOCK', label: 'Muelle' },
  { value: 'PURCHASING', label: 'Compras' },
  { value: 'CONTRACTOR', label: 'Contratista' },
  { value: 'SHARED', label: 'Compartido' },
  { value: 'UNDETERMINED', label: 'Indeterminado' },
  { value: 'OTHER', label: 'Otro' },
] as const

export function SharedResponsibilityEditor({ parties, onChange, readonly = false }: SharedResponsibilityEditorProps) {
  const [drafts, setDrafts] = useState<PartyDraft[]>(
    parties.map((p) => ({
      party_name: p.party_name,
      party_type: p.party_type,
      role: p.role,
      percentage: String(p.percentage ?? ''),
      rationale: p.rationale ?? '',
    }))
  )

  const totalPercentage = drafts.reduce((sum, d) => sum + (parseFloat(d.percentage) || 0), 0)

  const addParty = () => {
    const newDrafts = [...drafts, { party_name: '', party_type: 'SUPPLIER', role: 'SHARED', percentage: '', rationale: '' }]
    setDrafts(newDrafts)
    onChange(newDrafts.map(d => ({
      party_name: d.party_name,
      party_type: d.party_type as ReceptionDifferenceResponsibleParty['party_type'],
      role: (d.role || 'SHARED') as ReceptionDifferenceResponsibleParty['role'],
      percentage: d.percentage || undefined,
      rationale: d.rationale || undefined,
    })))
  }

  const removeParty = (index: number) => {
    const newDrafts = drafts.filter((_, i) => i !== index)
    setDrafts(newDrafts)
    onChange(newDrafts.map(d => ({
      party_name: d.party_name,
      party_type: d.party_type as ReceptionDifferenceResponsibleParty['party_type'],
      role: (d.role || 'SHARED') as ReceptionDifferenceResponsibleParty['role'],
      percentage: d.percentage || undefined,
      rationale: d.rationale || undefined,
    })))
  }

  const updateDraft = (index: number, field: keyof PartyDraft, value: string) => {
    const newDrafts = drafts.map((d, i) => (i === index ? { ...d, [field]: value } : d))
    setDrafts(newDrafts)
    onChange(newDrafts.map(d => ({
      party_name: d.party_name,
      party_type: d.party_type as ReceptionDifferenceResponsibleParty['party_type'],
      role: (d.role || 'SHARED') as ReceptionDifferenceResponsibleParty['role'],
      percentage: d.percentage || undefined,
      rationale: d.rationale || undefined,
    })))
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold text-slate-800">Responsabilidad compartida</h3>
        {!readonly && (
          <button
            type="button"
            onClick={addParty}
            className="rounded-lg border border-slate-200 px-2 py-1 text-[10px] font-semibold text-slate-600 hover:bg-slate-50"
          >
            + Agregar
          </button>
        )}
      </div>

      {totalPercentage > 100 && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-2 text-xs text-rose-700">
          El total de porcentajes ({totalPercentage}%) excede 100%.
        </div>
      )}

      {drafts.length === 0 ? (
        <p className="text-xs text-slate-400">No hay responsables asignados.</p>
      ) : (
        <div className="space-y-3">
          {drafts.map((draft, index) => (
            <div key={index} className="rounded-lg border border-slate-200 p-3 text-xs">
              <div className="mb-2 flex items-center justify-between">
                <span className="text-[10px] font-bold text-slate-400">Responsable {index + 1}</span>
                {!readonly && (
                  <button
                    type="button"
                    onClick={() => removeParty(index)}
                    className="text-[10px] font-semibold text-rose-500 hover:text-rose-700"
                  >
                    Eliminar
                  </button>
                )}
              </div>

              <div className="grid grid-cols-2 gap-2">
                <label className="block text-slate-600">
                  Nombre *
                  <input
                    type="text"
                    value={draft.party_name}
                    onChange={(e) => updateDraft(index, 'party_name', e.target.value)}
                    className="mt-1 w-full rounded border border-slate-300 p-1.5 text-xs"
                    disabled={readonly}
                  />
                </label>
                <label className="block text-slate-600">
                  Tipo
                  <select
                    value={draft.party_type}
                    onChange={(e) => updateDraft(index, 'party_type', e.target.value)}
                    className="mt-1 w-full rounded border border-slate-300 p-1.5 text-xs"
                    disabled={readonly}
                  >
                    {PARTY_TYPES.map((pt) => (
                      <option key={pt.value} value={pt.value}>{pt.label}</option>
                    ))}
                  </select>
                </label>
                <label className="block text-slate-600">
                  Rol
                  <input
                    type="text"
                    value={draft.role}
                    onChange={(e) => updateDraft(index, 'role', e.target.value)}
                    className="mt-1 w-full rounded border border-slate-300 p-1.5 text-xs"
                    disabled={readonly}
                  />
                </label>
                <label className="block text-slate-600">
                  Porcentaje %
                  <input
                    type="text"
                    value={draft.percentage}
                    onChange={(e) => updateDraft(index, 'percentage', e.target.value)}
                    className="mt-1 w-full rounded border border-slate-300 p-1.5 text-xs"
                    placeholder="0"
                    disabled={readonly}
                  />
                </label>
              </div>

              <label className="mt-2 block text-slate-600">
                Razón
                <textarea
                  value={draft.rationale}
                  onChange={(e) => updateDraft(index, 'rationale', e.target.value)}
                  className="mt-1 w-full rounded border border-slate-300 p-1.5 text-xs"
                  rows={2}
                  disabled={readonly}
                />
              </label>
            </div>
          ))}
        </div>
      )}

      <p className="text-[10px] text-slate-400">
        Los porcentajes deben sumar 100% para una distribución completa.
      </p>
    </div>
  )
}
