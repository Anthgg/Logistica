import type { FutureQuarantineRecommendation, FutureClaimPreparation, QualityInspectionPreparation } from '../types/reception-differences'

interface FutureQuarantineRecommendationsPanelProps {
  recommendations: FutureQuarantineRecommendation[]
}

export function FutureQuarantineRecommendationsPanel({ recommendations }: FutureQuarantineRecommendationsPanelProps) {
  return (
    <div className="space-y-3">
      <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800" role="status">
        Recomendación futura. La cuarentena todavía no ha sido creada.
      </div>

      {recommendations.length === 0 ? (
        <p className="text-xs text-slate-400">No hay recomendaciones de cuarentena.</p>
      ) : (
        <div className="space-y-2">
          {recommendations.map((r) => (
            <div key={r.recommendation_id} className="rounded-lg border border-slate-200 p-3 text-xs">
              <p className="font-semibold text-slate-800">{r.product.name} ({r.product.sku})</p>
              <p className="text-slate-500">{r.quantity} {r.unit.symbol} · {r.reason}</p>
              <p className="text-slate-600">{r.recommendation}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

interface FutureClaimPreparationPanelProps {
  preparation: FutureClaimPreparation | null
}

export function FutureClaimPreparationPanel({ preparation }: FutureClaimPreparationPanelProps) {
  if (!preparation) return <p className="text-xs text-slate-400">No hay información de reclamo disponible.</p>

  return (
    <div className="space-y-3">
      <div className="rounded-lg border border-blue-200 bg-blue-50 p-3 text-xs text-blue-800" role="status">
        Información preparada para un flujo futuro de reclamos. No existe un reclamo creado.
      </div>

      <div className="grid grid-cols-2 gap-3 text-xs">
        <InfoCell label="Proveedor" value={preparation.supplier?.name ?? '—'} />
        <InfoCell label="Transportista" value={preparation.carrier?.name ?? '—'} />
        <InfoCell label="Evidencias" value={String(preparation.evidence_count)} />
        <InfoCell label="Diferencias" value={String(preparation.differences.length)} />
      </div>
    </div>
  )
}

interface QualityInspectionPreparationPanelProps {
  preparation: QualityInspectionPreparation | null
}

export function QualityInspectionPreparationPanel({ preparation }: QualityInspectionPreparationPanelProps) {
  if (!preparation) return <p className="text-xs text-slate-400">No hay información de calidad disponible.</p>

  return (
    <div className="space-y-3">
      <div className="rounded-lg border border-purple-200 bg-purple-50 p-3 text-xs text-purple-800" role="status">
        La Fase 041 configurará los planes de calidad reutilizables.
      </div>

      <div className="text-xs">
        <InfoCell label="Severidad general" value={preparation.overall_severity} />
        <InfoCell label="Productos" value={String(preparation.products.length)} />
        <InfoCell label="Evidencias" value={String(preparation.evidence_count)} />
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
