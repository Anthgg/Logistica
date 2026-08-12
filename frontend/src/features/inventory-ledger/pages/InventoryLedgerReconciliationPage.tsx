import { useMemo, useState } from 'react'
import { PageHeader } from '../../../components/common/PageHeader'
import { Button } from '../../../components/common/Button'
import { Alert } from '../../../components/common/Alert'
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton'
import { LogisticsIcon } from '../../../components/common/LogisticsIcon'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { useMutation, useQuery } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsAccess } from '../../logistics-me/hooks/useLogisticsAccess'
import { getErrorMessage } from '../../../utils/errors'
import { InventoryLedgerPhaseNav } from '../components/InventoryLedgerPhaseNav'
import { InventoryLedgerContextEmptyState } from '../components/InventoryLedgerContextEmptyState'
import { inventoryLedgerIntegrityApi } from '../api/inventoryLedgerIntegrityApi'
import type {
  InventoryLedgerReconciliationJobApi,
  InventoryLedgerReconciliationResultApi,
} from '../types/inventory-ledger-api'

interface ReconciliationScopeForm {
  warehouse_id: string
  source_system: string
  period_from: string
  period_to: string
}

const EMPTY_SCOPE: ReconciliationScopeForm = {
  warehouse_id: '',
  source_system: '',
  period_from: '',
  period_to: '',
}

export function InventoryLedgerReconciliationPage() {
  const { hasPermission } = useLogisticsPermissions()
  const { currentContext } = useLogisticsAccess()
  const canView = hasPermission(LOGISTICS_PERMISSIONS.inventoryLedger.view)
  const canReconcile = hasPermission(LOGISTICS_PERMISSIONS.inventoryLedger.reconcile)
  const organizationId = currentContext.organization_id
  const [form, setForm] = useState<ReconciliationScopeForm>(EMPTY_SCOPE)
  const [currentJobId, setCurrentJobId] = useState<string | null>(null)

  const job = useQuery<InventoryLedgerReconciliationJobApi>(
    ['inventory-ledger', 'reconciliation', organizationId, currentJobId],
    currentJobId ? `/logistics/inventory/ledger/reconciliation-jobs/${currentJobId}` : '',
    organizationId && currentJobId ? { organization_id: organizationId } : undefined,
    { enabled: canView && Boolean(organizationId) && Boolean(currentJobId) },
  )

  const results = useQuery<InventoryLedgerReconciliationResultApi[]>(
    ['inventory-ledger', 'reconciliation', organizationId, currentJobId, 'results'],
    currentJobId ? `/logistics/inventory/ledger/reconciliation-jobs/${currentJobId}/results` : '',
    organizationId && currentJobId ? { organization_id: organizationId } : undefined,
    { enabled: canView && Boolean(organizationId) && Boolean(currentJobId) },
  )

  const scope = useMemo<Record<string, unknown>>(() => ({
    warehouse_id: form.warehouse_id || undefined,
    source_system: form.source_system || undefined,
    period_from: form.period_from ? `${form.period_from}T00:00:00Z` : undefined,
    period_to: form.period_to ? `${form.period_to}T23:59:59Z` : undefined,
  }), [form])

  const createJob = useMutation<void, InventoryLedgerReconciliationJobApi>(
    () => inventoryLedgerIntegrityApi.createInventoryLedgerReconciliationJob(
      organizationId ?? '',
      Object.fromEntries(Object.entries(scope).filter(([, value]) => value !== undefined)),
    ),
    { onSuccess: (result) => setCurrentJobId(result.id) },
  )

  if (!canView) {
    return (
      <div className="space-y-4">
        <PageHeader title="Reconciliación" />
        <Alert variant="error">No tienes permisos para ver la reconciliación.</Alert>
      </div>
    )
  }

  const status = job.data?.status ?? (createJob.isPending ? 'PROCESSING' : 'READY')

  return (
    <div className="space-y-6 pb-10">
      <PageHeader
        eyebrow="Fase 044 · Control cruzado"
        title="Reconciliación del ledger"
        description="Compara eventos fuente y movimientos publicados sin ejecutar correcciones automáticas."
      />

      <InventoryLedgerPhaseNav />

      {!organizationId && (
        <InventoryLedgerContextEmptyState
          title="Selecciona la organización a reconciliar"
          description="Cada ejecución compara únicamente los eventos y movimientos del contexto elegido."
        />
      )}

      {organizationId && (
        <>
          <section className="grid gap-6 lg:grid-cols-[1.15fr_0.85fr]">
            <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex items-center gap-3"><span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-blue-50 text-blue-700"><LogisticsIcon name="check-square" size={21} aria-hidden="true" /></span><div><p className="text-xs font-semibold uppercase tracking-wide text-orange-600">Nueva ejecución</p><h2 className="mt-1 text-xl font-bold text-slate-950">Define el alcance</h2></div></div>
              <p className="mt-3 text-sm leading-6 text-slate-500">Deja los campos vacíos para reconciliar toda la organización o reduce el análisis por almacén, fuente y periodo.</p>

              <div className="mt-6 grid gap-4 sm:grid-cols-2">
                <label><span className="text-sm font-semibold text-slate-700">Almacén ID</span><input type="text" value={form.warehouse_id} onChange={(event) => setForm((current) => ({ ...current, warehouse_id: event.target.value }))} placeholder="Opcional" className="mt-2 min-h-11 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm outline-none focus:border-blue-400 focus:bg-white focus:ring-4 focus:ring-blue-50" /></label>
                <label><span className="text-sm font-semibold text-slate-700">Sistema fuente</span><input type="text" value={form.source_system} onChange={(event) => setForm((current) => ({ ...current, source_system: event.target.value }))} placeholder="Ej. INBOUND" className="mt-2 min-h-11 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm outline-none focus:border-blue-400 focus:bg-white focus:ring-4 focus:ring-blue-50" /></label>
                <label><span className="text-sm font-semibold text-slate-700">Periodo desde</span><input type="date" value={form.period_from} onChange={(event) => setForm((current) => ({ ...current, period_from: event.target.value }))} className="mt-2 min-h-11 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm outline-none focus:border-blue-400 focus:bg-white focus:ring-4 focus:ring-blue-50" /></label>
                <label><span className="text-sm font-semibold text-slate-700">Periodo hasta</span><input type="date" value={form.period_to} onChange={(event) => setForm((current) => ({ ...current, period_to: event.target.value }))} className="mt-2 min-h-11 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm outline-none focus:border-blue-400 focus:bg-white focus:ring-4 focus:ring-blue-50" /></label>
              </div>

              {canReconcile ? <Button className="mt-6 w-full justify-center" onClick={() => createJob.mutate(undefined)} disabled={createJob.isPending}>{createJob.isPending ? 'Ejecutando reconciliación…' : 'Ejecutar reconciliación'}</Button> : <Alert variant="warning">No tienes capacidad para iniciar reconciliaciones.</Alert>}
              {createJob.error && <p className="mt-3 text-sm text-red-600" role="alert">{createJob.error}</p>}
            </div>

            <aside className="rounded-3xl border border-slate-200 bg-slate-950 p-6 text-white shadow-sm">
              <div className="flex items-center justify-between gap-4"><div><p className="text-xs font-semibold uppercase tracking-wide text-orange-300">Estado actual</p><h2 className="mt-2 text-3xl font-bold">{status}</h2></div><span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white/10 text-sky-300"><LogisticsIcon name={status === 'COMPLETED' ? 'check' : 'activity'} size={23} aria-hidden="true" /></span></div>
              <p className="mt-4 text-sm leading-6 text-slate-300">La ejecución es auditable y no modifica eventos ni movimientos. Los hallazgos quedan disponibles para revisión.</p>
              <div className="mt-6 rounded-2xl border border-white/10 bg-white/5 p-4"><p className="text-xs text-slate-400">Job actual</p><p className="mt-1 truncate font-mono text-xs text-slate-200">{currentJobId ?? 'Aún no ejecutado'}</p></div>
            </aside>
          </section>

          {job.isLoading && <LoadingSkeleton rows={4} />}
          {job.isError && <Alert variant="error">{getErrorMessage(job.error)}</Alert>}

          {job.data && (
            <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Resultado de reconciliación">
              {([
                ['activity' as const, 'Eventos vistos', job.data.total_events_seen, 'bg-blue-50 text-blue-700'],
                ['package' as const, 'Movimientos vistos', job.data.total_movements_seen, 'bg-violet-50 text-violet-700'],
                ['alert' as const, 'Hallazgos', job.data.issue_count, job.data.issue_count ? 'bg-red-50 text-red-700' : 'bg-emerald-50 text-emerald-700'],
                ['clock' as const, 'Estado', job.data.status, 'bg-orange-50 text-orange-700'],
              ] as const).map(([icon, label, value, color]) => <div key={String(label)} className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex items-start justify-between gap-3"><div><p className="text-sm text-slate-500">{label}</p><p className="mt-2 text-2xl font-bold text-slate-950">{value}</p></div><span className={`flex h-10 w-10 items-center justify-center rounded-2xl ${color}`}><LogisticsIcon name={icon} size={19} aria-hidden="true" /></span></div></div>)}
            </section>
          )}

          {results.isLoading && <LoadingSkeleton rows={4} />}
          {results.isError && <Alert variant="error">{getErrorMessage(results.error)}</Alert>}
          {results.data && (
            <section aria-labelledby="reconciliation-results-title">
              <div className="mb-4"><p className="text-xs font-semibold uppercase tracking-[0.16em] text-orange-600">Resultado técnico</p><h2 id="reconciliation-results-title" className="mt-1 text-xl font-bold text-slate-950">Hallazgos ({results.data.length})</h2></div>
              {results.data.length === 0 ? (
                <div className="rounded-3xl border border-emerald-200 bg-emerald-50 px-6 py-10 text-center"><div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-600 text-white"><LogisticsIcon name="check" size={24} aria-hidden="true" /></div><h3 className="mt-5 font-bold text-emerald-950">Sin diferencias detectadas</h3><p className="mt-2 text-sm text-emerald-800">Los eventos y movimientos revisados son consistentes.</p></div>
              ) : (
                <div className="space-y-3">{results.data.map((result) => <article key={result.id} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex flex-wrap items-start justify-between gap-3"><div><span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${result.severity === 'HIGH' || result.severity === 'CRITICAL' ? 'bg-red-50 text-red-700' : 'bg-orange-50 text-orange-700'}`}>{result.severity}</span><h3 className="mt-3 font-bold text-slate-950">{result.result_code}</h3></div><span className="text-xs text-slate-500">{new Date(result.detected_at).toLocaleString()}</span></div><p className="mt-3 text-sm leading-6 text-slate-600">{result.description}</p>{result.movement_code && <p className="mt-3 font-mono text-xs text-slate-500">MOV: {result.movement_code}</p>}</article>)}</div>
              )}
            </section>
          )}
        </>
      )}
    </div>
  )
}
