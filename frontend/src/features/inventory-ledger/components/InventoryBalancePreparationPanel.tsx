import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { useQuery } from '../../inbound-docks/hooks/useQuery'
import { getErrorMessage } from '../../../utils/errors'
import { Alert } from '../../../components/common/Alert'
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton'
import type { InventoryBalancePreparationRow } from '../types/inventory-ledger'

interface Props {
  movementId: string
}

export function InventoryBalancePreparationPanel({ movementId }: Props) {
  const { hasPermission } = useLogisticsPermissions()
  const canView = hasPermission(LOGISTICS_PERMISSIONS.inventoryLedger.viewBalancePreparation)

  const rows = useQuery<InventoryBalancePreparationRow[]>(
    ['inventory-balance-preparation', movementId],
    `/logistics/inventory/movements/${movementId}/balance-preparation`,
    undefined,
    { enabled: canView && !!movementId },
  )

  if (!canView) return null

  return (
    <div className="bg-white p-4 rounded-lg border space-y-3">
      <Alert variant="info">
        Estos deltas alimentarán los saldos reconciliables de la Fase 045. Todavía no existe un saldo editable o definitivo.
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
                  MOV {r.movement_code} · Línea {r.line_id} · #{r.ledger_sequence}
                </div>
                <div className="text-xs text-gray-500">
                  Posición: {r.position.location?.code ?? r.position.external_boundary ?? '—'} · Estado: {r.availability_state} / {r.quality_state}
                </div>
              </div>
              <div className="text-right text-sm">
                <div>
                  <span className="text-green-600">+{r.entry_quantity.value}</span>
                  {' / '}
                  <span className="text-orange-600">-{r.exit_quantity.value}</span>
                </div>
                <div className="text-xs text-gray-500">
                  Δ {r.delta.value} {r.unit.symbol}
                </div>
                <div className="text-xs font-mono text-gray-400">
                  hash: {r.hash ?? '—'}
                </div>
                <div className="text-xs font-mono text-gray-400">
                  key: {r.materialization_key}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {rows.data && rows.data.length === 0 && (
        <div className="text-center py-4 text-gray-500">
          Sin deltas de preparación para este movimiento.
        </div>
      )}
    </div>
  )
}
