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
import { DecimalDisplay } from '../components/DecimalDisplay'
import { DataQualityBadge } from '../components/DataQualityBadge'
import type { InventoryProductBalance, PaginatedResponse, InventoryBalanceFilters } from '../types/inventory-balances'

export function InventoryProductBalancesPage() {
  const navigate = useNavigate()
  const { currentContext } = useLogisticsAccess()
  const { hasPermission } = useLogisticsPermissions()
  const canView = hasPermission(LOGISTICS_PERMISSIONS.inventoryLedger.view)
  const organizationId = currentContext?.organization_id

  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')

  const filters: InventoryBalanceFilters = {
    organization_id: organizationId ?? '',
    page,
    page_size: 25,
    search: search || undefined,
  }

  const products = useQuery<PaginatedResponse<InventoryProductBalance>>(
    ['inventory-balances', 'products', organizationId ?? '', page, search],
    '/logistics/inventory/balances/products',
    organizationId ? filters : undefined,
    { enabled: canView && Boolean(organizationId) },
  )

  if (!canView) {
    return (
      <div className="space-y-4">
        <PageHeader title="Saldos por producto" />
        <Alert variant="error">No tienes permisos para ver los saldos de inventario.</Alert>
      </div>
    )
  }

  return (
    <div className="space-y-6 pb-10">
      <PageHeader
        eyebrow="Fase 045"
        title="Saldos por producto"
        description="Saldo consolidado agrupado por producto."
      />

      <div className="flex gap-3 items-center">
        <input
          type="text"
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1) }}
          placeholder="Buscar por SKU o nombre de producto..."
          className="flex-1 max-w-md text-sm border border-[#DDE4E8] rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-primary/30"
          aria-label="Buscar productos"
        />
      </div>

      {products.isLoading && <LoadingSkeleton rows={10} />}

      {products.isError && (
        <Alert variant="error">{getErrorMessage(products.error)}</Alert>
      )}

      {products.data && products.data.items.length === 0 && (
        <Alert variant="info">No se encontraron productos con saldo.</Alert>
      )}

      {products.data && products.data.items.length > 0 && (
        <>
          <div className="overflow-x-auto">
            <table className="w-full text-xs border-collapse">
              <thead>
                <tr className="border-b border-[#DDE4E8]">
                  <th className="text-left py-2 px-2 font-semibold text-muted">SKU</th>
                  <th className="text-left py-2 px-2 font-semibold text-muted">Producto</th>
                  <th className="text-left py-2 px-2 font-semibold text-muted">Unidad</th>
                  <th className="text-left py-2 px-2 font-semibold text-muted">Almacenes</th>
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
                {products.data.items.map((p) => (
                  <tr key={p.product_id} className="border-b border-[#EEF1F4] hover:bg-slate-50">
                    <td className="py-2 px-2 text-ink font-medium">{p.product.sku}</td>
                    <td className="py-2 px-2 text-ink">{p.product.name}</td>
                    <td className="py-2 px-2 text-muted">{p.unit.code}</td>
                    <td className="py-2 px-2 text-muted">{p.warehouse_count}</td>
                    <td className="py-2 px-2 text-right text-ink"><DecimalDisplay value={p.physical} /></td>
                    <td className="py-2 px-2 text-right text-ink"><DecimalDisplay value={p.available} /></td>
                    <td className="py-2 px-2 text-right text-ink"><DecimalDisplay value={p.reserved} /></td>
                    <td className="py-2 px-2 text-right text-ink"><DecimalDisplay value={p.blocked} /></td>
                    <td className="py-2 px-2 text-right text-ink"><DecimalDisplay value={p.quarantine} /></td>
                    <td className="py-2 px-2 text-right text-ink"><DecimalDisplay value={p.transit} /></td>
                    <td className="py-2 px-2 text-right text-ink"><DecimalDisplay value={p.damaged} /></td>
                    <td className="py-2 px-2 text-right text-ink"><DecimalDisplay value={p.expired} /></td>
                    <td className="py-2 px-2"><DataQualityBadge status={p.data_quality} /></td>
                    <td className="py-2 px-2">
                      <button
                        onClick={() => navigate(`/logistics/inventory/stock/products/${p.product_id}`)}
                        className="text-primary hover:underline text-[10px]"
                      >
                        Detalle
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between text-xs text-muted">
            <span>{products.data.total.toLocaleString('es-PE')} productos</span>
            <div className="flex gap-2">
              <button
                disabled={!products.data.has_previous}
                onClick={() => setPage((p) => p - 1)}
                className="px-3 py-1 border rounded text-ink disabled:opacity-50"
              >
                Anterior
              </button>
              <button
                disabled={!products.data.has_next}
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
