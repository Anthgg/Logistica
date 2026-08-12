import { useState } from 'react'
import { useMutation } from '../../../features/inbound-docks/hooks/useQuery'
import { qualityPlanVersionsApi } from '../api/qualityPlanVersionsApi'
import type {
  QualityInspectionPlanVersion,
  QualityInspectionPlanCapabilities,
  QualityPlanValidation,
} from '../types/quality-inspection-plans'
import { Button } from '../../../components/common/Button'

interface ActivateQualityPlanVersionDialogProps {
  version: QualityInspectionPlanVersion
  capabilities: QualityInspectionPlanCapabilities
  validation?: QualityPlanValidation | null
  onSuccess: () => void
}

export function ActivateQualityPlanVersionDialog({
  version,
  capabilities,
  validation,
  onSuccess,
}: ActivateQualityPlanVersionDialogProps) {
  const [confirmed, setConfirmed] = useState(false)
  const [scheduledFor, setScheduledFor] = useState('')

  const activateMutation = useMutation(
    async () => {
      return qualityPlanVersionsApi.activate(version.version_id, {
        confirmation: true,
        scheduled_for: scheduled_for || undefined,
      })
    },
    { onSuccess: () => onSuccess() },
  )

  const scheduled_for = scheduledFor

  const handleActivate = () => {
    if (!confirmed) return
    activateMutation.mutate(undefined as never)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onSuccess} />
      <div className="relative z-10 w-full max-w-lg rounded-xl bg-white p-6 shadow-xl text-xs">
        <h2 className="mb-2 text-sm font-bold text-slate-800">Activar versión</h2>
        <p className="mb-4 text-slate-500">
          Revise la información antes de activar. Esta acción puede tener efectos en inspecciones futuras.
        </p>

        <dl className="mb-4 grid grid-cols-2 gap-1 text-[11px]">
          <dt className="text-slate-500">Plan:</dt>
          <dd className="font-semibold text-slate-800">{version.plan_id}</dd>
          <dt className="text-slate-500">Versión:</dt>
          <dd>{version.version_number}</dd>
          <dt className="text-slate-500">Vigencia:</dt>
          <dd>{version.valid_from ?? '—'} → {version.valid_until ?? '—'}</dd>
          <dt className="text-slate-500">Prioridad:</dt>
          <dd>{version.priority}</dd>
          <dt className="text-slate-500">Scopes:</dt>
          <dd>{version.scope_count}</dd>
          <dt className="text-slate-500">Controles:</dt>
          <dd>{version.control_count}</dd>
          <dt className="text-slate-500">Tolerancias:</dt>
          <dd>{version.tolerance_count}</dd>
          <dt className="text-slate-500">Muestreos:</dt>
          <dd>{version.sampling_count}</dd>
          <dt className="text-slate-500">Certificados:</dt>
          <dd>{version.certificate_count}</dd>
          <dt className="text-slate-500">Validación:</dt>
          <dd>
            <span
              className={`inline-flex rounded-full px-1.5 py-0.5 text-[10px] font-semibold ${
                version.validation_status === 'VALID'
                  ? 'bg-emerald-100 text-emerald-700'
                  : version.validation_status === 'INVALID'
                    ? 'bg-rose-100 text-rose-700'
                    : version.validation_status === 'WARNING'
                      ? 'bg-amber-100 text-amber-700'
                      : 'bg-slate-100 text-slate-600'
              }`}
            >
              {version.validation_status}
            </span>
          </dd>
          <dt className="text-slate-500">Conflictos:</dt>
          <dd>{version.conflict_count}</dd>
          <dt className="text-slate-500">Hash:</dt>
          <dd className="font-mono">{version.hash?.slice(0, 16) ?? '—'}</dd>
        </dl>

        {validation && validation.activation_options.conflicts_to_resolve > 0 && (
          <div className="mb-3 rounded-lg bg-amber-50 p-2 text-amber-700">
            Hay {validation.activation_options.conflicts_to_resolve} conflicto(s) pendiente(s).
          </div>
        )}

        {!capabilities.can_activate && (
          <div className="mb-3 rounded-lg bg-rose-50 p-2 text-rose-700">
            No tiene permisos para activar esta versión.
          </div>
        )}

        <label className="mb-3 block">
          <span className="text-slate-500">Programar activación (opcional)</span>
          <input
            type="datetime-local"
            value={scheduledFor}
            onChange={(e) => setScheduledFor(e.target.value)}
            className="mt-0.5 w-full rounded-lg border border-slate-300 p-1.5 text-[11px]"
          />
        </label>

        <label className="mb-4 flex items-center gap-2 text-[11px] text-slate-600">
          <input
            type="checkbox"
            checked={confirmed}
            onChange={(e) => setConfirmed(e.target.checked)}
            className="h-4 w-4 rounded border-slate-300"
          />
          Confirmo que revisé la validación, conflictos y configuración antes de activar.
        </label>

        {activateMutation.error && (
          <p className="mb-3 text-rose-500">{activateMutation.error}</p>
        )}

        <div className="flex justify-end gap-2">
          <Button variant="secondary" size="small" onClick={onSuccess}>
            Cancelar
          </Button>
          <Button
            variant="primary"
            size="small"
            isLoading={activateMutation.isPending}
            disabled={!confirmed || !capabilities.can_activate}
            onClick={handleActivate}
          >
            Activar
          </Button>
        </div>
      </div>
    </div>
  )
}
