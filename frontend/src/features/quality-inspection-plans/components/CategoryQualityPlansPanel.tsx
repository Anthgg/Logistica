import { useQuery } from '../../inbound-docks/hooks/useQuery'
import { Button } from '../../../components/common/Button'
import type {
  QualityPlanScope,
  QualityPlanConflict,
  QualityInspectionPlan,
} from '../types/quality-inspection-plans'

interface CategoryQualityPlansPanelProps {
  categoryId: string
}

interface CategoryQualityPlansData {
  direct_plans: QualityInspectionPlan[]
  inherited_plans: QualityInspectionPlan[]
  exclusions: QualityPlanScope[]
  affected_products: number
  conflicts: QualityPlanConflict[]
  validity_from: string | null
  validity_until: string | null
}

const STATUS_LABELS: Record<string, string> = {
  DRAFT: 'Borrador',
  VALIDATED: 'Validado',
  SCHEDULED: 'Programado',
  ACTIVE: 'Activo',
  RETIRED: 'Retirado',
  ARCHIVED: 'Archivado',
}

const STATUS_COLORS: Record<string, string> = {
  DRAFT: 'bg-slate-100 text-slate-600',
  VALIDATED: 'bg-blue-100 text-blue-700',
  SCHEDULED: 'bg-amber-100 text-amber-700',
  ACTIVE: 'bg-emerald-100 text-emerald-700',
  RETIRED: 'bg-rose-100 text-rose-700',
  ARCHIVED: 'bg-slate-100 text-slate-500',
}

const CONFLICT_LEVEL_COLORS: Record<string, string> = {
  INFO: 'bg-blue-100 text-blue-700',
  WARNING: 'bg-amber-100 text-amber-700',
  ERROR: 'bg-rose-100 text-rose-700',
}

export function CategoryQualityPlansPanel({ categoryId }: CategoryQualityPlansPanelProps) {
  const query = useQuery<CategoryQualityPlansData>(
    ['category-quality-plans', categoryId],
    `/logistics/quality-inspection-plans/category-plans`,
    { category_id: categoryId },
    { enabled: !!categoryId },
  )

  const data = query.data
  const isLoading = query.isLoading
  const isError = query.isError

  if (isLoading) {
    return (
      <div className="space-y-3">
        <h3 className="text-sm font-bold text-slate-800">Planes de calidad de categoría</h3>
        <p className="text-xs text-slate-400">Cargando planes…</p>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="space-y-3">
        <h3 className="text-sm font-bold text-slate-800">Planes de calidad de categoría</h3>
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800">
          {query.error || 'Error al cargar los planes de la categoría.'}
        </div>
      </div>
    )
  }

  const directPlans = data?.direct_plans ?? []
  const inheritedPlans = data?.inherited_plans ?? []
  const exclusions = data?.exclusions ?? []
  const affectedProducts = data?.affected_products ?? 0
  const conflicts = data?.conflicts ?? []
  const validityFrom = data?.validity_from ?? null
  const validityUntil = data?.validity_until ?? null

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold text-slate-800">Planes de calidad de categoría</h3>
        <span className="text-xs text-slate-500">
          {directPlans.length + inheritedPlans.length} plan{directPlans.length + inheritedPlans.length !== 1 ? 'es' : ''}
        </span>
      </div>

      <div className="rounded-lg border border-slate-200 p-3 text-xs">
        <div className="grid grid-cols-2 gap-3">
          <InfoCell label="Productos afectados" value={String(affectedProducts)} />
          <InfoCell label="Exclusiones" value={String(exclusions.length)} />
          <InfoCell label="Validez desde" value={formatDate(validityFrom)} />
          <InfoCell label="Validez hasta" value={formatDate(validityUntil)} />
        </div>
      </div>

      {directPlans.length > 0 && (
        <div className="space-y-2">
          <p className="text-[10px] font-semibold uppercase text-slate-400">
            Planes directos ({directPlans.length})
          </p>
          {directPlans.map((plan) => (
            <PlanCard key={plan.plan_id} plan={plan} />
          ))}
        </div>
      )}

      {inheritedPlans.length > 0 && (
        <div className="space-y-2">
          <p className="text-[10px] font-semibold uppercase text-slate-400">
            Planes heredados ({inheritedPlans.length})
          </p>
          {inheritedPlans.map((plan) => (
            <PlanCard key={plan.plan_id} plan={plan} inherited />
          ))}
        </div>
      )}

      {exclusions.length > 0 && (
        <div className="space-y-2">
          <p className="text-[10px] font-semibold uppercase text-slate-400">
            Exclusiones ({exclusions.length})
          </p>
          {exclusions.map((exc) => (
            <div
              key={exc.scope_id}
              className="rounded-lg border border-rose-200 bg-rose-50 p-2 text-xs"
            >
              <div className="flex items-center justify-between">
                <span className="font-semibold text-rose-800">
                  {exc.scope_type === 'PRODUCT' ? exc.product_name : exc.category_name}
                </span>
                <span className="text-[10px] text-rose-500">{exc.action}</span>
              </div>
              {exc.branch_name && (
                <p className="text-rose-600">Sucursal: {exc.branch_name}</p>
              )}
              {exc.warehouse_name && (
                <p className="text-rose-600">Bodega: {exc.warehouse_name}</p>
              )}
            </div>
          ))}
        </div>
      )}

      {conflicts.length > 0 && (
        <div className="space-y-2">
          <p className="text-[10px] font-semibold uppercase text-slate-400">
            Conflictos ({conflicts.length})
          </p>
          {conflicts.map((c) => (
            <div
              key={c.conflict_id}
              className="rounded-lg border border-amber-200 bg-amber-50 p-2 text-xs"
            >
              <div className="flex items-center justify-between">
                <span className="font-semibold text-amber-800">
                  {c.conflict_type.replace(/_/g, ' ')}
                </span>
                <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${CONFLICT_LEVEL_COLORS[c.level]}`}>
                  {c.level}
                </span>
              </div>
              <p className="text-amber-700">{c.rule_description}</p>
              <p className="text-amber-600">
                Plan actual: {c.current_plan_code} · Plan en conflicto: {c.conflicting_plan_code}
              </p>
            </div>
          ))}
        </div>
      )}

      {directPlans.length === 0 && inheritedPlans.length === 0 && (
        <p className="text-xs text-slate-400">
          No hay planes de inspección asignados a esta categoría.
        </p>
      )}

      <div className="flex flex-wrap gap-2 pt-1">
        <Button variant="secondary" size="small">
          Ver todos los planes
        </Button>
        <Button variant="secondary" size="small">
          Agregar plan
        </Button>
      </div>
    </div>
  )
}

function PlanCard({ plan, inherited = false }: { plan: QualityInspectionPlan; inherited?: boolean }) {
  return (
    <div className="rounded-lg border border-slate-200 p-3 text-xs">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-slate-800">{plan.code}</span>
          {inherited && (
            <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-bold text-slate-500">
              Heredado
            </span>
          )}
        </div>
        <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${STATUS_COLORS[plan.status]}`}>
          {STATUS_LABELS[plan.status]}
        </span>
      </div>
      <p className="text-slate-600">{plan.name}</p>
      <div className="mt-1 flex flex-wrap gap-2 text-[10px] text-slate-500">
        <span>Familia: {plan.family}</span>
        <span>Controles: {plan.control_count}</span>
        <span>Productos: {plan.product_count}</span>
        <span>Prioridad: {plan.priority}</span>
        {plan.conflict_count > 0 && (
          <span className="text-amber-600">Conflictos: {plan.conflict_count}</span>
        )}
      </div>
    </div>
  )
}

function InfoCell({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[10px] font-semibold uppercase text-slate-400">{label}</p>
      <p className="text-slate-800">{value}</p>
    </div>
  )
}

function formatDate(date: string | null): string {
  if (!date) return '—'
  try {
    return new Date(date).toLocaleDateString('es-CL')
  } catch {
    return date
  }
}
