import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { PageHeader } from '../../../components/common/PageHeader'
import { Button } from '../../../components/common/Button'
import { Alert } from '../../../components/common/Alert'
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton'
import { StatusBadge } from '../../../components/common/StatusBadge'
import { useQuery } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsAccess } from '../../logistics-me/hooks/useLogisticsAccess'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { getErrorMessage } from '../../../utils/errors'
import { DecimalDisplay } from '../components/DecimalDisplay'
import { DataQualityBadge } from '../components/DataQualityBadge'
import { DrillDownDrawer } from '../components/DrillDownDrawer'
import type { InventoryPositionBalance, PaginatedResponse, InventoryBalanceFilters } from '../types/inventory-balances'

export function InventoryBalancesPage() {
  const navigate = useNavigate()
  const { currentContext } = useLogisticsAccess()
  const { hasPermission } = useLogisticsPermissions()
  const canView = hasPermission(LOGISTICS_PERMISSIONS.inventoryLedger.view)
  const organizationId = currentContext?.organization_id

  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [selectedBalance, setSelectedBalance] = useState<InventoryPositionBalance | null>(null)

  const filters: InventoryBalanceFilters = {
    organization_id: organizationId ?? '',
    page,
    page_size: 25,
    search: search || undefined,
  }

  const balances = useQuery<PaginatedResponse<InventoryPositionBalance>>(
    ['inventory-balances', 'list', organizationId ?? '', page, search],
    '/logistics/inventory/balances',
    organizationId ? filters : undefined,
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

  return (
    <div className="space-y-6 pb-10">
      <PageHeader
        eyebrow="Fase 045"
        title="Saldos de inventario"
        description="Listado completo de posiciones con sus métricas de saldo."
        actions={
          <Button onClick={() => navigate('/logistics/inventory/stock/products')}>
            Vista por producto
          </Button>
        }
      />

      <div className="flex gap-3 items-center">
        <input
          type="text"
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1) }}
          placeholder="Buscar por SKU, producto, almacén, posición..."
          className="flex-1 max-w-md text-sm border border-[#DDE4E8] rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-primary/30"
          aria-label="Buscar saldos"
        />
      </div>

      {balances.isLoading && <LoadingSkeleton rows={10} />}

      {balances.isError && (
        <Alert variant="error">{getErrorMessage(balances.error)}</Alert>
      )}

      {balances.data && balances.data.items.length === 0 && (
        <Alert variant="info">No se encontraron saldos para los filtros seleccionados.</Alert>
      )}

      {balances.data && balances.data.items.length > 0 && (
        <>
          <div className="overflow-x-auto">
            <table className="w-full text-xs border-collapse">
              <thead>
                <tr className="border-b border-[#DDE4E8]">
                  <th className="text-left py-2 px-2 font-semibold text-muted">SKU</th>
                  <th className="text-left py-2 px-2 font-semibold text-muted">Producto</th>
                  <th className="text-left py-2 px-2 font-semibold text-muted">Almacén</th>
                  <th className="text-left py-2 px-2 font-semibold text-muted">Ubicación</th>
                  <th className="text-right py-2 px-2 font-semibold text-muted">Físico</th>
                  <th className="text-right py-2 px-2 font-semibold text-muted">Disponible</th>
                  <th className="text-right py-2 px-2 font-semibold text-muted">Reservado</th>
                  <th className="text-right py-2 px-2 font-semibold text-muted">Bloqueado</th>
                  <th className="text-right py-2 px-2 font-semibold text-muted">Cuarentena</th>
                  <th className="text-right py-2 px-2 font-semibold text-muted">Tránsito</th>
                  <th className="text-right py-2 px-2 font-semibold text-muted">Dañado</th>
                  <th className="text-right py-2 px-2 font-semibold text-muted">Vencido</th>
                  <th className="text-left py-2 px-2 font-semibold text-muted">Calidad</th>
                  <th className="text-left py-2 px-2 font-semibold text-muted">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {balances.data.items.map((b) => (
                  <tr key={b.position_id} className="border-b border-[#EEF1F4] hover:bg-slate-50">
                    <td className="py-2 px-2 text-ink font-medium">{b.product.sku}</td>
                    <td className="py-2 px-2 text-ink">{b.product.name}</td>
                    <td className="py-2 px-2 text-ink">{b.warehouse.code}</td>
                    <td className="py-2 px-2 text-muted">{b.location?.code ?? '—'}</td>
                    <td className="py-2 px-2 text-right text-ink"><DecimalDisplay value={b.physical} /></td>
                    <td className="py-2 px-2 text-right text-ink"><DecimalDisplay value={b.available} /></td>
                    <td className="py-2 px-2 text-right text-ink"><DecimalDisplay value={b.reserved} /></td>
                    <td className="py-2 px-2 text-right text-ink"><DecimalDisplay value={b.blocked} /></td>
                    <td className="py-2 px-2 text-right text-ink"><DecimalDisplay value={b.quarantine} /></td>
                    <td className="py-2 px-2 text-right text-ink"><DecimalDisplay value={b.transit} /></td>
                    <td className="py-2 px-2 text-right text-ink"><DecimalDisplay value={b.damaged} /></td>
                    <td className="py-2 px-2 text-right text-ink"><DecimalDisplay value={b.expired} /></td>
                    <td className="py-2 px-2"><DataQualityBadge status={b.data_quality} /></td>
                    <td className="py-2 px-2">
                      <div className="flex gap-1">
                        <button
                          onClick={() => setSelectedBalance(b)}
                          className="text-primary hover:underline text-[10px]"
                        >
                          Detalle
                        </button>
                        <button
                          onClick={() => navigate(`/logistics/inventory/ledger/movements?product_id=${b.product_id}&warehouse_id=${b.warehouse_id}`)}
                          className="text-primary hover:underline text-[10px]"
                        >
                          MOV
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between text-xs text-muted">
            <span>
              {balances.data.total.toLocaleString('es-PE')} posiciones · Página {balances.data.page}
            </span>
            <div className="flex gap-2">
              <Button
                size="sm"
                variant="secondary"
                disabled={!balances.data.has_previous}
                onClick={() => setPage((p) => p - 1)}
              >
                Anterior
              </Button>
              <Button
                size="sm"
                variant="secondary"
                disabled={!balances.data.has_next}
                onClick={() => setPage((p) => p + 1)}
              >
                Siguiente
              </Button>
            </div>
          </div>
        </>
      )}

      {selectedBalance && (
        <DrillDownDrawer balance={selectedBalance} onClose={() => setSelectedBalance(null)} />
      )}
    </div>
  )
}
