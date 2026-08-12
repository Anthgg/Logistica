import { useQuery } from '../../inbound-docks/hooks/useQuery'
import { Button } from '../../../components/common/Button'
import type {
  QualityPlanPreview,
  QualityControlDefinition,
} from '../types/quality-inspection-plans'

interface ReceptionDifferenceQualityPlanPreviewPanelProps {
  caseId: string
}

interface DifferencePreviewData {
  difference_id: string
  difference_type: string
  severity: string
  product: {
    product_id: string
    name: string
    sku: string
    category?: string
  }
  damage_description: string | null
  temperature_recorded: string | null
  temperature_unit: string | null
  expiration_date: string | null
  certificates_present: boolean
  certificate_types: string[]
  applicable_plan: QualityPlanPreview | null
  future_controls: QualityControlDefinition[]
}

const SEVERITY_COLORS: Record<string, string> = {
  LOW: 'bg-slate-100 text-slate-700',
  MEDIUM: 'bg-amber-100 text-amber-700',
  HIGH: 'bg-orange-100 text-orange-700',
  CRITICAL: 'bg-rose-100 text-rose-700',
}

const DIFFERENCE_TYPE_LABELS: Record<string, string> = {
  SHORTAGE: 'Faltante',
  OVERAGE: 'Sobrante',
  DAMAGE: 'Daño',
  WRONG_PRODUCT: 'Producto equivocado',
  MISSING_DOCUMENT: 'Documento faltante',
  BROKEN_SEAL: 'Precinto roto',
  QUALITY_ISSUE: 'Problema de calidad',
  OTHER: 'Otro',
}

export function ReceptionDifferenceQualityPlanPreviewPanel({ caseId }: ReceptionDifferenceQualityPlanPreviewPanelProps) {
  const query = useQuery<DifferencePreviewData>(
    ['quality-plan-preview-difference', caseId],
    `/logistics/reception-difference-cases/${caseId}/quality-preview`,
    undefined,
    { enabled: !!caseId },
  )

  const data = query.data
  const isLoading = query.isLoading
  const isError = query.isError

  if (isLoading) {
    return (
      <div className="space-y-3">
        <h3 className="text-sm font-bold text-slate-800">Vista previa del plan de calidad</h3>
        <p className="text-xs text-slate-400">Cargando información…</p>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="space-y-3">
        <h3 className="text-sm font-bold text-slate-800">Vista previa del plan de calidad</h3>
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800">
          {query.error || 'Error al cargar la vista previa del plan.'}
        </div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="space-y-3">
        <h3 className="text-sm font-bold text-slate-800">Vista previa del plan de calidad</h3>
        <p className="text-xs text-slate-400">No hay información disponible para esta diferencia.</p>
      </div>
    )
  }

  const plan = data.applicable_plan

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold text-slate-800">Vista previa del plan de calidad</h3>
        {data.severity && (
          <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${SEVERITY_COLORS[data.severity]}`}>
            {data.severity}
          </span>
        )}
      </div>

      <div className="rounded-lg border border-purple-200 bg-purple-50 p-3 text-xs text-purple-800" role="status">
        Esta vista indica qué controles corresponderían. No crea una inspección de calidad.
      </div>

      <div className="rounded-lg border border-slate-200 p-3 text-xs">
        <p className="text-[10px] font-semibold uppercase text-slate-400 mb-2">Diferencia</p>
        <div className="grid grid-cols-2 gap-3">
          <InfoCell label="Tipo" value={DIFFERENCE_TYPE_LABELS[data.difference_type] ?? data.difference_type} />
          <InfoCell label="Severidad" value={data.severity} />
        </div>
      </div>

      <div className="rounded-lg border border-slate-200 p-3 text-xs">
        <p className="text-[10px] font-semibold uppercase text-slate-400 mb-2">Producto</p>
        <div className="grid grid-cols-2 gap-3">
          <InfoCell label="Nombre" value={data.product.name} />
          <InfoCell label="SKU" value={data.product.sku} />
          {data.product.category && (
            <InfoCell label="Categoría" value={data.product.category} />
          )}
        </div>
      </div>

      {(data.damage_description || data.temperature_recorded || data.expiration_date || data.certificates_present) && (
        <div className="rounded-lg border border-slate-200 p-3 text-xs">
          <p className="text-[10px] font-semibold uppercase text-slate-400 mb-2">Condiciones reportadas</p>
          <div className="grid grid-cols-2 gap-3">
            {data.damage_description && (
              <InfoCell label="Daño" value={data.damage_description} />
            )}
            {data.temperature_recorded && (
              <InfoCell
                label="Temperatura"
                value={`${data.temperature_recorded}${data.temperature_unit ? ` ${data.temperature_unit}` : ''}`}
              />
            )}
            {data.expiration_date && (
              <InfoCell label="Vencimiento" value={formatDate(data.expiration_date)} />
            )}
            <InfoCell
              label="Certificados"
              value={data.certificates_present ? `${data.certificate_types.length} presentes` : 'No presentes'}
            />
          </div>
        </div>
      )}

      {plan ? (
        <div className="space-y-2">
          <p className="text-[10px] font-semibold uppercase text-slate-400">Plan aplicable</p>
          <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-xs">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-emerald-800">
                {plan.plan_code} v{plan.version_number}
              </span>
              <span className="text-[10px] text-emerald-600">
                Especificidad: {plan.specificity}
              </span>
            </div>
            <p className="text-emerald-700">{plan.plan_name}</p>

            {plan.controls.length > 0 && (
              <div className="mt-2 space-y-1">
                <p className="text-[10px] font-semibold text-emerald-600">Controles ({plan.controls.length})</p>
                {plan.controls.map((ctrl) => (
                  <div key={ctrl.control_id} className="flex items-center gap-2 text-emerald-700">
                    <span className="font-mono text-[10px]">{ctrl.code}</span>
                    <span>{ctrl.name}</span>
                    {ctrl.required && (
                      <span className="rounded bg-emerald-200 px-1 py-0.5 text-[10px] font-bold text-emerald-800">
                        Requerido
                      </span>
                    )}
                  </div>
                ))}
              </div>
            )}

            {plan.certificates.length > 0 && (
              <div className="mt-2 space-y-1">
                <p className="text-[10px] font-semibold text-emerald-600">
                  Certificados ({plan.certificates.length})
                </p>
                {plan.certificates.map((cert) => (
                  <div key={cert.requirement_id} className="text-emerald-700">
                    <span className="font-mono text-[10px]">{cert.code}</span> {cert.name}
                  </div>
                ))}
              </div>
            )}

            {plan.sampling && (
              <div className="mt-2">
                <p className="text-[10px] font-semibold text-emerald-600">Muestreo</p>
                <p className="text-emerald-700">{plan.sampling.name} ({plan.sampling.sampling_type})</p>
              </div>
            )}

            {plan.warnings.length > 0 && (
              <div className="mt-2 space-y-1">
                {plan.warnings.map((w, i) => (
                  <div key={i} className="rounded bg-amber-100 p-1.5 text-[10px] text-amber-800">
                    {w}
                  </div>
                ))}
              </div>
            )}

            {plan.explanation && (
              <p className="mt-2 text-[10px] text-emerald-600 italic">{plan.explanation}</p>
            )}
          </div>
        </div>
      ) : (
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs text-slate-500">
          No se encontró un plan de inspección aplicable para esta diferencia.
        </div>
      )}

      {data.future_controls.length > 0 && (
        <div className="space-y-2">
          <p className="text-[10px] font-semibold uppercase text-slate-400">
            Controles futuros ({data.future_controls.length})
          </p>
          {data.future_controls.map((ctrl) => (
            <div
              key={ctrl.control_id}
              className="rounded-lg border border-blue-200 bg-blue-50 p-2 text-xs"
            >
              <div className="flex items-center justify-between">
                <span className="font-semibold text-blue-800">{ctrl.name}</span>
                <span className="text-[10px] text-blue-500">{ctrl.control_type}</span>
              </div>
              {ctrl.description && (
                <p className="text-blue-600">{ctrl.description}</p>
              )}
              {ctrl.future_responsibilities.length > 0 && (
                <p className="text-[10px] text-blue-500 mt-1">
                  Responsabilidades: {ctrl.future_responsibilities.join(', ')}
                </p>
              )}
            </div>
          ))}
        </div>
      )}

      <div className="flex flex-wrap gap-2 pt-1">
        <Button variant="secondary" size="small">
          Ver plan completo
        </Button>
        <Button variant="secondary" size="small">
          Comparar con otros planes
        </Button>
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
