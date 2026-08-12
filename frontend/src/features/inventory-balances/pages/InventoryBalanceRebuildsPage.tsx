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
import { inventoryBalanceRebuildApi, type CreateRebuildRequest } from '../api/inventory-balance-rebuild-api'
import type { InventoryBalanceRebuildJob } from '../types/inventory-balances'

export function InventoryBalanceRebuildsPage() {
  const { currentContext } = useLogisticsAccess()
  const { hasPermission } = useLogisticsPermissions()
  const canRebuild = hasPermission(LOGISTICS_PERMISSIONS.inventoryLedger.reconcile)
  const organizationId = currentContext?.organization_id

  const [selectedJobId, setSelectedJobId] = useState<string | null>(null)

  const rebuilds = useQuery<{ items: InventoryBalanceRebuildJob[]; total: number }>(
    ['inventory-balances', 'rebuilds', organizationId ?? ''],
    '/logistics/inventory/balances/rebuilds',
    organizationId ? { organization_id: organizationId } : undefined,
    { enabled: Boolean(organizationId) },
  )

  const selectedJob = useQuery<InventoryBalanceRebuildJob>(
    ['inventory-balances', 'rebuild', selectedJobId ?? ''],
    `/logistics/inventory/balances/rebuilds/${selectedJobId}`,
    undefined,
    { enabled: Boolean(selectedJobId) },
  )

  const createRebuild = useMutation(
    async (input: CreateRebuildRequest) => inventoryBalanceRebuildApi.createRebuild(input),
    { onSuccess: () => { void rebuilds.refetch() } },
  )

  const handleCreate = async () => {
    if (!organizationId) return
    await createRebuild.mutate({
      organization_id: organizationId,
      rebuild_type: 'PARTITION',
      scope: organizationId,
    })
  }

  return (
    <div className="space-y-6 pb-10">
      <PageHeader
        eyebrow="Fase 045"
        title="Rebuilds de saldo"
        description="Reconstrucción de saldos desde el libro de movimientos."
        actions={
          canRebuild ? (
            <Button onClick={handleCreate} disabled={createRebuild.isPending}>
              {createRebuild.isPending ? 'Creando...' : 'Nuevo rebuild'}
            </Button>
          ) : undefined
        }
      />

      {rebuilds.isLoading && <LoadingSkeleton rows={6} />}
      {rebuilds.isError && <Alert variant="error">{getErrorMessage(rebuilds.error)}</Alert>}

      {rebuilds.data && rebuilds.data.items.length === 0 && (
        <Alert variant="info">No hay rebuilds registrados.</Alert>
      )}

      {rebuilds.data && rebuilds.data.items.length > 0 && (
        <div className="space-y-3">
          {rebuilds.data.items.map((r) => (
            <div
              key={r.job_id}
              className={`bg-white border rounded-[10px] p-4 cursor-pointer transition-colors ${selectedJobId === r.job_id ? 'border-primary' : 'border-[#DDE4E8] hover:border-[#C8D4DC]'}`}
              onClick={() => setSelectedJobId(r.job_id)}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-medium text-ink">{r.job_id.slice(0, 8)}</span>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-muted">{r.rebuild_type}</span>
                  <span className={`text-[10px] px-2 py-0.5 rounded-full border ${
                    r.status === 'COMPLETED' ? 'border-emerald-200 bg-emerald-50 text-emerald-700' :
                    r.status === 'RUNNING' ? 'border-blue-200 bg-blue-50 text-blue-700' :
                    r.status === 'FAILED' ? 'border-rose-200 bg-rose-50 text-rose-700' :
                    'border-slate-200 bg-slate-50 text-slate-600'
                  }`}>{r.status}</span>
                </div>
              </div>
              <div className="text-xs text-muted grid grid-cols-2 md:grid-cols-4 gap-2">
                <div>Posiciones: <span className="text-ink">{r.positions_processed}</span></div>
                <div>Diferencias: <span className="text-ink">{r.differences_found}</span></div>
                {r.progress_percent != null && <div>Progreso: <span className="text-ink">{r.progress_percent}%</span></div>}
                {r.duration_ms && <div>Duración: <span className="text-ink">{(r.duration_ms / 1000).toFixed(1)}s</span></div>}
              </div>
              {r.status === 'RUNNING' && r.progress_percent != null && (
                <div className="mt-2 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                  <div className="h-full bg-primary rounded-full transition-all" style={{ width: `${r.progress_percent}%` }} />
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {selectedJob.data && (
        <div className="bg-white border border-[#DDE4E8] rounded-[10px] p-4 text-xs space-y-2">
          <h3 className="text-sm font-semibold text-ink">Detalle del rebuild</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
            <div>Tipo: <span className="text-ink">{selectedJob.data.rebuild_type}</span></div>
            <div>Alcance: <span className="text-ink">{selectedJob.data.scope}</span></div>
            <div>Secuencia inicial: <span className="text-ink">{selectedJob.data.initial_sequence ?? '—'}</span></div>
            <div>Secuencia final: <span className="text-ink">{selectedJob.data.final_sequence ?? '—'}</span></div>
            <div>Movimientos procesados: <span className="text-ink">{selectedJob.data.movements_processed}</span></div>
            <div>Throughput: <span className="text-ink">{selectedJob.data.throughput_per_second?.toFixed(1) ?? '—'} /s</span></div>
          </div>
          {selectedJob.data.error_message && (
            <p className="text-rose-600 mt-2">{selectedJob.data.error_message}</p>
          )}
        </div>
      )}
    </div>
  )
}
