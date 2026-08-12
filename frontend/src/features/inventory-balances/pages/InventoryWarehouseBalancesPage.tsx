import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { PageHeader } from '../../../components/common/PageHeader'
import { Alert } from '../../../components/common/Alert'
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton'
import { useQuery } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsAccess } from '../../logistics-me/hooks/useLogisticsAccess'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { getErrorMessage } from '../../../utils/errors'
import { DataQualityBadge } from '../components/DataQualityBadge'
import type { InventoryWarehouseBalance, PaginatedResponse, InventoryBalanceFilters } from '../types/inventory-balances'

export function InventoryWarehouseBalancesPage() {
  const navigate = useNavigate()
  const { currentContext } = useLogisticsAccess()
  const { hasPermission } = useLogisticsPermissions()
  const canView = hasPermission(LOGISTICS_PERMISSIONS.inventoryLedger.view)
  const organizationId = currentContext?.organization_id

  const [page, setPage] = useState(1)

  const filters: InventoryBalanceFilters = {
    organization_id: organizationId ?? '',
    page,
    page_size: 25,
  }

  const warehouses = useQuery<PaginatedResponse<InventoryWarehouseBalance>>(
    ['inventory-balances', 'warehouses', organizationId ?? '', page],
    '/logistics/inventory/balances/warehouses',
    organizationId ? filters : undefined,
    { enabled: canView && Boolean(organizationId) },
  )

  if (!canView) {
    return (
      <div className="space-y-4">
        <PageHeader title="Saldos por almacén" />
        <Alert variant="error">No tienes permisos para ver los saldos de inventario.</Alert>
      </div>
    )
  }

  return (
    <div className="space-y-6 pb-10">
      <PageHeader
        eyebrow="Fase 045"
        title="Saldos por almacén"
        description="Vista consolidada de saldos por almacén."
      />

      {warehouses.isLoading && <LoadingSkeleton rows={8} />}

      {warehouses.isError && (
        <Alert variant="error">{getErrorMessage(warehouses.error)}</Alert>
      )}

      {warehouses.data && warehouses.data.items.length === 0 && (
        <Alert variant="info">No se encontraron almacenes con saldo.</Alert>
      )}

      {warehouses.data && warehouses.data.items.length > 0 && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {warehouses.data.items.map((w) => (
              <div
                key={w.warehouse_id}
                className="bg-white border border-[#DDE4E8] rounded-[10px] p-4 hover:shadow-sm transition-shadow cursor-pointer"
                onClick={() => navigate(`/logistics/inventory/stock/warehouses/${w.warehouse_id}`)}
              >
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-sm font-semibold text-ink">{w.warehouse.name}</h3>
                  <DataQualityBadge status={w.data_quality} />
                </div>
                <p className="text-xs text-muted mb-3">{w.warehouse.code}</p>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div>Productos: <span className="font-medium text-ink">{w.product_count}</span></div>
                  <div>Ubicaciones: <span className="font-medium text-ink">{w.location_count}</span></div>
                  <div>Disponibles: <span className="font-medium text-ink">{w.available_products}</span></div>
                  <div>Reservados: <span className="font-medium text-ink">{w.reserved_products}</span></div>
                  <div>Bloqueados: <span className="font-medium text-ink">{w.blocked_products}</span></div>
                  <div>Cuarentena: <span className="font-medium text-ink">{w.quarantine_products}</span></div>
                </div>
                {w.projection_lag_movements > 0 && (
                  <p className="text-[10px] text-amber-600 mt-2">
                    Lag: {w.projection_lag_movements.toLocaleString('es-PE')} movimientos
                  </p>
                )}
              </div>
            ))}
          </div>

          <div className="flex items-center justify-between text-xs text-muted">
            <span>{warehouses.data.total.toLocaleString('es-PE')} almacenes</span>
            <div className="flex gap-2">
              <button
                disabled={!warehouses.data.has_previous}
                onClick={() => setPage((p) => p - 1)}
                className="px-3 py-1 border rounded text-ink disabled:opacity-50"
              >
                Anterior
              </button>
              <button
                disabled={!warehouses.data.has_next}
                onClick={() => setPage((p) => p + 1)}
                className="px-3 py-1 border rounded text-ink disabled:opacity-50"
              >
                Siguiente
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
