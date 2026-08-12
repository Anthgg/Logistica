import { PageHeader } from '../../../components/common/PageHeader'
import { Alert } from '../../../components/common/Alert'
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton'
import { Button } from '../../../components/common/Button'
import { useQuery } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsAccess } from '../../logistics-me/hooks/useLogisticsAccess'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { getErrorMessage } from '../../../utils/errors'
import type { InventoryBalanceCheckpoint } from '../types/inventory-balances'

export function InventoryBalanceCheckpointsPage() {
  const { currentContext } = useLogisticsAccess()
  const { hasPermission } = useLogisticsPermissions()
  const canCreate = hasPermission(LOGISTICS_PERMISSIONS.inventoryLedger.createCheckpoint)
  const organizationId = currentContext?.organization_id

  const checkpoints = useQuery<{ items: InventoryBalanceCheckpoint[]; total: number }>(
    ['inventory-balances', 'checkpoints', organizationId ?? ''],
    '/logistics/inventory/balances/checkpoints',
    organizationId ? { organization_id: organizationId } : undefined,
    { enabled: Boolean(organizationId) },
  )

  return (
    <div className="space-y-6 pb-10">
      <PageHeader
        eyebrow="Fase 045"
        title="Checkpoints de saldo"
        description="Instantáneas del estado de saldos para reconstrucciones parciales."
        actions={
          canCreate ? (
            <Button onClick={() => {}}>
              Crear checkpoint
            </Button>
          ) : undefined
        }
      />

      {checkpoints.isLoading && <LoadingSkeleton rows={6} />}
      {checkpoints.isError && <Alert variant="error">{getErrorMessage(checkpoints.error)}</Alert>}

      {checkpoints.data && checkpoints.data.items.length === 0 && (
        <Alert variant="info">No hay checkpoints registrados.</Alert>
      )}

      {checkpoints.data && checkpoints.data.items.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-xs border-collapse">
            <thead>
              <tr className="border-b border-[#DDE4E8]">
                <th className="text-left py-2 px-2 font-semibold text-muted">Partición</th>
                <th className="text-right py-2 px-2 font-semibold text-muted">Secuencia</th>
                <th className="text-right py-2 px-2 font-semibold text-muted">Posiciones</th>
                <th className="text-right py-2 px-2 font-semibold text-muted">Productos</th>
                <th className="text-left py-2 px-2 font-semibold text-muted">Fórmula</th>
                <th className="text-left py-2 px-2 font-semibold text-muted">Estado</th>
                <th className="text-left py-2 px-2 font-semibold text-muted">Creado</th>
                <th className="text-left py-2 px-2 font-semibold text-muted">Verificado</th>
              </tr>
            </thead>
            <tbody>
              {checkpoints.data.items.map((c) => (
                <tr key={c.checkpoint_id} className="border-b border-[#EEF1F4]">
                  <td className="py-2 px-2 text-ink font-medium">{c.partition_key}</td>
                  <td className="py-2 px-2 text-right text-ink">{c.sequence.toLocaleString('es-PE')}</td>
                  <td className="py-2 px-2 text-right text-ink">{c.position_count}</td>
                  <td className="py-2 px-2 text-right text-ink">{c.product_count}</td>
                  <td className="py-2 px-2 text-muted">{c.formula_version}</td>
                  <td className="py-2 px-2">
                    <span className={`text-[10px] px-2 py-0.5 rounded-full border ${
                      c.status === 'VALID' ? 'border-emerald-200 bg-emerald-50 text-emerald-700' :
                      c.status === 'INVALID' ? 'border-rose-200 bg-rose-50 text-rose-700' :
                      'border-slate-200 bg-slate-50 text-slate-600'
                    }`}>{c.status}</span>
                  </td>
                  <td className="py-2 px-2 text-muted">{new Date(c.created_at).toLocaleString('es-PE')}</td>
                  <td className="py-2 px-2 text-muted">{c.verified_at ? new Date(c.verified_at).toLocaleString('es-PE') : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
