import { useCallback, useEffect, useState } from 'react'
import { vehicleVerificationsApi } from '../api/vehicle-verifications-api'
import { LoadingSkeleton } from '../components/common/LoadingSkeleton'
import { PageHeader } from '../components/common/PageHeader'
import { VehicleVerificationConflictsPanel } from '../components/vehicle-verifications/VehicleVerificationConflictsPanel'
import { useSensitiveOperationGuard } from '../features/continuous-auth/hooks/useSensitiveOperationGuard'
import { useLogisticsPermissions } from '../features/logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../features/logistics-permissions/logistics-permissions-map'
import type { VehicleVerificationConflict, VehicleVerificationConflictResolve } from '../types/vehicle-verifications'

export function VehicleVerificationConflictsPage() {
  const { hasPermission } = useLogisticsPermissions()
  const canResolve = hasPermission(LOGISTICS_PERMISSIONS.vehicleVerifications.resolveConflict)
  const { guardSensitiveAction } = useSensitiveOperationGuard()

  const [conflicts, setConflicts] = useState<VehicleVerificationConflict[]>([])
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState<string>('OPEN')

  const loadConflicts = useCallback(async () => {
    setLoading(true)
    try {
      const res = await vehicleVerificationsApi.listConflicts(statusFilter || undefined)
      setConflicts(res)
    } finally {
      setLoading(false)
    }
  }, [statusFilter])

  useEffect(() => {
    void loadConflicts()
  }, [loadConflicts])

  const handleResolveConflict = async (conflictId: string, data: VehicleVerificationConflictResolve) => {
    try {
      const executed = await guardSensitiveAction(async () => {
        await vehicleVerificationsApi.resolveConflict(conflictId, data)
      })
      if (executed) void loadConflicts()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Error al resolver conflicto')
    }
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <PageHeader
        title="Panel de Discrepancias y Conflictos Vehiculares"
        description="Auditoría y resolución justificada de conflictos entre datos declarados y fuentes oficiales."
      />

      {/* Filter */}
      <div className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-xs text-xs">
        <span className="font-bold text-slate-700">Estado de Conflictos:</span>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-xl border border-slate-300 px-3 py-2 bg-white font-medium text-slate-700"
        >
          <option value="OPEN">Abiertos / Pendientes</option>
          <option value="UNDER_REVIEW">En Revisión</option>
          <option value="RESOLVED_APPLY_VERIFIED">Resueltos (Verificado Aplicado)</option>
          <option value="RESOLVED_KEEP_MASTER">Resueltos (Maestro Conservado)</option>
          <option value="DISMISSED">Descartados</option>
          <option value="">Todos los Estados</option>
        </select>
      </div>

      {loading ? (
        <LoadingSkeleton rows={6} />
      ) : (
        <VehicleVerificationConflictsPanel
          conflicts={conflicts}
          onResolveConflict={handleResolveConflict}
          canResolve={canResolve}
        />
      )}
    </div>
  )
}
