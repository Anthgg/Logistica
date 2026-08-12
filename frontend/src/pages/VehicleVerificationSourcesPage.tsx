import { useCallback, useEffect, useState } from 'react'
import { vehicleVerificationsApi } from '../api/vehicle-verifications-api'
import { LoadingSkeleton } from '../components/common/LoadingSkeleton'
import { PageHeader } from '../components/common/PageHeader'
import { VehicleVerificationProviderHealthPanel } from '../components/vehicle-verifications/VehicleVerificationProviderHealthPanel'
import { useSensitiveOperationGuard } from '../features/continuous-auth/hooks/useSensitiveOperationGuard'
import { useLogisticsPermissions } from '../features/logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../features/logistics-permissions/logistics-permissions-map'
import type { VehicleVerificationSourceHealth, VehicleVerificationSourceType } from '../types/vehicle-verifications'

export function VehicleVerificationSourcesPage() {
  const { hasPermission } = useLogisticsPermissions()
  const canManage = hasPermission(LOGISTICS_PERMISSIONS.vehicleVerifications.manageSources)

  const { guardSensitiveAction } = useSensitiveOperationGuard()

  const [sources, setSources] = useState<VehicleVerificationSourceHealth[]>([])
  const [loading, setLoading] = useState(true)

  const loadSources = useCallback(async () => {
    setLoading(true)
    try {
      const res = await vehicleVerificationsApi.listSourcesHealth()
      setSources(res)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadSources()
  }, [loadSources])

  const handleToggleSource = async (sourceType: string, currentStatus: string) => {
    try {
      const executed = await guardSensitiveAction(async () => {
        if (currentStatus === 'DISABLED') {
          await vehicleVerificationsApi.enableSource(sourceType as VehicleVerificationSourceType, 'Rehabilitación manual desde consola autorizada')
        } else {
          await vehicleVerificationsApi.disableSource(sourceType as VehicleVerificationSourceType, 'Deshabilitación manual preventiva')
        }
      })
      if (executed) void loadSources()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Error al cambiar estado de fuente')
    }
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <PageHeader
        title="Fuentes Registrales y Proveedores Autorizados"
        description="Monitoreo de disponibilidad, latencia, circuit breaker y estado operativo de fuentes externas de verificación."
      />

      {loading ? (
        <LoadingSkeleton rows={6} />
      ) : (
        <VehicleVerificationProviderHealthPanel
          sources={sources}
          onToggleSource={handleToggleSource}
          canManageSources={canManage}
        />
      )}
    </div>
  )
}
