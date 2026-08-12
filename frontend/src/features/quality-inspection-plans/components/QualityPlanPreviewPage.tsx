import { useState } from 'react'
import { useMutation } from '../../../features/inbound-docks/hooks/useQuery'
import { qualityPlanAnalyticsApi } from '../api/qualityPlanResolutionApi'
import type { QualityPlanPreviewRequest, QualityPlanPreview } from '../types/quality-inspection-plans'
import { Button } from '../../../components/common/Button'

interface QualityPlanPreviewPageProps {
  planId: string
}

const EMPTY_CONTEXT: QualityPlanPreviewRequest = {
  product_id: '',
  category_id: '',
  branch_id: '',
  warehouse_id: '',
  date: '',
  quantity: '',
  unit_id: '',
  context: '',
  declared_conditions: {},
}

export function QualityPlanPreviewPage({ planId }: QualityPlanPreviewPageProps) {
  const [form, setForm] = useState<QualityPlanPreviewRequest>(EMPTY_CONTEXT)
  const [conditionKey, setConditionKey] = useState('')
  const [conditionValue, setConditionValue] = useState('')

  const [previewData, setPreviewData] = useState<QualityPlanPreview | null>(null)

  const previewMutation = useMutation<QualityPlanPreviewRequest, QualityPlanPreview>(
    async (data) => {
      const cleaned: QualityPlanPreviewRequest = {}
      if (data.product_id) cleaned.product_id = data.product_id
      if (data.category_id) cleaned.category_id = data.category_id
      if (data.branch_id) cleaned.branch_id = data.branch_id
      if (data.warehouse_id) cleaned.warehouse_id = data.warehouse_id
      if (data.date) cleaned.date = data.date
      if (data.quantity) cleaned.quantity = data.quantity
      if (data.unit_id) cleaned.unit_id = data.unit_id
      if (data.context) cleaned.context = data.context
      if (data.declared_conditions && Object.keys(data.declared_conditions).length > 0) {
        cleaned.declared_conditions = data.declared_conditions
      }
      return qualityPlanAnalyticsApi.preview(planId, cleaned)
    },
    {
      onSuccess: (result) => setPreviewData(result),
    }
  )

  const updateField = (field: keyof QualityPlanPreviewRequest, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  const addCondition = () => {
    if (!conditionKey) return
    setForm((prev) => ({
      ...prev,
      declared_conditions: {
        ...(prev.declared_conditions ?? {}),
        [conditionKey]: conditionValue,
      },
    }))
    setConditionKey('')
    setConditionValue('')
  }

  const removeCondition = (key: string) => {
    setForm((prev) => {
      const next = { ...(prev.declared_conditions ?? {}) }
      delete next[key]
      return { ...prev, declared_conditions: next }
    })
  }

  const preview = previewData

  return (
    <div className="space-y-4 text-xs">
      <div className="rounded-xl border border-slate-200 bg-white p-4">
        <h2 className="text-sm font-bold text-slate-800">Vista previa del plan</h2>
        <p className="mt-1 text-amber-600 font-medium">
          Vista previa. No crea una inspección ni modifica inventario.
        </p>

        <div className="mt-3 grid grid-cols-2 gap-3 md:grid-cols-4">
          <label className="block">
            <span className="text-slate-500">Producto</span>
            <input
              type="text"
              value={form.product_id ?? ''}
              onChange={(e) => updateField('product_id', e.target.value)}
              className="mt-0.5 w-full rounded-lg border border-slate-300 p-1.5 text-[11px]"
              placeholder="product_id"
            />
          </label>
          <label className="block">
            <span className="text-slate-500">Categoría</span>
            <input
              type="text"
              value={form.category_id ?? ''}
              onChange={(e) => updateField('category_id', e.target.value)}
              className="mt-0.5 w-full rounded-lg border border-slate-300 p-1.5 text-[11px]"
              placeholder="category_id"
            />
          </label>
          <label className="block">
            <span className="text-slate-500">Sucursal</span>
            <input
              type="text"
              value={form.branch_id ?? ''}
              onChange={(e) => updateField('branch_id', e.target.value)}
              className="mt-0.5 w-full rounded-lg border border-slate-300 p-1.5 text-[11px]"
              placeholder="branch_id"
            />
          </label>
          <label className="block">
            <span className="text-slate-500">Almacén</span>
            <input
              type="text"
              value={form.warehouse_id ?? ''}
              onChange={(e) => updateField('warehouse_id', e.target.value)}
              className="mt-0.5 w-full rounded-lg border border-slate-300 p-1.5 text-[11px]"
              placeholder="warehouse_id"
            />
          </label>
          <label className="block">
            <span className="text-slate-500">Fecha</span>
            <input
              type="date"
              value={form.date ?? ''}
              onChange={(e) => updateField('date', e.target.value)}
              className="mt-0.5 w-full rounded-lg border border-slate-300 p-1.5 text-[11px]"
            />
          </label>
          <label className="block">
            <span className="text-slate-500">Cantidad</span>
            <input
              type="text"
              value={form.quantity ?? ''}
              onChange={(e) => updateField('quantity', e.target.value)}
              className="mt-0.5 w-full rounded-lg border border-slate-300 p-1.5 text-[11px]"
              placeholder="100.00"
            />
          </label>
          <label className="block">
            <span className="text-slate-500">Unidad</span>
            <input
              type="text"
              value={form.unit_id ?? ''}
              onChange={(e) => updateField('unit_id', e.target.value)}
              className="mt-0.5 w-full rounded-lg border border-slate-300 p-1.5 text-[11px]"
              placeholder="unit_id"
            />
          </label>
          <label className="block">
            <span className="text-slate-500">Contexto</span>
            <input
              type="text"
              value={form.context ?? ''}
              onChange={(e) => updateField('context', e.target.value)}
              className="mt-0.5 w-full rounded-lg border border-slate-300 p-1.5 text-[11px]"
              placeholder="contexto libre"
            />
          </label>
        </div>

        <div className="mt-3">
          <span className="text-slate-500">Condiciones declaradas</span>
          <div className="mt-1 flex gap-2">
            <input
              type="text"
              value={conditionKey}
              onChange={(e) => setConditionKey(e.target.value)}
              className="w-1/3 rounded-lg border border-slate-300 p-1.5 text-[11px]"
              placeholder="campo"
            />
            <input
              type="text"
              value={conditionValue}
              onChange={(e) => setConditionValue(e.target.value)}
              className="flex-1 rounded-lg border border-slate-300 p-1.5 text-[11px]"
              placeholder="valor"
            />
            <Button variant="secondary" size="small" onClick={addCondition}>
              Agregar
            </Button>
          </div>
          {form.declared_conditions && Object.keys(form.declared_conditions).length > 0 && (
            <ul className="mt-1 flex flex-wrap gap-1">
              {Object.entries(form.declared_conditions).map(([k, v]) => (
                <li key={k} className="inline-flex items-center gap-1 rounded bg-slate-100 px-1.5 py-0.5 text-[10px]">
                  <span className="font-mono text-slate-600">{k}={v}</span>
                  <button
                    type="button"
                    onClick={() => removeCondition(k)}
                    className="text-slate-400 hover:text-rose-500"
                  >
                    ×
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="mt-3">
          <Button
            variant="primary"
            size="small"
            isLoading={previewMutation.isPending}
            onClick={() => previewMutation.mutate(form)}
          >
            Generar vista previa
          </Button>
          {previewMutation.error && (
            <p className="mt-2 text-rose-500">{previewMutation.error}</p>
          )}
        </div>
      </div>

      {preview && (
        <>
          <div className="rounded-xl border border-slate-200 bg-white p-4">
            <h3 className="text-sm font-bold text-slate-800">Plan resuelto</h3>
            <dl className="mt-2 grid grid-cols-2 gap-1 text-[11px] md:grid-cols-4">
              <dt className="text-slate-500">Plan:</dt>
              <dd className="font-semibold text-slate-800">{preview.plan_code} — {preview.plan_name}</dd>
              <dt className="text-slate-500">Versión:</dt>
              <dd>{preview.version_number}</dd>
              <dt className="text-slate-500">Especificidad:</dt>
              <dd>{preview.specificity}</dd>
              {preview.scope && (
                <>
                  <dt className="text-slate-500">Ámbito:</dt>
                  <dd>{preview.scope.scope_type} — {preview.scope.action}</dd>
                </>
              )}
            </dl>
          </div>

          {preview.controls.length > 0 && (
            <div className="rounded-xl border border-slate-200 bg-white p-4">
              <h3 className="text-sm font-bold text-slate-800">Controles ({preview.controls.length})</h3>
              <ol className="mt-2 space-y-2">
                {preview.controls.map((ctrl: any) => (
                  <li key={ctrl.control_id} className="rounded-lg border border-slate-100 p-2.5">
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="mr-1 font-mono text-[10px] text-slate-400">{ctrl.display_order}.</span>
                        <span className="font-semibold text-slate-800">{ctrl.name}</span>
                        <span className="ml-1 text-slate-400">({ctrl.control_type})</span>
                        {ctrl.required && <span className="ml-1 text-rose-500">*</span>}
                        {ctrl.blocking_future && <span className="ml-1 text-amber-500">⚡</span>}
                      </div>
                      <span className="text-[10px] text-slate-400">{ctrl.result_value_type}</span>
                    </div>
                    {ctrl.description && <p className="mt-0.5 text-slate-500">{ctrl.description}</p>}
                    {ctrl.tolerance_name && (
                      <p className="mt-0.5 text-[10px] text-slate-500">
                        Tolerancia: <span className="font-medium text-slate-700">{ctrl.tolerance_name}</span>
                      </p>
                    )}
                    {ctrl.sampling_plan_name && (
                      <p className="mt-0.5 text-[10px] text-slate-500">
                        Muestreo: <span className="font-medium text-slate-700">{ctrl.sampling_plan_name}</span>
                      </p>
                    )}
                    {ctrl.certificate_requirement_name && (
                      <p className="mt-0.5 text-[10px] text-slate-500">
                        Certificado: <span className="font-medium text-slate-700">{ctrl.certificate_requirement_name}</span>
                      </p>
                    )}
                  </li>
                ))}
              </ol>
            </div>
          )}

          {preview.tolerances.length > 0 && (
            <div className="rounded-xl border border-slate-200 bg-white p-4">
              <h3 className="text-sm font-bold text-slate-800">Tolerancias ({preview.tolerances.length})</h3>
              <ul className="mt-2 space-y-1">
                {preview.tolerances.map((t: any) => (
                  <li key={t.tolerance_id} className="text-[11px] text-slate-600">
                    <span className="font-semibold">{t.name}</span> — {t.tolerance_type} ({t.dimension})
                    <span className="ml-1 text-slate-400">obj: {t.target_value}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {preview.sampling && (
            <div className="rounded-xl border border-slate-200 bg-white p-4">
              <h3 className="text-sm font-bold text-slate-800">Muestreo</h3>
              <dl className="mt-2 grid grid-cols-2 gap-1 text-[11px] md:grid-cols-4">
                <dt className="text-slate-500">Nombre:</dt>
                <dd className="font-semibold text-slate-800">{preview.sampling.name}</dd>
                <dt className="text-slate-500">Tipo:</dt>
                <dd>{preview.sampling.sampling_type}</dd>
                <dt className="text-slate-500">Unidad:</dt>
                <dd>{preview.sampling.sample_unit}</dd>
                {preview.sampling.fixed_quantity && (
                  <>
                    <dt className="text-slate-500">Cantidad fija:</dt>
                    <dd>{preview.sampling.fixed_quantity}</dd>
                  </>
                )}
                {preview.sampling.percentage && (
                  <>
                    <dt className="text-slate-500">Porcentaje:</dt>
                    <dd>{preview.sampling.percentage}%</dd>
                  </>
                )}
                <dt className="text-slate-500">Selección:</dt>
                <dd>{preview.sampling.selection_method}</dd>
              </dl>
            </div>
          )}

          {preview.certificates.length > 0 && (
            <div className="rounded-xl border border-slate-200 bg-white p-4">
              <h3 className="text-sm font-bold text-slate-800">Certificados ({preview.certificates.length})</h3>
              <ul className="mt-2 space-y-1">
                {preview.certificates.map((cert: any) => (
                  <li key={cert.requirement_id} className="text-[11px] text-slate-600">
                    <span className="font-semibold">{cert.name}</span>
                    {cert.required && <span className="ml-1 text-rose-500">*</span>}
                    {cert.file_required && <span className="ml-1 text-amber-500">📁</span>}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {preview.evidence_requirements.length > 0 && (
            <div className="rounded-xl border border-slate-200 bg-white p-4">
              <h3 className="text-sm font-bold text-slate-800">Requisitos de evidencia</h3>
              <ul className="mt-2 list-disc pl-4 text-[11px] text-slate-600">
                {preview.evidence_requirements.map((er: any, i: number) => (
                  <li key={i}>{er}</li>
                ))}
              </ul>
            </div>
          )}

          {preview.future_responsibilities.length > 0 && (
            <div className="rounded-xl border border-slate-200 bg-white p-4">
              <h3 className="text-sm font-bold text-slate-800">Responsabilidades futuras</h3>
              <ul className="mt-2 list-disc pl-4 text-[11px] text-slate-600">
                {preview.future_responsibilities.map((fr: any, i: number) => (
                  <li key={i}>{fr}</li>
                ))}
              </ul>
            </div>
          )}

          {preview.warnings.length > 0 && (
            <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
              <h3 className="text-sm font-bold text-amber-800">Advertencias</h3>
              <ul className="mt-2 list-disc pl-4 text-[11px] text-amber-700">
                {preview.warnings.map((w: any, i: number) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </div>
          )}

          {preview.exclusions.length > 0 && (
            <div className="rounded-xl border border-slate-200 bg-white p-4">
              <h3 className="text-sm font-bold text-slate-800">Exclusiones ({preview.exclusions.length})</h3>
              <ul className="mt-2 space-y-1">
                {preview.exclusions.map((ex: any) => (
                  <li key={ex.scope_id} className="text-[11px] text-slate-600">
                    {ex.scope_type}: {ex.product_name ?? ex.category_name ?? ex.scope_id}
                    <span className="ml-1 text-slate-400">({ex.action})</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {preview.conflicts.length > 0 && (
            <div className="rounded-xl border border-rose-200 bg-rose-50 p-4">
              <h3 className="text-sm font-bold text-rose-800">Conflictos ({preview.conflicts.length})</h3>
              <ul className="mt-2 space-y-1">
                {preview.conflicts.map((c: any) => (
                  <li key={c.conflict_id} className="text-[11px] text-rose-700">
                    {c.conflicting_plan_code} — {c.rule_description}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {preview.explanation && (
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
              <h3 className="text-sm font-bold text-slate-800">Explicación</h3>
              <p className="mt-1 text-[11px] text-slate-600">{preview.explanation}</p>
            </div>
          )}
        </>
      )}
    </div>
  )
}
