import type { RucFieldProvenance } from '../../types/ruc-integration'
import { DataSourceBadge } from './DataSourceBadge'

interface Props {
  provenanceList: RucFieldProvenance[]
}

export function FieldProvenanceViewer({ provenanceList }: Props) {
  if (!provenanceList || provenanceList.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-slate-200 p-4 text-center text-xs text-slate-500">
        Sin trazabilidad de origen por campo.
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">
        Procedencia por Campo
      </h4>
      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
        <table className="min-w-full divide-y divide-slate-100 text-xs">
          <thead className="bg-slate-50 text-slate-600">
            <tr>
              <th className="px-3 py-2 text-left font-semibold">Campo</th>
              <th className="px-3 py-2 text-left font-semibold">Valor</th>
              <th className="px-3 py-2 text-left font-semibold">Fuente</th>
              <th className="px-3 py-2 text-left font-semibold">Fecha</th>
              <th className="px-3 py-2 text-center font-semibold">Confianza</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 bg-white">
            {provenanceList.map((item) => (
              <tr key={item.field_name} className="hover:bg-slate-50/50">
                <td className="px-3 py-2 font-medium text-slate-700">{item.field_label}</td>
                <td className="px-3 py-2 text-slate-800 font-mono text-[11px] truncate max-w-[200px]">
                  {item.value || '—'}
                </td>
                <td className="px-3 py-2">
                  <DataSourceBadge source={item.source} label={item.source_label} size="sm" />
                </td>
                <td className="px-3 py-2 text-slate-500">
                  {new Date(item.source_date).toLocaleDateString('es-PE')}
                </td>
                <td className="px-3 py-2 text-center">
                  <span
                    className={`inline-block px-1.5 py-0.5 text-[10px] font-bold rounded ${
                      item.confidence === 'HIGH'
                        ? 'bg-emerald-100 text-emerald-800'
                        : item.confidence === 'MEDIUM'
                        ? 'bg-blue-100 text-blue-800'
                        : 'bg-amber-100 text-amber-800'
                    }`}
                  >
                    {item.confidence}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
