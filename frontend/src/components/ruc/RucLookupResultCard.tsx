import { LogisticsIcon } from '../common/LogisticsIcon'
import type { RucAnnexAddress, RucLookupResponse } from '../../types/ruc-integration'
import { DataFreshnessIndicator } from './DataFreshnessIndicator'
import { DataSourceBadge } from './DataSourceBadge'
import { FieldProvenanceViewer } from './FieldProvenanceViewer'
import { RucAnnexAddressesPanel } from './RucAnnexAddressesPanel'
import { RucDataConflictsPanel } from './RucDataConflictsPanel'

interface Props {
  result: RucLookupResponse
  onProposeAnnexCandidate?: (annex: RucAnnexAddress) => void
  onApplyDataToPartner?: () => void
  isTechnicalUser?: boolean
}

export function RucLookupResultCard({
  result,
  onProposeAnnexCandidate,
  onApplyDataToPartner,
  isTechnicalUser = false,
}: Props) {
  const isActivo = result.taxpayer_status === 'ACTIVO'
  const isHabido = result.domicile_condition === 'HABIDO'

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-6">
      {/* Header with Title & Source Badges */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-slate-100 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-2xl font-bold text-slate-800">{result.ruc}</span>
            <DataSourceBadge source={result.source} label={result.source_label} />
          </div>
          <h3 className="text-lg font-bold text-slate-900 mt-1">{result.legal_name}</h3>
          {result.trade_name && (
            <p className="text-xs text-slate-500">Nombre comercial: {result.trade_name}</p>
          )}
        </div>

        <div className="flex flex-col items-start sm:items-end gap-2">
          <DataFreshnessIndicator
            freshnessStatus={result.freshness_status}
            sourceDate={result.source_date}
            ageInDays={result.age_in_days}
          />
          {onApplyDataToPartner && (
            <button
              type="button"
              onClick={onApplyDataToPartner}
              className="rounded-xl bg-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-indigo-700 transition-colors"
            >
              Aplicar datos a socio →
            </button>
          )}
        </div>
      </div>

      {/* Warnings & Alerts */}
      {result.warnings && result.warnings.length > 0 && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 space-y-1">
          <span className="text-xs font-bold text-amber-800 uppercase tracking-wider block">
            Advertencias de consulta
          </span>
          <ul className="list-disc list-inside text-xs text-amber-700 space-y-0.5">
            {result.warnings.map((w, idx) => (
              <li key={idx}>{w}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Key Fields Grid */}
      <div className="grid grid-cols-2 gap-4 rounded-xl border border-slate-100 bg-slate-50/70 p-4 sm:grid-cols-4 text-xs">
        <div>
          <span className="font-bold uppercase tracking-wider text-slate-400 block mb-1">
            Estado Contribuyente
          </span>
          <span
            className={`inline-block rounded-full px-2.5 py-0.5 font-bold ${
              isActivo ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'
            }`}
          >
            {result.taxpayer_status_label || result.taxpayer_status}
          </span>
        </div>

        <div>
          <span className="font-bold uppercase tracking-wider text-slate-400 block mb-1">
            Condición Domicilio
          </span>
          <span
            className={`inline-block rounded-full px-2.5 py-0.5 font-bold ${
              isHabido ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
            }`}
          >
            {result.domicile_condition_label || result.domicile_condition}
          </span>
        </div>

        <div>
          <span className="font-bold uppercase tracking-wider text-slate-400 block mb-1">
            Ubigeo Fiscal
          </span>
          <span className="font-mono font-medium text-slate-800">{result.ubigeo || '—'}</span>
        </div>

        <div>
          <span className="font-bold uppercase tracking-wider text-slate-400 block mb-1">
            Nivel de Confianza
          </span>
          <span className="font-bold text-slate-700">{result.confidence_level}</span>
        </div>
      </div>

      {/* Contextual Note */}
      <p className="text-[11px] text-slate-500 italic bg-blue-50/50 p-2.5 rounded-lg border border-blue-100 flex items-start gap-1.5">
        <LogisticsIcon name="info" size={14} aria-hidden /> <span><strong>Nota operativa:</strong> El estado tributario no equivale a aprobación interna como proveedor, cliente o transportista.</span>
      </p>

      {/* Fiscal Address if present */}
      {result.fiscal_address && (
        <div className="text-xs">
          <span className="font-bold uppercase tracking-wider text-slate-400 block mb-1">
            Dirección Fiscal Registrada
          </span>
          <p className="font-mono text-slate-800 bg-slate-50 p-2.5 rounded-lg border border-slate-200">
            {result.fiscal_address}
          </p>
        </div>
      )}

      {/* Conflicts if present */}
      <RucDataConflictsPanel conflicts={result.conflicts} />

      {/* Provenance by Field */}
      <FieldProvenanceViewer provenanceList={result.provenance_by_field} />

      {/* Annex Addresses */}
      <RucAnnexAddressesPanel
        annexes={result.annex_addresses}
        onProposeCandidate={onProposeAnnexCandidate}
      />

      {/* Technical Cache & Dataset Metadata */}
      {isTechnicalUser && (
        <div className="border-t border-slate-100 pt-3 text-[10px] text-slate-400 space-y-1 font-mono">
          <p>Dataset Version: {result.dataset_version || 'N/A'}</p>
          <p>Provider Used: {result.provider_used || 'None (Internal Padron)'}</p>
          <p>Cache State: {result.is_cached ? 'Cached Response' : 'Fresh Query'}</p>
          <p>Lookup DateTime: {new Date(result.lookup_date).toLocaleString('es-PE')}</p>
        </div>
      )}
    </div>
  )
}
