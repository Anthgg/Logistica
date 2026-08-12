import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { PageHeader } from '../../../components/common/PageHeader'
import { Button } from '../../../components/common/Button'
import { Alert } from '../../../components/common/Alert'
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton'
import { LogisticsIcon } from '../../../components/common/LogisticsIcon'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { useQuery } from '../../inbound-docks/hooks/useQuery'
import { useLogisticsAccess } from '../../logistics-me/hooks/useLogisticsAccess'
import { getErrorMessage } from '../../../utils/errors'
import { InventoryLedgerPhaseNav } from '../components/InventoryLedgerPhaseNav'
import { InventoryLedgerContextEmptyState } from '../components/InventoryLedgerContextEmptyState'

interface InventoryLedgerPartitionApi {
  id: string
  organization_id: string
  partition_key: string
  warehouse_id: string | null
  fiscal_year: number | null
  current_sequence: number
  last_movement_id: string | null
  last_movement_hash: string | null
}

export function InventoryLedgerPartitionsPage() {
  const navigate = useNavigate()
  const { hasPermission } = useLogisticsPermissions()
  const { currentContext } = useLogisticsAccess()
  const canView = hasPermission(LOGISTICS_PERMISSIONS.inventoryLedger.view)
  const canVerify = hasPermission(LOGISTICS_PERMISSIONS.inventoryLedger.verifyPartition)
  const canCheckpoint = hasPermission(LOGISTICS_PERMISSIONS.inventoryLedger.createCheckpoint)
  const organizationId = currentContext.organization_id

  const partitions = useQuery<InventoryLedgerPartitionApi[]>(
    ['inventory-ledger', 'partitions', organizationId],
    '/logistics/inventory/ledger/partitions',
    organizationId ? { organization_id: organizationId } : undefined,
    { enabled: canView && Boolean(organizationId) },
  )

  const metrics = useMemo(() => {
    const items = partitions.data ?? []
    return {
      total: items.length,
      sequences: items.reduce((sum, item) => sum + item.current_sequence, 0),
      warehouseScoped: items.filter((item) => Boolean(item.warehouse_id)).length,
      activeChains: items.filter((item) => Boolean(item.last_movement_hash)).length,
    }
  }, [partitions.data])

  if (!canView) {
    return (
      <div className="space-y-4">
        <PageHeader title="Particiones del libro" />
        <Alert variant="error">No tienes permisos para ver particiones.</Alert>
      </div>
    )
  }

  return (
    <div className="space-y-6 pb-10">
      <PageHeader
        eyebrow="Fase 044 · Topología"
        title="Particiones del libro"
        description="Secuencias independientes por organización, almacén y periodo fiscal."
        actions={
          <Button variant="secondary" onClick={() => navigate('/logistics/inventory/ledger/checkpoints')}>
            Ver checkpoints
          </Button>
        }
      />

      <InventoryLedgerPhaseNav />

      {!organizationId && (
        <InventoryLedgerContextEmptyState
          title="Selecciona la organización de las particiones"
          description="Cada organización mantiene su propio conjunto de secuencias y cadenas de integridad."
        />
      )}

      {organizationId && (
        <>
          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Resumen de particiones">
            {([
              ['layers' as const, 'Particiones', metrics.total, 'bg-blue-50 text-blue-700'],
              ['timeline' as const, 'Secuencias', metrics.sequences.toLocaleString(), 'bg-violet-50 text-violet-700'],
              ['building' as const, 'Por almacén', metrics.warehouseScoped, 'bg-orange-50 text-orange-700'],
              ['shield' as const, 'Cadenas activas', metrics.activeChains, 'bg-emerald-50 text-emerald-700'],
            ] as const).map(([icon, label, value, color]) => (
              <div key={String(label)} className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
                <div className="flex items-start justify-between gap-4"><div><p className="text-sm font-medium text-slate-500">{label}</p><p className="mt-2 text-3xl font-bold tracking-tight text-slate-950">{value}</p></div><span className={`flex h-11 w-11 items-center justify-center rounded-2xl ${color}`}><LogisticsIcon name={icon} size={21} aria-hidden="true" /></span></div>
              </div>
            ))}
          </section>

          {partitions.isLoading && <LoadingSkeleton rows={5} />}
          {partitions.isError && <Alert variant="error">{getErrorMessage(partitions.error)}</Alert>}

          {partitions.data && partitions.data.length === 0 && (
            <section className="rounded-3xl border border-dashed border-slate-300 bg-white px-6 py-12 text-center shadow-sm">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-3xl bg-slate-100 text-slate-600"><LogisticsIcon name="layers" size={28} aria-hidden="true" /></div>
              <h2 className="mt-6 text-xl font-bold text-slate-950">El ledger aún no tiene particiones</h2>
              <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-slate-600">La primera partición se crea al publicar el primer movimiento válido de esta organización.</p>
              <Button className="mt-6" onClick={() => navigate('/logistics/inventory/ledger/movements')}>Revisar movimientos</Button>
            </section>
          )}

          {partitions.data && partitions.data.length > 0 && (
            <section aria-labelledby="partition-list-title">
              <div className="mb-4"><p className="text-xs font-semibold uppercase tracking-[0.16em] text-orange-600">Estructura activa</p><h2 id="partition-list-title" className="mt-1 text-xl font-bold text-slate-950">Particiones disponibles</h2></div>
              <div className="grid gap-4 lg:grid-cols-2">
                {partitions.data.map((partition) => (
                  <article key={partition.id} className="group rounded-3xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-blue-200 hover:shadow-md">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex min-w-0 items-center gap-3"><span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-blue-50 text-blue-700"><LogisticsIcon name="layers" size={21} aria-hidden="true" /></span><div className="min-w-0"><h3 className="truncate font-bold text-slate-950">{partition.partition_key}</h3><p className="mt-1 text-sm text-slate-500">Año fiscal {partition.fiscal_year ?? 'no definido'}</p></div></div>
                      <span className={`rounded-full px-3 py-1 text-xs font-semibold ${partition.last_movement_hash ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-600'}`}>{partition.last_movement_hash ? 'Cadena activa' : 'Vacía'}</span>
                    </div>
                    <dl className="mt-5 grid grid-cols-2 gap-3"><div className="rounded-2xl bg-slate-50 p-4"><dt className="text-xs uppercase tracking-wide text-slate-500">Secuencia actual</dt><dd className="mt-1 text-xl font-bold text-slate-950">#{partition.current_sequence.toLocaleString()}</dd></div><div className="rounded-2xl bg-slate-50 p-4"><dt className="text-xs uppercase tracking-wide text-slate-500">Alcance</dt><dd className="mt-1 truncate text-sm font-semibold text-slate-900">{partition.warehouse_id ? `Almacén ${partition.warehouse_id.slice(0, 8)}` : 'Organización'}</dd></div></dl>
                    <div className="mt-4 rounded-2xl border border-slate-200 p-4"><p className="text-xs uppercase tracking-wide text-slate-500">Último hash</p><p className="mt-2 truncate font-mono text-xs text-slate-700">{partition.last_movement_hash ?? 'Cadena aún no inicializada'}</p></div>
                    {(canVerify || canCheckpoint) && <Button variant="secondary" className="mt-4 w-full justify-center" onClick={() => navigate(`/logistics/inventory/ledger/partitions/${partition.id}`)}>Abrir control de integridad</Button>}
                  </article>
                ))}
              </div>
            </section>
          )}
        </>
      )}
    </div>
  )
}
