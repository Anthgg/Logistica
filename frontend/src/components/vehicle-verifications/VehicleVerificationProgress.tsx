import { useEffect } from 'react'
import type { VehicleVerification } from '../../types/vehicle-verifications'
import { VehicleVerificationSourceBadge } from './VehicleVerificationSourceBadge'

interface Props {
  verification: VehicleVerification
  onRefreshNeeded?: () => void
}

export function VehicleVerificationProgress({ verification, onRefreshNeeded }: Props) {
  const isInProgress =
    verification.status === 'REQUESTED' ||
    verification.status === 'QUEUED' ||
    verification.status === 'IN_PROGRESS'

  // Controlled polling every 5 seconds only while in progress
  useEffect(() => {
    if (!isInProgress || !onRefreshNeeded) return

    const timer = setInterval(() => {
      onRefreshNeeded()
    }, 5000)

    return () => clearInterval(timer)
  }, [isInProgress, onRefreshNeeded])

  const statusStepMap: Record<string, number> = {
    REQUESTED: 1,
    QUEUED: 2,
    IN_PROGRESS: 3,
    COMPLETED: 4,
    UNDER_REVIEW: 4,
    FAILED: 4,
    CANCELLED: 4,
  }

  const currentStep = statusStepMap[verification.status] || 1

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs space-y-4 text-xs">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div className="flex items-center gap-2">
          <VehicleVerificationSourceBadge sourceType={verification.source_type} sourceName={verification.source_name} size="sm" />
          <span className="font-bold text-slate-800">{verification.domain_label || verification.domain}</span>
        </div>
        <span className="font-mono text-[11px] text-slate-400">
          Solicitado: {new Date(verification.requested_at).toLocaleString('es-PE')}
        </span>
      </div>

      {/* Progress Bar */}
      <div className="space-y-2">
        <div className="flex justify-between text-[11px] font-bold text-slate-600">
          <span>Estado de Ejecución: <strong className="text-indigo-700">{verification.status}</strong></span>
          {isInProgress && <span className="animate-pulse text-indigo-600 font-mono">● Procesando en background...</span>}
        </div>

        <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
          <div
            className={`h-full transition-colors duration-500 ${
              verification.status === 'COMPLETED'
                ? 'bg-emerald-500'
                : verification.status === 'FAILED'
                ? 'bg-rose-500'
                : 'bg-indigo-600 animate-pulse'
            }`}
            style={{ width: `${(currentStep / 4) * 100}%` }}
          />
        </div>
      </div>

      <div className="grid grid-cols-4 gap-2 text-center text-[10px]">
        <div className={currentStep >= 1 ? 'font-bold text-indigo-700' : 'text-slate-400'}>1. Solicitada</div>
        <div className={currentStep >= 2 ? 'font-bold text-indigo-700' : 'text-slate-400'}>2. En Cola</div>
        <div className={currentStep >= 3 ? 'font-bold text-indigo-700' : 'text-slate-400'}>3. Consultando</div>
        <div className={currentStep >= 4 ? 'font-bold text-slate-800' : 'text-slate-400'}>4. Finalizado</div>
      </div>
    </div>
  )
}
