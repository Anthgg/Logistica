import { useCallback, useEffect, useState } from 'react'
import { vehicleVerificationsApi } from '../api/vehicle-verifications-api'
import { Button } from '../components/common/Button'
import { LoadingSkeleton } from '../components/common/LoadingSkeleton'
import { PageHeader } from '../components/common/PageHeader'
import { VehicleVerificationRequirementForm } from '../components/vehicle-verifications/VehicleVerificationRequirementForm'
import { useSensitiveOperationGuard } from '../features/continuous-auth/hooks/useSensitiveOperationGuard'
import { useLogisticsPermissions } from '../features/logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../features/logistics-permissions/logistics-permissions-map'
import type {
  VehicleVerificationRequirement,
  VehicleVerificationRequirementCreate,
  VehicleVerificationRequirementUpdate,
} from '../types/vehicle-verifications'

export function VehicleVerificationRequirementsPage() {
  const { hasPermission } = useLogisticsPermissions()
  const canManage = hasPermission(LOGISTICS_PERMISSIONS.vehicleVerifications.manageRequirements)
  const canActivate = hasPermission(LOGISTICS_PERMISSIONS.vehicleVerifications.activateRequirements)
  const { guardSensitiveAction } = useSensitiveOperationGuard()

  const [requirements, setRequirements] = useState<VehicleVerificationRequirement[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState<VehicleVerificationRequirement | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const loadReqs = useCallback(async () => {
    setLoading(true)
    try {
      const res = await vehicleVerificationsApi.listRequirements()
      setRequirements(res)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadReqs()
  }, [loadReqs])

  const handleCreate = async (data: VehicleVerificationRequirementCreate | VehicleVerificationRequirementUpdate) => {
    setSubmitting(true)
    try {
      if (editing) {
        await vehicleVerificationsApi.updateRequirement(editing.id, data as VehicleVerificationRequirementUpdate)
      } else {
        await vehicleVerificationsApi.createRequirement(data as VehicleVerificationRequirementCreate)
      }
      setShowForm(false)
      setEditing(null)
      void loadReqs()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Error al guardar requisito')
    } finally {
      setSubmitting(false)
    }
  }

  const handleValidate = async (id: string) => {
    setSubmitting(true)
    try {
      await vehicleVerificationsApi.validateRequirement(id)
      void loadReqs()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Error al validar requisito')
    } finally {
      setSubmitting(false)
    }
  }

  const handleActivate = async (id: string) => {
    setSubmitting(true)
    try {
      const executed = await guardSensitiveAction(async () => {
        await vehicleVerificationsApi.activateRequirement(id)
      })
      if (executed) void loadReqs()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Error al activar requisito')
    } finally {
      setSubmitting(false)
    }
  }

  const handleRetire = async (id: string) => {
    const reason = window.prompt('Motivo de retiro del requisito:')
    if (!reason) return
    setSubmitting(true)
    try {
      await vehicleVerificationsApi.retireRequirement(id, reason)
      void loadReqs()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Error al retirar requisito')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <PageHeader
        title="Requisitos Normativos y Políticas de Verificación"
        description="Definición de reglas autoritativas por tipo vehicular, carrocería, fuente preferida y antigüedad máxima."
        actions={
          canManage && (
            <Button
              size="small"
              onClick={() => {
                setEditing(null)
                setShowForm(true)
              }}
            >
              + Nuevo Requisito
            </Button>
          )
        }
      />

      {showForm && (
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
          <h3 className="text-sm font-bold text-slate-800 border-b border-slate-100 pb-2">
            {editing ? 'Editar Requisito (DRAFT)' : 'Crear Requisito (DRAFT)'}
          </h3>
          <VehicleVerificationRequirementForm
            initial={editing ?? undefined}
            isSubmitting={submitting}
            onSubmit={handleCreate}
            onCancel={() => {
              setShowForm(false)
              setEditing(null)
            }}
          />
        </div>
      )}

      {loading ? (
        <LoadingSkeleton rows={6} />
      ) : requirements.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-12 text-center text-slate-500 text-xs">
          No hay requisitos de verificación configurados.
        </div>
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-xs text-xs">
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50 text-slate-600">
              <tr>
                <th className="px-4 py-3 text-left font-semibold">Tipo Vehicular</th>
                <th className="px-4 py-3 text-left font-semibold">Dominio Normativo</th>
                <th className="px-4 py-3 text-left font-semibold">Fuente Preferida</th>
                <th className="px-4 py-3 text-center font-semibold">Obligatoria</th>
                <th className="px-4 py-3 text-center font-semibold">Bloqueante</th>
                <th className="px-4 py-3 text-right font-semibold">Antigüedad Máx.</th>
                <th className="px-4 py-3 text-center font-semibold">Confianza Mín.</th>
                <th className="px-4 py-3 text-center font-semibold">Estado</th>
                <th className="px-4 py-3 text-right font-semibold">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {requirements.map((r) => (
                <tr key={r.id} className="hover:bg-slate-50">
                  <td className="px-4 py-3 font-bold text-slate-800">{r.vehicle_type}</td>
                  <td className="px-4 py-3 font-bold text-indigo-700">{r.domain}</td>
                  <td className="px-4 py-3 text-slate-700">{r.preferred_source}</td>
                  <td className="px-4 py-3 text-center">
                    <span className={`rounded px-2 py-0.5 text-[10px] font-bold ${r.is_mandatory ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-600'}`}>
                      {r.is_mandatory ? 'Sí' : 'No'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className={`rounded px-2 py-0.5 text-[10px] font-bold ${r.is_blocking ? 'bg-rose-100 text-rose-800' : 'bg-slate-100 text-slate-600'}`}>
                      {r.is_blocking ? 'Sí' : 'No'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right font-mono font-bold text-slate-800">
                    {r.max_age_days} días
                  </td>
                  <td className="px-4 py-3 text-center font-mono font-bold">
                    {Math.round(r.min_confidence_score * 100)}%
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className={`rounded px-2 py-0.5 text-[10px] font-bold ${
                      r.status === 'ACTIVE'
                        ? 'bg-emerald-100 text-emerald-800'
                        : r.status === 'RETIRED'
                          ? 'bg-slate-200 text-slate-600'
                          : 'bg-amber-100 text-amber-800'
                    }`}>
                      {r.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex justify-end gap-1.5">
                      {canManage && r.status === 'DRAFT' && (
                        <>
                          <button
                            type="button"
                            onClick={() => {
                              setEditing(r)
                              setShowForm(true)
                            }}
                            className="font-semibold text-indigo-600 hover:underline"
                          >
                            Editar
                          </button>
                          <button
                            type="button"
                            onClick={() => void handleValidate(r.id)}
                            disabled={submitting}
                            className="font-semibold text-slate-600 hover:text-indigo-600 hover:underline"
                          >
                            Validar
                          </button>
                        </>
                      )}
                      {canActivate && r.status === 'DRAFT' && (
                        <button
                          type="button"
                          onClick={() => void handleActivate(r.id)}
                          disabled={submitting}
                          className="font-semibold text-emerald-700 hover:underline"
                        >
                          Activar (Step-Up)
                        </button>
                      )}
                      {canManage && r.status === 'ACTIVE' && (
                        <button
                          type="button"
                          onClick={() => void handleRetire(r.id)}
                          disabled={submitting}
                          className="font-semibold text-rose-600 hover:underline"
                        >
                          Retirar
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}