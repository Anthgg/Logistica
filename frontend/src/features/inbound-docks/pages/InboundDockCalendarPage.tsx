import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { PageHeader } from '../../../components/common/PageHeader'
import { Button } from '../../../components/common/Button'
import { useLogisticsContextSelector } from '../../logistics-permissions/hooks/useLogisticsContextSelector'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { DockQueueFilters, type QueueFilter } from '../components/Filters'
import { ErrorPanel, SectionPanel, SkeletonRows } from '../components/ui/Primitives'
import { InboundDockDailyCalendar } from '../components/WarehouseDockSchedules'
import { DailySummary } from '../components/DailySummary'
import { useInboundDockAssignments, useInboundDockQueueSummary, useUnloadingOperationsList } from '../hooks/useInboundDocksQueries'
import { useQuery } from '../hooks/useQuery'
import type { UnloadingOperation } from '../types/inbound-docks'

export function InboundDockCalendarPage() {
  const navigate = useNavigate()
  const { context, options } = useLogisticsContextSelector()
  const { hasPermission } = useLogisticsPermissions()
  const canView = hasPermission('logistics.inbound_docks.read')
  const [filter, setFilter] = useState<QueueFilter>({})
  const warehouseId = filter.warehouse_id ?? context.warehouse_id ?? options.warehouses[0]?.id ?? ''
  const summary = useInboundDockQueueSummary(warehouseId)
  const assignments = useInboundDockAssignments(
    { warehouse_id: warehouseId, date_from: filter.date_from, date_to: filter.date_to },
    { refetchIntervalMs: 10_000 },
  )
  const operations = useUnloadingOperationsList(
    { warehouse_id: warehouseId },
    { refetchIntervalMs: 10_000 },
  )
  const docksQuery = useQuery<{ items: Array<{ id: string; code: string; name: string }> }>(
    ['docks-for-calendar', warehouseId],
    warehouseId ? `/logistics/warehouse-docks?warehouse_id=${warehouseId}&page_size=100` : '',
    undefined,
    { enabled: Boolean(warehouseId) },
  )
  if (!canView) {
    return (
      <div className="page">
        <PageHeader title="Calendario diario" />
        <ErrorPanel message="No tienes capability para visualizar el calendario." />
      </div>
    )
  }
  return (
    <div className="page">
      <PageHeader
        eyebrow="Fase 038"
        title="Calendario diario"
        description="Eventos operativos del backend. No se generan intervalos ficticios."
        actions={
          <Button size="small" variant="secondary" onClick={() => navigate('/logistics/inbound/docks')}>
            Tablero
          </Button>
        }
      />
      <DailySummary summary={summary.data ?? null} />
      <DockQueueFilters
        value={filter}
        onChange={setFilter}
        warehouses={options.warehouses.length ? options.warehouses : (warehouseId ? [{ id: warehouseId, label: warehouseId }] : [])}
        docks={docksQuery.data?.items.map((d) => ({ id: d.id, label: `${d.code} — ${d.name}` })) ?? []}
      />
      {assignments.isLoading || operations.isLoading ? (
        <SkeletonRows rows={4} />
      ) : (
        <InboundDockDailyCalendar
          assignments={assignments.data?.items}
          operations={operations.data?.items as unknown as UnloadingOperation[] | undefined}
          loading={assignments.isLoading || operations.isLoading}
          error={assignments.error ?? operations.error}
          onSelectAssignment={(id) => navigate(`/logistics/inbound/dock-assignments/${id}`)}
          onSelectOperation={(id) => navigate(`/logistics/inbound/unloading/${id}`)}
        />
      )}
      <SectionPanel title="Leyenda" description="Cómo leer el calendario">
        <p className="text-xs text-slate-600">Las asignaciones y operaciones provienen del backend. La hora es la del servidor.</p>
      </SectionPanel>
    </div>
  )
}
