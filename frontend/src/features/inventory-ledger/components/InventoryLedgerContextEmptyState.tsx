import { LogisticsIcon } from '../../../components/common/LogisticsIcon'
import { LogisticsContextSwitcher } from '../../../components/logistics/LogisticsContextSwitcher'

interface InventoryLedgerContextEmptyStateProps {
  title?: string
  description?: string
}

export function InventoryLedgerContextEmptyState({
  title = 'Selecciona una organización',
  description = 'El libro de inventario se consulta dentro de un contexto organizacional concreto.',
}: InventoryLedgerContextEmptyStateProps) {
  return (
    <section className="relative overflow-hidden rounded-3xl border border-slate-200 bg-white p-6 shadow-sm md:p-9">
      <div className="absolute -right-20 -top-24 h-64 w-64 rounded-full bg-blue-50" aria-hidden="true" />
      <div className="relative max-w-2xl">
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-50 text-blue-700 ring-1 ring-blue-100">
          <LogisticsIcon name="building" size={25} aria-hidden="true" />
        </div>
        <p className="mt-6 text-xs font-semibold uppercase tracking-[0.18em] text-orange-600">
          Contexto requerido
        </p>
        <h2 className="mt-2 text-2xl font-bold tracking-tight text-slate-950">{title}</h2>
        <p className="mt-3 text-base leading-7 text-slate-600">{description}</p>
        <div className="mt-6 flex flex-wrap items-center gap-4">
          <LogisticsContextSwitcher compact />
          <span className="text-sm text-slate-500">La selección no modifica el ledger.</span>
        </div>
      </div>
    </section>
  )
}
