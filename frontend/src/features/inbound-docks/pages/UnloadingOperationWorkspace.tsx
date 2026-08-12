import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { PageHeader } from '../../../components/common/PageHeader'
import { Button } from '../../../components/common/Button'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { StartUnloadingDialog } from '../components/dialogs/OperationalDialogs'
import {
  AbortUnloadingDialog,
  CompleteUnloadingDialog,
  PauseUnloadingDialog,
  ResumeUnloadingDialog,
} from '../components/dialogs/UnloadingActionDialogs'
import { DockOperationsServerClock } from '../components/ui/DockOperationsServerClock'
import { ErrorPanel, InlineTabs, KeyValueGrid, SectionPanel, SkeletonRows, StatusPill } from '../components/ui/Primitives'
import { ReceivingScanPreparationPanel } from '../components/ReceivingAndHistoryPanels'
import {
  ServerBasedOperationTimer,
} from '../components/ui/ServerBasedOperationTimer'
import { UnloadingCompletionChecklist } from '../components/UnloadingCompletionChecklist'
import { UnloadingExpectedLoadPanel } from '../components/UnloadingExpectedLoadPanel'
import { UnloadingPausesPanel } from '../components/UnloadingPausesPanel'
import { UnloadingReadinessChecklist } from '../components/UnloadingReadinessChecklist'
import { UnloadingResponsiblesPanel } from '../components/UnloadingResponsiblesPanel'
import { UnloadingSealPanel } from '../components/UnloadingSealPanel'
import { UnloadingPauseBanner } from '../components/dialogs/UnloadingSupportDialogs'
import { UnloadingEquipmentPanel } from '../components/ReceivingAndHistoryPanels'
import { DockOperationTimeline } from '../components/DockOperationTimeline'
import {
  DockOperationalTimesPanel,
  DockOperationMetricsPanel,
  OperationalTimeQualityPanel,
} from '../components/DockOperationalTimesPanels'
import { formatServerTime, unloadingStatusLabel } from '../utils/format'
import {
  useUnloadingCompletionChecks,
  useUnloadingEquipment,
  useUnloadingExpectedLoad,
  useUnloadingOperation,
  useUnloadingPauses,
  useUnloadingReadinessChecks,
  useUnloadingResponsibles,
  useUnloadingSealOpening,
  useReceivingPreparationByOperation,
} from '../hooks/useInboundDocksQueries'
import { useQuery } from '../hooks/useQuery'
import type { UnloadingOperation, UnloadingReadinessCheck, UnloadingCompletionCheck } from '../types/inbound-docks'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'

type Tab = 'ready' | 'responsibles' | 'seal' | 'unloading' | 'pauses' | 'completion' | 'times' | 'metrics' | 'prep' | 'history'

const TABS: Array<{ key: Tab; label: string }> = [
  { key: 'ready', label: 'Readiness' },
  { key: 'responsibles', label: 'Responsables' },
  { key: 'seal', label: 'Precinto' },
  { key: 'unloading', label: 'Descarga' },
  { key: 'pauses', label: 'Pausas' },
  { key: 'completion', label: 'Cierre' },
  { key: 'times', label: 'Tiempos' },
  { key: 'metrics', label: 'Métricas' },
  { key: 'prep', label: 'Fase 039' },
  { key: 'history', label: 'Historial' },
]

export function UnloadingOperationWorkspace() {
  const { operationId } = useParams<{ operationId: string }>()
  const navigate = useNavigate()
  const { hasPermission } = useLogisticsPermissions()
  const canStart = hasPermission(LOGISTICS_PERMISSIONS.inboundDocks.startUnloading)
  const canPause = hasPermission(LOGISTICS_PERMISSIONS.inboundDocks.pause)
  const canResume = hasPermission(LOGISTICS_PERMISSIONS.inboundDocks.resume)
  const canAbort = hasPermission(LOGISTICS_PERMISSIONS.inboundDocks.abort)
  const canComplete = hasPermission(LOGISTICS_PERMISSIONS.inboundDocks.complete)
  const [tab, setTab] = useState<Tab>('ready')
  const [startOpen, setStartOpen] = useState(false)
  const [pauseOpen, setPauseOpen] = useState(false)
  const [resumeOpen, setResumeOpen] = useState(false)
  const [abortOpen, setAbortOpen] = useState(false)
  const [completeOpen, setCompleteOpen] = useState(false)
  const op = useUnloadingOperation(operationId ?? null)
  const readiness = useUnloadingReadinessChecks(operationId ?? null)
  const completion = useUnloadingCompletionChecks(operationId ?? null)
  const expected = useUnloadingExpectedLoad(operationId ?? null)
  const responsibles = useUnloadingResponsibles(operationId ?? null)
  const equipment = useUnloadingEquipment(operationId ?? null)
  const seal = useUnloadingSealOpening(operationId ?? null)
  const pauses = useUnloadingPauses(operationId ?? null)
  const prep = useReceivingPreparationByOperation(operationId ?? null)
  const history = useQuery<Array<{ id: string; event_type: string; occurred_at: string; actor: { display_name: string } | null; previous_status: string | null; new_status: string | null; reason: string | null; result: string | null }>>(
    ['unloading-operation-history', operationId],
    operationId ? `/logistics/inbound/unloading/${operationId}/history` : '',
    undefined,
    { enabled: Boolean(operationId), refetchIntervalMs: 15_000 },
  )
  const metricsQuery = useQuery<{ assignment_id: string; wait_seconds: number | null; movement_seconds: number | null; dock_wait_seconds: number | null; unloading_gross_seconds: number | null; unloading_pause_seconds: number | null; unloading_net_seconds: number | null; release_delay_seconds: number | null; dock_occupancy_seconds: number | null; total_cycle_seconds: number | null; gate_control_seconds: number | null; data_quality: 'COMPLETE' | 'PARTIAL' | 'MISSING_EVENT' | 'INVALID_ORDER' | 'CORRECTED' | 'IMPORTED' | 'INTEGRITY_FAILED'; impact_on_kpi: string[] }>(
    ['unloading-operation-metrics', operationId],
    operationId ? `/logistics/inbound/unloading/${operationId}/metrics` : '',
    undefined,
    { enabled: Boolean(operationId), refetchIntervalMs: 15_000 },
  )
  const integrity = useQuery<{ assignment_id: string; status: 'VALID' | 'FAILED' | 'PENDING'; failures: string[]; last_checked_at: string | null; partial_hash: string | null }>(
    ['unloading-operation-integrity', operationId],
    operationId ? `/logistics/inbound/unloading/${operationId}/integrity` : '',
    undefined,
    { enabled: Boolean(operationId), refetchIntervalMs: 15_000 },
  )
  if (op.isLoading) return <SkeletonRows rows={4} />
  if (op.isError) return <ErrorPanel message={op.error ?? 'No se pudo cargar la operación.'} />
  const operation: UnloadingOperation | null = op.data ?? null
  if (!operation) return <ErrorPanel message="Operación no encontrada" />
  const status = operation.status
  const isActive = status === 'ACTIVE'
  const isPaused = status === 'PAUSED'
  const isReady = status === 'READY' || status === 'READINESS_PENDING' || status === 'CREATED'
  const isCompleted = status === 'COMPLETED' || status === 'ABORTED' || status === 'CANCELLED'
  const readinessSummary = readiness.data
    ? {
        total: readiness.data.length,
        pending: readiness.data.filter((c: UnloadingReadinessCheck) => !c.result).length,
        failed: readiness.data.filter((c: UnloadingReadinessCheck) => c.result === 'FAIL').length,
        passed: readiness.data.filter((c: UnloadingReadinessCheck) => c.result === 'PASS' || c.result === 'NOT_APPLICABLE').length,
      }
    : undefined
  const completionSummary = completion.data
    ? {
        total: completion.data.length,
        pending: completion.data.filter((c: UnloadingCompletionCheck) => !c.result).length,
        failed: completion.data.filter((c: UnloadingCompletionCheck) => c.result === 'FAIL').length,
        passed: completion.data.filter((c: UnloadingCompletionCheck) => c.result === 'PASS' || c.result === 'NOT_APPLICABLE').length,
      }
    : undefined
  return (
    <div className="page">
      <PageHeader
        eyebrow={`Operación ${operation.id.slice(0, 8)}`}
        title={`${operation.cpv_code ?? operation.cit_code ?? '—'} · ${operation.vehicle?.plate ?? '—'}`}
        description={`Muelle ${operation.dock_code} — ${operation.dock_name} · Estado: ${unloadingStatusLabel(status)}`}
        actions={
          <>
            <DockOperationsServerClock serverTimeIso={operation.server_time} timezone={null} />
            {canStart && isReady && (
              <Button size="small" variant="primary" onClick={() => setStartOpen(true)}>
                Iniciar descarga
              </Button>
            )}
            {canPause && isActive && (
              <Button size="small" variant="danger" onClick={() => setPauseOpen(true)}>
                Pausar
              </Button>
            )}
            {canResume && isPaused && (
              <Button size="small" variant="primary" onClick={() => setResumeOpen(true)}>
                Reanudar
              </Button>
            )}
            {canAbort && (isActive || isPaused || isReady) && (
              <Button size="small" variant="danger" onClick={() => setAbortOpen(true)}>
                Abortar
              </Button>
            )}
            {canComplete && isActive === false && isPaused === false && !isCompleted && (
              <Button size="small" variant="primary" onClick={() => setCompleteOpen(true)}>
                Finalizar
              </Button>
            )}
            <Button
              size="small"
              variant="secondary"
              onClick={() => navigate(`/logistics/inbound/dock-assignments/${operation.assignment_id}`)}
            >
              Ver asignación
            </Button>
          </>
        }
      />
      <SectionPanel
        title="Encabezado operativo"
        description="Datos principales de la operación"
        actions={<StatusPill tone="info">{unloadingStatusLabel(status)}</StatusPill>}
      >
        <KeyValueGrid
          items={[
            { label: 'Muelle', value: `${operation.dock_code} — ${operation.dock_name}` },
            { label: 'Estado', value: unloadingStatusLabel(status) },
            { label: 'Readiness', value: operation.readiness_status },
            { label: 'Inicio (servidor)', value: operation.started_at_server ? formatServerTime(operation.started_at_server) : '—' },
            { label: 'Inicio', value: operation.started_at ? formatServerTime(operation.started_at) : '—' },
            { label: 'Fin', value: operation.completed_at ? formatServerTime(operation.completed_at) : '—' },
            { label: 'Pausa activa', value: operation.active_pause?.reason_label ?? '—' },
            { label: 'Pausa acumulada', value: `${operation.accumulated_pause_seconds ?? 0}s` },
            { label: 'Alertas', value: operation.alerts?.length ? `${operation.alerts.length} alerta(s)` : '—' },
          ]}
        />
      </SectionPanel>
      <ServerBasedOperationTimer
        serverTimeIso={operation.server_time}
        startedAt={operation.started_at_server ?? operation.started_at}
        activePauseStartedAt={operation.active_pause_started_at}
        accumulatedPauseSeconds={operation.accumulated_pause_seconds ?? 0}
        status={status}
        officialDurationSeconds={metricsQuery.data?.unloading_gross_seconds ?? null}
      />
      {operation.active_pause && (
        <UnloadingPauseBanner
          pause={operation.active_pause}
          canResume={canResume}
          canAbort={canAbort}
          onResume={() => setResumeOpen(true)}
          onAbort={() => setAbortOpen(true)}
        />
      )}
      {operation.alerts && operation.alerts.length > 0 && (
        <SectionPanel title="Alertas" description="Listado del backend">
          <ul className="list-disc pl-4 text-xs text-rose-700">
            {operation.alerts.map((al) => (
              <li key={al}>{al}</li>
            ))}
          </ul>
        </SectionPanel>
      )}
      <InlineTabs tabs={TABS} value={tab} onChange={setTab} />
      {tab === 'ready' && (
        <div className="space-y-3">
          <UnloadingReadinessChecklist
            operation={operation}
            checks={readiness.data}
            loading={readiness.isLoading}
            error={readiness.error}
            onChanged={() => { void readiness.refetch(); void op.refetch() }}
          />
        </div>
      )}
      {tab === 'responsibles' && (
        <UnloadingResponsiblesPanel
          operation={operation}
          responsibles={responsibles.data}
          loading={responsibles.isLoading}
          error={responsibles.error}
          onChanged={() => { void responsibles.refetch() }}
        />
      )}
      {tab === 'seal' && (
        <UnloadingSealPanel
          operation={operation}
          seal={seal.data}
          loading={seal.isLoading}
          error={seal.error}
          onChanged={() => { void seal.refetch() }}
        />
      )}
      {tab === 'unloading' && (
        <div className="space-y-3">
          <UnloadingExpectedLoadPanel load={expected.data} loading={expected.isLoading} error={expected.error} />
          <UnloadingEquipmentPanel
            equipment={equipment.data}
            loading={equipment.isLoading}
            error={equipment.error}
          />
        </div>
      )}
      {tab === 'pauses' && (
        <UnloadingPausesPanel pauses={pauses.data} loading={pauses.isLoading} error={pauses.error} />
      )}
      {tab === 'completion' && (
        <UnloadingCompletionChecklist
          operation={operation}
          checks={completion.data}
          loading={completion.isLoading}
          error={completion.error}
          onChanged={() => { void completion.refetch(); void op.refetch() }}
        />
      )}
      {tab === 'times' && (
        <DockOperationTimeline
          events={history.data as unknown as import('../types/inbound-docks').DockOperationHistoryEvent[] | undefined}
          loading={history.isLoading}
          error={history.error}
        />
      )}
      {tab === 'metrics' && (
        <div className="space-y-3">
          <DockOperationMetricsPanel metrics={metricsQuery.data} loading={metricsQuery.isLoading} error={metricsQuery.error} />
          <OperationalTimeQualityPanel
            status={metricsQuery.data?.data_quality}
            lastValidatedAt={integrity.data?.last_checked_at}
            missing={[]}
            corrected={[]}
            impact={metricsQuery.data?.impact_on_kpi ?? []}
          />
        </div>
      )}
      {tab === 'prep' && (
        <ReceivingScanPreparationPanel prep={prep.data} loading={prep.isLoading} error={prep.error} />
      )}
      {tab === 'history' && (
        <DockOperationTimeline
          events={history.data as unknown as import('../types/inbound-docks').DockOperationHistoryEvent[] | undefined}
          loading={history.isLoading}
          error={history.error}
        />
      )}
      <DockOperationalTimesPanel
        times={
          metricsQuery.data
            ? {
                assignment_id: operation.assignment_id,
                gate_arrival_at: null,
                gate_clearance_at: null,
                queue_entry_at: null,
                assigned_at: null,
                movement_started_at: null,
                dock_arrival_at: null,
                unloading_started_at: operation.started_at_server ?? operation.started_at,
                unloading_completed_at: operation.completed_at,
                dock_released_at: null,
                pauses: pauses.data ?? [],
                data_quality: metricsQuery.data.data_quality,
                missing_events: [],
                corrections: [],
                last_validated_at: integrity.data?.last_checked_at ?? null,
              }
            : undefined
        }
        loading={metricsQuery.isLoading}
        error={metricsQuery.error}
      />
      <StartUnloadingDialog
        open={startOpen}
        operation={operation}
        readinessSummary={readinessSummary}
        onOpenChange={setStartOpen}
        onStarted={() => { void op.refetch() }}
      />
      <PauseUnloadingDialog
        open={pauseOpen}
        operation={operation}
        onOpenChange={setPauseOpen}
        onPaused={() => { void op.refetch() }}
      />
      <ResumeUnloadingDialog
        open={resumeOpen}
        operation={operation}
        onOpenChange={setResumeOpen}
        onResumed={() => { void op.refetch() }}
      />
      <AbortUnloadingDialog
        open={abortOpen}
        operation={operation}
        onOpenChange={setAbortOpen}
        onAborted={() => { void op.refetch() }}
      />
      <CompleteUnloadingDialog
        open={completeOpen}
        operation={operation}
        completionCheckSummary={completionSummary}
        onOpenChange={setCompleteOpen}
        onCompleted={() => { void op.refetch() }}
      />
    </div>
  )
}

