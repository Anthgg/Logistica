import type {
  QualityInspection,
  QualityInspectionControl,
  QualityInspectionSampleSet,
  QualityCertificateReview,
  QualityInspectionOverallResult,
} from '../types/quarantine'
import { StatusBadge } from '../../../components/common/StatusBadge'

export interface QualityInspectionProgressPanelProps {
  inspection: QualityInspection
  controls: QualityInspectionControl[]
  sampleSets: QualityInspectionSampleSet[]
  certificateReviews: QualityCertificateReview[]
}

interface ProgressMetrics {
  totalControls: number
  requiredControls: number
  completedControls: number
  pendingControls: number
  failedControls: number
  controlsWithObservation: number
  missingEvidence: number
  pendingSamples: number
  pendingCertificates: number
  backendResult: QualityInspectionOverallResult
  hasBlocks: boolean
}

function computeMetrics(
  inspection: QualityInspection,
  controls: QualityInspectionControl[],
  sampleSets: QualityInspectionSampleSet[],
  certificateReviews: QualityCertificateReview[],
): ProgressMetrics {
  const totalControls = controls.length
  const requiredControls = controls.filter((c) => c.required).length
  const completedControls = controls.filter((c) => c.status === 'COMPLETED').length
  const pendingControls = controls.filter((c) => c.status === 'PENDING' || c.status === 'IN_PROGRESS').length
  const failedControls = controls.filter((c) => c.status === 'FAILED').length
  const controlsWithObservation = controls.filter((c) => c.result_status === 'CORRECTED').length

  const missingEvidence = controls.filter(
    (c) => c.evidence_required && c.evidence.length === 0,
  ).length

  const allSamples = sampleSets.flatMap((ss) => ss.samples ?? [])
  const pendingSamples = allSamples.filter((s) => !s.inspected).length

  const pendingCertificates = certificateReviews.filter(
    (cr) => cr.status === 'PENDING' || cr.status === 'REVIEW_REQUESTED',
  ).length

  const hasBlocks = controls.some(
    (c) => c.is_blocking && c.status !== 'COMPLETED' && c.status !== 'NOT_APPLICABLE',
  )

  const backendResult: QualityInspectionOverallResult = inspection.overall_result ?? 'NOT_COMPUTED'

  return {
    totalControls,
    requiredControls,
    completedControls,
    pendingControls,
    failedControls,
    controlsWithObservation,
    missingEvidence,
    pendingSamples,
    pendingCertificates,
    backendResult,
    hasBlocks,
  }
}

const resultVariantMap: Record<QualityInspectionOverallResult, string> = {
  PASS: 'emerald',
  PASS_WITH_OBSERVATIONS: 'amber',
  FAIL: 'rose',
  INCONCLUSIVE: 'slate',
  REINSPECTION_REQUIRED: 'amber',
  NOT_COMPUTED: 'slate',
}

export function QualityInspectionProgressPanel({
  inspection,
  controls,
  sampleSets,
  certificateReviews,
}: QualityInspectionProgressPanelProps) {
  const metrics = computeMetrics(inspection, controls, sampleSets, certificateReviews)

  const progressPercentage = metrics.totalControls > 0
    ? Math.round((metrics.completedControls / metrics.totalControls) * 100)
    : 0

  const effectivePercentage = metrics.hasBlocks && progressPercentage === 100
    ? 99
    : progressPercentage

  const progressColor = effectivePercentage === 100
    ? 'bg-emerald-500'
    : effectivePercentage >= 60
      ? 'bg-blue-500'
      : effectivePercentage > 0
        ? 'bg-amber-500'
        : 'bg-slate-300'

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 text-xs space-y-4">
      <div className="flex items-start justify-between gap-2">
        <h4 className="font-semibold text-sm text-slate-800">Progreso de inspección</h4>
        <StatusBadge value={inspection.status.toLowerCase().replace(/_/g, ' ')} />
      </div>

      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <span className="text-slate-600 font-medium">Progreso general</span>
          <span className="font-bold text-sm">{effectivePercentage}%</span>
        </div>
        <div className="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-300 ${progressColor}`}
            style={{ width: `${effectivePercentage}%` }}
          />
        </div>
        {metrics.hasBlocks && (
          <p className="text-[10px] text-amber-600">
            No se alcanza 100% porque existen controles bloqueantes pendientes.
          </p>
        )}
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-lg bg-slate-50 border border-slate-200 p-2.5">
          <div className="text-[10px] text-slate-500 uppercase tracking-wide">Total controles</div>
          <div className="text-lg font-bold text-slate-800 mt-0.5">{metrics.totalControls}</div>
        </div>
        <div className="rounded-lg bg-slate-50 border border-slate-200 p-2.5">
          <div className="text-[10px] text-slate-500 uppercase tracking-wide">Requeridos</div>
          <div className="text-lg font-bold text-slate-800 mt-0.5">{metrics.requiredControls}</div>
        </div>
        <div className="rounded-lg bg-emerald-50 border border-emerald-200 p-2.5">
          <div className="text-[10px] text-emerald-600 uppercase tracking-wide">Completados</div>
          <div className="text-lg font-bold text-emerald-700 mt-0.5">{metrics.completedControls}</div>
        </div>
        <div className="rounded-lg bg-blue-50 border border-blue-200 p-2.5">
          <div className="text-[10px] text-blue-600 uppercase tracking-wide">Pendientes</div>
          <div className="text-lg font-bold text-blue-700 mt-0.5">{metrics.pendingControls}</div>
        </div>
        <div className="rounded-lg bg-rose-50 border border-rose-200 p-2.5">
          <div className="text-[10px] text-rose-600 uppercase tracking-wide">Fallidos</div>
          <div className="text-lg font-bold text-rose-700 mt-0.5">{metrics.failedControls}</div>
        </div>
        <div className="rounded-lg bg-amber-50 border border-amber-200 p-2.5">
          <div className="text-[10px] text-amber-600 uppercase tracking-wide">Con observación</div>
          <div className="text-lg font-bold text-amber-700 mt-0.5">{metrics.controlsWithObservation}</div>
        </div>
      </div>

      {(metrics.missingEvidence > 0 || metrics.pendingSamples > 0 || metrics.pendingCertificates > 0) && (
        <div className="space-y-1.5">
          {metrics.missingEvidence > 0 && (
            <div className="flex items-center gap-2 rounded bg-amber-50 border border-amber-200 px-2.5 py-1.5 text-[11px]">
              <span className="h-1.5 w-1.5 rounded-full bg-amber-500 shrink-0" />
              <span className="text-amber-700 font-medium">{metrics.missingEvidence} control(es) con evidencia faltante</span>
            </div>
          )}
          {metrics.pendingSamples > 0 && (
            <div className="flex items-center gap-2 rounded bg-blue-50 border border-blue-200 px-2.5 py-1.5 text-[11px]">
              <span className="h-1.5 w-1.5 rounded-full bg-blue-500 shrink-0" />
              <span className="text-blue-700 font-medium">{metrics.pendingSamples} muestra(s) pendientes de inspeccionar</span>
            </div>
          )}
          {metrics.pendingCertificates > 0 && (
            <div className="flex items-center gap-2 rounded bg-purple-50 border border-purple-200 px-2.5 py-1.5 text-[11px]">
              <span className="h-1.5 w-1.5 rounded-full bg-purple-500 shrink-0" />
              <span className="text-purple-700 font-medium">{metrics.pendingCertificates} certificado(s) pendientes de revisión</span>
            </div>
          )}
        </div>
      )}

      <div className="border-t border-slate-200 pt-3">
        <div className="flex items-center justify-between">
          <span className="text-[11px] text-slate-500 font-medium">Resultado backend</span>
          <span className={`text-[11px] font-bold ${
            resultVariantMap[metrics.backendResult] === 'emerald' ? 'text-emerald-600' :
            resultVariantMap[metrics.backendResult] === 'rose' ? 'text-rose-600' :
            resultVariantMap[metrics.backendResult] === 'amber' ? 'text-amber-600' :
            'text-slate-500'
          }`}>
            {metrics.backendResult.replace(/_/g, ' ')}
          </span>
        </div>
        <div className="flex items-center justify-between mt-1">
          <span className="text-[11px] text-slate-500">Controles completados / Total</span>
          <span className="text-[11px] font-medium text-slate-700">
            {metrics.completedControls} / {metrics.totalControls}
          </span>
        </div>
        {inspection.control_count > 0 && (
          <div className="flex items-center justify-between mt-0.5">
            <span className="text-[11px] text-slate-500">Mediciones registradas</span>
            <span className="text-[11px] font-medium text-slate-700">{inspection.measurement_count}</span>
          </div>
        )}
        {inspection.sample_set_count > 0 && (
          <div className="flex items-center justify-between mt-0.5">
            <span className="text-[11px] text-slate-500">Conjuntos de muestras</span>
            <span className="text-[11px] font-medium text-slate-700">{inspection.sample_set_count}</span>
          </div>
        )}
        {inspection.evidence_count > 0 && (
          <div className="flex items-center justify-between mt-0.5">
            <span className="text-[11px] text-slate-500">Evidencias</span>
            <span className="text-[11px] font-medium text-slate-700">{inspection.evidence_count}</span>
          </div>
        )}
        {inspection.certificate_review_count > 0 && (
          <div className="flex items-center justify-between mt-0.5">
            <span className="text-[11px] text-slate-500">Revisión de certificados</span>
            <span className="text-[11px] font-medium text-slate-700">{inspection.certificate_review_count}</span>
          </div>
        )}
      </div>
    </div>
  )
}
