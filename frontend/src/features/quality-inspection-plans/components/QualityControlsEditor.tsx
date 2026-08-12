import { useCallback, useState } from 'react'
import { Button } from '../../../components/common/Button'
import { useMutation } from '../../inbound-docks/hooks/useQuery'
import { apiRequest, getCsrfToken } from '../../../api/api-client'
import { StatusPill, EmptyPanel, ErrorPanel } from '../../inbound-docks/components/ui/Primitives'
import { PackagingQualityControlForm, WeightQualityControlForm, TemperatureQualityControlForm, GenericQualityControlForm } from './QualityControlForms'
import type {
  QualityControlDefinition,
  QualityInspectionPlanCapabilities,
  QualityControlType,
  CreateQualityControlRequest,
  ReorderQualityControlsRequest,
} from '../types/quality-inspection-plans'

const CONTROL_TYPE_LABEL: Record<QualityControlType, string> = {
  PACKAGING: 'Embalaje',
  WEIGHT: 'Peso',
  TEMPERATURE: 'Temperatura',
  VISUAL: 'Visual',
  DOCUMENT: 'Documento',
  CERTIFICATE: 'Certificado',
  MEASUREMENT: 'Medición',
  COUNT: 'Conteo',
  OTHER: 'Otro',
}

const CONTROL_TYPE_TONE: Record<QualityControlType, 'neutral' | 'info' | 'success' | 'warning' | 'danger' | 'muted'> = {
  PACKAGING: 'info',
  WEIGHT: 'info',
  TEMPERATURE: 'warning',
  VISUAL: 'neutral',
  DOCUMENT: 'neutral',
  CERTIFICATE: 'success',
  MEASUREMENT: 'neutral',
  COUNT: 'neutral',
  OTHER: 'muted',
}

interface ControlFormData {
  code: string
  name: string
  description: string
  control_type: QualityControlType
  required: boolean
  blocking_future: boolean
  evidence_required: boolean
}

const EMPTY_CONTROL_FORM: ControlFormData = {
  code: '',
  name: '',
  description: '',
  control_type: 'VISUAL',
  required: true,
  blocking_future: false,
  evidence_required: false,
}

export function QualityControlsEditor({
  versionId,
  controls,
  capabilities,
  onRefresh,
}: {
  versionId: string
  controls: QualityControlDefinition[]
  capabilities: QualityInspectionPlanCapabilities
  onRefresh: () => void
}) {
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState<ControlFormData>(EMPTY_CONTROL_FORM)
  const [editingControlId, setEditingControlId] = useState<string | null>(null)
  const [expandedControlId, setExpandedControlId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const createControlMutation = useMutation<CreateQualityControlRequest, { control_id: string }>(
    async (input) => {
      const csrf = await getCsrfToken()
      return apiRequest<{ control_id: string }>({
        path: `/logistics/quality/versions/${versionId}/controls`,
        method: 'POST',
        body: input,
        headers: { 'X-CSRF-Token': csrf },
      })
    },
    {
      onSuccess: () => {
        setShowForm(false)
        setFormData(EMPTY_CONTROL_FORM)
        onRefresh()
      },
      onError: (err) => setError(err.message),
    },
  )

  const updateControlMutation = useMutation<{ controlId: string; data: Partial<CreateQualityControlRequest> }, void>(
    async (input) => {
      const csrf = await getCsrfToken()
      await apiRequest({
        path: `/logistics/quality/controls/${input.controlId}`,
        method: 'PATCH',
        body: input.data,
        headers: { 'X-CSRF-Token': csrf },
      })
    },
    { onSuccess: () => { setShowForm(false); setEditingControlId(null); onRefresh() }, onError: (err) => setError(err.message) },
  )

  const deactivateControlMutation = useMutation<{ controlId: string }, void>(
    async (input) => {
      const csrf = await getCsrfToken()
      await apiRequest({
        path: `/logistics/quality/controls/${input.controlId}/deactivate`,
        method: 'POST',
        headers: { 'X-CSRF-Token': csrf },
      })
    },
    { onSuccess: () => onRefresh(), onError: (err) => setError(err.message) },
  )

  const cloneControlMutation = useMutation<{ controlId: string }, { control_id: string }>(
    async (input) => {
      const csrf = await getCsrfToken()
      return apiRequest<{ control_id: string }>({
        path: `/logistics/quality/controls/${input.controlId}/clone`,
        method: 'POST',
        headers: { 'X-CSRF-Token': csrf },
      })
    },
    { onSuccess: () => onRefresh(), onError: (err) => setError(err.message) },
  )

  const reorderMutation = useMutation<ReorderQualityControlsRequest, void>(
    async (input) => {
      const csrf = await getCsrfToken()
      await apiRequest({
        path: `/logistics/quality/versions/${versionId}/controls/reorder`,
        method: 'PUT',
        body: input,
        headers: { 'X-CSRF-Token': csrf },
      })
    },
    { onSuccess: () => onRefresh(), onError: (err) => setError(err.message) },
  )

  const handleAddControl = useCallback(() => {
    setShowForm(true)
    setEditingControlId(null)
    setFormData(EMPTY_CONTROL_FORM)
  }, [])

  const handleEditControl = useCallback((control: QualityControlDefinition) => {
    setEditingControlId(control.control_id)
    setShowForm(true)
    setFormData({
      code: control.code,
      name: control.name,
      description: control.description ?? '',
      control_type: control.control_type,
      required: control.required,
      blocking_future: control.blocking_future,
      evidence_required: control.evidence_required,
    })
  }, [])

  const handleCloneControl = useCallback((controlId: string) => {
    cloneControlMutation.mutate({ controlId })
  }, [cloneControlMutation])

  const handleDeactivateControl = useCallback((controlId: string) => {
    if (window.confirm('¿Desactivar este control? No se eliminará, pero no se aplicará en nuevas inspecciones.')) {
      deactivateControlMutation.mutate({ controlId })
    }
  }, [deactivateControlMutation])

  const handleMoveUp = useCallback((index: number) => {
    if (index === 0) return
    const orderedIds = controls.map((c) => c.control_id)
    const temp = orderedIds[index - 1]
    orderedIds[index - 1] = orderedIds[index]
    orderedIds[index] = temp
    reorderMutation.mutate({ ordered_control_ids: orderedIds })
  }, [controls, reorderMutation])

  const handleMoveDown = useCallback((index: number) => {
    if (index >= controls.length - 1) return
    const orderedIds = controls.map((c) => c.control_id)
    const temp = orderedIds[index]
    orderedIds[index] = orderedIds[index + 1]
    orderedIds[index + 1] = temp
    reorderMutation.mutate({ ordered_control_ids: orderedIds })
  }, [controls, reorderMutation])

  const handleSubmitControl = useCallback(() => {
    const payload: CreateQualityControlRequest = {
      code: formData.code,
      name: formData.name,
      description: formData.description || undefined,
      control_type: formData.control_type,
      required: formData.required,
      blocking_future: formData.blocking_future,
      evidence_required: formData.evidence_required,
      result_value_type: formData.control_type === 'PACKAGING' || formData.control_type === 'VISUAL' || formData.control_type === 'DOCUMENT' || formData.control_type === 'CERTIFICATE' || formData.control_type === 'OTHER'
        ? 'BOOLEAN'
        : formData.control_type === 'WEIGHT' || formData.control_type === 'MEASUREMENT'
          ? 'DECIMAL'
          : formData.control_type === 'TEMPERATURE'
            ? 'TEMPERATURE'
            : 'INTEGER',
    }

    if (editingControlId) {
      updateControlMutation.mutate({ controlId: editingControlId, data: payload })
    } else {
      createControlMutation.mutate(payload)
    }
  }, [formData, editingControlId, createControlMutation, updateControlMutation])

  const handleCancel = useCallback(() => {
    setShowForm(false)
    setEditingControlId(null)
    setFormData(EMPTY_CONTROL_FORM)
    setError(null)
  }, [])

  const handleToggleExpand = useCallback((controlId: string) => {
    setExpandedControlId((prev) => (prev === controlId ? null : controlId))
  }, [])

  if (error && !showForm) {
    return <ErrorPanel message={error} onRetry={() => { setError(null); onRefresh() }} />
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-bold text-slate-800">Controles de inspección</h3>
          <p className="text-xs text-slate-500">
            Defina los controles que se aplicarán durante la inspección de calidad.
          </p>
        </div>
        {capabilities.can_manage_controls && !showForm && (
          <Button variant="primary" size="small" onClick={handleAddControl}>
            Agregar control
          </Button>
        )}
      </div>

      {showForm && (
        <div className="rounded-xl border border-indigo-200 bg-indigo-50/30 p-4">
          <h4 className="mb-3 text-xs font-bold text-slate-800">
            {editingControlId ? 'Editar control' : 'Nuevo control'}
          </h4>
          {error && (
            <div className="mb-3 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700">
              {error}
            </div>
          )}
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            <div>
              <label className="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                Código
              </label>
              <input
                type="text"
                value={formData.code}
                onChange={(e) => setFormData((p) => ({ ...p, code: e.target.value }))}
                placeholder="EJ: EMB-001"
                className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-800 focus:border-[#1F4E6D] focus:outline-none focus:ring-1 focus:ring-[#1F4E6D]"
              />
            </div>
            <div>
              <label className="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                Nombre
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData((p) => ({ ...p, name: e.target.value }))}
                placeholder="Descripción del control"
                className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-800 focus:border-[#1F4E6D] focus:outline-none focus:ring-1 focus:ring-[#1F4E6D]"
              />
            </div>
            <div>
              <label className="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                Tipo
              </label>
              <select
                value={formData.control_type}
                onChange={(e) => setFormData((p) => ({ ...p, control_type: e.target.value as QualityControlType }))}
                className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-800 focus:border-[#1F4E6D] focus:outline-none focus:ring-1 focus:ring-[#1F4E6D]"
              >
                {Object.entries(CONTROL_TYPE_LABEL).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>
            <div className="sm:col-span-2 lg:col-span-3">
              <label className="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                Descripción
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData((p) => ({ ...p, description: e.target.value }))}
                rows={2}
                className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-800 focus:border-[#1F4E6D] focus:outline-none focus:ring-1 focus:ring-[#1F4E6D]"
              />
            </div>
            <div className="flex items-end gap-4">
              <label className="flex items-center gap-2 text-xs text-slate-700">
                <input
                  type="checkbox"
                  checked={formData.required}
                  onChange={(e) => setFormData((p) => ({ ...p, required: e.target.checked }))}
                  className="h-3.5 w-3.5 rounded border-slate-300 text-[#1F4E6D] focus:ring-[#1F4E6D]"
                />
                Requerido
              </label>
              <label className="flex items-center gap-2 text-xs text-slate-700">
                <input
                  type="checkbox"
                  checked={formData.blocking_future}
                  onChange={(e) => setFormData((p) => ({ ...p, blocking_future: e.target.checked }))}
                  className="h-3.5 w-3.5 rounded border-slate-300 text-[#1F4E6D] focus:ring-[#1F4E6D]"
                />
                Bloquea evidencia futura
              </label>
              <label className="flex items-center gap-2 text-xs text-slate-700">
                <input
                  type="checkbox"
                  checked={formData.evidence_required}
                  onChange={(e) => setFormData((p) => ({ ...p, evidence_required: e.target.checked }))}
                  className="h-3.5 w-3.5 rounded border-slate-300 text-[#1F4E6D] focus:ring-[#1F4E6D]"
                />
                Evidencia requerida
              </label>
            </div>
          </div>

          <div className="mt-4">
            <p className="mb-2 rounded-lg bg-amber-50 px-3 py-2 text-[10px] text-amber-700">
              Esta configuración define qué se revisará. No registra una inspección.
            </p>
            {formData.control_type === 'PACKAGING' && (
              <PackagingQualityControlForm />
            )}
            {formData.control_type === 'WEIGHT' && (
              <WeightQualityControlForm />
            )}
            {formData.control_type === 'TEMPERATURE' && (
              <TemperatureQualityControlForm />
            )}
            {!['PACKAGING', 'WEIGHT', 'TEMPERATURE'].includes(formData.control_type) && (
              <GenericQualityControlForm />
            )}
          </div>

          <div className="mt-4 flex items-center justify-end gap-2">
            <Button variant="ghost" size="small" onClick={handleCancel}>
              Cancelar
            </Button>
            <Button
              variant="primary"
              size="small"
              onClick={handleSubmitControl}
              isLoading={createControlMutation.isPending || updateControlMutation.isPending}
            >
              {editingControlId ? 'Guardar cambios' : 'Agregar control'}
            </Button>
          </div>
        </div>
      )}

      {controls.length === 0 && !showForm ? (
        <EmptyPanel
          title="Sin controles configurados"
          description="Agregue controles para definir qué se verificará durante la inspección de calidad."
        />
      ) : (
        <div className="space-y-2">
          {controls.map((control, index) => (
            <div
              key={control.control_id}
              className={`rounded-xl border ${
                !control.active
                  ? 'border-slate-200 bg-slate-50/50 opacity-60'
                  : expandedControlId === control.control_id
                    ? 'border-indigo-200 bg-indigo-50/20'
                    : 'border-slate-200 bg-white hover:border-slate-300'
              } transition-colors`}
            >
              <div className="flex items-center gap-3 px-4 py-3">
                <div className="flex flex-col gap-0.5">
                  <button
                    type="button"
                    onClick={() => handleMoveUp(index)}
                    disabled={index === 0 || !capabilities.can_manage_controls}
                    className="rounded p-0.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600 disabled:opacity-30 disabled:cursor-not-allowed"
                    aria-label="Mover arriba"
                  >
                    <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M5 15l7-7 7 7" />
                    </svg>
                  </button>
                  <button
                    type="button"
                    onClick={() => handleMoveDown(index)}
                    disabled={index === controls.length - 1 || !capabilities.can_manage_controls}
                    className="rounded p-0.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600 disabled:opacity-30 disabled:cursor-not-allowed"
                    aria-label="Mover abajo"
                  >
                    <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                </div>

                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-slate-100 text-[10px] font-bold text-slate-600">
                  {control.display_order}
                </span>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-slate-800">{control.code}</span>
                    <span className="text-xs text-slate-600 truncate">{control.name}</span>
                    <StatusPill tone={CONTROL_TYPE_TONE[control.control_type]}>
                      {CONTROL_TYPE_LABEL[control.control_type]}
                    </StatusPill>
                    {control.required && <StatusPill tone="warning">Requerido</StatusPill>}
                    {control.blocking_future && <StatusPill tone="danger">Bloquea</StatusPill>}
                    {control.evidence_required && <StatusPill tone="info">Evidencia</StatusPill>}
                    {!control.active && <StatusPill tone="muted">Inactivo</StatusPill>}
                  </div>
                </div>

                <div className="flex items-center gap-1">
                  <button
                    type="button"
                    onClick={() => handleToggleExpand(control.control_id)}
                    className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
                    aria-label={expandedControlId === control.control_id ? 'Colapsar' : 'Expandir'}
                  >
                    <svg className={`h-4 w-4 transition-transform ${expandedControlId === control.control_id ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                  {capabilities.can_manage_controls && (
                    <Button variant="ghost" size="small" onClick={() => handleEditControl(control)}>
                      Editar
                    </Button>
                  )}
                  {capabilities.can_manage_controls && (
                    <Button variant="ghost" size="small" onClick={() => handleCloneControl(control.control_id)}>
                      Clonar
                    </Button>
                  )}
                  {capabilities.can_manage_controls && control.active && (
                    <Button variant="ghost" size="small" onClick={() => handleDeactivateControl(control.control_id)}>
                      Desactivar
                    </Button>
                  )}
                </div>
              </div>

              {expandedControlId === control.control_id && (
                <div className="border-t border-slate-100 px-4 py-3">
                  <p className="mb-2 rounded-lg bg-amber-50 px-3 py-2 text-[10px] text-amber-700">
                    Esta configuración define qué se revisará. No registra una inspección.
                  </p>
                  {control.control_type === 'PACKAGING' && (
                    <PackagingQualityControlForm config={control.configuration.type === 'PACKAGING' ? control.configuration : undefined} />
                  )}
                  {control.control_type === 'WEIGHT' && (
                    <WeightQualityControlForm config={control.configuration.type === 'WEIGHT' ? control.configuration : undefined} />
                  )}
                  {control.control_type === 'TEMPERATURE' && (
                    <TemperatureQualityControlForm config={control.configuration.type === 'TEMPERATURE' ? control.configuration : undefined} />
                  )}
                  {!['PACKAGING', 'WEIGHT', 'TEMPERATURE'].includes(control.control_type) && (
                    <GenericQualityControlForm config={control.configuration.type === 'GENERIC' ? control.configuration : undefined} />
                  )}
                  <dl className="mt-3 grid grid-cols-2 gap-x-4 gap-y-1 text-xs sm:grid-cols-3">
                    <dt className="text-[10px] font-semibold uppercase text-slate-500">Tolerancia</dt>
                    <dd className="text-slate-800">{control.tolerance_name ?? '—'}</dd>
                    <dt className="text-[10px] font-semibold uppercase text-slate-500">Muestreo</dt>
                    <dd className="text-slate-800">{control.sampling_plan_name ?? '—'}</dd>
                    <dt className="text-[10px] font-semibold uppercase text-slate-500">Certificado</dt>
                    <dd className="text-slate-800">{control.certificate_requirement_name ?? '—'}</dd>
                  </dl>
                  {control.conditions.length > 0 && (
                    <div className="mt-3">
                      <p className="mb-1 text-[10px] font-semibold uppercase text-slate-500">Condiciones</p>
                      <div className="space-y-1">
                        {control.conditions.map((cond) => (
                          <div key={cond.condition_id} className="flex items-center gap-2 rounded-lg bg-slate-50 px-2 py-1 text-[10px] text-slate-600">
                            <span className="font-mono">{cond.condition_field}</span>
                            <span className="text-slate-400">{cond.operator}</span>
                            <span className="font-mono">{cond.value ?? '—'}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
