import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { PageHeader } from '../../../components/common/PageHeader'
import { Button } from '../../../components/common/Button'
import { useLogisticsContextSelector } from '../../logistics-permissions/hooks/useLogisticsContextSelector'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { DockQueueFilters, type QueueFilter } from '../components/Filters'
import { InboundDockQueueTable } from '../components/InboundDockQueueTable'
import { ChangeDockQueuePriorityDialog } from '../components/dialogs/ChangeDockQueuePriorityDialog'
import { DockOperationsServerClock } from '../components/ui/DockOperationsServerClock'
import { ErrorPanel, SkeletonRows } from '../components/ui/Primitives'
import { DailySummary } from '../components/DailySummary'
import { useInboundDockQueue, useInboundDockQueueSummary } from '../hooks/useInboundDocksQueries'
import type { InboundDockQueueEntry } from '../types/inbound-docks'

export function InboundDockQueuePage() {
  const navigate = useNavigate()
  const { context, options } = useLogisticsContextSelector()
  const { hasPermission } = useLogisticsPermissions()
  const canViewQueue = hasPermission('logistics.inbound_docks.view_queue')
  const canChangePriority = hasPermission('logistics.inbound_docks.change_priority')
  const [filter, setFilter] = useState<QueueFilter>({})
  const [page, setPage] = useState(1)
  const [priorityEntry, setPriorityEntry] = useState<InboundDockQueueEntry | null>(null)
  const warehouseId = filter.warehouse_id ?? context.warehouse_id ?? options.warehouses[0]?.id ?? ''
  useEffect(() => {
    if (!filter.warehouse_id && warehouseId) {
      setFilter((prev) => ({ ...prev, warehouse_id: warehouseId }))
    }
  }, [filter.warehouse_id, warehouseId])
  const summary = useInboundDockQueueSummary(warehouseId)
  const queue = useInboundDockQueue({ ...filter, page, page_size: 50 })
  return (
    <div className="page">
      <PageHeader
        eyebrow="Fase 038"
        title="Cola de muelles"
        description="Vehículos autorizados. El orden proviene del backend."
        actions={
          <>
            <DockOperationsServerClock serverTimeIso={summary.data?.server_time} timezone={summary.data?.timezone} />
            <Button size="small" variant="secondary" onClick={() => navigate('/logistics/inbound/docks')}>
              Tablero
            </Button>
          </>
        }
      />
      <DailySummary summary={summary.data ?? null} />
      <DockQueueFilters
        value={filter}
        onChange={(next) => {
          setPage(1)
          setFilter(next)
        }}
        warehouses={options.warehouses.length ? options.warehouses : (warehouseId ? [{ id: warehouseId, label: warehouseId }] : [])}
      />
      {!canViewQueue && <ErrorPanel message="No tienes capability para visualizar la cola." />}
      {canViewQueue && queue.isLoading && <SkeletonRows rows={4} />}
      {canViewQueue && queue.isError && <ErrorPanel message={queue.error ?? 'No se pudo cargar la cola.'} />}
      {canViewQueue && !queue.isLoading && !queue.isError && (
        <>
          <InboundDockQueueTable
            entries={queue.data?.items ?? []}
            onSelect={(entry) => navigate(`/logistics/inbound/docks/queue/${entry.id}`)}
            onChangePriority={canChangePriority ? (entry) => setPriorityEntry(entry) : undefined}
            capabilities={{ can_change_priority: canChangePriority }}
          />
          {queue.data && queue.data.total_pages > 1 && (
            <div className="flex items-center justify-end gap-2 text-xs text-slate-500">
              <Button size="small" variant="secondary" onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page <= 1}>
                Anterior
              </Button>
              <span>Página {page} de {queue.data.total_pages}</span>
              <Button
                size="small"
                variant="secondary"
                onClick={() => setPage((p) => Math.min(queue.data!.total_pages, p + 1))}
                disabled={page >= queue.data.total_pages}
              >
                Siguiente
              </Button>
            </div>
          )}
        </>
      )}
      <ChangeDockQueuePriorityDialog
        open={Boolean(priorityEntry)}
        entry={priorityEntry}
        onOpenChange={(o) => { if (!o) setPriorityEntry(null) }}
        onChanged={() => { void queue.refetch() }}
      />
    </div>
  )
}
