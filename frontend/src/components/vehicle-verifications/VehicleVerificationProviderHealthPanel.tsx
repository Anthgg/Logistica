import type { VehicleVerificationSourceHealth } from '../../types/vehicle-verifications'
import { VehicleVerificationSourceBadge } from './VehicleVerificationSourceBadge'

interface Props {
  sources: VehicleVerificationSourceHealth[]
  onToggleSource?: (sourceType: string, currentStatus: string) => void
  canManageSources?: boolean
}

export function VehicleVerificationProviderHealthPanel({
  sources,
  onToggleSource,
  canManageSources = false,
}: Props) {
  return (
    <div className="space-y-4 text-xs">
      <div className="flex items-center justify-between">
        <h4 className="font-bold text-slate-800 text-sm">
          Estado y Salud de Fuentes / Proveedores Autorizados ({sources.length})
        </h4>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {sources.map((s) => (
          <div key={s.id} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs space-y-3">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <VehicleVerificationSourceBadge sourceType={s.source_type} sourceName={s.source_name} />
              <span
                className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${
                  s.operational_status === 'OPERATIONAL'
                    ? 'bg-emerald-100 text-emerald-800'
                    : s.operational_status === 'DEGRADED'
                    ? 'bg-amber-100 text-amber-800'
                    : 'bg-rose-100 text-rose-800'
                }`}
              >
                {s.operational_status}
              </span>
            </div>

            <div className="space-y-1 text-[11px] text-slate-600">
              <div>Autoridad: <strong className="text-slate-800">{s.authority_name}</strong></div>
              <div>Método: <strong className="text-indigo-700">{s.method}</strong></div>
              <div>
                Latencia: <span className="font-mono font-bold">{s.latency_ms ? `${s.latency_ms} ms` : '—'}</span>
              </div>
              <div>
                Circuit Breaker: <span className={s.circuit_breaker_open ? 'text-rose-600 font-bold' : 'text-emerald-700'}>
                  {s.circuit_breaker_open ? 'Abierto (Bloqueado)' : 'Cerrado (Normal)'}
                </span>
              </div>
              <div>
                Última consulta exitosa:{' '}
                <span className="font-mono">{s.last_successful_call_at ? new Date(s.last_successful_call_at).toLocaleString('es-PE') : '—'}</span>
              </div>
            </div>

            {canManageSources && onToggleSource && (
              <div className="pt-2 border-t border-slate-100 flex justify-end">
                <button
                  type="button"
                  onClick={() => onToggleSource(s.source_type, s.operational_status)}
                  className="font-semibold text-xs text-indigo-600 hover:underline"
                >
                  {s.operational_status === 'DISABLED' ? 'Habilitar (Step-Up)' : 'Deshabilitar (Step-Up)'}
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
