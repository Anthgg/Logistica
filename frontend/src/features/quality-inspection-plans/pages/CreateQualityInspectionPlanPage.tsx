import { useCallback, useState } from 'react'
import type { FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { PageHeader } from '../../../components/common/PageHeader'
import { Button } from '../../../components/common/Button'
import { Input } from '../../../components/common/Input'
import { Alert } from '../../../components/common/Alert'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { useMutation } from '../../inbound-docks/hooks/useQuery'
import { qualityInspectionPlansApi } from '../api/qualityInspectionPlansApi'
import { getErrorMessage } from '../../../utils/errors'
import type { QualityInspectionPlanFamily } from '../types/quality-inspection-plans'

const FAMILY_OPTIONS: { value: QualityInspectionPlanFamily; label: string }[] = [
  { value: 'GENERAL', label: 'General' },
  { value: 'PRODUCT', label: 'Producto' },
  { value: 'CATEGORY', label: 'Categoría' },
  { value: 'WAREHOUSE', label: 'Almacén' },
  { value: 'SUPPLIER', label: 'Proveedor' },
  { value: 'TEMPERATURE', label: 'Temperatura' },
  { value: 'HAZMAT', label: 'Hazardous' },
]

export function CreateQualityInspectionPlanPage() {
  const navigate = useNavigate()
  const { hasPermission } = useLogisticsPermissions()
  const canCreate = hasPermission('logistics.procurement_approvals.create' as never)

  const [code, setCode] = useState('')
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [family, setFamily] = useState<QualityInspectionPlanFamily>('GENERAL')

  const createMutation = useMutation(
    (input: { code: string; name: string; description?: string; family: QualityInspectionPlanFamily }) =>
      qualityInspectionPlansApi.create(input),
    {
      onSuccess: (result) => {
        navigate(`/logistics/quality-inspection-plans/${(result as { plan_id: string }).plan_id}`, { replace: true })
      },
    },
  )

  const isValid = code.trim().length >= 2 && name.trim().length >= 2

  const onSubmit = useCallback(
    (e: FormEvent<HTMLFormElement>) => {
      e.preventDefault()
      if (!isValid || createMutation.isPending) return
      createMutation.mutate({
        code: code.trim(),
        name: name.trim(),
        description: description.trim() || undefined,
        family,
      })
    },
    [isValid, createMutation, code, name, description, family],
  )

  if (!canCreate) {
    return (
      <div className="space-y-4">
        <PageHeader title="Crear plan de inspección" />
        <Alert variant="error">No tienes permisos para crear planes de inspección de calidad.</Alert>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <PageHeader
        eyebrow="Fase 041"
        title="Crear plan de inspección"
        description="Define el código, nombre, descripción y familia del nuevo plan."
        actions={
          <Button size="small" variant="ghost" onClick={() => navigate('/logistics/quality-inspection-plans')}>
            ← Volver
          </Button>
        }
      />

      <form
        onSubmit={(e) => void onSubmit(e)}
        className="max-w-2xl space-y-4 rounded-2xl border border-[#EEF2F5] bg-white p-5 shadow-sm"
      >
        <Input
          label="Código"
          placeholder="Ej: QIP-001"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          maxLength={50}
          required
        />

        <Input
          label="Nombre"
          placeholder="Nombre del plan de inspección"
          value={name}
          onChange={(e) => setName(e.target.value)}
          maxLength={150}
          required
        />

        <label className="block">
          <span className="mb-1 block text-xs font-semibold text-slate-700">Descripción</span>
          <textarea
            rows={3}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Descripción opcional del plan"
            className="w-full rounded-lg border border-[#DDE4E8] px-3 py-2 text-xs outline-none focus:border-[#1F4E6D] focus:ring-2 focus:ring-[#1F4E6D]/20"
          />
        </label>

        <label className="block">
          <span className="mb-1 block text-xs font-semibold text-slate-700">Familia</span>
          <select
            value={family}
            onChange={(e) => setFamily(e.target.value as QualityInspectionPlanFamily)}
            className="min-h-11 w-full rounded-lg border border-[#DDE4E8] px-3 text-xs bg-white outline-none focus:border-[#1F4E6D] focus:ring-2 focus:ring-[#1F4E6D]/20"
          >
            {FAMILY_OPTIONS.map((f) => (
              <option key={f.value} value={f.value}>{f.label}</option>
            ))}
          </select>
        </label>

        {createMutation.error && (
          <Alert variant="error">{getErrorMessage(createMutation.error)}</Alert>
        )}

        <div className="flex justify-end gap-2 pt-2">
          <Button
            type="button"
            variant="secondary"
            size="small"
            disabled={createMutation.isPending}
            onClick={() => navigate('/logistics/quality-inspection-plans')}
          >
            Cancelar
          </Button>
          <Button
            type="submit"
            size="small"
            isLoading={createMutation.isPending}
            disabled={!isValid || createMutation.isPending}
          >
            Crear plan
          </Button>
        </div>
      </form>
    </div>
  )
}
