import type { VehicleCompliance } from '../../types/vehicles'
import { VehicleComplianceBadge, VehicleOperationalBadge } from './VehicleStatusBadge'
import { LogisticsIcon } from '../common/LogisticsIcon'

interface Props {
  compliance: VehicleCompliance
}

export function VehicleCompliancePanel({ compliance }: Props) {
  return (
    <div className="space-y-6 text-xs">
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-slate-100 pb-4">
          <div>
            <span className="font-bold uppercase tracking-wider text-slate-400 text-[10px]">
              Evaluación de Cumplimiento Autoritativa
            </span>
            <h3 className="text-base font-bold text-slate-800">Estado de Operatividad y Normativa</h3>
          </div>

          <div className="flex items-center gap-2">
            <VehicleComplianceBadge status={compliance.general_status} />
            <VehicleOperationalBadge status={compliance.operational_status} />
          </div>
        </div>

        {/* Blocking Reasons & Warnings */}
        {compliance.blocking_reasons && compliance.blocking_reasons.length > 0 && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-4 space-y-1">
            <span className="flex items-center gap-1.5 font-bold text-red-800 text-xs uppercase tracking-wider">
              <LogisticsIcon name="lock" size={13} aria-hidden />
              Motivos Bloqueantes
            </span>
            <ul className="list-disc list-inside text-red-700 space-y-0.5">
              {compliance.blocking_reasons.map((r, idx) => <li key={idx}>{r}</li>)}
            </ul>
          </div>
        )}

        {compliance.warnings && compliance.warnings.length > 0 && (
          <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 space-y-1">
            <span className="flex items-center gap-1.5 font-bold text-amber-800 text-xs uppercase tracking-wider">
              <LogisticsIcon name="alert" size={13} aria-hidden />
              Advertencias de Flota
            </span>
            <ul className="list-disc list-inside text-amber-700 space-y-0.5">
              {compliance.warnings.map((w, idx) => <li key={idx}>{w}</li>)}
            </ul>
          </div>
        )}

        {/* Breakdown Grid */}
        <div className="grid grid-cols-2 gap-4 rounded-xl border border-slate-100 bg-slate-50 p-4 sm:grid-cols-4">
          <div>
            <span className="font-bold uppercase text-[10px] text-slate-400 block mb-1">Propietario Vigente</span>
            <span className={`flex items-center gap-1 font-bold ${compliance.is_owner_valid ? 'text-emerald-700' : 'text-amber-600'}`}>
              {compliance.is_owner_valid
                ? <><LogisticsIcon name="check" size={13} aria-hidden /> Válido</>
                : <><LogisticsIcon name="alert" size={13} aria-hidden /> Pendiente</>}
            </span>
          </div>

          <div>
            <span className="font-bold uppercase text-[10px] text-slate-400 block mb-1">Transportista CARRIER</span>
            <span className={`flex items-center gap-1 font-bold ${compliance.is_carrier_valid ? 'text-emerald-700' : 'text-red-600'}`}>
              {compliance.is_carrier_valid
                ? <><LogisticsIcon name="check" size={13} aria-hidden /> Asignado</>
                : <><LogisticsIcon name="x" size={13} aria-hidden /> Sin asignación</>}
            </span>
          </div>

          <div>
            <span className="font-bold uppercase text-[10px] text-slate-400 block mb-1">Perfil de Capacidad</span>
            <span className={`flex items-center gap-1 font-bold ${compliance.is_capacity_configured ? 'text-emerald-700' : 'text-amber-600'}`}>
              {compliance.is_capacity_configured
                ? <><LogisticsIcon name="check" size={13} aria-hidden /> Configurado</>
                : <><LogisticsIcon name="alert" size={13} aria-hidden /> Sin perfil</>}
            </span>
          </div>

          <div>
            <span className="font-bold uppercase text-[10px] text-slate-400 block mb-1">Documentos Vencidos</span>
            <span className={`font-bold ${compliance.expired_documents_count > 0 ? 'text-red-600 font-mono' : 'text-emerald-700'}`}>
              {compliance.expired_documents_count}
            </span>
          </div>
        </div>

        <div className="border-t border-slate-100 pt-3 text-[10px] text-slate-400 text-right font-mono">
          Evaluado por backend el {new Date(compliance.evaluation_date).toLocaleString('es-PE')}
        </div>
      </div>
    </div>
  )
}
