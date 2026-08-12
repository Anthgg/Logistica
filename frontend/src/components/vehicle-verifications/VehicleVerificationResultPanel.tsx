import { LogisticsIcon } from '../common/LogisticsIcon'
import type { VehicleVerification } from '../../types/vehicle-verifications'
import { VehicleVerificationEvidencePanel } from './VehicleVerificationEvidencePanel'
import { VehicleVerificationFreshnessIndicator } from './VehicleVerificationFreshnessIndicator'
import { VehicleVerificationProvenanceTable } from './VehicleVerificationProvenanceTable'
import { VehicleVerificationSourceBadge } from './VehicleVerificationSourceBadge'

interface Props {
  verification: VehicleVerification
  onApplyRequested?: () => void
  canApply?: boolean
}

export function VehicleVerificationResultPanel({
  verification,
  onApplyRequested,
  canApply = false,
}: Props) {
  return (
    <div className="space-y-6 text-xs">
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-slate-100 pb-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <VehicleVerificationSourceBadge sourceType={verification.source_type} sourceName={verification.source_name} />
              <span className="font-mono text-slate-400 text-xs">ID: {verification.id.slice(0, 8)}...</span>
            </div>
            <h3 className="text-base font-bold text-slate-800">
              Resultado: {verification.domain_label || verification.domain}
            </h3>
          </div>

          <div className="flex items-center gap-3">
            <VehicleVerificationFreshnessIndicator
              freshness={verification.freshness}
              sourceDate={verification.source_date}
              expirationDate={verification.expires_at}
              daysUntilExpiration={verification.days_until_expiration}
            />

            {canApply && onApplyRequested && verification.result_status === 'VALIDATED' && (
              <button
                type="button"
                onClick={onApplyRequested}
                className="rounded-xl bg-indigo-600 px-4 py-2 text-xs font-bold text-white shadow-xs hover:bg-indigo-700 transition-colors"
              >
                Aplicar a Ficha Vehículo →
              </button>
            )}
          </div>
        </div>

        {/* Warnings */}
        {verification.warnings && verification.warnings.length > 0 && (
          <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 space-y-1">
            <span className="font-bold text-amber-800 flex items-center gap-1.5 text-xs uppercase tracking-wider">
              <LogisticsIcon name="alert" size={14} aria-hidden /> Advertencias Observadas
            </span>
            <ul className="list-disc list-inside text-amber-700 space-y-0.5">
              {verification.warnings.map((w, idx) => <li key={idx}>{w}</li>)}
            </ul>
          </div>
        )}

        {/* Provenance Table */}
        <VehicleVerificationProvenanceTable provenanceFields={verification.provenance_fields} />

        {/* Evidences */}
        <VehicleVerificationEvidencePanel evidences={verification.evidences} verificationId={verification.id} />
      </div>
    </div>
  )
}
