import { LogisticsIcon } from '../common/LogisticsIcon'
import type { VehicleVerificationFieldProvenance } from '../../types/vehicle-verifications'
import { VehicleVerificationSourceBadge } from './VehicleVerificationSourceBadge'

interface Props {
  provenanceFields: VehicleVerificationFieldProvenance[]
}

export function VehicleVerificationProvenanceTable({ provenanceFields }: Props) {
  if (!provenanceFields || provenanceFields.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-slate-200 p-4 text-center text-xs text-slate-400">
        Sin desglose de procedencia por campo.
      </div>
    )
  }

  return (
    <div className="space-y-3 text-xs">
      <h4 className="font-bold uppercase tracking-wider text-slate-500 text-[11px]">
        Procedencia de Datos Campo por Campo
      </h4>

      <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
        <table className="min-w-full divide-y divide-slate-200">
          <thead className="bg-slate-50 text-slate-600">
            <tr>
              <th className="px-4 py-2.5 text-left font-semibold">Campo Atributo</th>
              <th className="px-4 py-2.5 text-left font-semibold">Valor en Maestro</th>
              <th className="px-4 py-2.5 text-left font-semibold">Valor Verificado</th>
              <th className="px-4 py-2.5 text-left font-semibold">Fuente Registrada</th>
              <th className="px-4 py-2.5 text-center font-semibold">Confianza</th>
              <th className="px-4 py-2.5 text-center font-semibold">Estado Discrepancia</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 bg-white">
            {provenanceFields.map((field, idx) => (
              <tr key={idx} className={field.has_conflict ? 'bg-rose-50/50 hover:bg-rose-50' : 'hover:bg-slate-50'}>
                <td className="px-4 py-2.5 font-bold text-slate-800">{field.field_label || field.field_name}</td>
                <td className="px-4 py-2.5 font-mono text-slate-700">{field.master_value || '—'}</td>
                <td className="px-4 py-2.5 font-mono font-bold text-indigo-700">{field.verified_value || '—'}</td>
                <td className="px-4 py-2.5">
                  <VehicleVerificationSourceBadge sourceType={field.source_type} sourceName={field.source_name} size="sm" />
                </td>
                <td className="px-4 py-2.5 text-center font-mono font-bold text-slate-700">
                  {Math.round(field.confidence_score * 100)}%
                </td>
                <td className="px-4 py-2.5 text-center">
                  {field.has_conflict ? (
                    <span className="inline-flex items-center gap-1 rounded bg-rose-100 px-2 py-0.5 font-bold text-rose-800 text-[10px]">
                      <LogisticsIcon name="alert" size={12} aria-hidden /> Conflicto
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 rounded bg-emerald-100 px-2 py-0.5 font-bold text-emerald-800 text-[10px]">
                      <LogisticsIcon name="check" size={12} aria-hidden /> Coincide
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
