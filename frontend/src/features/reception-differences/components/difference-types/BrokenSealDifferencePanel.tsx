import type { ReceptionDifferenceItem } from '../../types/reception-differences'

interface BrokenSealDifferencePanelProps {
  item: ReceptionDifferenceItem
}

export function BrokenSealDifferencePanel({ item }: BrokenSealDifferencePanelProps) {
  const seal = item.seal_detail

  return (
    <div className="space-y-3 text-xs">
      <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-rose-800" role="alert">
        Esta diferencia documenta una anomalía. No determina fraude, robo ni responsabilidad legal.
      </div>

      <div className="grid grid-cols-2 gap-3">
        {seal?.expected_seal_redacted && <InfoCell label="Precinto esperado" value={seal.expected_seal_redacted} />}
        {seal?.observed_seal_redacted && <InfoCell label="Precinto observado" value={seal.observed_seal_redacted} />}
        {seal?.gate_status && <InfoCell label="Estado en garita" value={seal.gate_status} />}
        {seal?.opening_status && <InfoCell label="Estado al abrir" value={seal.opening_status} />}
        {seal?.opening_time && <InfoCell label="Hora de apertura" value={seal.opening_time} />}
        {seal?.guard_name && <InfoCell label="Guardia" value={seal.guard_name} />}
        {seal?.supervisor_name && <InfoCell label="Supervisor" value={seal.supervisor_name} />}
      </div>

      <InfoCell label="Descripción" value={item.description ?? '—'} />
    </div>
  )
}

function InfoCell({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[10px] font-semibold uppercase text-slate-400">{label}</p>
      <p className="text-slate-800">{value}</p>
    </div>
  )
}
