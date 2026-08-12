import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
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
  InventoryLedgerCheckpointApi,
  InventoryLedgerVerificationApi,
} from '../types/inventory-ledger-api'

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

export function InventoryLedgerPartitionIntegrityPage() {
  const navigate = useNavigate()
  const { partitionId = '' } = useParams()
  const { hasPermission } = useLogisticsPermissions()
  const { currentContext } = useLogisticsAccess()
  const canView = hasPermission(LOGISTICS_PERMISSIONS.inventoryLedger.view)
  const canVerify = hasPermission(LOGISTICS_PERMISSIONS.inventoryLedger.verifyPartition)
  const canCheckpoint = hasPermission(LOGISTICS_PERMISSIONS.inventoryLedger.createCheckpoint)
  const organizationId = currentContext.organization_id
  const [fromSequence, setFromSequence] = useState(1)
  const [toSequence, setToSequence] = useState(1)
  const [createdCheckpoint, setCreatedCheckpoint] = useState<InventoryLedgerCheckpointApi | null>(null)

  const partition = useQuery<InventoryLedgerPartitionApi>(
    ['inventory-ledger', 'partition', organizationId, partitionId],
    `/logistics/inventory/ledger/partitions/${partitionId}`,
    organizationId ? { organization_id: organizationId } : undefined,
    { enabled: canView && Boolean(organizationId) && Boolean(partitionId) },
  )

  const integrity = useQuery<InventoryLedgerVerificationApi>(
    ['inventory-ledger', 'partition-integrity', organizationId, partitionId],
    `/logistics/inventory/ledger/partitions/${partitionId}/integrity`,
    organizationId ? { organization_id: organizationId } : undefined,
    { enabled: canView && Boolean(organizationId) && Boolean(partitionId) },
  )

  useEffect(() => {
    if (partition.data?.current_sequence) {
      setToSequence(partition.data.current_sequence)
    }
  }, [partition.data?.current_sequence])

  const verify = useMutation<void, InventoryLedgerVerificationApi>(
    () => inventoryLedgerIntegrityApi.verifyInventoryLedgerPartition(organizationId ?? '', partitionId),
    { onSuccess: () => void integrity.refetch() },
  )

  const checkpoint = useMutation<void, InventoryLedgerCheckpointApi>(
    () => inventoryLedgerIntegrityApi.createInventoryLedgerCheckpoint(
      organizationId ?? '',
      partitionId,
      fromSequence,
      toSequence,
    ),
    { onSuccess: (result) => setCreatedCheckpoint(result) },
  )

  if (!canView) {
    return (
      <div className="space-y-4">
        <PageHeader title="Integridad de partición" />
        <Alert variant="error">No tienes permisos para ver la integridad de la partición.</Alert>
      </div>
    )
  }

  const verificationOk = integrity.data?.verification_status === 'OK'
  const invalidRange = fromSequence < 1 || toSequence < fromSequence || toSequence > (partition.data?.current_sequence ?? 0)

  return (
    <div className="space-y-6 pb-10">
      <PageHeader
        eyebrow="Fase 044 · Control de integridad"
        title="Verificación de partición"
        description={partition.data?.partition_key ?? `Partición ${partitionId}`}
        actions={
          <Button variant="secondary" onClick={() => navigate('/logistics/inventory/ledger/partitions')}>
            Volver a particiones
          </Button>
        }
      />

      <InventoryLedgerPhaseNav />

      {!organizationId && (
        <InventoryLedgerContextEmptyState
          title="Selecciona la organización de la partición"
          description="La verificación compara hashes únicamente dentro del ledger al que pertenece la partición."
        />
      )}

      {(partition.isLoading || integrity.isLoading) && <LoadingSkeleton rows={7} />}
      {partition.isError && <Alert variant="error">{getErrorMessage(partition.error)}</Alert>}
      {integrity.isError && <Alert variant="error">{getErrorMessage(integrity.error)}</Alert>}

      {partition.data && integrity.data && (
        <>
          <section className={`relative overflow-hidden rounded-3xl border p-6 shadow-sm md:p-8 ${verificationOk ? 'border-emerald-200 bg-emerald-950 text-white' : 'border-orange-200 bg-orange-950 text-white'}`}>
            <div className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-white/5" aria-hidden="true" />
            <div className="relative flex flex-col justify-between gap-6 lg:flex-row lg:items-end">
              <div>
                <span className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold ${verificationOk ? 'bg-emerald-300/15 text-emerald-200' : 'bg-orange-300/15 text-orange-200'}`}><span className={`h-1.5 w-1.5 rounded-full ${verificationOk ? 'bg-emerald-300' : 'bg-orange-300'}`} aria-hidden="true" />{integrity.data.verification_status}</span>
                <h2 className="mt-5 text-3xl font-bold tracking-tight">{verificationOk ? 'Cadena verificada' : 'Revisión requerida'}</h2>
                <p className="mt-2 max-w-xl text-sm leading-6 text-white/70">Algoritmo canónico {integrity.data.algorithm_version}. Última secuencia comprobada #{integrity.data.last_sequence ?? '—'}.</p>
              </div>
              {canVerify && <Button onClick={() => verify.mutate(undefined)} disabled={verify.isPending}>{verify.isPending ? 'Verificando…' : 'Verificar nuevamente'}</Button>}
            </div>
          </section>

          {verify.error && <Alert variant="error">{verify.error}</Alert>}

          <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4" aria-label="Resumen de la partición">
            {([
              ['timeline' as const, 'Secuencia actual', `#${partition.data.current_sequence.toLocaleString()}`, 'bg-blue-50 text-blue-700'],
              ['calendar' as const, 'Año fiscal', partition.data.fiscal_year ?? '—', 'bg-violet-50 text-violet-700'],
              ['building' as const, 'Alcance', partition.data.warehouse_id ? 'Almacén' : 'Organización', 'bg-orange-50 text-orange-700'],
              ['shield' as const, 'Estado', integrity.data.verification_status, verificationOk ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'],
            ] as const).map(([icon, label, value, color]) => <div key={String(label)} className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex items-start justify-between gap-3"><div><p className="text-sm text-slate-500">{label}</p><p className="mt-2 text-xl font-bold text-slate-950">{value}</p></div><span className={`flex h-10 w-10 items-center justify-center rounded-2xl ${color}`}><LogisticsIcon name={icon} size={19} aria-hidden="true" /></span></div></div>)}
          </section>

          <section className="grid gap-6 lg:grid-cols-[1fr_1fr]">
            <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex items-center gap-3"><span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-100 text-slate-700"><LogisticsIcon name="key" size={20} aria-hidden="true" /></span><div><h2 className="text-lg font-bold text-slate-950">Extremos de la cadena</h2><p className="text-sm text-slate-500">Evidencia usada en la verificación.</p></div></div>
              <dl className="mt-5 space-y-4"><div className="rounded-2xl border border-slate-200 p-4"><dt className="text-xs uppercase tracking-wide text-slate-500">Primer hash</dt><dd className="mt-2 break-all font-mono text-xs text-slate-700">{integrity.data.first_hash ?? '—'}</dd></div><div className="rounded-2xl border border-slate-200 p-4"><dt className="text-xs uppercase tracking-wide text-slate-500">Último hash</dt><dd className="mt-2 break-all font-mono text-xs text-slate-700">{integrity.data.last_hash ?? '—'}</dd></div></dl>
            </div>

            <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex items-center gap-3"><span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-blue-50 text-blue-700"><LogisticsIcon name="document" size={20} aria-hidden="true" /></span><div><h2 className="text-lg font-bold text-slate-950">Crear checkpoint</h2><p className="text-sm text-slate-500">Genera un manifiesto para un rango ya publicado.</p></div></div>

              {canCheckpoint ? (
                <div className="mt-5">
                  <div className="grid grid-cols-2 gap-3">
                    <label><span className="text-sm font-semibold text-slate-700">Desde secuencia</span><input type="number" min={1} max={partition.data.current_sequence} value={fromSequence} onChange={(event) => setFromSequence(Number(event.target.value))} className="mt-2 min-h-11 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2 text-sm outline-none focus:border-blue-400 focus:ring-4 focus:ring-blue-50" /></label>
                    <label><span className="text-sm font-semibold text-slate-700">Hasta secuencia</span><input type="number" min={1} max={partition.data.current_sequence} value={toSequence} onChange={(event) => setToSequence(Number(event.target.value))} className="mt-2 min-h-11 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-2 text-sm outline-none focus:border-blue-400 focus:ring-4 focus:ring-blue-50" /></label>
                  </div>
                  {invalidRange && <p className="mt-2 text-sm text-red-600" role="alert">El rango debe estar entre 1 y #{partition.data.current_sequence}.</p>}
                  <Button className="mt-4 w-full justify-center" onClick={() => checkpoint.mutate(undefined)} disabled={checkpoint.isPending || invalidRange || partition.data.current_sequence === 0}>{checkpoint.isPending ? 'Creando checkpoint…' : 'Crear checkpoint verificable'}</Button>
                  {checkpoint.error && <p className="mt-3 text-sm text-red-600" role="alert">{checkpoint.error}</p>}
                </div>
              ) : <Alert variant="warning">No tienes la capacidad para crear checkpoints.</Alert>}
            </div>
          </section>

          {createdCheckpoint && (
            <section className="rounded-3xl border border-emerald-200 bg-emerald-50 p-6 shadow-sm" aria-live="polite">
              <div className="flex items-start gap-4"><span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-emerald-600 text-white"><LogisticsIcon name="check" size={21} aria-hidden="true" /></span><div className="min-w-0"><p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">Checkpoint creado</p><h2 className="mt-1 text-lg font-bold text-emerald-950">Rango #{createdCheckpoint.from_sequence}–#{createdCheckpoint.to_sequence}</h2><p className="mt-2 break-all font-mono text-xs text-emerald-800">Manifest: {createdCheckpoint.manifest_hash}</p></div></div>
            </section>
          )}
        </>
      )}
    </div>
  )
}
