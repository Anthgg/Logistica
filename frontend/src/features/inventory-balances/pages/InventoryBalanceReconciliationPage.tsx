import { useState } from 'react'
import { PageHeader } from '../../../components/common/PageHeader'
import { Alert } from '../../../components/common/Alert'
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton'
import { Button } from '../../../components/common/Button'
import { useQuery, useMutation } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsAccess } from '../../logistics-me/hooks/useLogisticsAccess'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { getErrorMessage } from '../../../utils/errors'
import { inventoryBalanceReconciliationApi, type CreateReconciliationRequest } from '../api/inventory-balance-reconciliation-api'
import type { InventoryBalanceReconciliationJob, InventoryBalanceReconciliationDifference } from '../types/inventory-balances'

export function InventoryBalanceReconciliationPage() {
  const { currentContext } = useLogisticsAccess()
  const { hasPermission } = useLogisticsPermissions()
  const canReconcile = hasPermission(LOGISTICS_PERMISSIONS.inventoryLedger.reconcile)
  const organizationId = currentContext?.organization_id

  const [selectedJobId, setSelectedJobId] = useState<string | null>(null)

  const jobs = useQuery<{ items: InventoryBalanceReconciliationJob[]; total: number }>(
    ['inventory-balances', 'reconciliation', organizationId ?? ''],
    '/logistics/inventory/balances/reconciliation',
    organizationId ? { organization_id: organizationId } : undefined,
    { enabled: Boolean(organizationId) },
  )

  const differences = useQuery<{ items: InventoryBalanceReconciliationDifference[]; total: number }>(
    ['inventory-balances', 'reconciliation-differences', selectedJobId ?? ''],
    `/logistics/inventory/balances/reconciliation/${selectedJobId}/differences`,
    undefined,
    { enabled: Boolean(selectedJobId) },
  )

  const createReconciliation = useMutation(
    async (input: CreateReconciliationRequest) => inventoryBalanceReconciliationApi.createReconciliation(input),
    {
      onSuccess: () => { void jobs.refetch() },
    },
  )

  const handleCreate = async () => {
    if (!organizationId) return
    await createReconciliation.mutate({ organization_id: organizationId })
  }

  return (
    <div className="space-y-6 pb-10">
      <PageHeader
        eyebrow="Fase 045"
        title="Reconciliación de saldos"
        description="Comparación de saldos proyectados contra replay del libro."
        actions={
          canReconcile ? (
            <Button onClick={handleCreate} disabled={createReconciliation.isPending}>
              {createReconciliation.isPending ? 'Creando...' : 'Nueva reconciliación'}
            </Button>
          ) : undefined
        }
      />

      {jobs.isLoading && <LoadingSkeleton rows={6} />}
      {jobs.isError && <Alert variant="error">{getErrorMessage(jobs.error)}</Alert>}

      {jobs.data && jobs.data.items.length === 0 && (
        <Alert variant="info">No hay reconciliaciones registradas.</Alert>
      )}

      {jobs.data && jobs.data.items.length > 0 && (
        <div className="space-y-3">
          {jobs.data.items.map((job) => (
            <div
              key={job.job_id}
              className={`bg-white border rounded-[10px] p-4 cursor-pointer transition-colors ${selectedJobId === job.job_id ? 'border-primary' : 'border-[#DDE4E8] hover:border-[#C8D4DC]'}`}
              onClick={() => setSelectedJobId(job.job_id)}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-medium text-ink">{job.job_id.slice(0, 8)}</span>
                <span className={`text-[10px] px-2 py-0.5 rounded-full border ${
                  job.status === 'COMPLETED' ? 'border-emerald-200 bg-emerald-50 text-emerald-700' :
                  job.status === 'RUNNING' ? 'border-blue-200 bg-blue-50 text-blue-700' :
                  job.status === 'FAILED' ? 'border-rose-200 bg-rose-50 text-rose-700' :
                  'border-slate-200 bg-slate-50 text-slate-600'
                }`}>{job.status}</span>
              </div>
              <div className="text-xs text-muted grid grid-cols-2 md:grid-cols-4 gap-2">
                <div>Diferencias: <span className="text-ink">{job.differences_count}</span></div>
                <div>Creado: <span className="text-ink">{new Date(job.created_at).toLocaleString('es-PE')}</span></div>
                {job.duration_ms && <div>Duración: <span className="text-ink">{(job.duration_ms / 1000).toFixed(1)}s</span></div>}
                {job.requested_by && <div>Solicitante: <span className="text-ink">{job.requested_by.display_name}</span></div>}
              </div>
            </div>
          ))}
        </div>
      )}

      {selectedJobId && differences.data && differences.data.items.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-semibold text-ink">Diferencias</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-xs border-collapse">
              <thead>
                <tr className="border-b border-[#DDE4E8]">
                  <th className="text-left py-2 px-2 font-semibold text-muted">Tipo</th>
                  <th className="text-left py-2 px-2 font-semibold text-muted">Producto</th>
                  <th className="text-left py-2 px-2 font-semibold text-muted">Almacén</th>
                  <th className="text-right py-2 px-2 font-semibold text-muted">Proyectado</th>
                  <th className="text-right py-2 px-2 font-semibold text-muted">Replay</th>
                  <th className="text-right py-2 px-2 font-semibold text-muted">Delta</th>
                  <th className="text-left py-2 px-2 font-semibold text-muted">Severidad</th>
                </tr>
              </thead>
              <tbody>
                {differences.data.items.map((d) => (
                  <tr key={d.difference_id} className="border-b border-[#EEF1F4]">
                    <td className="py-2 px-2 text-ink">{d.difference_type}</td>
                    <td className="py-2 px-2 text-ink">{d.product.sku}</td>
                    <td className="py-2 px-2 text-muted">{d.warehouse.code}</td>
                    <td className="py-2 px-2 text-right text-ink">{d.projected_quantity.value}</td>
                    <td className="py-2 px-2 text-right text-ink">{d.replay_quantity.value}</td>
                    <td className="py-2 px-2 text-right text-ink font-medium">{d.delta.value}</td>
                    <td className="py-2 px-2">
                      <span className={`text-[10px] px-2 py-0.5 rounded-full border ${
                        d.severity === 'CRITICAL' ? 'border-rose-200 bg-rose-50 text-rose-700' :
                        d.severity === 'HIGH' ? 'border-amber-200 bg-amber-50 text-amber-700' :
                        'border-slate-200 bg-slate-50 text-slate-600'
                      }`}>{d.severity}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
