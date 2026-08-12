import { LogisticsContextSwitcher } from '../../../components/logistics/LogisticsContextSwitcher'
import { LogisticsIcon } from '../../../components/common/LogisticsIcon'

interface PutawayContextEmptyStateProps {
  title: string
  description: string
}

export function PutawayContextEmptyState({ title, description }: PutawayContextEmptyStateProps) {
  return (
    <section className="relative overflow-hidden rounded-3xl border border-slate-200 bg-white p-7 shadow-sm md:p-10" aria-labelledby="putaway-context-title">
      <div className="absolute -right-20 -top-24 h-72 w-72 rounded-full bg-blue-50" aria-hidden="true" />
      <div className="relative max-w-2xl">
        <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-50 text-blue-700 ring-1 ring-blue-100"><LogisticsIcon name="location" size={25} aria-hidden="true" /></span>
        <p className="mt-6 text-xs font-semibold uppercase tracking-[0.17em] text-orange-600">Contexto requerido</p>
        <h2 id="putaway-context-title" className="mt-2 text-2xl font-bold tracking-tight text-slate-950 md:text-3xl">{title}</h2>
        <p className="mt-3 max-w-xl text-sm leading-6 text-slate-600 md:text-base">{description}</p>
        <div className="mt-7 flex flex-wrap items-center gap-4"><LogisticsContextSwitcher compact /><span className="text-sm text-slate-500">La selección define el alcance operativo.</span></div>
      </div>
    </section>
  )
}
