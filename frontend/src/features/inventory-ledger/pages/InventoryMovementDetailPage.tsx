import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
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
import type {
  InventoryMovementDetailApi,
  InventoryMovementIntegrityApi,
} from '../types/inventory-ledger-api'

type DetailTab = 'summary' | 'lines' | 'sources' | 'positions' | 'integrity' | 'audit'

const TABS: Array<{ id: DetailTab; label: string; icon: 'dashboard' | 'list' | 'route' | 'location' | 'shield' | 'key' }> = [
  { id: 'summary', label: 'Resumen', icon: 'dashboard' },
  { id: 'lines', label: 'Líneas', icon: 'list' },
  { id: 'sources', label: 'Fuentes', icon: 'route' },
  { id: 'positions', label: 'Posiciones', icon: 'location' },
  { id: 'integrity', label: 'Integridad', icon: 'shield' },
  { id: 'audit', label: 'Capacidades', icon: 'key' },
]

function ShortId({ value }: { value: string | null | undefined }) {
  return <span className="font-mono text-xs text-slate-600">{value ? `${value.slice(0, 12)}…` : '—'}</span>
}

interface Props {
  section?: DetailTab
}

export function InventoryMovementDetailPage({ section }: Props) {
  const navigate = useNavigate()
  const { movementId = '' } = useParams()
  const { hasPermission } = useLogisticsPermissions()
  const { currentContext } = useLogisticsAccess()
  const canView = hasPermission(LOGISTICS_PERMISSIONS.inventoryLedger.view)
  const organizationId = currentContext.organization_id
  const [activeTab, setActiveTab] = useState<DetailTab>(section ?? 'summary')

  const movement = useQuery<InventoryMovementDetailApi>(
    ['inventory-movement', organizationId, movementId],
    `/logistics/inventory/movements/${movementId}`,
    organizationId ? { organization_id: organizationId } : undefined,
    { enabled: canView && Boolean(organizationId) && Boolean(movementId) },
  )

  const integrity = useQuery<InventoryMovementIntegrityApi>(
    ['inventory-movement', organizationId, movementId, 'integrity'],
    `/logistics/inventory/movements/${movementId}/integrity`,
    organizationId ? { organization_id: organizationId } : undefined,
    {
      enabled:
        canView &&
        Boolean(organizationId) &&
        Boolean(movementId) &&
        activeTab === 'integrity',
    },
  )

  if (!canView) {
    return (
      <div className="space-y-4">
        <PageHeader title="Detalle del movimiento" />
        <Alert variant="error">No tienes permisos para ver este movimiento.</Alert>
      </div>
    )
  }

  const data = movement.data
  const record = data?.movement

  return (
    <div className="space-y-6 pb-10">
      <PageHeader
        eyebrow={record ? `Fase 044 · Secuencia #${record.ledger_sequence}` : 'Fase 044 · Movimiento'}
        title={record?.movement_code ?? 'Detalle del movimiento'}
        description={record ? `${record.movement_type} · ${record.movement_family}` : 'Evidencia técnica del libro append-only.'}
        actions={
          <Button variant="secondary" onClick={() => navigate('/logistics/inventory/ledger/movements')}>
            Volver a movimientos
          </Button>
        }
      />

      <InventoryLedgerPhaseNav />

      {!organizationId && (
        <InventoryLedgerContextEmptyState
          title="Selecciona la organización del movimiento"
          description="El identificador del movimiento solo se resuelve dentro de su contexto organizacional."
        />
      )}

      {movement.isLoading && <LoadingSkeleton rows={8} />}

      {movement.isError && (
        <Alert variant="error">{getErrorMessage(movement.error)}</Alert>
      )}

      {record && data && (
        <>
          <section className="relative overflow-hidden rounded-3xl border border-slate-200 bg-slate-950 p-6 text-white shadow-sm md:p-8">
            <div className="absolute -right-20 -top-24 h-72 w-72 rounded-full bg-blue-500/10" aria-hidden="true" />
            <div className="relative flex flex-col justify-between gap-6 lg:flex-row lg:items-end">
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="rounded-full bg-emerald-400/15 px-3 py-1 text-xs font-semibold text-emerald-300">
                    {record.status}
                  </span>
                  <span className="rounded-full bg-white/10 px-3 py-1 text-xs font-semibold text-slate-200">
                    {record.valuation_status}
                  </span>
                </div>
                <h2 className="mt-5 text-2xl font-bold tracking-tight md:text-3xl">{record.movement_code}</h2>
                <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-300">
                  Publicado {new Date(record.posted_at).toLocaleString()} · Partición {record.ledger_partition_key}
                </p>
              </div>
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                {[
                  ['Secuencia', `#${record.ledger_sequence}`],
                  ['Líneas', record.line_count.toLocaleString()],
                  ['Cantidad base', record.total_base_quantity_reference ?? '—'],
                ].map(([label, value]) => (
                  <div key={String(label)} className="min-w-28 rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                    <p className="text-xs text-slate-400">{label}</p>
                    <p className="mt-1 font-semibold text-white">{String(value)}</p>
                  </div>
                ))}
              </div>
            </div>
          </section>

          <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white p-1.5 shadow-sm" role="tablist" aria-label="Detalle del movimiento">
            <div className="flex min-w-max gap-1">
              {TABS.map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  role="tab"
                  aria-selected={activeTab === tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`inline-flex min-h-10 items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 ${activeTab === tab.id ? 'bg-blue-600 text-white' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-950'}`}
                >
                  <LogisticsIcon name={tab.icon} size={16} aria-hidden="true" />
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          {activeTab === 'summary' && (
            <section className="grid gap-4 lg:grid-cols-2">
              <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
                <h2 className="text-lg font-bold text-slate-950">Identidad contable</h2>
                <dl className="mt-5 grid gap-4 sm:grid-cols-2">
                  {[
                    ['Organización', record.organization_id],
                    ['Sede', record.branch_id],
                    ['Almacén', record.warehouse_scope_id],
                    ['Versión de esquema', record.schema_version],
                    ['Canonización', record.canonicalization_version],
                    ['Código de motivo', record.reason_code],
                  ].map(([label, value]) => (
                    <div key={String(label)} className="rounded-2xl bg-slate-50 p-4">
                      <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</dt>
                      <dd className="mt-1 truncate text-sm font-semibold text-slate-900">{value ?? '—'}</dd>
                    </div>
                  ))}
                </dl>
              </div>

              <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
                <div className="flex items-center gap-3">
                  <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-700">
                    <LogisticsIcon name="shield" size={20} aria-hidden="true" />
                  </span>
                  <div>
                    <h2 className="text-lg font-bold text-slate-950">Cadena de integridad</h2>
                    <p className="text-sm text-slate-500">Hash encadenado del movimiento.</p>
                  </div>
                </div>
                <dl className="mt-5 space-y-4">
                  <div className="rounded-2xl border border-slate-200 p-4">
                    <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">Hash anterior</dt>
                    <dd className="mt-2 break-all font-mono text-xs text-slate-700">{record.previous_movement_hash ?? 'Inicio de cadena'}</dd>
                  </div>
                  <div className="rounded-2xl border border-slate-200 p-4">
                    <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">Hash del movimiento</dt>
                    <dd className="mt-2 break-all font-mono text-xs text-slate-700">{record.movement_hash}</dd>
                  </div>
                </dl>
              </div>
            </section>
          )}

          {activeTab === 'lines' && (
            <section className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
              <div className="border-b border-slate-200 px-5 py-4">
                <h2 className="font-bold text-slate-950">Líneas del movimiento</h2>
                <p className="mt-1 text-sm text-slate-500">{data.lines.length} línea(s) inmutables.</p>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200 text-sm">
                  <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
                    <tr><th className="px-5 py-3">Línea</th><th className="px-5 py-3">Producto</th><th className="px-5 py-3">Dirección</th><th className="px-5 py-3">Cantidad</th><th className="px-5 py-3">Cantidad base</th><th className="px-5 py-3">Hash</th></tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {data.lines.map((line) => (
                      <tr key={line.id} className="hover:bg-slate-50">
                        <td className="px-5 py-4 font-semibold text-slate-900">#{line.line_number}</td>
                        <td className="px-5 py-4"><ShortId value={line.product_id} /></td>
                        <td className="px-5 py-4 text-slate-600">{line.quantity_direction}</td>
                        <td className="px-5 py-4 font-medium text-slate-900">{line.quantity}</td>
                        <td className="px-5 py-4 text-slate-600">{line.base_quantity}</td>
                        <td className="px-5 py-4"><ShortId value={line.content_hash} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}

          {activeTab === 'sources' && (
            <section className="grid gap-4 lg:grid-cols-2">
              {data.sources.length === 0 ? (
                <Alert variant="info">Este movimiento no declara fuentes adicionales.</Alert>
              ) : data.sources.map((source) => (
                <article key={source.id} className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
                  <div className="flex items-start justify-between gap-4">
                    <div><p className="text-xs font-semibold uppercase tracking-wide text-orange-600">{source.source_system}</p><h2 className="mt-1 font-bold text-slate-950">{source.source_event_type}</h2></div>
                    <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">v{source.source_event_version}</span>
                  </div>
                  <dl className="mt-5 space-y-3 text-sm">
                    <div className="flex justify-between gap-4"><dt className="text-slate-500">Evento</dt><dd className="truncate font-mono text-xs text-slate-800">{source.source_event_id}</dd></div>
                    <div className="flex justify-between gap-4"><dt className="text-slate-500">Adaptador</dt><dd className="font-medium text-slate-800">{source.adapter_name} · {source.adapter_version}</dd></div>
                    <div className="flex justify-between gap-4"><dt className="text-slate-500">Documento</dt><dd className="font-medium text-slate-800">{source.source_document_code ?? '—'}</dd></div>
                  </dl>
                </article>
              ))}
            </section>
          )}

          {activeTab === 'positions' && (
            <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {data.positions.map((position) => (
                <article key={position.id} className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
                  <div className="flex items-center gap-3"><span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-violet-50 text-violet-700"><LogisticsIcon name="location" size={19} aria-hidden="true" /></span><div><h2 className="font-bold text-slate-950">{position.boundary_type}</h2><ShortId value={position.id} /></div></div>
                  <dl className="mt-5 grid grid-cols-2 gap-3 text-sm">
                    {[['Disponibilidad', position.availability_state], ['Calidad', position.quality_state], ['Tránsito', position.transit_state], ['Daño', position.damage_state], ['Expiración', position.expiration_state], ['Almacén', position.warehouse_id?.slice(0, 8) ?? '—']].map(([label, value]) => <div key={String(label)} className="rounded-xl bg-slate-50 p-3"><dt className="text-xs text-slate-500">{label}</dt><dd className="mt-1 font-semibold text-slate-900">{value}</dd></div>)}
                  </dl>
                </article>
              ))}
            </section>
          )}

          {activeTab === 'integrity' && (
            <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
              {integrity.isLoading && <LoadingSkeleton rows={4} />}
              {integrity.isError && <Alert variant="error">{getErrorMessage(integrity.error)}</Alert>}
              {integrity.data && (
                <div className="grid gap-5 lg:grid-cols-[0.75fr_1.25fr]">
                  <div className="rounded-3xl bg-emerald-50 p-6 text-emerald-950">
                    <LogisticsIcon name="shield" size={28} aria-hidden="true" />
                    <p className="mt-5 text-xs font-semibold uppercase tracking-wide text-emerald-700">Verificación</p>
                    <p className="mt-2 text-3xl font-bold">{integrity.data.verification_status}</p>
                    <p className="mt-2 text-sm text-emerald-800">Secuencia #{integrity.data.last_sequence ?? '—'}</p>
                  </div>
                  <dl className="space-y-3">
                    <div className="rounded-2xl border border-slate-200 p-4"><dt className="text-xs uppercase tracking-wide text-slate-500">Primer hash</dt><dd className="mt-2 break-all font-mono text-xs text-slate-700">{integrity.data.first_hash ?? '—'}</dd></div>
                    <div className="rounded-2xl border border-slate-200 p-4"><dt className="text-xs uppercase tracking-wide text-slate-500">Último hash</dt><dd className="mt-2 break-all font-mono text-xs text-slate-700">{integrity.data.last_hash ?? '—'}</dd></div>
                    <div className="flex flex-wrap gap-2 text-xs"><span className="rounded-full bg-slate-100 px-3 py-1 font-semibold text-slate-600">{integrity.data.hash_algorithm}</span><span className="rounded-full bg-slate-100 px-3 py-1 font-semibold text-slate-600">Canon {integrity.data.algorithm_version}</span></div>
                  </dl>
                </div>
              )}
            </section>
          )}

          {activeTab === 'audit' && (
            <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-bold text-slate-950">Capacidades efectivas</h2>
              <p className="mt-1 text-sm text-slate-500">Permisos devueltos por el backend para este movimiento.</p>
              <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {Object.entries(data.capabilities).map(([capability, enabled]) => (
                  <div key={capability} className="flex items-center gap-3 rounded-2xl border border-slate-200 p-4">
                    <span className={`flex h-8 w-8 items-center justify-center rounded-full ${enabled ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-400'}`}><LogisticsIcon name={enabled ? 'check' : 'x'} size={16} aria-hidden="true" /></span>
                    <span className="text-sm font-medium text-slate-700">{capability.replace(/^can_/, '').replaceAll('_', ' ')}</span>
                  </div>
                ))}
              </div>
            </section>
          )}
        </>
      )}
    </div>
  )
}
