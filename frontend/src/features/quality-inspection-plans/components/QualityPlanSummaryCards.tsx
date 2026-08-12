import type { QualityInspectionPlanSummary } from '../types/quality-inspection-plans'

interface QualityPlanSummaryCardsProps {
  summary: QualityInspectionPlanSummary | null
}

interface CardDef {
  label: string
  key: keyof QualityInspectionPlanSummary
  color: string
  icon: string
}

const CARDS: CardDef[] = [
  { label: 'Planes activos', key: 'active_plans', color: 'border-emerald-200 bg-emerald-50', icon: '●' },
  { label: 'Versiones borrador', key: 'draft_versions', color: 'border-slate-200 bg-slate-50', icon: '○' },
  { label: 'Versiones programadas', key: 'scheduled_versions', color: 'border-amber-200 bg-amber-50', icon: '◐' },
  { label: 'Planes con conflictos', key: 'plans_with_conflicts', color: 'border-rose-200 bg-rose-50', icon: '!' },
  { label: 'Productos con plan', key: 'products_with_plan', color: 'border-blue-200 bg-blue-50', icon: '□' },
  { label: 'Categorías con plan', key: 'categories_with_plan', color: 'border-indigo-200 bg-indigo-50', icon: '▢' },
  { label: 'Planes con temperatura', key: 'plans_with_temperature', color: 'border-orange-200 bg-orange-50', icon: '🌡' },
  { label: 'Planes con certificados', key: 'plans_with_certificates', color: 'border-purple-200 bg-purple-50', icon: '📋' },
  { label: 'Versiones por vencer', key: 'versions_expiring_soon', color: 'border-amber-200 bg-amber-50', icon: '⏰' },
]

export function QualityPlanSummaryCards({ summary }: QualityPlanSummaryCardsProps) {
  if (!summary) {
    return (
      <div className="space-y-3">
        <h3 className="text-sm font-bold text-slate-800">Resumen de planes de calidad</h3>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-5">
          {CARDS.map((card) => (
            <div
              key={card.key}
              className="animate-pulse rounded-lg border border-slate-200 bg-white p-3"
            >
              <div className="h-3 w-16 rounded bg-slate-200" />
              <div className="mt-2 h-6 w-10 rounded bg-slate-100" />
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold text-slate-800">Resumen de planes de calidad</h3>
        <span className="text-xs text-slate-500">
          {summary.total_plans} plan{summary.total_plans !== 1 ? 'es' : ''} total
          {summary.products_without_plan !== null && (
            <> · {summary.products_without_plan} producto{summary.products_without_plan !== 1 ? 's' : ''} sin plan</>
          )}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-5">
        {CARDS.map((card) => {
          const value = summary[card.key]
          const numValue = typeof value === 'number' ? value : 0
          const isHigh = card.key === 'plans_with_conflicts' || card.key === 'versions_expiring_soon'

          return (
            <div
              key={card.key}
              className={`rounded-lg border p-3 ${card.color} transition-colors`}
            >
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-semibold uppercase text-slate-500">
                  {card.label}
                </span>
                <span className="text-sm" aria-hidden="true">{card.icon}</span>
              </div>
              <p className={`mt-1 text-lg font-bold ${isHigh && numValue > 0 ? 'text-rose-700' : 'text-slate-800'}`}>
                {numValue}
              </p>
            </div>
          )
        })}
      </div>
    </div>
  )
}
