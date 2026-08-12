import type { QualityPlanValidation, QualityPlanValidationStatus } from '../types/quality-inspection-plans'
import { Button } from '../../../components/common/Button'

interface QualityPlanValidationPanelProps {
  validation: QualityPlanValidation | null
  onValidate: () => void
}

const STATUS_CONFIG: Record<QualityPlanValidationStatus, { label: string; tone: string }> = {
  NOT_VALIDATED: { label: 'Sin validar', tone: 'bg-slate-100 text-slate-600' },
  VALID: { label: 'VALID', tone: 'bg-emerald-50 text-emerald-700 border border-emerald-200' },
  INVALID: { label: 'INVALID', tone: 'bg-rose-50 text-rose-700 border border-rose-200' },
  WARNING: { label: 'WARNING', tone: 'bg-amber-50 text-amber-700 border border-amber-200' },
}

export function QualityPlanValidationPanel({ validation, onValidate }: QualityPlanValidationPanelProps) {
  if (!validation) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-4 text-xs">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-slate-800">Validación</h2>
          <Button variant="primary" size="small" onClick={onValidate}>
            Validar versión
          </Button>
        </div>
        <p className="mt-2 text-slate-500">No se ha ejecutado la validación.</p>
      </div>
    )
  }

  const cfg = STATUS_CONFIG[validation.status]

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 text-xs">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-bold text-slate-800">Validación</h2>
        <div className="flex items-center gap-2">
          <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-semibold ${cfg.tone}`}>
            {cfg.label}
          </span>
          <Button variant="secondary" size="small" onClick={onValidate}>
            Re-validar
          </Button>
        </div>
      </div>

      {validation.blocking_errors.length > 0 && (
        <div className="mt-3">
          <h3 className="mb-1 font-semibold text-rose-700">Errores bloqueantes ({validation.blocking_errors.length})</h3>
          <ul className="space-y-1">
            {validation.blocking_errors.map((err, i) => (
              <li key={i} className="rounded bg-rose-50 px-2 py-1 text-rose-700">
                <span className="font-mono text-[10px] text-rose-500">{err.code}</span>
                <span className="ml-2">{err.message}</span>
                {err.field && <span className="ml-1 text-rose-400">({err.field})</span>}
              </li>
            ))}
          </ul>
        </div>
      )}

      {validation.warnings.length > 0 && (
        <div className="mt-3">
          <h3 className="mb-1 font-semibold text-amber-700">Advertencias ({validation.warnings.length})</h3>
          <ul className="space-y-1">
            {validation.warnings.map((w, i) => (
              <li key={i} className="rounded bg-amber-50 px-2 py-1 text-amber-700">
                <span className="font-mono text-[10px] text-amber-500">{w.code}</span>
                <span className="ml-2">{w.message}</span>
                {w.field && <span className="ml-1 text-amber-400">({w.field})</span>}
              </li>
            ))}
          </ul>
        </div>
      )}

      <dl className="mt-3 grid grid-cols-2 gap-1 text-[11px] text-slate-600 md:grid-cols-3">
        <dt className="text-slate-500">Scopes válidos:</dt>
        <dd>{validation.scopes_valid ? 'Sí' : 'No'}</dd>
        {validation.duplicate_controls.length > 0 && (
          <>
            <dt className="text-slate-500">Controles duplicados:</dt>
            <dd className="text-rose-600">{validation.duplicate_controls.length}</dd>
          </>
        )}
        {validation.invalid_units.length > 0 && (
          <>
            <dt className="text-slate-500">Unidades inválidas:</dt>
            <dd className="text-rose-600">{validation.invalid_units.length}</dd>
          </>
        )}
        {validation.invalid_tolerances.length > 0 && (
          <>
            <dt className="text-slate-500">Tolerancias inválidas:</dt>
            <dd className="text-rose-600">{validation.invalid_tolerances.length}</dd>
          </>
        )}
        {validation.invalid_sampling.length > 0 && (
          <>
            <dt className="text-slate-500">Muestreos inválidos:</dt>
            <dd className="text-rose-600">{validation.invalid_sampling.length}</dd>
          </>
        )}
        {validation.incomplete_certificates.length > 0 && (
          <>
            <dt className="text-slate-500">Certificados incompletos:</dt>
            <dd className="text-amber-600">{validation.incomplete_certificates.length}</dd>
          </>
        )}
        {validation.inactive_references.length > 0 && (
          <>
            <dt className="text-slate-500">Referencias inactivas:</dt>
            <dd className="text-amber-600">{validation.inactive_references.length}</dd>
          </>
        )}
      </dl>

      <div className="mt-3 border-t border-slate-100 pt-2">
        <h3 className="mb-1 font-semibold text-slate-700">Opciones de activación</h3>
        <dl className="grid grid-cols-2 gap-1 text-[11px] text-slate-600">
          <dt className="text-slate-500">Puede activar ahora:</dt>
          <dd>{validation.activation_options.can_activate_now ? 'Sí' : 'No'}</dd>
          <dt className="text-slate-500">Requiere programación:</dt>
          <dd>{validation.activation_options.requires_scheduling ? 'Sí' : 'No'}</dd>
          <dt className="text-slate-500">Activación más temprana:</dt>
          <dd>{validation.activation_options.earliest_activation ?? '—'}</dd>
          <dt className="text-slate-500">Conflictos a resolver:</dt>
          <dd>{validation.activation_options.conflicts_to_resolve}</dd>
        </dl>
      </div>

      <dl className="mt-2 grid grid-cols-2 gap-1 text-[11px] text-slate-500">
        <dt>Servidor:</dt>
        <dd>{validation.server_time}</dd>
        <dt>Hash:</dt>
        <dd className="font-mono">{validation.validation_hash?.slice(0, 16) ?? '—'}</dd>
      </dl>
    </div>
  )
}
