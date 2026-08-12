import { useState } from 'react'
import type { ReceptionDifferenceEvidence } from '../types/reception-differences'

interface ReceptionDifferenceEvidencePanelProps {
  evidence: ReceptionDifferenceEvidence[]
  onUpload?: () => void
  canUpload?: boolean
}

const EVIDENCE_TYPE_LABELS: Record<string, string> = {
  PRODUCT: 'Producto',
  DAMAGE: 'Daño',
  PACKAGING: 'Embalaje',
  LABEL: 'Etiqueta',
  COUNT: 'Conteo',
  DOCUMENT: 'Documento',
  SEAL: 'Precinto',
  VEHICLE: 'Vehículo',
  OTHER: 'Otro',
}

export function ReceptionDifferenceEvidencePanel({ evidence, onUpload, canUpload = false }: ReceptionDifferenceEvidencePanelProps) {
  const [filter, setFilter] = useState<string>('ALL')

  const filtered = filter === 'ALL' ? evidence : evidence.filter((e) => e.evidence_type === filter)

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold text-slate-800">Evidencias ({evidence.length})</h3>
        {canUpload && onUpload && (
          <button
            type="button"
            onClick={onUpload}
            className="rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#173a55]"
          >
            Subir evidencia
          </button>
        )}
      </div>

      <div className="flex flex-wrap gap-1.5">
        <FilterChip label="Todas" active={filter === 'ALL'} onClick={() => setFilter('ALL')} />
        {Object.entries(EVIDENCE_TYPE_LABELS).map(([key, label]) => (
          <FilterChip key={key} label={label} active={filter === key} onClick={() => setFilter(key)} />
        ))}
      </div>

      {filtered.length === 0 ? (
        <p className="text-xs text-slate-400">No hay evidencias registradas.</p>
      ) : (
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
          {filtered.map((e) => (
            <div key={e.evidence_id} className="rounded-lg border border-slate-200 p-2 text-xs">
              <p className="font-semibold text-slate-700">{EVIDENCE_TYPE_LABELS[e.evidence_type] ?? e.evidence_type}</p>
              <p className="truncate text-slate-500">{e.file.filename}</p>
              <p className="text-[10px] text-slate-400">{e.created_at}</p>
              {e.anti_malware_status && (
                <span className="mt-1 inline-block rounded bg-emerald-100 px-1.5 py-0.5 text-[10px] font-bold text-emerald-700">
                  {e.anti_malware_status}
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function FilterChip({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-lg px-2 py-1 text-[10px] font-semibold transition-colors ${
        active
          ? 'bg-[#1F4E6D] text-white'
          : 'border border-slate-200 bg-white text-slate-600 hover:bg-slate-50'
      }`}
    >
      {label}
    </button>
  )
}
