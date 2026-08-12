import { useNavigate } from 'react-router-dom'
import { PageHeader } from '../../../components/common/PageHeader'
import { MetricCard } from '../../../components/common/MetricCard'
import { Button } from '../../../components/common/Button'
import { Alert } from '../../../components/common/Alert'
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton'
import { useQuery } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsAccess } from '../../logistics-me/hooks/useLogisticsAccess'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { getErrorMessage } from '../../../utils/errors'
import { OverlapWarning } from '../components/OverlapWarning'
import { BalanceFreshnessBanner } from '../components/BalanceFreshnessBanner'
import type { InventoryBalanceSummary } from '../types/inventory-balances'

export function InventoryStockDashboardPage() {
  const navigate = useNavigate()
  const { currentContext } = useLogisticsAccess()
  const { hasPermission } = useLogisticsPermissions()
  const canView = hasPermission(LOGISTICS_PERMISSIONS.inventoryLedger.view)
  const organizationId = currentContext?.organization_id

  const summary = useQuery<InventoryBalanceSummary>(
    ['inventory-balances', 'dashboard', organizationId ?? ''],
    '/logistics/inventory/balances/summary',
    organizationId ? { organization_id: organizationId } : undefined,
    { enabled: canView && Boolean(organizationId) },
  )

  if (!canView) {
    return (
      <div className="space-y-4">
        <PageHeader title="Saldos de inventario" />
        <Alert variant="error">No tienes permisos para ver los saldos de inventario.</Alert>
      </div>
    )
  }

  if (!organizationId) {
    return (
      <div className="space-y-6 pb-10">
        <PageHeader
          eyebrow="Fase 045"
          title="Saldos de inventario"
          description="Consulta técnica de saldos derivados del libro de movimientos."
        />
        <Alert variant="info">Selecciona una organización para consultar sus saldos de inventario.</Alert>
      </div>
    )
  }

  return (
    <div className="space-y-6 pb-10">
      <PageHeader
        eyebrow="Fase 045"
        title="Saldos de inventario"
        description="Consulta técnica de saldos derivados del libro de movimientos."
        actions={
          <div className="flex gap-2">
            <Button onClick={() => navigate('/logistics/inventory/stock/products')}>
              Por producto
            </Button>
            <Button variant="secondary" onClick={() => navigate('/logistics/inventory/stock/warehouses')}>
              Por almacén
            </Button>
            <Button variant="secondary" onClick={() => navigate('/logistics/inventory/stock')}>
              Listado completo
            </Button>
          </div>
        }
      />

      <OverlapWarning />

      {summary.isLoading && <LoadingSkeleton rows={6} />}

      {summary.isError && (
        <Alert variant="error">{getErrorMessage(summary.error)}</Alert>
      )}

      {summary.data && (
        <>
          {summary.data.freshness_state !== 'CURRENT' && summary.data.freshness_state !== 'NEAR_REAL_TIME' && (
            <Alert variant="warning">
              La proyección de saldos tiene {summary.data.projection_lag_movements.toLocaleString('es-PE')} movimientos de retraso.
              Los datos pueden no reflejar el estado actual.
            </Alert>
          )}

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
            <MetricCard
              label="Productos con físico"
              value={summary.data.total_products}
              detail={`${summary.data.total_positions} posiciones`}
              icon="box"
              tone="primary"
            />
            <MetricCard
              label="Almacenes"
              value={summary.data.total_warehouses}
              detail={`${summary.data.total_locations} ubicaciones`}
              icon="dock"
              tone="neutral"
            />
            {summary.data.metrics.map((m) => (
              <MetricCard
                key={m.metric_code}
                label={m.label}
                value={m.count_products}
                detail={`${m.count_positions} posiciones`}
                icon={m.metric_code === 'PHYSICAL' ? 'box' : m.metric_code === 'AVAILABLE' ? 'check-square' : m.metric_code === 'RESERVED' ? 'clipboard' : m.metric_code === 'BLOCKED' ? 'lock' : m.metric_code === 'QUARANTINE' ? 'shield' : m.metric_code === 'TRANSIT' ? 'route' : m.metric_code === 'DAMAGED' ? 'alert' : m.metric_code === 'EXPIRED' ? 'timeline' : 'list'}
                tone={m.metric_code === 'PHYSICAL' ? 'primary' : m.metric_code === 'AVAILABLE' ? 'success' : m.metric_code === 'RESERVED' ? 'warning' : m.metric_code === 'BLOCKED' ? 'danger' : 'neutral'}
              />
            ))}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="bg-white border border-[#DDE4E8] rounded-[10px] p-4">
              <h3 className="text-xs font-semibold text-muted uppercase tracking-wide mb-2">Secuencia</h3>
              <p className="text-sm text-ink">
                Último MOV: <span className="font-medium">{summary.data.latest_movement_sequence?.toLocaleString('es-PE') ?? '—'}</span>
              </p>
              <p className="text-sm text-ink">
                Balance: <span className="font-medium">{summary.data.balance_sequence?.toLocaleString('es-PE') ?? '—'}</span>
              </p>
            </div>
            <div className="bg-white border border-[#DDE4E8] rounded-[10px] p-4">
              <h3 className="text-xs font-semibold text-muted uppercase tracking-wide mb-2">Calidad</h3>
              <p className="text-sm text-ink">{summary.data.data_quality}</p>
              <p className="text-xs text-muted">
                Corte: {new Date(summary.data.as_of).toLocaleString('es-PE')}
              </p>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
