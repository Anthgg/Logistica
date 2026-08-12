import type { QualityPlanConflict, QualityPlanConflictLevel } from '../types/quality-inspection-plans'
import { Button } from '../../../components/common/Button'

interface QualityPlanConflictsPanelProps {
  conflicts: QualityPlanConflict[]
  onAction?: (action: string, conflict: QualityPlanConflict) => void
}

const LEVEL_STYLES: Record<QualityPlanConflictLevel, { row: string; badge: string; label: string }> = {
  INFO: { row: 'bg-blue-50/40', badge: 'bg-blue-100 text-blue-700', label: 'INFO' },
  WARNING: { row: 'bg-amber-50/40', badge: 'bg-amber-100 text-amber-700', label: 'WARNING' },
  ERROR: { row: 'bg-rose-50/40', badge: 'bg-rose-100 text-rose-700', label: 'ERROR' },
}

const CONFLICT_TYPE_LABELS: Record<string, string> = {
  SCOPE_OVERLAP: 'Solapamiento de ámbito',
  PRIORITY_CONFLICT: 'Conflicto de prioridad',
  VALIDITY_OVERLAP: 'Solapamiento de vigencia',
  PRODUCT_AMBIGUITY: 'Ambigüedad de producto',
}

export function QualityPlanConflictsPanel({ conflicts, onAction }: QualityPlanConflictsPanelProps) {
  if (conflicts.length === 0) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-4 text-xs">
        <h2 className="text-sm font-bold text-slate-800">Conflictos</h2>
        <p className="mt-2 text-slate-500">No se detectaron conflictos.</p>
      </div>
    )
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 text-xs">
      <h2 className="mb-3 text-sm font-bold text-slate-800">Conflictos ({conflicts.length})</h2>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-[11px]">
          <thead>
            <tr className="border-b border-slate-200 text-slate-500">
              <th className="pb-1 pr-2 font-medium">Plan actual</th>
              <th className="pb-1 pr-2 font-medium">Plan conflictivo</th>
              <th className="pb-1 pr-2 font-medium">Recurso</th>
              <th className="pb-1 pr-2 font-medium">Tipo</th>
              <th className="pb-1 pr-2 font-medium">Nivel</th>
              <th className="pb-1 pr-2 font-medium">Prioridad</th>
              <th className="pb-1 pr-2 font-medium">Especificidad</th>
              <th className="pb-1 pr-2 font-medium">Vigencia</th>
              <th className="pb-1 pr-2 font-medium">Regla</th>
              {onAction && <th className="pb-1 font-medium">Acciones</th>}
            </tr>
          </thead>
          <tbody>
            {conflicts.map((c) => {
              const lvl = LEVEL_STYLES[c.level]
              return (
                <tr key={c.conflict_id} className={`border-b border-slate-100 ${lvl.row}`}>
                  <td className="py-1.5 pr-2 font-semibold text-slate-800">{c.current_plan_code}</td>
                  <td className="py-1.5 pr-2 font-semibold text-slate-800">{c.conflicting_plan_code}</td>
                  <td className="py-1.5 pr-2">
                    {c.affected_resource_name}
                    <span className="ml-1 text-slate-400">({c.affected_scope_type})</span>
                  </td>
                  <td className="py-1.5 pr-2">{CONFLICT_TYPE_LABELS[c.conflict_type] ?? c.conflict_type}</td>
                  <td className="py-1.5 pr-2">
                    <span className={`inline-flex rounded-full px-1.5 py-0.5 text-[10px] font-semibold ${lvl.badge}`}>
                      {lvl.label}
                    </span>
                  </td>
                  <td className="py-1.5 pr-2">
                    <span className="text-slate-600">{c.current_priority}</span>
                    <span className="mx-0.5 text-slate-400">→</span>
                    <span className="text-slate-600">{c.conflicting_priority}</span>
                  </td>
                  <td className="py-1.5 pr-2">
                    <span className="text-slate-600">{c.current_specificity}</span>
                    <span className="mx-0.5 text-slate-400">→</span>
                    <span className="text-slate-600">{c.conflicting_specificity}</span>
                  </td>
                  <td className="py-1.5 pr-2 text-[10px] text-slate-500">
                    <div>{c.current_valid_from ?? '—'} → {c.current_valid_until ?? '—'}</div>
                    <div>{c.conflicting_valid_from ?? '—'} → {c.conflicting_valid_until ?? '—'}</div>
                  </td>
                  <td className="py-1.5 pr-2 text-slate-600">{c.rule_description}</td>
                  {onAction && (
                    <td className="py-1.5">
                      <div className="flex flex-wrap gap-1">
                        <Button variant="ghost" size="small" onClick={() => onAction('open_other', c)}>
                          Abrir
                        </Button>
                        <Button variant="ghost" size="small" onClick={() => onAction('modify_priority', c)}>
                          Prioridad
                        </Button>
                        <Button variant="ghost" size="small" onClick={() => onAction('modify_scope', c)}>
                          Ámbito
                        </Button>
                        <Button variant="ghost" size="small" onClick={() => onAction('create_exclusion', c)}>
                          Exclusión
                        </Button>
                        <Button variant="ghost" size="small" onClick={() => onAction('change_validity', c)}>
                          Vigencia
                        </Button>
                        <Button variant="ghost" size="small" onClick={() => onAction('request_review', c)}>
                          Revisión
                        </Button>
                      </div>
                    </td>
                  )}
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
