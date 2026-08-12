import type { VehicleDimensions } from '../../types/vehicles'

interface Props {
  dimensions: VehicleDimensions | null
}

export function VehicleDimensionsPanel({ dimensions }: Props) {
  if (!dimensions) {
    return (
      <div className="rounded-xl border border-dashed border-slate-200 p-6 text-center text-xs text-slate-400">
        No se han configurado dimensiones para este vehículo.
      </div>
    )
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-4 text-xs">
      <h3 className="text-sm font-bold text-slate-800 border-b border-slate-100 pb-2">
        Dimensiones Exteriores e Interiores
      </h3>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {/* Exterior */}
        <div className="rounded-xl border border-slate-100 bg-slate-50 p-4 space-y-2">
          <span className="font-bold uppercase tracking-wider text-slate-400 text-[10px] block">
            Dimensiones Exteriores ({dimensions.length_unit_code})
          </span>
          <div className="grid grid-cols-3 gap-2 font-mono font-bold text-slate-800">
            <div><span className="text-[10px] font-normal text-slate-400 block">Largo:</span>{dimensions.exterior_length}</div>
            <div><span className="text-[10px] font-normal text-slate-400 block">Ancho:</span>{dimensions.exterior_width}</div>
            <div><span className="text-[10px] font-normal text-slate-400 block">Alto:</span>{dimensions.exterior_height}</div>
          </div>
        </div>

        {/* Interior */}
        <div className="rounded-xl border border-slate-100 bg-slate-50 p-4 space-y-2">
          <span className="font-bold uppercase tracking-wider text-slate-400 text-[10px] block">
            Dimensiones Útiles Interiores ({dimensions.length_unit_code})
          </span>
          <div className="grid grid-cols-3 gap-2 font-mono font-bold text-slate-800">
            <div><span className="text-[10px] font-normal text-slate-400 block">Largo:</span>{dimensions.interior_length || '—'}</div>
            <div><span className="text-[10px] font-normal text-slate-400 block">Ancho:</span>{dimensions.interior_width || '—'}</div>
            <div><span className="text-[10px] font-normal text-slate-400 block">Alto:</span>{dimensions.interior_height || '—'}</div>
          </div>
        </div>
      </div>

      <div className="flex justify-between items-center pt-2 border-t border-slate-100 text-slate-600">
        <div>
          <span>Volumen Informado: </span>
          <strong className="font-mono text-slate-800">{dimensions.reported_volume || '—'} {dimensions.volume_unit_code}</strong>
        </div>
        <div>
          <span>Volumen Calculado por Backend: </span>
          <strong className="font-mono text-indigo-700">{dimensions.calculated_volume || '—'} {dimensions.volume_unit_code}</strong>
        </div>
      </div>
    </div>
  )
}
