import { PageHeader } from '../../../components/common/PageHeader'
import { Alert } from '../../../components/common/Alert'
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton'
import { useQuery } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsAccess } from '../../logistics-me/hooks/useLogisticsAccess'
import { getErrorMessage } from '../../../utils/errors'
import { BalanceFreshnessBanner } from '../components/BalanceFreshnessBanner'
import type { InventoryBalanceFreshness } from '../types/inventory-balances'

export function InventoryBalanceFreshnessPage() {
  const { currentContext } = useLogisticsAccess()
  const organizationId = currentContext?.organization_id

  const freshness = useQuery<InventoryBalanceFreshness[]>(
    ['inventory-balances', 'freshness', organizationId ?? ''],
    '/logistics/inventory/balances/freshness',
    organizationId ? { organization_id: organizationId } : undefined,
    { enabled: Boolean(organizationId) },
  )

  return (
    <div className="space-y-6 pb-10">
      <PageHeader
        eyebrow="Fase 045"
        title="Frescura de saldos"
        description="Estado de proyección y latencia de los saldos por partición."
      />

      {freshness.isLoading && <LoadingSkeleton rows={6} />}
      {freshness.isError && <Alert variant="error">{getErrorMessage(freshness.error)}</Alert>}

      {freshness.data && freshness.data.length === 0 && (
        <Alert variant="info">No hay datos de frescura disponibles.</Alert>
      )}

      {freshness.data && freshness.data.length > 0 && (
        <div className="space-y-2">
          {freshness.data.map((f) => (
            <BalanceFreshnessBanner key={f.partition_key} freshness={f} />
          ))}
        </div>
      )}
    </div>
  )
}
