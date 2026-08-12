import { useQuery } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import type { QualityInspection, QualityInspectionControl } from '../types/quarantine'

interface ValidationSummary {
  pending_controls: number
  failed_controls: number
  invalid_measurements: number
  incompatible_units: number
  incomplete_samples: number
  missing_certificates: number
  missing_evidence: number
  integrity_errors: string[]
  warnings: string[]
  closure_options: string[]
}

function computeValidationSummary(
  inspection: QualityInspection,
  controls: QualityInspectionControl[] | undefined,
): ValidationSummary {
  const pendingControls = controls?.filter((c) => c.status === 'PENDING' || c.status === 'IN_PROGRESS').length ?? 0
  const failedControls = controls?.filter((c) => c.status === 'FAILED').length ?? 0
  const invalidMeasurements = controls?.reduce((acc, c) => {
    const invalid = c.measurements.filter((m) => m.tolerance_result === 'OUTSIDE_TOLERANCE').length
    return acc + invalid
  }, 0) ?? 0
  const incompleteSamples = controls?.reduce((acc, c) => {
    const incomplete = c.sample_references.filter((s) => !s.inspected).length
    return acc + incomplete
  }, 0) ?? 0
  const missingCertificates = inspection.certificate_review_count === 0 && inspection.control_count > 0 ? 1 : 0
  const missingEvidence = inspection.evidence_count === 0 && inspection.control_count > 0 ? 1 : 0

  const errors: string[] = []
  const warnings: string[] = []
  const closureOptions: string[] = []

  if (pendingControls > 0) {
    errors.push(`${pendingControls} control(es) pendiente(s) de completar`)
  }
  if (failedControls > 0) {
    errors.push(`${failedControls} control(es) con resultado FAIL`)
  }
  if (invalidMeasurements > 0) {
    errors.push(`${invalidMeasurements} medición(es) fuera de tolerancia`)
  }
  if (incompleteSamples > 0) {
    warnings.push(`${incompleteSamples} muestra(s) sin inspeccionar`)
  }
  if (missingCertificates > 0) {
    warnings.push('Certificados requeridos no registrados')
  }
  if (missingEvidence > 0) {
    warnings.push('Evidencia requerida no cargada')
  }

  if (errors.length === 0 && warnings.length === 0) {
    closureOptions.push('Completar inspección')
    closureOptions.push('Solicitar validación')
  } else if (errors.length === 0) {
    closureOptions.push('Completar con advertencias')
  }

  return {
    pending_controls: pendingControls,
    failed_controls: failedControls,
    invalid_measurements: invalidMeasurements,
    incompatible_units: 0,
    incomplete_samples: incompleteSamples,
    missing_certificates: missingCertificates,
    missing_evidence: missingEvidence,
    integrity_errors: errors,
    warnings,
    closure_options: closureOptions,
  }
}

function ValidationRow({
  label,
  count,
  tone,
}: {
  label: string
  count: number
  tone: 'success' | 'danger' | 'warning' | 'neutral'
}) {
  const toneClasses = {
    success: 'border-emerald-100 bg-emerald-50 text-emerald-700',
    danger: 'border-rose-100 bg-rose-50 text-rose-700',
    warning: 'border-amber-100 bg-amber-50 text-amber-700',
    neutral: 'border-slate-100 bg-slate-50 text-slate-600',
  }
  return (
    <div className={`flex items-center justify-between rounded-lg border px-3 py-2 text-xs ${toneClasses[tone]}`}>
      <span className="font-medium">{label}</span>
      <span className="text-sm font-bold">{count}</span>
    </div>
  )
}

export function QualityInspectionValidationPanel({
  inspectionId,
}: {
  inspectionId: string
}) {
  const { hasPermission } = useLogisticsPermissions()
  const canValidate = hasPermission(LOGISTICS_PERMISSIONS.quarantine.validateInspection)

  const {
    data: inspection,
    isLoading: isLoadingInspection,
    isError: isInspectionError,
    error: inspectionError,
  } = useQuery<QualityInspection>(
    ['inspection', inspectionId],
    `/logistics/quality-inspections/inspections/${inspectionId}`,
  )

  const {
    data: controls,
    isLoading: isLoadingControls,
    isError: isControlsError,
    error: controlsError,
  } = useQuery<QualityInspectionControl[]>(
    ['inspection-controls', inspectionId],
    `/logistics/quality-inspections/inspections/${inspectionId}/controls`,
  )

  if (!canValidate) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
        <h2 className="text-sm font-bold text-slate-800">Panel de validación</h2>
        <p className="mt-2 text-xs text-slate-500">No tiene permisos para validar.</p>
      </div>
    )
  }

  const isLoading = isLoadingInspection || isLoadingControls
  const isError = isInspectionError || isControlsError
  const error = inspectionError ?? controlsError

  const summary = inspection ? computeValidationSummary(inspection, controls) : null

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
      <header className="mb-3 border-b border-slate-100 pb-2">
        <h2 className="text-sm font-bold text-slate-800">Panel de validación</h2>
        <p className="mt-0.5 text-xs text-slate-500">
          Resultado del backend de validación de la inspección.
        </p>
      </header>

      {isLoading && (
        <div className="space-y-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-10 w-full animate-pulse rounded-lg bg-slate-100" />
          ))}
        </div>
      )}

      {isError && (
        <div className="rounded-lg border border-rose-100 bg-rose-50/40 p-3 text-xs text-rose-700">
          {error ?? 'Error al cargar datos de validación.'}
        </div>
      )}

      {summary && (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            <ValidationRow label="Controles pendientes" count={summary.pending_controls} tone={summary.pending_controls > 0 ? 'danger' : 'success'} />
            <ValidationRow label="Controles fallidos" count={summary.failed_controls} tone={summary.failed_controls > 0 ? 'danger' : 'success'} />
            <ValidationRow label="Mediciones inválidas" count={summary.invalid_measurements} tone={summary.invalid_measurements > 0 ? 'danger' : 'success'} />
            <ValidationRow label="Unidades incompatibles" count={summary.incompatible_units} tone={summary.incompatible_units > 0 ? 'danger' : 'success'} />
          </div>
          <div className="grid grid-cols-3 gap-2">
            <ValidationRow label="Muestras incompletas" count={summary.incomplete_samples} tone={summary.incomplete_samples > 0 ? 'warning' : 'success'} />
            <ValidationRow label="Certificados faltantes" count={summary.missing_certificates} tone={summary.missing_certificates > 0 ? 'warning' : 'success'} />
            <ValidationRow label="Evidencia faltante" count={summary.missing_evidence} tone={summary.missing_evidence > 0 ? 'warning' : 'success'} />
          </div>

          {summary.integrity_errors.length > 0 && (
            <div className="rounded-lg border border-rose-100 bg-rose-50/40 p-3">
              <h3 className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-rose-600">
                Errores de integridad
              </h3>
              <ul className="space-y-1 text-xs text-rose-700">
                {summary.integrity_errors.map((err, i) => (
                  <li key={i}>• {err}</li>
                ))}
              </ul>
            </div>
          )}

          {summary.warnings.length > 0 && (
            <div className="rounded-lg border border-amber-100 bg-amber-50/40 p-3">
              <h3 className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-amber-600">
                Advertencias
              </h3>
              <ul className="space-y-1 text-xs text-amber-700">
                {summary.warnings.map((warn, i) => (
                  <li key={i}>• {warn}</li>
                ))}
              </ul>
            </div>
          )}

          {summary.closure_options.length > 0 && (
            <div className="rounded-lg border border-slate-200 bg-slate-50/60 p-3">
              <h3 className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                Opciones de cierre
              </h3>
              <ul className="space-y-1 text-xs text-slate-700">
                {summary.closure_options.map((opt, i) => (
                  <li key={i}>• {opt}</li>
                ))}
              </ul>
            </div>
          )}

          {summary.integrity_errors.length === 0 && summary.warnings.length === 0 && (
            <div className="rounded-lg border border-emerald-100 bg-emerald-50/40 p-3 text-xs text-emerald-700">
              La validación del backend no reporta errores. La inspección puede completarse.
            </div>
          )}
        </div>
      )}
    </div>
  )
}
