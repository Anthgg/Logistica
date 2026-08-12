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
import { InventoryLedgerPhaseNav } from '../components/InventoryLedgerPhaseNav'
import { InventoryLedgerContextEmptyState } from '../components/InventoryLedgerContextEmptyState'

export function PreparedInventoryEventsPage() {
  const navigate = useNavigate()
  const { hasPermission } = useLogisticsPermissions()
  const { currentContext } = useLogisticsAccess()
  const canView = hasPermission(LOGISTICS_PERMISSIONS.inventoryLedger.view)
  const organizationId = currentContext.organization_id

  const sourceTypes = useQuery<string[]>(
    ['inventory-ledger', 'source-types'],
    '/logistics/inventory/kardex/source-types',
    undefined,
    { enabled: canView },
  )

  const movementTypes = useQuery<string[]>(
    ['inventory-ledger', 'movement-types'],
    '/logistics/inventory/kardex/movement-types',
    undefined,
    { enabled: canView },
  )

  if (!canView) {
    return (
      <div className="space-y-4">
        <PageHeader title="Eventos preparados" />
        <Alert variant="error">No tienes permisos para consultar la integración del ledger.</Alert>
      </div>
    )
  }

  const pipeline = [
    { icon: 'route' as const, title: 'Adaptador fuente', description: 'Normaliza el evento del módulo operativo.' },
    { icon: 'check-square' as const, title: 'Validación', description: 'Comprueba dimensiones, cantidades y transición.' },
    { icon: 'lock' as const, title: 'Publicación idempotente', description: 'Registra el MOV una sola vez.' },
    { icon: 'shield' as const, title: 'Cadena íntegra', description: 'Encadena secuencia y hash en la partición.' },
  ]

  return (
    <div className="space-y-6 pb-10">
      <PageHeader
        eyebrow="Fase 044 · Ingesta"
        title="Eventos preparados"
        description="Superficie técnica de validación y publicación idempotente hacia el libro."
        actions={
          <Button variant="secondary" onClick={() => navigate('/logistics/inventory/ledger/movements')}>
            Ver movimientos publicados
          </Button>
        }
      />

      <InventoryLedgerPhaseNav />

      {!organizationId && (
        <InventoryLedgerContextEmptyState
          title="Selecciona el destino de publicación"
          description="Los catálogos técnicos pueden consultarse sin contexto, pero cada validación y publicación requiere una organización."
        />
      )}

      <section className="relative overflow-hidden rounded-3xl border border-slate-200 bg-slate-950 p-6 text-white shadow-sm md:p-8" aria-labelledby="prepared-pipeline-title">
        <div className="absolute -right-24 -top-24 h-72 w-72 rounded-full bg-blue-500/10" aria-hidden="true" />
        <div className="relative">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-orange-300">Pipeline controlado</p>
          <h2 id="prepared-pipeline-title" className="mt-2 text-2xl font-bold tracking-tight">Del evento fuente al movimiento inmutable</h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-300">La interfaz no permite construir líneas manualmente. Los módulos autorizados preparan el evento y el backend valida el contrato antes de publicarlo.</p>

          <ol className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {pipeline.map((step, index) => (
              <li key={step.title} className="relative rounded-2xl border border-white/10 bg-white/5 p-5">
                <div className="flex items-center justify-between"><span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-white/10 text-sky-300"><LogisticsIcon name={step.icon} size={19} aria-hidden="true" /></span><span className="text-xs font-semibold text-slate-500">0{index + 1}</span></div>
                <h3 className="mt-5 font-semibold text-white">{step.title}</h3>
                <p className="mt-2 text-sm leading-5 text-slate-300">{step.description}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <Alert variant="info">
        El backend actual publica validación y posting por identificador de evento; no ofrece un listado global de eventos preparados. Esta pantalla muestra únicamente catálogos y capacidades reales.
      </Alert>

      {(sourceTypes.isLoading || movementTypes.isLoading) && <LoadingSkeleton rows={6} />}

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm" aria-labelledby="source-adapters-title">
          <div className="flex items-center gap-3"><span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-blue-50 text-blue-700"><LogisticsIcon name="route" size={21} aria-hidden="true" /></span><div><p className="text-xs font-semibold uppercase tracking-wide text-orange-600">Registro técnico</p><h2 id="source-adapters-title" className="mt-1 text-lg font-bold text-slate-950">Adaptadores habilitados</h2></div></div>
          <div className="mt-5 flex flex-wrap gap-2">
            {(sourceTypes.data ?? []).length === 0 ? <p className="text-sm text-slate-500">No hay adaptadores declarados.</p> : sourceTypes.data?.map((source) => <span key={source} className="rounded-xl border border-blue-100 bg-blue-50 px-3 py-2 text-sm font-semibold text-blue-800">{source}</span>)}
          </div>
        </section>

        <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm" aria-labelledby="movement-types-title">
          <div className="flex items-center gap-3"><span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-violet-50 text-violet-700"><LogisticsIcon name="package" size={21} aria-hidden="true" /></span><div><p className="text-xs font-semibold uppercase tracking-wide text-orange-600">Contrato de dominio</p><h2 id="movement-types-title" className="mt-1 text-lg font-bold text-slate-950">Movimientos admitidos</h2></div></div>
          <div className="mt-5 max-h-72 overflow-y-auto pr-1">
            <div className="grid gap-2 sm:grid-cols-2">
              {(movementTypes.data ?? []).length === 0 ? <p className="text-sm text-slate-500">No hay tipos declarados.</p> : movementTypes.data?.map((type) => <div key={type} className="flex items-center gap-2 rounded-xl bg-slate-50 px-3 py-2 text-xs font-medium text-slate-700"><span className="h-1.5 w-1.5 shrink-0 rounded-full bg-violet-500" aria-hidden="true" />{type}</div>)}
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}
