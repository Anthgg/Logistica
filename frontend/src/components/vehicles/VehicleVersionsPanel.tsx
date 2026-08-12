import type { VehicleVersion } from '../../types/vehicles'

interface Props {
  versions: VehicleVersion[]
}

export function VehicleVersionsPanel({ versions }: Props) {
  if (!versions || versions.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-slate-200 p-6 text-center text-xs text-slate-400">
        Sin historial de versiones registradas.
      </div>
    )
  }

  return (
    <div className="space-y-4 text-xs">
      <h4 className="font-bold uppercase tracking-wider text-slate-500 text-xs">
        Versiones Inmutables del Vehículo ({versions.length})
      </h4>

      <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
        <table className="min-w-full divide-y divide-slate-200">
          <thead className="bg-slate-50 text-slate-600">
            <tr>
              <th className="px-4 py-3 text-left font-semibold">Versión</th>
              <th className="px-4 py-3 text-left font-semibold">Placa Snapshot</th>
              <th className="px-4 py-3 text-left font-semibold">Marca / Modelo</th>
              <th className="px-4 py-3 text-center font-semibold">Estado</th>
              <th className="px-4 py-3 text-left font-semibold">Creado por</th>
              <th className="px-4 py-3 text-left font-semibold">Fecha</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 bg-white">
            {versions.map((v) => (
              <tr key={v.id} className="hover:bg-slate-50">
                <td className="px-4 py-3 font-mono font-bold text-indigo-700">v{v.version_number}</td>
                <td className="px-4 py-3 font-mono font-bold text-slate-800">{v.plate_number}</td>
                <td className="px-4 py-3 text-slate-700">{v.make_name} {v.model_name}</td>
                <td className="px-4 py-3 text-center">
                  <span
                    className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${
                      v.status === 'ACTIVE'
                        ? 'bg-emerald-100 text-emerald-800'
                        : 'bg-slate-100 text-slate-600'
                    }`}
                  >
                    {v.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-600">{v.created_by_name}</td>
                <td className="px-4 py-3 text-slate-500">{new Date(v.created_at).toLocaleString('es-PE')}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
