import type { VehicleDuplicateCandidate } from '../../types/vehicles'
import { LogisticsIcon } from '../common/LogisticsIcon'

interface Props {
  candidates: VehicleDuplicateCandidate[]
  onSelectCandidate?: (candidate: VehicleDuplicateCandidate) => void
}

export function VehicleDuplicateWarning({ candidates, onSelectCandidate }: Props) {
  if (!candidates || candidates.length === 0) return null

  return (
    <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 space-y-3 text-xs">
      <div className="flex items-center gap-2 text-amber-800 font-bold">
        <LogisticsIcon name="alert" size={15} aria-hidden />
        <span>Posibles Vehículos Duplicados Detectados ({candidates.length})</span>
      </div>
      <p className="text-amber-700">
        Existen registros previos en el sistema con coincidencias en placa, VIN o identificadores.
      </p>

      <div className="space-y-2">
        {candidates.map((c) => (
          <div
            key={c.id}
            className="flex flex-col gap-2 rounded-lg border border-amber-200 bg-white p-3 sm:flex-row sm:items-center sm:justify-between"
          >
            <div className="space-y-0.5">
              <div className="flex items-center gap-2">
                <span className="font-mono font-bold text-slate-800">{c.plate_number}</span>
                <span className="font-medium text-slate-700">{c.make_name} {c.model_name} ({c.year_of_manufacture})</span>
              </div>
              <p className="text-[11px] text-amber-800">
                Coincidencias: {c.match_reasons.join(', ')}
              </p>
            </div>

            {onSelectCandidate && (
              <button
                type="button"
                onClick={() => onSelectCandidate(c)}
                className="shrink-0 rounded-lg border border-amber-300 bg-amber-100 px-3 py-1 font-semibold text-amber-900 hover:bg-amber-200"
              >
                Ver Vehículo Existente
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
