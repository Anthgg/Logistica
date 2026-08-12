import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { useQuery } from '../../inbound-docks/hooks/useQuery'
import { getErrorMessage } from '../../../utils/errors'
import { Alert } from '../../../components/common/Alert'
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton'
import type { InventoryTraceabilityPreparationRow } from '../types/inventory-ledger'

interface Props {
  movementId: string
}

export function InventoryTraceabilityPreparationPanel({ movementId }: Props) {
  const { hasPermission } = useLogisticsPermissions()
  const canView = hasPermission(LOGISTICS_PERMISSIONS.inventoryLedger.viewTraceabilityPreparation)

  const rows = useQuery<InventoryTraceabilityPreparationRow[]>(
    ['inventory-traceability-preparation', movementId],
    `/logistics/inventory/movements/${movementId}/traceability-preparation`,
    undefined,
    { enabled: canView && !!movementId },
  )

  if (!canView) return null

  return (
    <div className="bg-white p-4 rounded-lg border space-y-3">
      <Alert variant="info">
        Las entidades definitivas de lote, serie, caja, pallet y contenedor se crearán en la Fase 046.
      </Alert>

      {rows.isLoading && <LoadingSkeleton rows={3} />}

      {rows.isError && (
        <Alert variant="error">{getErrorMessage(rows.error)}</Alert>
      )}

      {rows.data && rows.data.length > 0 && (
        <div className="space-y-1">
          {rows.data.map((r) => (
            <div key={r.row_id} className="flex items-center justify-between p-2 bg-gray-50 rounded text-sm">
              <div>
                <div className="font-medium">{r.product.sku}</div>
                <div className="text-xs text-gray-500 font-mono">
                  MOV {r.movement_code} · Línea {r.line_id}
                </div>
                <div className="text-xs text-gray-500">
                  {r.origin.location?.code ?? r.origin.external_boundary ?? '—'} →{' '}
                  {r.destination.location?.code ?? r.destination.external_boundary ?? '—'}
                </div>
                <div className="text-xs text-gray-500">
                  Lotes observados: {r.observed_lots.length > 0 ? r.observed_lots.join(', ') : '—'}
                </div>
                <div className="text-xs text-gray-500">
                  Series observadas: {r.observed_serials.length > 0 ? '•••' : '—'}
                </div>
                {r.packaging_type && (
                  <div className="text-xs text-gray-500">Empaque: {r.packaging_type}</div>
                )}
                {r.logistics_unit_reference && (
                  <div className="text-xs text-gray-500">Unidad logística: {r.logistics_unit_reference}</div>
                )}
              </div>
              <div className="text-right text-sm">
                <div>{r.quantity.value} {r.unit.symbol}</div>
                <div className="text-xs font-mono text-gray-400">hash: {r.hash ?? '—'}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {rows.data && rows.data.length === 0 && (
        <div className="text-center py-4 text-gray-500">
          Sin preparación de trazabilidad para este movimiento.
        </div>
      )}
    </div>
  )
}
