import { useQuery } from '../../inbound-docks/hooks/useQuery'
import { Button } from '../../../components/common/Button'
import type {
  QualityPlanResolution,
  QualityPlanPreview,
} from '../types/quality-inspection-plans'

interface QualityPlanApplicabilityPanelProps {
  productId: string
}

export function QualityPlanApplicabilityPanel({ productId }: QualityPlanApplicabilityPanelProps) {
  const resolutionQuery = useQuery<QualityPlanResolution>(
    ['quality-plan-resolution', productId],
    `/logistics/quality-inspection-plans/resolve`,
    { product_id: productId },
    { enabled: !!productId },
  )

  const previewQuery = useQuery<QualityPlanPreview>(
    ['quality-plan-preview', productId],
    `/logistics/quality-inspection-plans/preview`,
    { product_id: productId },
    { enabled: !!productId },
  )

  const resolution = resolutionQuery.data
  const preview = previewQuery.data
  const isLoading = resolutionQuery.isLoading || previewQuery.isLoading
  const isError = resolutionQuery.isError || previewQuery.isError

  if (isLoading) {
    return (
      <div className="space-y-3">
        <h3 className="text-sm font-bold text-slate-800">Plan aplicable</h3>
        <p className="text-xs text-slate-400">Cargando información del plan…</p>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="space-y-3">
        <h3 className="text-sm font-bold text-slate-800">Plan aplicable</h3>
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800">
          {resolutionQuery.error || previewQuery.error || 'Error al cargar la información del plan.'}
        </div>
      </div>
    )
  }

  if (!resolution && !preview) {
    return (
      <div className="space-y-3">
        <h3 className="text-sm font-bold text-slate-800">Plan aplicable</h3>
        <p className="text-xs text-slate-400">No se encontró un plan de inspección aplicable para este producto.</p>
      </div>
    )
  }

  const planCode = preview?.plan_code ?? resolution?.resolved_plan_code ?? '—'
  const versionNumber = preview?.version_number ?? resolution?.resolved_version_number ?? null
  const validityFrom = preview?.scope?.valid_from ?? resolution?.valid_from ?? null
  const validityUntil = preview?.scope?.valid_until ?? resolution?.valid_until ?? null
  const specificity = preview?.specificity ?? resolution?.specificity ?? null
  const conflicts = preview?.conflicts ?? resolution?.conflicts ?? []
  const controls = preview?.controls ?? resolution?.controls ?? []
  const certificates = preview?.certificates ?? resolution?.certificates ?? []
  const sampling = preview?.sampling ?? resolution?.sampling ?? null
  const warnings = preview?.warnings ?? resolution?.warnings ?? []
  const explanation = preview?.explanation ?? resolution?.explanation ?? null

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-bold text-slate-800">Plan aplicable</h3>

      <div className="rounded-lg border border-slate-200 p-3 text-xs">
        <div className="grid grid-cols-2 gap-3">
          <InfoCell label="Código del plan" value={planCode} />
          <InfoCell label="Versión" value={versionNumber !== null ? `v${versionNumber}` : '—'} />
          <InfoCell label="Validez desde" value={formatDate(validityFrom)} />
          <InfoCell label="Validez hasta" value={formatDate(validityUntil)} />
          <InfoCell label="Especificidad" value={specificity !== null ? String(specificity) : '—'} />
          <InfoCell label="Controles" value={String(controls.length)} />
          <InfoCell label="Certificados" value={String(certificates.length)} />
          <InfoCell label="Muestreo" value={sampling ? sampling.name : 'No'} />
        </div>
      </div>

      {conflicts.length > 0 && (
        <div className="space-y-2">
          <p className="text-[10px] font-semibold uppercase text-slate-400">Conflictos ({conflicts.length})</p>
          {conflicts.map((c) => (
            <div
              key={c.conflict_id}
              className="rounded-lg border border-amber-200 bg-amber-50 p-2 text-xs text-amber-800"
            >
              <p className="font-semibold">{c.conflict_type.replace(/_/g, ' ')}</p>
              <p className="text-amber-700">{c.rule_description}</p>
            </div>
          ))}
        </div>
      )}

      {warnings.length > 0 && (
        <div className="space-y-2">
          <p className="text-[10px] font-semibold uppercase text-slate-400">Advertencias</p>
          {warnings.map((w, i) => (
            <div key={i} className="rounded-lg border border-blue-200 bg-blue-50 p-2 text-xs text-blue-800">
              {w}
            </div>
          ))}
        </div>
      )}

      {explanation && (
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600">
          <p className="text-[10px] font-semibold uppercase text-slate-400 mb-1">Explicación de selección</p>
          <p>{explanation}</p>
        </div>
      )}

      <div className="flex flex-wrap gap-2 pt-1">
        {resolution?.resolved_plan_id && (
          <Button
            variant="secondary"
            size="small"
            onClick={() => {
              window.location.href = `/quality-inspection-plans/${resolution.resolved_plan_id}`
            }}
          >
            Abrir plan
          </Button>
        )}
        <Button
          variant="secondary"
          size="small"
          onClick={() => previewQuery.refetch()}
        >
          Ejecutar preview
        </Button>
        <Button variant="secondary" size="small">
          Ver planes alternativos
        </Button>
        {explanation && (
          <Button variant="ghost" size="small">
            Explicar selección
          </Button>
        )}
      </div>
    </div>
  )
}

function InfoCell({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[10px] font-semibold uppercase text-slate-400">{label}</p>
      <p className="text-slate-800">{value}</p>
    </div>
  )
}

function formatDate(date: string | null): string {
  if (!date) return '—'
  try {
    return new Date(date).toLocaleDateString('es-CL')
  } catch {
    return date
  }
}
