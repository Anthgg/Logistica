import { useCallback, useEffect, useMemo, useState } from 'react'
import { Button } from '../../../components/common/Button'
import { useMutation, useQuery } from '../../inbound-docks/hooks/useQuery'
import { apiRequest, getCsrfToken } from '../../../api/api-client'
import { ErrorPanel, SkeletonRows } from '../../inbound-docks/components/ui/Primitives'
import { QualityPlanScopesEditor } from './QualityPlanScopesEditor'
import { QualityControlsEditor } from './QualityControlsEditor'
import { QualityPlanValidationPanel } from './QualityPlanValidationPanel'
import type {
  QualityInspectionPlanVersion,
  QualityInspectionPlanCapabilities,
  QualityPlanScope,
  QualityControlDefinition,
  QualityTolerance,
  QualitySamplingPlan,
  QualityCertificateRequirement,
  QualityPlanValidation,
  PaginatedResponse,
} from '../types/quality-inspection-plans'

const WIZARD_STEPS = [
  { key: 'info', label: 'Info general' },
  { key: 'validity', label: 'Vigencia y prioridad' },
  { key: 'scopes', label: 'Ambitos' },
  { key: 'controls', label: 'Controles' },
  { key: 'tolerances', label: 'Tolerancias' },
  { key: 'sampling', label: 'Muestreo' },
  { key: 'certificates', label: 'Certificados' },
  { key: 'conditions', label: 'Condiciones' },
  { key: 'future', label: 'Evidencias futuras' },
  { key: 'review', label: 'Revision' },
  { key: 'validation', label: 'Validacion' },
] as const


interface QualityPlanVersionWizardProps {
  planId: string
  versionId?: string
  onComplete: () => void
  onCancel: () => void
}

interface VersionFormData {
  valid_from: string
  valid_until: string
  priority: number
}

function formatDate(iso: string | null): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('es-EC', { year: 'numeric', month: 'short', day: 'numeric' })
}

export function QualityPlanVersionWizard({
  planId,
  versionId: initialVersionId,
  onComplete,
  onCancel,
}: QualityPlanVersionWizardProps) {
  const [currentStepIndex, setCurrentStepIndex] = useState(0)
  const [versionId, setVersionId] = useState<string | null>(initialVersionId ?? null)
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set())
  const [error, setError] = useState<string | null>(null)



  const [formData, setFormData] = useState<VersionFormData>({
    valid_from: '',
    valid_until: '',
    priority: 0,
  })

  const [capabilities, setCapabilities] = useState<QualityInspectionPlanCapabilities | null>(null)

  const currentStep = WIZARD_STEPS[currentStepIndex]

  const versionQueryKey = useMemo(() => ['quality-plan-version', versionId], [versionId])
  const { data: versionData, isLoading: versionLoading } = useQuery<QualityInspectionPlanVersion>(
    versionQueryKey,
    `/logistics/quality-plan-versions/${versionId}`,
    {},
    { enabled: Boolean(versionId) },
  )

  const scopesQueryKey = useMemo(() => ['quality-plan-scopes', versionId], [versionId])
  const { data: scopesData, isLoading: scopesLoading, refetch: refetchScopes } = useQuery<QualityPlanScope[]>(
    scopesQueryKey,
    `/logistics/quality-plan-scopes`,
    { version_id: versionId },
    { enabled: Boolean(versionId) && currentStep.key === 'scopes' },
  )

  const controlsQueryKey = useMemo(() => ['quality-plan-controls', versionId], [versionId])
  const { data: controlsData, isLoading: controlsLoading, refetch: refetchControls } = useQuery<QualityControlDefinition[]>(
    controlsQueryKey,
    `/logistics/quality-controls`,
    { version_id: versionId },
    { enabled: Boolean(versionId) && currentStep.key === 'controls' },
  )

  const tolerancesQueryKey = useMemo(() => ['quality-plan-tolerances'], [])
  const { data: tolerancesData, isLoading: tolerancesLoading } = useQuery<PaginatedResponse<QualityTolerance>>(
    tolerancesQueryKey,
    `/logistics/quality-tolerances`,
    {},
    { enabled: currentStep.key === 'tolerances' },
  )

  const samplingQueryKey = useMemo(() => ['quality-plan-sampling'], [])
  const { data: samplingData, isLoading: samplingLoading } = useQuery<PaginatedResponse<QualitySamplingPlan>>(
    samplingQueryKey,
    `/logistics/quality-sampling-plans`,
    {},
    { enabled: currentStep.key === 'sampling' },
  )

  const certificatesQueryKey = useMemo(() => ['quality-plan-certificates'], [])
  const { data: certificatesData, isLoading: certificatesLoading } = useQuery<PaginatedResponse<QualityCertificateRequirement>>(
    certificatesQueryKey,
    `/logistics/quality-certificate-requirements`,
    {},
    { enabled: currentStep.key === 'certificates' },
  )

  const validationQueryKey = useMemo(() => ['quality-plan-validation', versionId], [versionId])
  const { data: validationData, isLoading: validationLoading } = useQuery<QualityPlanValidation>(
    validationQueryKey,
    `/logistics/quality-plan-versions/${versionId}/validate`,
    {},
    { enabled: Boolean(versionId) && currentStep.key === 'validation' },
  )



  const createVersionMutation = useMutation<VersionFormData, QualityInspectionPlanVersion>(
    async (input) => {
      const csrf = await getCsrfToken()
      return apiRequest<QualityInspectionPlanVersion>({
        path: `/logistics/quality-plan-versions?plan_id=${planId}`,
        method: 'POST',
        headers: { 'X-CSRF-Token': csrf, 'Idempotency-Key': crypto.randomUUID() },
        body: {
          valid_from: input.valid_from || undefined,
          valid_until: input.valid_until || undefined,
          priority: input.priority,
        },
      })
    },
    {
      onSuccess: (result) => {
        setVersionId(result.version_id)
        setFormData({
          valid_from: result.valid_from ?? '',
          valid_until: result.valid_until ?? '',
          priority: result.priority,
        })
        setCompletedSteps((prev) => new Set([...prev, 0]))
        setCurrentStepIndex(1)
        setError(null)
      },
      onError: (err) => setError(err.message),
    },
  )

  const updateVersionMutation = useMutation<VersionFormData, QualityInspectionPlanVersion>(
    async (input) => {
      if (!versionId) throw new Error('No version ID')
      const csrf = await getCsrfToken()
      return apiRequest<QualityInspectionPlanVersion>({
        path: `/logistics/quality-plan-versions/${versionId}`,
        method: 'PATCH',
        headers: { 'X-CSRF-Token': csrf, 'Idempotency-Key': crypto.randomUUID() },
        body: {
          valid_from: input.valid_from || undefined,
          valid_until: input.valid_until || undefined,
          priority: input.priority,
        },
      })
    },
    {
      onSuccess: (result) => {
        setFormData({
          valid_from: result.valid_from ?? '',
          valid_until: result.valid_until ?? '',
          priority: result.priority,
        })
        setCompletedSteps((prev) => new Set([...prev, currentStepIndex]))
        setCurrentStepIndex((prev) => Math.min(prev + 1, WIZARD_STEPS.length - 1))
        setError(null)
      },
      onError: (err) => setError(err.message),
    },
  )

  const validateMutation = useMutation<void, QualityPlanValidation>(
    async () => {
      if (!versionId) throw new Error('No version ID')
      const csrf = await getCsrfToken()
      return apiRequest<QualityPlanValidation>({
        path: `/logistics/quality-plan-versions/${versionId}/validate`,
        method: 'POST',
        headers: { 'X-CSRF-Token': csrf },
        body: {},
      })
    },
    {
      onSuccess: () => {
        setCompletedSteps((prev) => new Set([...prev, currentStepIndex]))
      },
      onError: (err) => setError(err.message),
    },
  )

  useEffect(() => {
    if (versionData) {
      setFormData({
        valid_from: versionData.valid_from ?? '',
        valid_until: versionData.valid_until ?? '',
        priority: versionData.priority,
      })
    }
  }, [versionData])

  useEffect(() => {
    if (!versionId) return
    const csrfTokenPromise = getCsrfToken()
    csrfTokenPromise.then((csrf) => {
      apiRequest<QualityInspectionPlanCapabilities>({
        path: `/logistics/quality-inspection-plans/${planId}/capabilities`,
        method: 'GET',
        headers: { 'X-CSRF-Token': csrf },
      }).then((caps) => setCapabilities(caps)).catch(() => {})
    }).catch(() => {})
  }, [versionId, planId])

  const handleNext = useCallback(() => {
    setError(null)
    if (currentStepIndex === 0 && !versionId) {
      createVersionMutation.mutate(formData)
      return
    }
    if (currentStepIndex <= 1) {
      updateVersionMutation.mutate(formData)
      return
    }
    setCompletedSteps((prev) => new Set([...prev, currentStepIndex]))
    setCurrentStepIndex((prev) => Math.min(prev + 1, WIZARD_STEPS.length - 1))
  }, [currentStepIndex, versionId, formData, createVersionMutation, updateVersionMutation])

  const handlePrevious = useCallback(() => {
    setError(null)
    setCurrentStepIndex((prev) => Math.max(prev - 1, 0))
  }, [])

  const handleSubmit = useCallback(() => {
    if (currentStep.key === 'validation') {
      validateMutation.mutate()
    } else {
      onComplete()
    }
  }, [currentStep.key, validateMutation, onComplete])

  const handleScopesRefresh = useCallback(() => { refetchScopes() }, [refetchScopes])
  const handleControlsRefresh = useCallback(() => { refetchControls() }, [refetchControls])

  const isCreatingVersion = createVersionMutation.isPending
  const isUpdatingVersion = updateVersionMutation.isPending
  const isSaving = isCreatingVersion || isUpdatingVersion
  const isFirstStep = currentStepIndex === 0
  const isLastStep = currentStepIndex === WIZARD_STEPS.length - 1
  const canGoNext = !isSaving && !isLastStep
  const canGoPrevious = !isSaving && !isFirstStep
  const canSubmit = !isSaving && isLastStep

  const renderStepContent = () => {
    switch (currentStep.key) {
      case 'info':
        return (
          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-bold text-slate-800">Informacion general</h3>
              <p className="text-xs text-slate-500">
                Configure los datos基本icos de la version del plan de inspeccion.
              </p>
            </div>
            {versionData && (
              <div className="rounded-xl border border-slate-200 bg-white p-4">
                <dl className="grid grid-cols-2 gap-2 text-xs">
                  <dt className="text-[10px] font-semibold uppercase text-slate-500">Version</dt>
                  <dd className="text-slate-800">v{versionData.version_number}</dd>
                  <dt className="text-[10px] font-semibold uppercase text-slate-500">Estado</dt>
                  <dd className="text-slate-800">{versionData.status}</dd>
                  <dt className="text-[10px] font-semibold uppercase text-slate-500">Creado por</dt>
                  <dd className="text-slate-800">{versionData.created_by.display_name}</dd>
                  <dt className="text-[10px] font-semibold uppercase text-slate-500">Creado</dt>
                  <dd className="text-slate-800">{formatDate(versionData.created_at)}</dd>
                </dl>
              </div>
            )}
            {!versionId && (
              <div className="rounded-xl border border-indigo-200 bg-indigo-50/30 p-4">
                <p className="text-xs text-indigo-700">
                  Se creara una nueva version del plan de inspeccion al continuar.
                </p>
              </div>
            )}
          </div>
        )

      case 'validity':
        return (
          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-bold text-slate-800">Vigencia y prioridad</h3>
              <p className="text-xs text-slate-500">
                Defina el rango de fechas y la prioridad de esta version.
              </p>
            </div>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <div>
                <label className="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                  Valido desde
                </label>
                <input
                  type="date"
                  value={formData.valid_from}
                  onChange={(e) => setFormData((p) => ({ ...p, valid_from: e.target.value }))}
                  className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-800 focus:border-[#1F4E6D] focus:outline-none focus:ring-1 focus:ring-[#1F4E6D]"
                />
              </div>
              <div>
                <label className="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                  Valido hasta
                </label>
                <input
                  type="date"
                  value={formData.valid_until}
                  onChange={(e) => setFormData((p) => ({ ...p, valid_until: e.target.value }))}
                  className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-800 focus:border-[#1F4E6D] focus:outline-none focus:ring-1 focus:ring-[#1F4E6D]"
                />
              </div>
              <div>
                <label className="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                  Prioridad
                </label>
                <input
                  type="number"
                  min={0}
                  max={100}
                  value={formData.priority}
                  onChange={(e) => setFormData((p) => ({ ...p, priority: Number(e.target.value) }))}
                  className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-800 focus:border-[#1F4E6D] focus:outline-none focus:ring-1 focus:ring-[#1F4E6D]"
                />
              </div>
            </div>
            {versionData && (
              <div className="rounded-xl border border-slate-200 bg-white p-4">
                <h4 className="mb-2 text-xs font-bold text-slate-700">Resumen de la version</h4>
                <dl className="grid grid-cols-3 gap-2 text-[11px]">
                  <dt className="text-slate-500">Ambitos:</dt>
                  <dd className="text-slate-800">{versionData.scope_count}</dd>
                  <dt className="text-slate-500">Controles:</dt>
                  <dd className="text-slate-800">{versionData.control_count}</dd>
                  <dt className="text-slate-500">Tolerancias:</dt>
                  <dd className="text-slate-800">{versionData.tolerance_count}</dd>
                  <dt className="text-slate-500">Muestreo:</dt>
                  <dd className="text-slate-800">{versionData.sampling_count}</dd>
                  <dt className="text-slate-500">Certificados:</dt>
                  <dd className="text-slate-800">{versionData.certificate_count}</dd>
                  <dt className="text-slate-500">Conflictos:</dt>
                  <dd className="text-slate-800">{versionData.conflict_count}</dd>
                </dl>
              </div>
            )}
          </div>
        )

      case 'scopes':
        if (!versionId) return <ErrorPanel message="Primero debe crear la version." onRetry={() => {}} />
        if (scopesLoading) return <SkeletonRows rows={4} />
        return (
          <QualityPlanScopesEditor
            versionId={versionId}
            scopes={scopesData ?? []}
            capabilities={capabilities ?? {
              plan_id: planId,
              can_view: true,
              can_create: true,
              can_update: true,
              can_clone: true,
              can_archive: true,
              can_create_version: true,
              can_manage_scopes: true,
              can_manage_controls: true,
              can_manage_tolerances: true,
              can_manage_sampling: true,
              can_manage_certificates: true,
              can_validate: true,
              can_detect_conflicts: true,
              can_activate: true,
              can_retire: true,
              can_preview: true,
              can_resolve: true,
              can_view_history: true,
              can_view_integrity: true,
              can_view_future_inspection_template: true,
            }}
            onRefresh={handleScopesRefresh}
          />
        )

      case 'controls':
        if (!versionId) return <ErrorPanel message="Primero debe crear la version." onRetry={() => {}} />
        if (controlsLoading) return <SkeletonRows rows={4} />
        return (
          <QualityControlsEditor
            versionId={versionId}
            controls={controlsData ?? []}
            capabilities={capabilities ?? {
              plan_id: planId,
              can_view: true,
              can_create: true,
              can_update: true,
              can_clone: true,
              can_archive: true,
              can_create_version: true,
              can_manage_scopes: true,
              can_manage_controls: true,
              can_manage_tolerances: true,
              can_manage_sampling: true,
              can_manage_certificates: true,
              can_validate: true,
              can_detect_conflicts: true,
              can_activate: true,
              can_retire: true,
              can_preview: true,
              can_resolve: true,
              can_view_history: true,
              can_view_integrity: true,
              can_view_future_inspection_template: true,
            }}
            onRefresh={handleControlsRefresh}
          />
        )

      case 'tolerances':
        if (tolerancesLoading) return <SkeletonRows rows={4} />
        const tolerances = tolerancesData?.items ?? []
        return (
          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-bold text-slate-800">Tolerancias</h3>
              <p className="text-xs text-slate-500">
                Gestione las tolerancias disponibles para asociar a los controles de este plan.
              </p>
            </div>
            {tolerances.length === 0 ? (
              <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-6 text-center">
                <p className="text-xs text-slate-500">No hay tolerancias disponibles.</p>
                <p className="mt-1 text-[10px] text-slate-400">Cree tolerancias desde el modulo de Tolerancias.</p>
              </div>
            ) : (
              <div className="space-y-2">
                {tolerances.map((tol) => (
                  <div
                    key={tol.tolerance_id}
                    className="flex items-center gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3"
                  >
                    <span className="inline-flex items-center rounded-full border border-slate-200 bg-slate-50 px-2 py-0.5 text-[10px] font-semibold text-slate-600">
                      {tol.tolerance_type}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold text-slate-800">{tol.code}</span>
                        <span className="text-xs text-slate-600 truncate">{tol.name}</span>
                      </div>
                      <p className="text-[10px] text-slate-400">
                        {tol.dimension} — {tol.target_value}
                        {tol.min_value != null && ` | Min: ${tol.min_value}`}
                        {tol.max_value != null && ` | Max: ${tol.max_value}`}
                      </p>
                    </div>
                    <span
                      className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                        tol.status === 'ACTIVE'
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : 'bg-slate-100 text-slate-500'
                      }`}
                    >
                      {tol.status === 'ACTIVE' ? 'Activa' : 'Retirada'}
                    </span>
                  </div>
                ))}
              </div>
            )}
            <p className="text-[10px] text-slate-400">
              Para asociar una tolerancia a un control, edite el control en el paso "Controles" y seleccione la tolerancia.
            </p>
          </div>
        )

      case 'sampling':
        if (samplingLoading) return <SkeletonRows rows={4} />
        const samplingPlans = samplingData?.items ?? []
        return (
          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-bold text-slate-800">Planes de muestreo</h3>
              <p className="text-xs text-slate-500">
                Gestione los planes de muestreo disponibles para asociar a los controles.
              </p>
            </div>
            {samplingPlans.length === 0 ? (
              <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-6 text-center">
                <p className="text-xs text-slate-500">No hay planes de muestreo disponibles.</p>
                <p className="mt-1 text-[10px] text-slate-400">Cree planes desde el modulo de Muestreo.</p>
              </div>
            ) : (
              <div className="space-y-2">
                {samplingPlans.map((plan) => (
                  <div
                    key={plan.sampling_id}
                    className="flex items-center gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3"
                  >
                    <span className="inline-flex items-center rounded-full border border-slate-200 bg-slate-50 px-2 py-0.5 text-[10px] font-semibold text-slate-600">
                      {plan.sampling_type}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold text-slate-800">{plan.code}</span>
                        <span className="text-xs text-slate-600 truncate">{plan.name}</span>
                      </div>
                      <p className="text-[10px] text-slate-400">
                        Unidad: {plan.sample_unit}
                        {plan.fixed_quantity != null && ` | Cantidad: ${plan.fixed_quantity}`}
                        {plan.percentage != null && ` | Porcentaje: ${plan.percentage}%`}
                        {plan.minimum != null && ` | Min: ${plan.minimum}`}
                        {plan.maximum != null && ` | Max: ${plan.maximum}`}
                      </p>
                    </div>
                    <span
                      className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                        plan.status === 'ACTIVE'
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : 'bg-slate-100 text-slate-500'
                      }`}
                    >
                      {plan.status === 'ACTIVE' ? 'Activo' : 'Retirado'}
                    </span>
                  </div>
                ))}
              </div>
            )}
            <p className="text-[10px] text-slate-400">
              Para asociar un plan de muestreo a un control, edite el control en el paso "Controles".
            </p>
          </div>
        )

      case 'certificates':
        if (certificatesLoading) return <SkeletonRows rows={4} />
        const certificates = certificatesData?.items ?? []
        return (
          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-bold text-slate-800">Requisitos de certificados</h3>
              <p className="text-xs text-slate-500">
                Gestione los requisitos de certificados disponibles para asociar a los controles.
              </p>
            </div>
            {certificates.length === 0 ? (
              <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-6 text-center">
                <p className="text-xs text-slate-500">No hay requisitos de certificados disponibles.</p>
                <p className="mt-1 text-[10px] text-slate-400">Cree requisitos desde el modulo de Certificados.</p>
              </div>
            ) : (
              <div className="space-y-2">
                {certificates.map((cert) => (
                  <div
                    key={cert.requirement_id}
                    className="flex items-center gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold text-slate-800">{cert.code}</span>
                        <span className="text-xs text-slate-600 truncate">{cert.name}</span>
                        {cert.required && (
                          <span className="inline-flex items-center rounded-full border border-rose-200 bg-rose-50 px-2 py-0.5 text-[10px] font-semibold text-rose-700">
                            Requerido
                          </span>
                        )}
                      </div>
                      <p className="text-[10px] text-slate-400">
                        {cert.document_type_name ?? 'Sin tipo'}
                        {cert.issuer_pattern && ` | Emisor: ${cert.issuer_pattern}`}
                        {cert.minimum_validity_days != null && ` | Validez min: ${cert.minimum_validity_days} dias`}
                      </p>
                    </div>
                    <span
                      className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                        cert.status === 'ACTIVE'
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : 'bg-slate-100 text-slate-500'
                      }`}
                    >
                      {cert.status === 'ACTIVE' ? 'Activo' : 'Inactivo'}
                    </span>
                  </div>
                ))}
              </div>
            )}
            <p className="text-[10px] text-slate-400">
              Para asociar un certificado a un control, edite el control en el paso "Controles".
            </p>
          </div>
        )

      case 'conditions':
        if (controlsLoading) return <SkeletonRows rows={4} />
        return (
          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-bold text-slate-800">Condiciones de controles</h3>
              <p className="text-xs text-slate-500">
                Revise las condiciones configuradas en los controles de esta version.
              </p>
            </div>
            {(controlsData ?? []).length === 0 ? (
              <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-6 text-center">
                <p className="text-xs text-slate-500">No hay controles configurados.</p>
                <p className="mt-1 text-[10px] text-slate-400">Agregue controles en el paso "Controles".</p>
              </div>
            ) : (
              <div className="space-y-3">
                {(controlsData ?? []).map((ctrl) => (
                  <div
                    key={ctrl.control_id}
                    className="rounded-xl border border-slate-200 bg-white p-4"
                  >
                    <div className="mb-2 flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-slate-800">{ctrl.code}</span>
                      <span className="text-xs text-slate-600">{ctrl.name}</span>
                      <span className="inline-flex items-center rounded-full border border-slate-200 bg-slate-50 px-2 py-0.5 text-[10px] font-semibold text-slate-600">
                        {ctrl.control_type}
                      </span>
                    </div>
                    {ctrl.conditions.length === 0 ? (
                      <p className="text-[10px] text-slate-400">Sin condiciones configuradas.</p>
                    ) : (
                      <div className="space-y-1">
                        {ctrl.conditions.map((cond) => (
                          <div
                            key={cond.condition_id}
                            className="flex items-center gap-2 rounded-lg bg-slate-50 px-2 py-1 text-[10px] text-slate-600"
                          >
                            <span className="font-mono">{cond.condition_field}</span>
                            <span className="text-slate-400">{cond.operator}</span>
                            <span className="font-mono">{cond.value ?? '—'}</span>
                            <span className="text-slate-300">#{cond.display_order}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )

      case 'future':
        if (controlsLoading) return <SkeletonRows rows={4} />
        const evidenceTypes = new Set<string>()
        const futureRoles = new Set<string>()
        for (const ctrl of controlsData ?? []) {
          for (const ev of ctrl.evidence_types) evidenceTypes.add(ev)
          for (const fr of ctrl.future_responsibilities) futureRoles.add(fr)
        }
        return (
          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-bold text-slate-800">Evidencias futuras</h3>
              <p className="text-xs text-slate-500">
                Resumen de tipos de evidencia y responsabilidades futuras configuradas en los controles.
              </p>
            </div>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="rounded-xl border border-slate-200 bg-white p-4">
                <h4 className="mb-2 text-xs font-bold text-slate-700">Tipos de evidencia</h4>
                {evidenceTypes.size === 0 ? (
                  <p className="text-[10px] text-slate-400">No hay tipos de evidencia configurados.</p>
                ) : (
                  <div className="flex flex-wrap gap-1">
                    {[...evidenceTypes].map((ev) => (
                      <span
                        key={ev}
                        className="inline-flex items-center rounded-full border border-indigo-200 bg-indigo-50 px-2 py-0.5 text-[10px] text-indigo-700"
                      >
                        {ev}
                      </span>
                    ))}
                  </div>
                )}
              </div>
              <div className="rounded-xl border border-slate-200 bg-white p-4">
                <h4 className="mb-2 text-xs font-bold text-slate-700">Roles futuros</h4>
                {futureRoles.size === 0 ? (
                  <p className="text-[10px] text-slate-400">No hay roles futuros configurados.</p>
                ) : (
                  <div className="flex flex-wrap gap-1">
                    {[...futureRoles].map((role) => (
                      <span
                        key={role}
                        className="inline-flex items-center rounded-full border border-amber-200 bg-amber-50 px-2 py-0.5 text-[10px] text-amber-700"
                      >
                        {role}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
            <p className="text-[10px] text-slate-400">
              Los tipos de evidencia y roles futuros se definen al configurar cada control individual en el paso "Controles".
            </p>
          </div>
        )

      case 'review':
        if (versionLoading) return <SkeletonRows rows={4} />
        return (
          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-bold text-slate-800">Revision de la version</h3>
              <p className="text-xs text-slate-500">
                Revise toda la configuracion antes de validar.
              </p>
            </div>
            {versionData && (
              <div className="rounded-xl border border-slate-200 bg-white p-4">
                <h4 className="mb-3 text-xs font-bold text-slate-700">Datos de la version</h4>
                <dl className="grid grid-cols-2 gap-2 text-xs sm:grid-cols-3">
                  <dt className="text-[10px] font-semibold uppercase text-slate-500">Version</dt>
                  <dd className="text-slate-800">v{versionData.version_number}</dd>
                  <dt className="text-[10px] font-semibold uppercase text-slate-500">Estado</dt>
                  <dd className="text-slate-800">{versionData.status}</dd>
                  <dt className="text-[10px] font-semibold uppercase text-slate-500">Vigente desde</dt>
                  <dd className="text-slate-800">{formatDate(versionData.valid_from)}</dd>
                  <dt className="text-[10px] font-semibold uppercase text-slate-500">Vigente hasta</dt>
                  <dd className="text-slate-800">{formatDate(versionData.valid_until)}</dd>
                  <dt className="text-[10px] font-semibold uppercase text-slate-500">Prioridad</dt>
                  <dd className="text-slate-800">{versionData.priority}</dd>
                </dl>
              </div>
            )}
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
              <div className="rounded-xl border border-slate-200 bg-white p-4 text-center">
                <p className="text-2xl font-bold text-slate-800">{versionData?.scope_count ?? 0}</p>
                <p className="text-[10px] font-semibold uppercase text-slate-500">Ambitos</p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-white p-4 text-center">
                <p className="text-2xl font-bold text-slate-800">{versionData?.control_count ?? 0}</p>
                <p className="text-[10px] font-semibold uppercase text-slate-500">Controles</p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-white p-4 text-center">
                <p className="text-2xl font-bold text-slate-800">{versionData?.tolerance_count ?? 0}</p>
                <p className="text-[10px] font-semibold uppercase text-slate-500">Tolerancias</p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-white p-4 text-center">
                <p className="text-2xl font-bold text-slate-800">{versionData?.sampling_count ?? 0}</p>
                <p className="text-[10px] font-semibold uppercase text-slate-500">Muestreo</p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-white p-4 text-center">
                <p className="text-2xl font-bold text-slate-800">{versionData?.certificate_count ?? 0}</p>
                <p className="text-[10px] font-semibold uppercase text-slate-500">Certificados</p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-white p-4 text-center">
                <p className="text-2xl font-bold text-slate-800">{versionData?.conflict_count ?? 0}</p>
                <p className="text-[10px] font-semibold uppercase text-slate-500">Conflictos</p>
              </div>
            </div>
          </div>
        )

      case 'validation':
        if (validationLoading) return <SkeletonRows rows={4} />
        return (
          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-bold text-slate-800">Validacion</h3>
              <p className="text-xs text-slate-500">
                Valide la version para verificar que cumple con todos los requisitos.
              </p>
            </div>
            <QualityPlanValidationPanel
              validation={validationData ?? null}
              onValidate={() => validateMutation.mutate()}
            />
            {validationData && validationData.status === 'VALID' && (
              <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4">
                <p className="text-xs font-bold text-emerald-700">
                  La version esta lista para ser activada.
                </p>
                <p className="mt-1 text-[10px] text-emerald-600">
                  Puede proceder a activar la version desde el panel de versiones.
                </p>
              </div>
            )}
          </div>
        )

      default:
        return null
    }
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-slate-900">Wizard de version del plan</h1>
          <p className="text-xs text-slate-500">
            Configure paso a paso la version del plan de inspeccion de calidad.
          </p>
        </div>
        <Button variant="ghost" size="small" onClick={onCancel}>
          Cancelar
        </Button>
      </div>

      <nav aria-label="Progress">
        <ol className="flex items-center gap-1">
          {WIZARD_STEPS.map((step, index) => {
            const isCompleted = completedSteps.has(index)
            const isCurrent = index === currentStepIndex
            return (
              <li key={step.key} className="flex items-center">
                <button
                  type="button"
                  onClick={() => {
                    if (index <= currentStepIndex || isCompleted) {
                      setCurrentStepIndex(index)
                    }
                  }}
                  disabled={index > currentStepIndex && !isCompleted}
                  className={`flex items-center gap-1.5 rounded-full px-3 py-1.5 text-[10px] font-semibold transition-colors ${
                    isCurrent
                      ? 'bg-[#1F4E6D] text-white'
                      : isCompleted
                        ? 'bg-emerald-100 text-emerald-700 hover:bg-emerald-200'
                        : 'bg-slate-100 text-slate-400 hover:bg-slate-200'
                  } disabled:cursor-not-allowed disabled:opacity-50`}
                >
                  {isCompleted && !isCurrent ? (
                    <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                    </svg>
                  ) : (
                    <span className="flex h-4 w-4 items-center justify-center rounded-full bg-current/10 text-[9px]">
                      {index + 1}
                    </span>
                  )}
                  <span className="hidden sm:inline">{step.label}</span>
                </button>
                {index < WIZARD_STEPS.length - 1 && (
                  <div className={`mx-0.5 h-px w-2 ${isCompleted ? 'bg-emerald-300' : 'bg-slate-200'}`} />
                )}
              </li>
            )
          })}
        </ol>
      </nav>

      {error && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-xs text-rose-700">
          {error}
        </div>
      )}

      <div className="min-h-[400px] rounded-xl border border-slate-200 bg-white p-6">
        {renderStepContent()}
      </div>

      <div className="flex items-center justify-between">
        <div>
          {isFirstStep ? (
            <Button variant="ghost" size="small" onClick={onCancel}>
              Cancelar
            </Button>
          ) : (
            <Button
              variant="ghost"
              size="small"
              onClick={handlePrevious}
              disabled={!canGoPrevious}
            >
              Anterior
            </Button>
          )}
        </div>
        <div className="text-[10px] text-slate-400">
          Paso {currentStepIndex + 1} de {WIZARD_STEPS.length}
        </div>
        <div>
          {isLastStep ? (
            <Button
              variant="primary"
              size="small"
              onClick={handleSubmit}
              disabled={!canSubmit}
              isLoading={validateMutation.isPending}
            >
              {validationData?.status === 'VALID' ? 'Finalizar' : 'Validar'}
            </Button>
          ) : (
            <Button
              variant="primary"
              size="small"
              onClick={handleNext}
              disabled={!canGoNext}
              isLoading={isSaving}
            >
              {isFirstStep && !versionId ? 'Crear version' : 'Siguiente'}
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}
