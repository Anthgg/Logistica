import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { PageHeader } from '../../../components/common/PageHeader'
import { Button } from '../../../components/common/Button'
import { Alert } from '../../../components/common/Alert'
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton'
import { LogisticsIcon } from '../../../components/common/LogisticsIcon'
import { LogisticsContextSwitcher } from '../../../components/logistics/LogisticsContextSwitcher'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { useQuery } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsAccess } from '../../logistics-me/hooks/useLogisticsAccess'
import { getErrorMessage } from '../../../utils/errors'
import { InventoryLedgerPhaseNav } from '../components/InventoryLedgerPhaseNav'

interface InventoryLedgerPartitionApi {
  id: string
  partition_key: string
  warehouse_id: string | null
  fiscal_year: number | null
  current_sequence: number
  last_movement_hash: string | null
}

function CheckpointWorkflowGuide() {
  const steps = [
    {
      number: '01',
      title: 'Selecciona el contexto',
      description: 'Define la organización sobre la que se consultará el libro.',
    },
    {
      number: '02',
      title: 'Abre una partición',
      description: 'Revisa su secuencia y valida la continuidad de la cadena.',
    },
    {
      number: '03',
      title: 'Genera el checkpoint',
      description: 'Crea un manifiesto verificable para el rango seleccionado.',
    },
  ]

  return (
    <aside className="rounded-3xl border border-slate-200 bg-slate-950 p-6 text-white shadow-sm">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-white/10">
          <LogisticsIcon name="shield" size={20} aria-hidden="true" />
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-orange-300">
            Flujo de control
          </p>
          <h2 className="mt-1 text-lg font-semibold">Cómo funciona</h2>
        </div>
      </div>

      <ol className="mt-6 space-y-5">
        {steps.map((step) => (
          <li key={step.number} className="flex gap-4">
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-white/15 bg-white/5 text-xs font-semibold text-orange-300">
              {step.number}
            </span>
            <div>
              <h3 className="text-sm font-semibold text-white">{step.title}</h3>
              <p className="mt-1 text-sm leading-5 text-slate-300">{step.description}</p>
            </div>
          </li>
        ))}
      </ol>

      <div className="mt-6 rounded-2xl border border-white/10 bg-white/5 p-4">
        <div className="flex gap-3">
          <LogisticsIcon name="info" size={18} className="mt-0.5 shrink-0 text-sky-300" aria-hidden="true" />
          <p className="text-xs leading-5 text-slate-300">
            Un checkpoint prueba la integridad de un rango. No reemplaza una firma digital ni constituye blockchain.
          </p>
        </div>
      </div>
    </aside>
  )
}

export function InventoryLedgerCheckpointsPage() {
  const navigate = useNavigate()
  const { hasPermission } = useLogisticsPermissions()
  const { currentContext } = useLogisticsAccess()
  const canView = hasPermission(LOGISTICS_PERMISSIONS.inventoryLedger.view)
  const organizationId = currentContext.organization_id

  const partitions = useQuery<InventoryLedgerPartitionApi[]>(
    ['inventory-ledger', 'checkpoint-partitions', organizationId],
    '/logistics/inventory/ledger/partitions',
    organizationId ? { organization_id: organizationId } : undefined,
    { enabled: canView && Boolean(organizationId) },
  )

  const metrics = useMemo(() => {
    const items = partitions.data ?? []
    return {
      partitions: items.length,
      sequences: items.reduce((total, item) => total + item.current_sequence, 0),
      initializedChains: items.filter((item) => Boolean(item.last_movement_hash)).length,
    }
  }, [partitions.data])

  if (!canView) {
    return (
      <div className="space-y-4">
        <PageHeader title="Checkpoints" />
        <Alert variant="error">No tienes permisos para ver checkpoints.</Alert>
      </div>
    )
  }

  return (
    <div className="space-y-6 pb-10">
      <PageHeader
        eyebrow="Fase 044 · Integridad"
        title="Checkpoints del libro"
        description="Verifica la continuidad del ledger y crea manifiestos de integridad por partición."
        actions={
          <div className="flex flex-wrap gap-2">
            {organizationId && (
              <Button
                variant="secondary"
                onClick={() => navigate('/logistics/inventory/ledger/partitions')}
              >
                Ver particiones
              </Button>
            )}
            <Button variant="secondary" onClick={() => navigate('/logistics/inventory/ledger')}>
              Volver al tablero
            </Button>
          </div>
        }
      />

      <InventoryLedgerPhaseNav />

      {!organizationId ? (
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1.45fr)_minmax(300px,0.75fr)]">
          <section
            className="relative overflow-hidden rounded-3xl border border-slate-200 bg-white p-6 shadow-sm md:p-10"
            aria-labelledby="checkpoint-context-title"
          >
            <div className="absolute -right-16 -top-20 h-64 w-64 rounded-full bg-blue-50" aria-hidden="true" />
            <div className="absolute right-20 top-12 h-20 w-20 rounded-full bg-orange-50" aria-hidden="true" />

            <div className="relative max-w-2xl">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-50 text-blue-700 ring-1 ring-blue-100">
                <LogisticsIcon name="building" size={26} aria-hidden="true" />
              </div>
              <p className="mt-7 text-xs font-semibold uppercase tracking-[0.18em] text-orange-600">
                Contexto requerido
              </p>
              <h2 id="checkpoint-context-title" className="mt-2 text-2xl font-bold tracking-tight text-slate-950 md:text-3xl">
                Elige dónde validar el libro
              </h2>
              <p className="mt-3 max-w-xl text-base leading-7 text-slate-600">
                Los checkpoints pertenecen a una organización concreta. Selecciona el contexto operativo para cargar sus particiones y comenzar la verificación.
              </p>

              <div className="mt-7 flex flex-wrap items-center gap-4">
                <LogisticsContextSwitcher compact />
                <span className="text-sm text-slate-500">No modifica datos del inventario.</span>
              </div>

              <div className="mt-8 grid gap-3 sm:grid-cols-3">
                {[
                  ['lock', 'Acceso controlado'],
                  ['timeline', 'Cadena verificable'],
                  ['document', 'Manifiesto auditable'],
                ].map(([icon, label]) => (
                  <div key={label} className="flex items-center gap-2 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-medium text-slate-700">
                    <LogisticsIcon name={icon as 'lock' | 'timeline' | 'document'} size={17} className="text-blue-600" aria-hidden="true" />
                    {label}
                  </div>
                ))}
              </div>
            </div>
          </section>

          <CheckpointWorkflowGuide />
        </div>
      ) : (
        <>
          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3" aria-label="Resumen del ledger">
            <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-sm font-medium text-slate-500">Particiones disponibles</p>
                  <p className="mt-2 text-3xl font-bold tracking-tight text-slate-950">{metrics.partitions}</p>
                </div>
                <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-blue-50 text-blue-700">
                  <LogisticsIcon name="layers" size={21} aria-hidden="true" />
                </span>
              </div>
            </div>

            <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-sm font-medium text-slate-500">Secuencias registradas</p>
                  <p className="mt-2 text-3xl font-bold tracking-tight text-slate-950">{metrics.sequences.toLocaleString()}</p>
                </div>
                <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-violet-50 text-violet-700">
                  <LogisticsIcon name="timeline" size={21} aria-hidden="true" />
                </span>
              </div>
            </div>

            <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm sm:col-span-2 xl:col-span-1">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-sm font-medium text-slate-500">Cadenas inicializadas</p>
                  <p className="mt-2 text-3xl font-bold tracking-tight text-slate-950">{metrics.initializedChains}</p>
                </div>
                <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-700">
                  <LogisticsIcon name="shield" size={21} aria-hidden="true" />
                </span>
              </div>
            </div>
          </section>

          {partitions.isLoading && <LoadingSkeleton rows={5} />}

          {partitions.isError && (
            <Alert variant="error">{getErrorMessage(partitions.error)}</Alert>
          )}

          {partitions.data && partitions.data.length === 0 && (
            <div className="grid gap-6 lg:grid-cols-[minmax(0,1.45fr)_minmax(300px,0.75fr)]">
              <section className="rounded-3xl border border-dashed border-slate-300 bg-white px-6 py-12 text-center shadow-sm md:px-10">
                <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-3xl bg-slate-100 text-slate-600">
                  <LogisticsIcon name="archive" size={28} aria-hidden="true" />
                </div>
                <h2 className="mt-6 text-xl font-bold text-slate-950">Aún no hay particiones del libro</h2>
                <p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-slate-600">
                  La organización está seleccionada correctamente. La primera partición aparecerá cuando se publique el primer movimiento de inventario.
                </p>
                <div className="mt-6 flex flex-wrap justify-center gap-3">
                  <Button onClick={() => navigate('/logistics/inventory/ledger/movements')}>
                    Revisar movimientos
                  </Button>
                  <LogisticsContextSwitcher compact />
                </div>
              </section>

              <CheckpointWorkflowGuide />
            </div>
          )}

          {partitions.data && partitions.data.length > 0 && (
            <section aria-labelledby="checkpoint-partitions-title">
              <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-orange-600">Libro técnico</p>
                  <h2 id="checkpoint-partitions-title" className="mt-1 text-xl font-bold text-slate-950">Particiones listas para verificar</h2>
                </div>
                <LogisticsContextSwitcher compact />
              </div>

              <div className="grid gap-4 lg:grid-cols-2">
                {partitions.data.map((partition) => {
                  const initialized = Boolean(partition.last_movement_hash)
                  return (
                    <article key={partition.id} className="group rounded-3xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-blue-200 hover:shadow-md">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex min-w-0 items-center gap-3">
                          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-slate-100 text-slate-700">
                            <LogisticsIcon name="layers" size={21} aria-hidden="true" />
                          </span>
                          <div className="min-w-0">
                            <h3 className="truncate font-semibold text-slate-950">{partition.partition_key}</h3>
                            <p className="mt-1 text-sm text-slate-500">Año fiscal {partition.fiscal_year ?? 'no definido'}</p>
                          </div>
                        </div>
                        <span className={`inline-flex shrink-0 items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold ${initialized ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-600'}`}>
                          <span className={`h-1.5 w-1.5 rounded-full ${initialized ? 'bg-emerald-500' : 'bg-slate-400'}`} aria-hidden="true" />
                          {initialized ? 'Cadena activa' : 'Sin movimientos'}
                        </span>
                      </div>

                      <dl className="mt-5 grid grid-cols-2 gap-3">
                        <div className="rounded-2xl bg-slate-50 p-4">
                          <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">Secuencia actual</dt>
                          <dd className="mt-1 text-lg font-bold text-slate-950">#{partition.current_sequence.toLocaleString()}</dd>
                        </div>
                        <div className="rounded-2xl bg-slate-50 p-4">
                          <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">Alcance</dt>
                          <dd className="mt-1 truncate text-sm font-semibold text-slate-900">
                            {partition.warehouse_id ? `Almacén ${partition.warehouse_id.slice(0, 8)}` : 'Organización'}
                          </dd>
                        </div>
                      </dl>

                      <div className="mt-4 rounded-2xl border border-slate-200 px-4 py-3">
                        <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Último hash</p>
                        <p className="mt-1 truncate font-mono text-xs text-slate-700">
                          {partition.last_movement_hash ?? 'La cadena todavía no ha sido inicializada'}
                        </p>
                      </div>

                      <Button
                        variant="secondary"
                        className="mt-4 w-full justify-center"
                        onClick={() => navigate(`/logistics/inventory/ledger/partitions/${partition.id}`)}
                      >
                        Abrir verificación
                      </Button>
                    </article>
                  )
                })}
              </div>
            </section>
          )}
        </>
      )}
    </div>
  )
}
