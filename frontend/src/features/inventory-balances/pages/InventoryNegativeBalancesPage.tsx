import { useState } from 'react'
import { PageHeader } from '../../../components/common/PageHeader'
import { Alert } from '../../../components/common/Alert'
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton'
import { useQuery } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsAccess } from '../../logistics-me/hooks/useLogisticsAccess'
import { getErrorMessage } from '../../../utils/errors'
import { DecimalDisplay } from '../components/DecimalDisplay'
import type { InventoryPositionBalance, PaginatedResponse, InventoryBalanceFilters } from '../types/inventory-balances'

export function InventoryNegativeBalancesPage() {
  const { currentContext } = useLogisticsAccess()
  const organizationId = currentContext?.organization_id

  const [page, setPage] = useState(1)

  const negatives = useQuery<PaginatedResponse<InventoryPositionBalance>>(
    ['inventory-balances', 'negatives', organizationId ?? '', page],
    '/logistics/inventory/balances',
    organizationId ? {
      organization_id: organizationId,
      is_negative: true,
      page,
      page_size: 25,
    } : undefined,
    { enabled: Boolean(organizationId) },
  )

  return (
    <div className="space-y-6 pb-10">
      <PageHeader
        eyebrow="Fase 045"
        title="Saldos negativos"
        description="Posiciones con cantidades negativas. Requieren investigación."
      />

      <Alert variant="warning">
        Los saldos negativos son incidencias reales. No se ofrecen ajustes desde esta vista.
        Los ajustes pertenecen a una fase posterior.
      </Alert>

      {negatives.isLoading && <LoadingSkeleton rows={8} />}
      {negatives.isError && <Alert variant="error">{getErrorMessage(negatives.error)}</Alert>}

      {negatives.data && negatives.data.items.length === 0 && (
        <Alert variant="info">No se encontraron saldos negativos.</Alert>
      )}

      {negatives.data && negatives.data.items.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-xs border-collapse">
            <thead>
              <tr className="border-b border-[#DDE4E8]">
                <th className="text-left py-2 px-2 font-semibold text-muted">Producto</th>
                <th className="text-left py-2 px-2 font-semibold text-muted">Almacén</th>
                <th className="text-left py-2 px-2 font-semibold text-muted">Ubicación</th>
                <th className="text-left py-2 px-2 font-semibold text-muted">Posición</th>
                <th className="text-right py-2 px-2 font-semibold text-muted">Cantidad</th>
                <th className="text-left py-2 px-2 font-semibold text-muted">Unidad</th>
                <th className="text-left py-2 px-2 font-semibold text-muted">Último MOV</th>
                <th className="text-left py-2 px-2 font-semibold text-muted">Reconciliación</th>
              </tr>
            </thead>
            <tbody>
              {negatives.data.items.map((n) => (
                <tr key={n.position_id} className="border-b border-[#EEF1F4]">
                  <td className="py-2 px-2 text-ink">{n.product.name} ({n.product.sku})</td>
                  <td className="py-2 px-2 text-muted">{n.warehouse.code}</td>
                  <td className="py-2 px-2 text-muted">{n.location?.code ?? '—'}</td>
                  <td className="py-2 px-2 text-muted font-mono">{n.position_id_display}</td>
                  <td className="py-2 px-2 text-right text-rose-600 font-medium"><DecimalDisplay value={n.physical} /></td>
                  <td className="py-2 px-2 text-muted">{n.unit.code}</td>
                  <td className="py-2 px-2 text-muted">{n.last_movement?.movement_code ?? '—'}</td>
                  <td className="py-2 px-2 text-muted">{n.reconciliation_status ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
