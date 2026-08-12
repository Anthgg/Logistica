import { useCallback, useMemo } from 'react'
import { useQuery, type QueryState } from './useQuery'
import { inboundDockQueueApi } from '../api/inboundDockQueueApi'
import { warehouseDocksApi } from '../api/warehouseDocksApi'
import { dockAssignmentsApi } from '../api/dockAssignmentsApi'
import { unloadingOperationsApi } from '../api/unloadingOperationsApi'
import { dockOperationalMetricsApi } from '../api/dockOperationalMetricsApi'
import type {
  InboundDockQueueEntry,
  InboundDockQueueListQuery,
  InboundDockQueueSummary,
  PaginatedResponse,
  WarehouseDock,
  WarehouseDockAvailability,
  WarehouseDockListQuery,
  WarehouseDockSummary,
  WarehouseDockBlackout,
  WarehouseDockOperatingWindow,
  InboundDockAssignment,
  DockAssignmentPlan,
  DockAssignmentMetrics,
  DockOperationalTimes,
  DockOperationIntegrity,
  DockOperationHistoryEvent,
  ReceivingScanPreparation,
  UnloadingOperation,
  UnloadingReadinessCheck,
  UnloadingCompletionCheck,
  UnloadingExpectedLoad,
  UnloadingResponsibleAssignment,
  UnloadingEquipmentAssignment,
  UnloadingSealOpening,
  UnloadingPause,
} from '../types/inbound-docks'

const FIVE_SECONDS = 5_000
const TEN_SECONDS = 10_000
const THIRTY_SECONDS = 30_000

function normalizePaginatedResponse<T>(
  response: PaginatedResponse<T> | T[] | undefined,
  requestedPage = 1,
  requestedPageSize = 50,
): PaginatedResponse<T> | undefined {
  if (!response || !Array.isArray(response)) return response

  const page = Math.max(1, requestedPage)
  const pageSize = Math.max(1, requestedPageSize)
  const total = response.length
  const totalPages = Math.ceil(total / pageSize)
  const start = (page - 1) * pageSize

  return {
    items: response.slice(start, start + pageSize),
    page,
    page_size: pageSize,
    total,
    total_pages: totalPages,
  }
}

function omitUndefined<T extends Record<string, unknown>>(input: T): Partial<T> {
  const out: Partial<T> = {}
  for (const [k, v] of Object.entries(input)) {
    if (v !== undefined) (out as Record<string, unknown>)[k] = v
  }
  return out
}

export function useInboundDockQueue(
  query: InboundDockQueueListQuery,
  options: { refetchIntervalMs?: number | null; enabled?: boolean } = {},
): QueryState<PaginatedResponse<InboundDockQueueEntry>> {
  const stableQuery = useMemo(() => omitUndefined(query as Record<string, unknown>), [query])
  const result = useQuery<PaginatedResponse<InboundDockQueueEntry> | InboundDockQueueEntry[]>(
    ['dock-queue', JSON.stringify(stableQuery)],
    '/logistics/inbound-dock-queue',
    stableQuery as Record<string, unknown>,
    { enabled: options.enabled ?? true, refetchIntervalMs: options.refetchIntervalMs ?? TEN_SECONDS },
  )

  return {
    ...result,
    data: normalizePaginatedResponse(result.data, query.page ?? 1, query.page_size ?? 50),
  } as QueryState<PaginatedResponse<InboundDockQueueEntry>>
}

export function useInboundDockQueueEntry(entryId: string | null | undefined) {
  return useQuery<InboundDockQueueEntry>(
    ['dock-queue-entry', entryId],
    entryId ? `/logistics/inbound-dock-queue/${entryId}` : '',
    undefined,
    { enabled: Boolean(entryId), refetchIntervalMs: FIVE_SECONDS },
  )
}

export function useInboundDockQueueSummary(warehouseId: string | null | undefined) {
  return useQuery<InboundDockQueueSummary>(
    ['dock-queue-summary', warehouseId],
    '/logistics/inbound-dock-queue/summary',
    { warehouse_id: warehouseId ?? '' },
    { enabled: Boolean(warehouseId), refetchIntervalMs: TEN_SECONDS },
  )
}

export function useWarehouseDocks(
  query: WarehouseDockListQuery,
  options: { refetchIntervalMs?: number | null; enabled?: boolean } = {},
) {
  const stableQuery = useMemo(() => omitUndefined(query as Record<string, unknown>), [query])
  const result = useQuery<PaginatedResponse<WarehouseDockSummary> | WarehouseDockSummary[]>(
    ['warehouse-docks', JSON.stringify(stableQuery)],
    '/logistics/warehouse-docks',
    stableQuery as Record<string, unknown>,
    { enabled: options.enabled ?? true, refetchIntervalMs: options.refetchIntervalMs ?? THIRTY_SECONDS },
  )

  return {
    ...result,
    data: normalizePaginatedResponse(result.data, query.page ?? 1, query.page_size ?? 50),
  } as QueryState<PaginatedResponse<WarehouseDockSummary>>
}

export function useWarehouseDock(dockId: string | null | undefined) {
  return useQuery<WarehouseDock>(
    ['warehouse-dock', dockId],
    dockId ? `/logistics/warehouse-docks/${dockId}` : '',
    undefined,
    { enabled: Boolean(dockId), refetchIntervalMs: THIRTY_SECONDS },
  )
}

export function useWarehouseDockAvailability(dockId: string | null | undefined) {
  return useQuery<WarehouseDockAvailability>(
    ['warehouse-dock-availability', dockId],
    dockId ? `/logistics/warehouse-docks/${dockId}/availability` : '',
    undefined,
    { enabled: Boolean(dockId), refetchIntervalMs: FIVE_SECONDS },
  )
}

export function useWarehouseDockBlackouts(dockId: string | null | undefined) {
  return useQuery<WarehouseDockBlackout[]>(
    ['warehouse-dock-blackouts', dockId],
    dockId ? `/logistics/warehouse-docks/${dockId}/blackouts` : '',
    undefined,
    { enabled: Boolean(dockId), refetchIntervalMs: THIRTY_SECONDS },
  )
}

export function useWarehouseDockOperatingWindows(dockId: string | null | undefined) {
  return useQuery<WarehouseDockOperatingWindow[]>(
    ['warehouse-dock-windows', dockId],
    dockId ? `/logistics/warehouse-docks/${dockId}/operating-windows` : '',
    undefined,
    { enabled: Boolean(dockId), refetchIntervalMs: THIRTY_SECONDS },
  )
}

export function useInboundDockAssignment(assignmentId: string | null | undefined) {
  return useQuery<InboundDockAssignment>(
    ['dock-assignment', assignmentId],
    assignmentId ? `/logistics/inbound/dock-assignments/${assignmentId}` : '',
    undefined,
    { enabled: Boolean(assignmentId), refetchIntervalMs: FIVE_SECONDS },
  )
}

export function useDockAssignmentPlan(planId: string | null | undefined) {
  return useQuery<DockAssignmentPlan>(
    ['dock-assignment-plan', planId],
    planId ? `/logistics/inbound/dock-assignment-plans/${planId}` : '',
    undefined,
    { enabled: Boolean(planId), refetchIntervalMs: FIVE_SECONDS },
  )
}

export function useDockAssignmentMetrics(assignmentId: string | null | undefined) {
  return useQuery<DockAssignmentMetrics>(
    ['dock-assignment-metrics', assignmentId],
    assignmentId ? `/logistics/inbound/dock-assignments/${assignmentId}/metrics` : '',
    undefined,
    { enabled: Boolean(assignmentId), refetchIntervalMs: THIRTY_SECONDS },
  )
}

export function useDockOperationalTimes(assignmentId: string | null | undefined) {
  return useQuery<DockOperationalTimes>(
    ['dock-assignment-times', assignmentId],
    assignmentId ? `/logistics/inbound/dock-assignments/${assignmentId}/operational-times` : '',
    undefined,
    { enabled: Boolean(assignmentId), refetchIntervalMs: THIRTY_SECONDS },
  )
}

export function useDockAssignmentIntegrity(assignmentId: string | null | undefined) {
  return useQuery<DockOperationIntegrity>(
    ['dock-assignment-integrity', assignmentId],
    assignmentId ? `/logistics/inbound/dock-assignments/${assignmentId}/integrity` : '',
    undefined,
    { enabled: Boolean(assignmentId), refetchIntervalMs: THIRTY_SECONDS },
  )
}

export function useDockAssignmentHistory(assignmentId: string | null | undefined) {
  return useQuery<DockOperationHistoryEvent[]>(
    ['dock-assignment-history', assignmentId],
    assignmentId ? `/logistics/inbound/dock-assignments/${assignmentId}/history` : '',
    undefined,
    { enabled: Boolean(assignmentId), refetchIntervalMs: THIRTY_SECONDS },
  )
}

export function useReceivingPreparationByAssignment(assignmentId: string | null | undefined) {
  return useQuery<ReceivingScanPreparation>(
    ['dock-assignment-receiving-prep', assignmentId],
    assignmentId ? `/logistics/inbound/dock-assignments/${assignmentId}/receiving-preparation` : '',
    undefined,
    { enabled: Boolean(assignmentId), refetchIntervalMs: THIRTY_SECONDS },
  )
}

export function useUnloadingOperation(operationId: string | null | undefined) {
  return useQuery<UnloadingOperation>(
    ['unloading-op', operationId],
    operationId ? `/logistics/inbound/unloading/${operationId}` : '',
    undefined,
    { enabled: Boolean(operationId), refetchIntervalMs: FIVE_SECONDS },
  )
}

export function useUnloadingReadinessChecks(operationId: string | null | undefined) {
  return useQuery<UnloadingReadinessCheck[]>(
    ['unloading-readiness', operationId],
    operationId ? `/logistics/inbound/unloading/${operationId}/readiness-checks` : '',
    undefined,
    { enabled: Boolean(operationId), refetchIntervalMs: FIVE_SECONDS },
  )
}

export function useUnloadingCompletionChecks(operationId: string | null | undefined) {
  return useQuery<UnloadingCompletionCheck[]>(
    ['unloading-completion', operationId],
    operationId ? `/logistics/inbound/unloading/${operationId}/completion-checks` : '',
    undefined,
    { enabled: Boolean(operationId), refetchIntervalMs: FIVE_SECONDS },
  )
}

export function useUnloadingExpectedLoad(operationId: string | null | undefined) {
  return useQuery<UnloadingExpectedLoad>(
    ['unloading-expected', operationId],
    operationId ? `/logistics/inbound/unloading/${operationId}/expected-load` : '',
    undefined,
    { enabled: Boolean(operationId), refetchIntervalMs: THIRTY_SECONDS },
  )
}

export function useUnloadingResponsibles(operationId: string | null | undefined) {
  return useQuery<UnloadingResponsibleAssignment[]>(
    ['unloading-responsibles', operationId],
    operationId ? `/logistics/inbound/unloading/${operationId}/responsibles` : '',
    undefined,
    { enabled: Boolean(operationId), refetchIntervalMs: THIRTY_SECONDS },
  )
}

export function useUnloadingEquipment(operationId: string | null | undefined) {
  return useQuery<UnloadingEquipmentAssignment[]>(
    ['unloading-equipment', operationId],
    operationId ? `/logistics/inbound/unloading/${operationId}/equipment` : '',
    undefined,
    { enabled: Boolean(operationId), refetchIntervalMs: THIRTY_SECONDS },
  )
}

export function useUnloadingSealOpening(operationId: string | null | undefined) {
  return useQuery<UnloadingSealOpening | null>(
    ['unloading-seal', operationId],
    operationId ? `/logistics/inbound/unloading/${operationId}/seal-opening` : '',
    undefined,
    { enabled: Boolean(operationId), refetchIntervalMs: FIVE_SECONDS },
  )
}

export function useUnloadingPauses(operationId: string | null | undefined) {
  return useQuery<UnloadingPause[]>(
    ['unloading-pauses', operationId],
    operationId ? `/logistics/inbound/unloading/${operationId}/pauses` : '',
    undefined,
    { enabled: Boolean(operationId), refetchIntervalMs: FIVE_SECONDS },
  )
}

export function useReceivingPreparationByOperation(operationId: string | null | undefined) {
  return useQuery<ReceivingScanPreparation>(
    ['unloading-receiving-prep', operationId],
    operationId ? `/logistics/inbound/unloading/${operationId}/receiving-preparation` : '',
    undefined,
    { enabled: Boolean(operationId), refetchIntervalMs: THIRTY_SECONDS },
  )
}

export function useInboundDockAssignments(
  query: {
    warehouse_id?: string
    dock_id?: string
    status?: string
    supplier_id?: string
    carrier_id?: string
    date_from?: string
    date_to?: string
  },
  options: { refetchIntervalMs?: number | null; enabled?: boolean } = {},
) {
  const stable = useMemo(() => omitUndefined(query as Record<string, unknown>), [query])
  return useQuery<PaginatedResponse<InboundDockAssignment>>(
    ['dock-assignments', stable],
    '/logistics/inbound/dock-assignments',
    stable as Record<string, unknown>,
    { enabled: options.enabled ?? true, refetchIntervalMs: options.refetchIntervalMs ?? FIVE_SECONDS },
  )
}

export function useUnloadingOperationsList(
  query: {
    warehouse_id?: string
    dock_id?: string
    assignment_id?: string
    status?: string
  },
  options: { refetchIntervalMs?: number | null; enabled?: boolean } = {},
) {
  const stable = useMemo(() => omitUndefined(query as Record<string, unknown>), [query])
  return useQuery<PaginatedResponse<UnloadingOperation>>(
    ['unloading-ops', stable],
    '/logistics/inbound/unloading',
    stable as Record<string, unknown>,
    { enabled: options.enabled ?? true, refetchIntervalMs: options.refetchIntervalMs ?? FIVE_SECONDS },
  )
}

export function useDockMetricsSummary(
  warehouseId: string | null | undefined,
  range?: { date_from?: string; date_to?: string },
) {
  const stable = useMemo(
    () => omitUndefined({ warehouse_id: warehouseId ?? '', ...(range ?? {}) } as Record<string, unknown>),
    [warehouseId, range?.date_from, range?.date_to],
  )
  return useQuery<ReturnType<typeof dockOperationalMetricsApi.getSummary>>(
    ['dock-metrics-summary', stable],
    '/logistics/inbound/dock-metrics/summary',
    stable as Record<string, unknown>,
    { enabled: Boolean(warehouseId), refetchIntervalMs: THIRTY_SECONDS },
  )
}

export { inboundDockQueueApi, warehouseDocksApi, dockAssignmentsApi, unloadingOperationsApi, dockOperationalMetricsApi }

export function useNoop() {
  return useCallback(() => undefined, [])
}
