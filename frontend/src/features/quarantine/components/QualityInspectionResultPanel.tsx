import { useQuery } from '../../inbound-docks/hooks/useQuery'
import type {
  QualityInspection,
  QualityInspectionControl,
  QualityInspectionEvidence,
  QualityQuarantineIntegrity,
} from '../types/quarantine'
import { StatusBadge } from '../../../components/common/StatusBadge'

interface Props {
  inspection: QualityInspection
}

const RESULT_VARIANTS: Record<string, string> = {
  PASS: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  PASS_WITH_OBSERVATIONS: 'border-amber-200 bg-amber-50 text-amber-700',
  FAIL: 'border-rose-200 bg-rose-50 text-rose-700',
  INCONCLUSIVE: 'border-slate-200 bg-slate-50 text-slate-600',
  REINSPECTION_REQUIRED: 'border-blue-200 bg-blue-50 text-blue-700',
  NOT_COMPUTED: 'border-slate-200 bg-slate-50 text-slate-500',
}

export function QualityInspectionResultPanel({ inspection }: Props) {
  const controlsQuery = useQuery<{ items: QualityInspectionControl[] }>(
    ['inspection-controls', inspection.inspection_id],
    `/logistics/quality-inspections/inspections/${inspection.inspection_id}/controls`,
    {},
    { enabled: !!inspection.inspection_id },
  )

  const evidenceQuery = useQuery<{ items: QualityInspectionEvidence[] }>(
    ['inspection-evidence', inspection.inspection_id],
    `/logistics/quality-inspection-evidence/evidence?inspection_id=${inspection.inspection_id}`,
    {},
    { enabled: !!inspection.inspection_id },
  )

  const integrityQuery = useQuery<QualityQuarantineIntegrity>(
    ['inspection-integrity', inspection.inspection_id],
    `/logistics/quality-inspections/inspections/${inspection.inspection_id}/integrity`,
    {},
    { enabled: !!inspection.inspection_id },
  )

  const controls = controlsQuery.data?.items ?? []
  const evidenceItems = evidenceQuery.data?.items ?? []
  const integrity = integrityQuery.data ?? null

  const blockingControls = controls.filter((c) => c.is_blocking)
  const outOfRangeControls = controls.filter((c) => c.tolerance_result === 'OUTSIDE_TOLERANCE')
  const certificateCount = inspection.certificate_review_count

  const resultLabel: Record<string, string> = {
    PASS: 'PASS',
    PASS_WITH_OBSERVATIONS: 'PASS con observaciones',
    FAIL: 'FAIL',
    INCONCLUSIVE: 'Inconcluso',
    REINSPECTION_REQUIRED: 'Reinspección requerida',
    NOT_COMPUTED: 'No computado',
  }

  const resultClass = RESULT_VARIANTS[inspection.overall_result] ?? RESULT_VARIANTS.NOT_COMPUTED

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-sm font-semibold text-ink mb-3">Resultado de inspección de calidad</h3>
        <div className="rounded-lg border border-slate-200 divide-y divide-slate-200">
          {/* Overall Result */}
          <div className="p-4 text-xs">
            <span className="text-muted">Resultado calculado por backend</span>
            <div className="mt-2">
              <span className={`inline-flex items-center gap-1 rounded-full border px-3 py-1 text-xs font-semibold ${resultClass}`}>
                {resultLabel[inspection.overall_result] ?? inspection.overall_result}
              </span>
            </div>
          </div>

          {/* Basis */}
          <div className="grid grid-cols-2 gap-4 p-4 text-xs">
            <div>
              <span className="text-muted">Base de evaluación</span>
              <p className="font-medium text-ink">Inspección {inspection.inspection_code ?? inspection.inspection_id}</p>
            </div>
            <div>
              <span className="text-muted">Plan de inspección</span>
              <p className="font-medium text-ink">{inspection.plan_code ?? 'N/A'}</p>
            </div>
          </div>

          {/* Controls Summary */}
          <div className="grid grid-cols-2 gap-4 p-4 text-xs">
            <div>
              <span className="text-muted">Controles completados</span>
              <p className="font-medium text-ink">{inspection.controls_completed} / {inspection.control_count}</p>
            </div>
            <div>
              <span className="text-muted">Controles aprobados</span>
              <p className="font-medium text-emerald-600">{inspection.controls_passed}</p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 p-4 text-xs">
            <div>
              <span className="text-muted">Controles fallidos</span>
              <p className="font-medium text-rose-600">{inspection.controls_failed}</p>
            </div>
            <div>
              <span className="text-muted">Controles con observaciones</span>
              <p className="font-medium text-amber-600">{inspection.controls_with_observations}</p>
            </div>
          </div>

          {/* Blocking Controls */}
          {blockingControls.length > 0 && (
            <div className="p-4 text-xs">
              <span className="text-muted">Controles bloqueantes</span>
              <div className="mt-2 space-y-1">
                {blockingControls.map((ctrl) => (
                  <div key={ctrl.control_id} className="flex items-center gap-2 rounded border border-rose-200 bg-rose-50 p-2">
                    <StatusBadge value={ctrl.status} />
                    <span className="text-ink font-medium">{ctrl.name}</span>
                    <span className="text-muted ml-auto">{ctrl.code}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Out of Range */}
          {outOfRangeControls.length > 0 && (
            <div className="p-4 text-xs">
              <span className="text-muted">Mediciones fuera de rango</span>
              <div className="mt-2 space-y-1">
                {outOfRangeControls.map((ctrl) => (
                  <div key={ctrl.control_id} className="flex items-center gap-2 rounded border border-amber-200 bg-amber-50 p-2">
                    <span className="text-ink font-medium">{ctrl.name}</span>
                    <span className="text-muted ml-auto">
                      Esperado: {ctrl.expected_value ?? 'N/A'} | Resultado: {ctrl.result_value ?? ctrl.result_text ?? 'N/A'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Certificates */}
          <div className="grid grid-cols-2 gap-4 p-4 text-xs">
            <div>
              <span className="text-muted">Revisiones de certificados</span>
              <p className="font-medium text-ink">{certificateCount}</p>
            </div>
            <div>
              <span className="text-muted">Total de mediciones</span>
              <p className="font-medium text-ink">{inspection.measurement_count}</p>
            </div>
          </div>

          {/* Evidence */}
          <div className="p-4 text-xs">
            <div className="flex items-center justify-between mb-2">
              <span className="text-muted">Evidencia</span>
              <span className="font-medium text-ink">{evidenceItems.length} archivos</span>
            </div>
            {evidenceItems.length > 0 && (
              <div className="space-y-1">
                {evidenceItems.slice(0, 5).map((ev) => (
                  <div key={ev.evidence_id} className="flex items-center gap-2 text-[11px] text-muted">
                    <span className="w-1.5 h-1.5 rounded-full bg-slate-400 shrink-0" />
                    <span className="truncate">{ev.file.filename}</span>
                    <span className="text-ink font-medium">{ev.evidence_type}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Date & Inspector */}
          <div className="grid grid-cols-2 gap-4 p-4 text-xs">
            <div>
              <span className="text-muted">Fecha de completado</span>
              <p className="font-medium text-ink">
                {inspection.completed_at
                  ? new Date(inspection.completed_at).toLocaleString()
                  : 'N/A'}
              </p>
            </div>
            <div>
              <span className="text-muted">Inspector</span>
              <p className="font-medium text-ink">{inspection.inspector?.display_name ?? 'N/A'}</p>
            </div>
          </div>

          {/* Integrity */}
          {integrity && (
            <div className="p-4 text-xs">
              <span className="text-muted">Integridad</span>
              <div className="mt-1">
                <StatusBadge value={integrity.status.toLowerCase()} />
              </div>
              {integrity.last_verified_at && (
                <p className="text-muted mt-1">Última verificación: {new Date(integrity.last_verified_at).toLocaleString()}</p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
