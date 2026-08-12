import { LogisticsIcon } from '../common/LogisticsIcon'
import type { RucDataConflict } from '../../types/ruc-integration'

interface Props {
  conflicts: RucDataConflict[]
  onSelectValue?: (field: string, selectedValue: string) => void
}

export function RucDataConflictsPanel({ conflicts, onSelectValue }: Props) {
  if (!conflicts || conflicts.length === 0) {
    return null
  }

  return (
    <div className="rounded-xl border border-amber-200 bg-amber-50/50 p-4 space-y-3">
      <div className="flex items-center gap-2 text-amber-800">
        <span className="text-sm font-bold flex items-center gap-1.5"><LogisticsIcon name="alert" size={14} aria-hidden /> Conflictos de datos detectados ({conflicts.length})</span>
      </div>
      <p className="text-xs text-amber-700">
        Existen discrepancias entre el padrón oficial, el proveedor y los datos declarados por el socio.
      </p>

      <div className="space-y-3">
        {conflicts.map((conflict) => (
          <div key={conflict.id} className="rounded-lg border border-amber-200 bg-white p-3 space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-slate-800">{conflict.field_label}</span>
              <span className="rounded bg-amber-100 px-2 py-0.5 text-[10px] font-bold text-amber-800">
                {conflict.status}
              </span>
            </div>

            <div className="grid grid-cols-1 gap-2 text-xs sm:grid-cols-3">
              <div className="rounded border border-slate-100 bg-slate-50 p-2">
                <span className="text-[10px] font-bold uppercase text-slate-400 block">Padrón Oficial</span>
                <span className="font-mono text-slate-800">{conflict.padron_value || '—'}</span>
                {conflict.padron_date && (
                  <span className="text-[10px] text-slate-400 block mt-0.5">
                    {new Date(conflict.padron_date).toLocaleDateString('es-PE')}
                  </span>
                )}
                {onSelectValue && conflict.padron_value && (
                  <button
                    type="button"
                    onClick={() => onSelectValue(conflict.field_name, conflict.padron_value!)}
                    className="mt-1 text-[10px] font-medium text-indigo-600 hover:underline"
                  >
                    Usar padrón
                  </button>
                )}
              </div>

              <div className="rounded border border-slate-100 bg-slate-50 p-2">
                <span className="text-[10px] font-bold uppercase text-slate-400 block">Proveedor</span>
                <span className="font-mono text-slate-800">{conflict.provider_value || '—'}</span>
                {conflict.provider_date && (
                  <span className="text-[10px] text-slate-400 block mt-0.5">
                    {new Date(conflict.provider_date).toLocaleDateString('es-PE')}
                  </span>
                )}
                {onSelectValue && conflict.provider_value && (
                  <button
                    type="button"
                    onClick={() => onSelectValue(conflict.field_name, conflict.provider_value!)}
                    className="mt-1 text-[10px] font-medium text-indigo-600 hover:underline"
                  >
                    Usar proveedor
                  </button>
                )}
              </div>

              <div className="rounded border border-slate-100 bg-slate-50 p-2">
                <span className="text-[10px] font-bold uppercase text-slate-400 block">Socio (Actual)</span>
                <span className="font-mono text-slate-800">{conflict.partner_value || '—'}</span>
                {conflict.partner_date && (
                  <span className="text-[10px] text-slate-400 block mt-0.5">
                    {new Date(conflict.partner_date).toLocaleDateString('es-PE')}
                  </span>
                )}
                {onSelectValue && conflict.partner_value && (
                  <button
                    type="button"
                    onClick={() => onSelectValue(conflict.field_name, conflict.partner_value!)}
                    className="mt-1 text-[10px] font-medium text-indigo-600 hover:underline"
                  >
                    Mantener actual
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
