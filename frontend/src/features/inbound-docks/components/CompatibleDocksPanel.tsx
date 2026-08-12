import { StatusPill, EmptyPanel, SectionPanel } from './ui/Primitives'
import { compatibilityLabel, compatibilityTone, dockOperationalStatusLabel, dockOperationalStatusTone } from '../utils/format'
import type { DockCompatibilityResult } from '../types/inbound-docks'

export function CompatibleDocksPanel({
  compatible,
  incompatible,
  recommendedId,
  loading,
  onSelect,
}: {
  compatible: DockCompatibilityResult[]
  incompatible: DockCompatibilityResult[]
  recommendedId: string | null | undefined
  loading?: boolean
  onSelect?: (result: DockCompatibilityResult) => void
}) {
  if (loading) {
    return (
      <SectionPanel
        title="Compatibilidad de muelles"
        description="Calculada por el servidor para esta entrada de cola."
      >
        <p className="text-xs text-slate-500">Cargando compatibilidad…</p>
      </SectionPanel>
    )
  }
  if (!compatible.length && !incompatible.length) {
    return (
      <SectionPanel
        title="Compatibilidad de muelles"
        description="Calculada por el servidor para esta entrada de cola."
      >
        <EmptyPanel
          title="Sin muelles disponibles"
          description="No se obtuvo información de compatibilidad. Genera un plan para ver los resultados."
        />
      </SectionPanel>
    )
  }
  return (
    <div className="space-y-3">
      <SectionPanel
        title="Muelles compatibles"
        description={`${compatible.length} muelle(s) compatible(s)`}
      >
        <ul className="space-y-2">
          {compatible.map((c) => (
            <li
              key={c.dock_id}
              className="flex flex-col gap-1 rounded-lg border border-slate-200 bg-white p-3 text-xs"
            >
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-sm font-bold text-slate-800">{c.dock_code}</span>
                <span className="text-slate-500">{c.dock_name}</span>
                <StatusPill tone={compatibilityTone(c.compatibility_status)}>
                  {compatibilityLabel(c.compatibility_status)}
                </StatusPill>
                <StatusPill tone={dockOperationalStatusTone(c.operational_status)}>
                  {dockOperationalStatusLabel(c.operational_status)}
                </StatusPill>
                {c.recommendation_rank != null && (
                  <StatusPill tone="info">Ranking #{c.recommendation_rank}</StatusPill>
                )}
                {recommendedId === c.dock_id && (
                  <StatusPill tone="success">Recomendado</StatusPill>
                )}
              </div>
              {c.matched_capabilities.length > 0 && (
                <p className="text-[11px] text-slate-600">
                  <span className="font-semibold">Coincidencias:</span>{' '}
                  {c.matched_capabilities.join(', ')}
                </p>
              )}
              {c.warnings.length > 0 && (
                <ul className="list-disc pl-4 text-[11px] text-amber-700">
                  {c.warnings.map((w) => (
                    <li key={w}>{w}</li>
                  ))}
                </ul>
              )}
              {c.conflicts.length > 0 && (
                <ul className="list-disc pl-4 text-[11px] text-rose-700">
                  {c.conflicts.map((w) => (
                    <li key={w}>{w}</li>
                  ))}
                </ul>
              )}
              {c.missing_information.length > 0 && (
                <ul className="list-disc pl-4 text-[11px] text-slate-500">
                  {c.missing_information.map((w) => (
                    <li key={w}>{w}</li>
                  ))}
                </ul>
              )}
              {onSelect && (
                <div>
                  <button
                    type="button"
                    onClick={() => onSelect(c)}
                    className="rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-[11px] font-semibold text-white hover:bg-[#173a55]"
                  >
                    Asignar
                  </button>
                </div>
              )}
            </li>
          ))}
        </ul>
      </SectionPanel>
      {incompatible.length > 0 && (
        <SectionPanel
          title="Muelles no disponibles"
          description={`${incompatible.length} muelle(s) con restricciones o información incompleta. La asignación puede requerir override.`}
        >
          <ul className="space-y-2">
            {incompatible.map((c) => (
              <li
                key={c.dock_id}
                className="rounded-lg border border-rose-100 bg-rose-50/40 p-3 text-xs"
              >
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-sm font-bold text-slate-800">{c.dock_code}</span>
                  <span className="text-slate-500">{c.dock_name}</span>
                  <StatusPill tone={compatibilityTone(c.compatibility_status)}>
                    {compatibilityLabel(c.compatibility_status)}
                  </StatusPill>
                </div>
                {c.restriction_conflicts.length > 0 && (
                  <ul className="mt-1 list-disc pl-4 text-[11px] text-rose-700">
                    {c.restriction_conflicts.map((r) => (
                      <li key={r}>{r}</li>
                    ))}
                  </ul>
                )}
                {c.missing_capabilities.length > 0 && (
                  <ul className="mt-1 list-disc pl-4 text-[11px] text-amber-700">
                    {c.missing_capabilities.map((r) => (
                      <li key={r}>{r}</li>
                    ))}
                  </ul>
                )}
                {c.missing_information.length > 0 && (
                  <ul className="mt-1 list-disc pl-4 text-[11px] text-slate-500">
                    {c.missing_information.map((r) => (
                      <li key={r}>{r}</li>
                    ))}
                  </ul>
                )}
              </li>
            ))}
          </ul>
        </SectionPanel>
      )}
    </div>
  )
}
