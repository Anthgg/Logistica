import { LogisticsIcon } from '../common/LogisticsIcon'
import type { VehicleVerificationCompliance } from '../../types/vehicle-verifications'

interface Props {
  compliance: VehicleVerificationCompliance
}

export function VehicleVerificationCompliancePanel({ compliance }: Props) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-6 text-xs">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-slate-100 pb-4">
        <div>
          <span className="font-bold uppercase tracking-wider text-slate-400 text-[10px]">
            Evaluación de Verificaciones por Backend
          </span>
          <h3 className="text-base font-bold text-slate-800">Cumplimiento de Verificaciones Vehiculares</h3>
        </div>

        <span
          className={`rounded-full px-3 py-1 text-xs font-bold ${
            compliance.general_status === 'COMPLIANT'
              ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
              : compliance.general_status === 'EXPIRED'
              ? 'bg-rose-100 text-rose-800 border border-rose-300'
              : 'bg-amber-100 text-amber-800 border border-amber-300'
          }`}
        >
          {compliance.general_status}
        </span>
      </div>

      {compliance.blocking_reasons && compliance.blocking_reasons.length > 0 && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 space-y-1">
          <span className="font-bold text-red-800 flex items-center gap-1.5 text-xs uppercase tracking-wider">
            <LogisticsIcon name="lock" size={14} aria-hidden /> Motivos Bloqueantes
          </span>
          <ul className="list-disc list-inside text-red-700 space-y-0.5">
            {compliance.blocking_reasons.map((r, idx) => <li key={idx}>{r}</li>)}
          </ul>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4 rounded-xl border border-slate-100 bg-slate-50 p-4 sm:grid-cols-4">
        <div>
          <span className="font-bold uppercase text-[10px] text-slate-400 block mb-1">Dominios Requeridos</span>
          <span className="font-mono font-bold text-slate-800 text-base">{compliance.required_domains_count}</span>
        </div>

        <div>
          <span className="font-bold uppercase text-[10px] text-slate-400 block mb-1">Validados Vigentes</span>
          <span className="font-mono font-bold text-emerald-700 text-base">{compliance.validated_domains_count}</span>
        </div>

        <div>
          <span className="font-bold uppercase text-[10px] text-slate-400 block mb-1">Vencidos / Faltantes</span>
          <span className="font-mono font-bold text-rose-600 text-base">
            {compliance.expired_domains_count + compliance.missing_domains_count}
          </span>
        </div>

        <div>
          <span className="font-bold uppercase text-[10px] text-slate-400 block mb-1">Conflictos Abiertos</span>
          <span className="font-mono font-bold text-amber-700 text-base">{compliance.open_conflicts_count}</span>
        </div>
      </div>

      <div className="text-[10px] text-slate-400 text-right font-mono">
        Evaluación autoritativa del backend del {new Date(compliance.evaluation_date).toLocaleString('es-PE')}
      </div>
    </div>
  )
}
