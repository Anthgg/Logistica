import type { ReceptionDifferenceItem } from '../../types/reception-differences'

interface DamageDifferencePanelProps {
  item: ReceptionDifferenceItem
}

export function DamageDifferencePanel({ item }: DamageDifferencePanelProps) {
  const damage = item.damage_detail

  return (
    <div className="space-y-3 text-xs">
      <div className="grid grid-cols-2 gap-3">
        <InfoCell label="Producto" value={`${item.product.name} (${item.product.sku})`} />
        <InfoCell label="Cantidad afectada" value={`${item.observed_quantity} ${item.unit.symbol}`} />
        {damage?.damage_type && <InfoCell label="Tipo de daño" value={damage.damage_type} />}
        {damage?.damage_scope && <InfoCell label="Alcance" value={damage.damage_scope} />}
        {damage?.functional_impact && <InfoCell label="Impacto funcional" value={damage.functional_impact} />}
      </div>

      {damage?.safety_risk && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-2 text-rose-700">
          Riesgo de seguridad reportado
        </div>
      )}
      {damage?.possible_contamination && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-2 text-rose-700">
          Posible contaminación
        </div>
      )}
      {damage?.temperature_concern && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-2 text-amber-700">
          Preocupación de temperatura
        </div>
      )}

      <InfoCell label="Descripción" value={item.description ?? '—'} />
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
