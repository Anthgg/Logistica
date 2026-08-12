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
import { DrillDownDrawer } from '../components/DrillDownDrawer'
import type { InventoryPositionBalance, PaginatedResponse, InventoryBalanceFilters } from '../types/inventory-balances'

export function InventoryPositionsBalancesPage() {
  const navigate = useNavigate()
  const { currentContext } = useLogisticsAccess()
  const { hasPermission } = useLogisticsPermissions()
  const canView = hasPermission(LOGISTICS_PERMISSIONS.inventoryLedger.view)
  const organizationId = currentContext?.organization_id

  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [selectedPosition, setSelectedPosition] = useState<InventoryPositionBalance | null>(null)

  const filters: InventoryBalanceFilters = {
    organization_id: organizationId ?? '',
    page,
    page_size: 25,
    search: search || undefined,
  }

  const positions = useQuery<PaginatedResponse<InventoryPositionBalance>>(
    ['inventory-balances', 'positions', organizationId ?? '', page, search],
    '/logistics/inventory/balances/positions',
    organizationId ? filters : undefined,
    { enabled: canView && Boolean(organizationId) },
  )

  if (!canView) {
    return (
      <div className="space-y-4">
        <PageHeader title="Saldos por posición" />
        <Alert variant="error">No tienes permisos para ver los saldos de inventario.</Alert>
      </div>
    )
  }

  return (
    <div className="space-y-6 pb-10">
      <PageHeader
        eyebrow="Fase 045"
        title="Saldos por posición"
        description="Vista técnica más precisa. Cada fila es una posición individual."
      />

      <div className="flex gap-3 items-center">
        <input
          type="text"
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1) }}
          placeholder="Buscar por posición, producto, almacén..."
          className="flex-1 max-w-md text-sm border border-[#DDE4E8] rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-primary/30"
          aria-label="Buscar posiciones"
        />
      </div>

      {positions.isLoading && <LoadingSkeleton rows={10} />}

      {positions.isError && (
        <Alert variant="error">{getErrorMessage(positions.error)}</Alert>
      )}

      {positions.data && positions.data.items.length === 0 && (
        <Alert variant="info">No se encontraron posiciones con saldo.</Alert>
      )}

      {positions.data && positions.data.items.length > 0 && (
        <>
          <div className="overflow-x-auto">
            <table className="w-full text-xs border-collapse">
              <thead>
                <tr className="border-b border-[#DDE4E8]">
                  <th className="text-left py-2 px-2 font-semibold text-muted">Posición</th>
                  <th className="text-left py-2 px-2 font-semibold text-muted">Producto</th>
                  <th className="text-left py-2 px-2 font-semibold text-muted">Almacén</th>
                  <th className="text-left py-2 px-2 font-semibold text-muted">Ubicación</th>
                  <th className="text-right py-2 px-2 font-semibold text-muted">Cantidad</th>
                  <th className="text-left py-2 px-2 font-semibold text-muted">Unidad</th>
                  <th className="text-left py-2 px-2 font-semibold text-muted">Estado</th>
                  <th className="text-left py-2 px-2 font-semibold text-muted">Calidad</th>
                  <th className="text-left py-2 px-2 font-semibold text-muted">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {positions.data.items.map((pos) => (
                  <tr key={pos.position_id} className="border-b border-[#EEF1F4] hover:bg-slate-50">
                    <td className="py-2 px-2 text-ink font-medium font-mono text-[10px]">{pos.position_id_display}</td>
                    <td className="py-2 px-2 text-ink">{pos.product.name}</td>
                    <td className="py-2 px-2 text-muted">{pos.warehouse.code}</td>
                    <td className="py-2 px-2 text-muted">{pos.location?.code ?? '—'}</td>
                    <td className="py-2 px-2 text-right text-ink"><DecimalDisplay value={pos.physical} /></td>
                    <td className="py-2 px-2 text-muted">{pos.unit.code}</td>
                    <td className="py-2 px-2"><span className="text-[10px]">{pos.availability_state}</span></td>
                    <td className="py-2 px-2"><DataQualityBadge status={pos.data_quality} /></td>
                    <td className="py-2 px-2">
                      <div className="flex gap-1">
                        <button
                          onClick={() => setSelectedPosition(pos)}
                          className="text-primary hover:underline text-[10px]"
                        >
                          Detalle
                        </button>
                        <button
                          onClick={() => navigate(`/logistics/inventory/stock/positions/${pos.position_id}`)}
                          className="text-primary hover:underline text-[10px]"
                        >
                          Ver
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between text-xs text-muted">
            <span>{positions.data.total.toLocaleString('es-PE')} posiciones</span>
            <div className="flex gap-2">
              <button
                disabled={!positions.data.has_previous}
                onClick={() => setPage((p) => p - 1)}
                className="px-3 py-1 border rounded text-ink disabled:opacity-50"
              >
                Anterior
              </button>
              <button
                disabled={!positions.data.has_next}
                onClick={() => setPage((p) => p + 1)}
                className="px-3 py-1 border rounded text-ink disabled:opacity-50"
              >
                Siguiente
              </button>
            </div>
          </div>
        </>
      )}

      {selectedPosition && (
        <DrillDownDrawer balance={selectedPosition} onClose={() => setSelectedPosition(null)} />
      )}
    </div>
  )
}
