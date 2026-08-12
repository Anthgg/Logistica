import type { RucAnnexAddress } from '../../types/ruc-integration'
import { DataSourceBadge } from './DataSourceBadge'

interface Props {
  annexes: RucAnnexAddress[]
  onProposeCandidate?: (annex: RucAnnexAddress) => void
}

export function RucAnnexAddressesPanel({ annexes, onProposeCandidate }: Props) {
  if (!annexes || annexes.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-slate-200 p-6 text-center text-xs text-slate-500">
        No se registran locales anexos en el padrón para este RUC.
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">
          Locales Anexos ({annexes.length})
        </h4>
      </div>

      <div className="space-y-2">
        {annexes.map((annex) => (
          <div
            key={annex.id}
            className="flex flex-col gap-2 rounded-xl border border-slate-200 bg-white p-3.5 sm:flex-row sm:items-center sm:justify-between hover:border-slate-300 transition-colors"
          >
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="font-medium text-xs text-slate-800">{annex.address}</span>
                {annex.ubigeo && (
                  <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-mono text-slate-600">
                    Ubigeo {annex.ubigeo}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2 text-[11px] text-slate-500">
                <span>
                  {[annex.district, annex.province, annex.department].filter(Boolean).join(', ')}
                </span>
                <DataSourceBadge source={annex.source} label={annex.source_label} size="sm" />
              </div>
            </div>

            {onProposeCandidate && (
              <button
                type="button"
                onClick={() => onProposeCandidate(annex)}
                className="shrink-0 rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100 transition-colors"
              >
                Proponer como candidata
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
