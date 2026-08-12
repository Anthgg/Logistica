import { useState } from 'react'
import { useMutation } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { qualityInspectionsApi } from '../api/qualityInspectionsApi'
import type { QualityInspectionControl } from '../types/quarantine'
import { Button } from '../../../components/common/Button'
import { Input } from '../../../components/common/Input'
import { StatusBadge } from '../../../components/common/StatusBadge'
import { Alert } from '../../../components/common/Alert'

export interface PackagingInspectionControlProps {
  control: QualityInspectionControl
  onControlUpdated: (control: QualityInspectionControl) => void
}

interface PackagingFormData {
  type: string
  level: string
  integrity: string
  seal: string
  humidity: string
  tears: string
  deformation: string
  opening: string
  labeling: string
  visualCleanliness: string
  evidenceFileId: string
  observation: string
}

const INITIAL_FORM: PackagingFormData = {
  type: '',
  level: '',
  integrity: '',
  seal: '',
  humidity: '',
  tears: '',
  deformation: '',
  opening: '',
  labeling: '',
  visualCleanliness: '',
  evidenceFileId: '',
  observation: '',
}

const INTEGRITY_OPTIONS = ['INTEGRIDAD', 'DAÑO_LEVE', 'DAÑO_MODERADO', 'DAÑO_SEVERO', 'DESTRuido']
const SEAL_OPTIONS = ['SELLADO', 'SELLADO_ROTO', 'SIN_SELLO', 'SELLADO_PARCIAL']
const HUMIDITY_OPTIONS = ['SECO', 'HUMEDAD_LEVE', 'HUMEDAD_MODERADA', 'HUMEDAD_ALTA', 'EMPAPADO']
const CLEANLINEESS_OPTIONS = ['LIMPIO', 'SUCIEDAD_LEVE', 'SUCIEDAD_MODERADA', 'SUCIEDAD_ALTA', 'CONTAMINADO']

export function PackagingInspectionControl({
  control,
  onControlUpdated,
}: PackagingInspectionControlProps) {
  const auth = useLogisticsPermissions()
  const canRecord = auth.hasPermission(LOGISTICS_PERMISSIONS.quarantine.recordControlResult)

  const [form, setForm] = useState<PackagingFormData>(INITIAL_FORM)
  const [error, setError] = useState<string | null>(null)

  const recordMutation = useMutation(
    (input: Record<string, unknown>) =>
      qualityInspectionsApi.recordControlResult(control.control_id, input),
    {
      onSuccess: (result) => {
        onControlUpdated(result)
      },
      onError: (err) => {
        setError(err.message)
      },
    },
  )

  function updateField<K extends keyof PackagingFormData>(key: K, value: PackagingFormData[K]) {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  function handleRecord() {
    setError(null)
    const payload: Record<string, unknown> = {
      control_id: control.control_id,
      result_value: JSON.stringify({
        type: form.type,
        level: form.level,
        integrity: form.integrity,
        seal: form.seal,
        humidity: form.humidity,
        tears: form.tears,
        deformation: form.deformation,
        opening: form.opening,
        labeling: form.labeling,
        visual_cleanliness: form.visualCleanliness,
      }),
      result_text: form.observation || undefined,
      result_file_id: form.evidenceFileId || undefined,
    }
    void recordMutation.mutate(payload)
  }

  const isCompleted = control.status === 'COMPLETED'

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 text-xs space-y-3">
      <div className="flex items-start justify-between gap-2">
        <div>
          <h4 className="font-semibold text-sm text-slate-800">Inspección de empaque</h4>
          <p className="text-[11px] text-slate-500 mt-0.5">{control.description ?? 'Verificación de estado del empaque'}</p>
        </div>
        <StatusBadge value={control.status.toLowerCase().replace(/_/g, ' ')} />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <Input
          id={`pkg-type-${control.control_id}`}
          label="Tipo de empaque"
          value={form.type}
          onChange={(e) => updateField('type', e.target.value)}
          disabled={isCompleted || recordMutation.isPending}
          placeholder="Ej: Caja, Pallet, Bolsa"
        />

        <Input
          id={`pkg-level-${control.control_id}`}
          label="Nivel"
          value={form.level}
          onChange={(e) => updateField('level', e.target.value)}
          disabled={isCompleted || recordMutation.isPending}
          placeholder="Nivel de inspección"
        />

        <div>
          <label className="field__label text-xs" htmlFor={`pkg-integrity-${control.control_id}`}>
            Integridad
          </label>
          <select
            id={`pkg-integrity-${control.control_id}`}
            className="field__input text-xs"
            value={form.integrity}
            onChange={(e) => updateField('integrity', e.target.value)}
            disabled={isCompleted || recordMutation.isPending}
          >
            <option value="">Seleccionar…</option>
            {INTEGRITY_OPTIONS.map((opt) => (
              <option key={opt} value={opt}>{opt.replace(/_/g, ' ')}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="field__label text-xs" htmlFor={`pkg-seal-${control.control_id}`}>
            Sello
          </label>
          <select
            id={`pkg-seal-${control.control_id}`}
            className="field__input text-xs"
            value={form.seal}
            onChange={(e) => updateField('seal', e.target.value)}
            disabled={isCompleted || recordMutation.isPending}
          >
            <option value="">Seleccionar…</option>
            {SEAL_OPTIONS.map((opt) => (
              <option key={opt} value={opt}>{opt.replace(/_/g, ' ')}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="field__label text-xs" htmlFor={`pkg-humidity-${control.control_id}`}>
            Humedad
          </label>
          <select
            id={`pkg-humidity-${control.control_id}`}
            className="field__input text-xs"
            value={form.humidity}
            onChange={(e) => updateField('humidity', e.target.value)}
            disabled={isCompleted || recordMutation.isPending}
          >
            <option value="">Seleccionar…</option>
            {HUMIDITY_OPTIONS.map((opt) => (
              <option key={opt} value={opt}>{opt.replace(/_/g, ' ')}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="field__label text-xs" htmlFor={`pkg-tears-${control.control_id}`}>
            Desgarros
          </label>
          <select
            id={`pkg-tears-${control.control_id}`}
            className="field__input text-xs"
            value={form.tears}
            onChange={(e) => updateField('tears', e.target.value)}
            disabled={isCompleted || recordMutation.isPending}
          >
            <option value="">Seleccionar…</option>
            <option value="NINGUNO">Ninguno</option>
            <option value="LEVE">Leve</option>
            <option value="MODERADO">Moderado</option>
            <option value="SEVERO">Severo</option>
          </select>
        </div>

        <div>
          <label className="field__label text-xs" htmlFor={`pkg-deformation-${control.control_id}`}>
            Deformación
          </label>
          <select
            id={`pkg-deformation-${control.control_id}`}
            className="field__input text-xs"
            value={form.deformation}
            onChange={(e) => updateField('deformation', e.target.value)}
            disabled={isCompleted || recordMutation.isPending}
          >
            <option value="">Seleccionar…</option>
            <option value="NINGUNA">Ninguna</option>
            <option value="LEVE">Leve</option>
            <option value="MODERADA">Moderada</option>
            <option value="SEVERA">Severa</option>
          </select>
        </div>

        <div>
          <label className="field__label text-xs" htmlFor={`pkg-opening-${control.control_id}`}>
            Apertura
          </label>
          <select
            id={`pkg-opening-${control.control_id}`}
            className="field__input text-xs"
            value={form.opening}
            onChange={(e) => updateField('opening', e.target.value)}
            disabled={isCompleted || recordMutation.isPending}
          >
            <option value="">Seleccionar…</option>
            <option value="CERRADO">Cerrado</option>
            <option value="PARCIALMENTE_ABIERTO">Parcialmente abierto</option>
            <option value="ABIERTO">Abierto</option>
          </select>
        </div>

        <div>
          <label className="field__label text-xs" htmlFor={`pkg-labeling-${control.control_id}`}>
            Rotulado
          </label>
          <select
            id={`pkg-labeling-${control.control_id}`}
            className="field__input text-xs"
            value={form.labeling}
            onChange={(e) => updateField('labeling', e.target.value)}
            disabled={isCompleted || recordMutation.isPending}
          >
            <option value="">Seleccionar…</option>
            <option value="CORRECTO">Correcto</option>
            <option value="PARCIAL">Parcial</option>
            <option value="INCORRECTO">Incorrecto</option>
            <option value="AUSENTE">Ausente</option>
          </select>
        </div>

        <div>
          <label className="field__label text-xs" htmlFor={`pkg-clean-${control.control_id}`}>
            Limpieza visual
          </label>
          <select
            id={`pkg-clean-${control.control_id}`}
            className="field__input text-xs"
            value={form.visualCleanliness}
            onChange={(e) => updateField('visualCleanliness', e.target.value)}
            disabled={isCompleted || recordMutation.isPending}
          >
            <option value="">Seleccionar…</option>
            {CLEANLINEESS_OPTIONS.map((opt) => (
              <option key={opt} value={opt}>{opt.replace(/_/g, ' ')}</option>
            ))}
          </select>
        </div>
      </div>

      <Input
        id={`pkg-evidence-${control.control_id}`}
        label="ID de evidencia (opcional)"
        value={form.evidenceFileId}
        onChange={(e) => updateField('evidenceFileId', e.target.value)}
        disabled={isCompleted || recordMutation.isPending}
        placeholder="File ID de foto"
      />

      <div>
        <label className="field__label text-xs" htmlFor={`pkg-obs-${control.control_id}`}>
          Observación
        </label>
        <textarea
          id={`pkg-obs-${control.control_id}`}
          className="field__input text-xs min-h-[60px] resize-y"
          value={form.observation}
          onChange={(e) => updateField('observation', e.target.value)}
          disabled={isCompleted || recordMutation.isPending}
          placeholder="Observaciones adicionales sobre el empaque"
        />
      </div>

      {error && <Alert variant="error">{error}</Alert>}

      {!isCompleted && canRecord && (
        <Button
          type="button"
          variant="primary"
          size="small"
          onClick={handleRecord}
          isLoading={recordMutation.isPending}
          disabled={recordMutation.isPending}
        >
          Registrar inspección de empaque
        </Button>
      )}
    </div>
  )
}
