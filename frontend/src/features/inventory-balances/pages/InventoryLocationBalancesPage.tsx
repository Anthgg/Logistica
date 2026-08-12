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
import type { InventoryLocationBalance, PaginatedResponse, InventoryBalanceFilters } from '../types/inventory-balances'

export function InventoryLocationBalancesPage() {
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

  const locations = useQuery<PaginatedResponse<InventoryLocationBalance>>(
    ['inventory-balances', 'locations', organizationId ?? '', page, search],
    '/logistics/inventory/balances/locations',
    organizationId ? filters : undefined,
    { enabled: canView && Boolean(organizationId) },
  )

  if (!canView) {
    return (
      <div className="space-y-4">
        <PageHeader title="Saldos por ubicación" />
        <Alert variant="error">No tienes permisos para ver los saldos de inventario.</Alert>
      </div>
    )
  }

  return (
    <div className="space-y-6 pb-10">
      <PageHeader
        eyebrow="Fase 045"
        title="Saldos por ubicación"
        description="Saldos de inventario por ubicación física."
      />

      <div className="flex gap-3 items-center">
        <input
          type="text"
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1) }}
          placeholder="Buscar por ubicación, zona, producto..."
          className="flex-1 max-w-md text-sm border border-[#DDE4E8] rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-primary/30"
          aria-label="Buscar ubicaciones"
        />
      </div>

      {locations.isLoading && <LoadingSkeleton rows={10} />}

      {locations.isError && (
        <Alert variant="error">{getErrorMessage(locations.error)}</Alert>
      )}

      {locations.data && locations.data.items.length === 0 && (
        <Alert variant="info">No se encontraron ubicaciones con saldo.</Alert>
      )}

      {locations.data && locations.data.items.length > 0 && (
        <>
          <div className="overflow-x-auto">
            <table className="w-full text-xs border-collapse">
              <thead>
                <tr className="border-b border-[#DDE4E8]">
                  <th className="text-left py-2 px-2 font-semibold text-muted">Ubicación</th>
                  <th className="text-left py-2 px-2 font-semibold text-muted">Zona</th>
                  <th className="text-left py-2 px-2 font-semibold text-muted">Almacén</th>
                  <th className="text-left py-2 px-2 font-semibold text-muted">Producto</th>
                  <th className="text-left py-2 px-2 font-semibold text-muted">SKU</th>
                  <th className="text-right py-2 px-2 font-semibold text-muted">Físico</th>
                  <th className="text-right py-2 px-2 font-semibold text-muted">Disponible</th>
                  <th className="text-right py-2 px-2 font-semibold text-muted">Reservado</th>
                  <th className="text-right py-2 px-2 font-semibold text-muted">Bloqueado</th>
                  <th className="text-left py-2 px-2 font-semibold text-muted">Estado</th>
                  <th className="text-left py-2 px-2 font-semibold text-muted">Calidad</th>
                  <th className="text-left py-2 px-2 font-semibold text-muted">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {locations.data.items.map((l) => (
                  <tr key={`${l.location_id}-${l.product_id}`} className="border-b border-[#EEF1F4] hover:bg-slate-50">
                    <td className="py-2 px-2 text-ink font-medium">{l.location.code}</td>
                    <td className="py-2 px-2 text-muted">{l.location.zone ?? '—'}</td>
                    <td className="py-2 px-2 text-muted">{l.warehouse.code}</td>
                    <td className="py-2 px-2 text-ink">{l.product.name}</td>
                    <td className="py-2 px-2 text-muted">{l.product.sku}</td>
                    <td className="py-2 px-2 text-right text-ink"><DecimalDisplay value={l.physical} /></td>
                    <td className="py-2 px-2 text-right text-ink"><DecimalDisplay value={l.available} /></td>
                    <td className="py-2 px-2 text-right text-ink"><DecimalDisplay value={l.reserved} /></td>
                    <td className="py-2 px-2 text-right text-ink"><DecimalDisplay value={l.blocked} /></td>
                    <td className="py-2 px-2"><span className="text-[10px]">{l.availability_state}</span></td>
                    <td className="py-2 px-2"><DataQualityBadge status={l.data_quality} /></td>
                    <td className="py-2 px-2">
                      <button
                        onClick={() => navigate(`/logistics/inventory/stock/locations/${l.location_id}`)}
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
            <span>{locations.data.total.toLocaleString('es-PE')} registros</span>
            <div className="flex gap-2">
              <button
                disabled={!locations.data.has_previous}
                onClick={() => setPage((p) => p - 1)}
                className="px-3 py-1 border rounded text-ink disabled:opacity-50"
              >
                Anterior
              </button>
              <button
                disabled={!locations.data.has_next}
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
