import type { ReceptionDifferenceItem } from '../../types/reception-differences'

interface OverageDifferencePanelProps {
  item: ReceptionDifferenceItem
}

export function OverageDifferencePanel({ item }: OverageDifferencePanelProps) {
  return (
    <div className="space-y-3 text-xs">
      <div className="rounded-lg border border-blue-200 bg-blue-50 p-3 text-blue-800" role="alert">
        El sobrante no será incorporado al inventario en esta fase.
      </div>

      <div className="grid grid-cols-2 gap-3">
        <InfoCell label="Esperado" value={item.expected_quantity} />
        <InfoCell label="Observado" value={item.observed_quantity} />
        <InfoCell label="Sobrante" value={item.difference_quantity} highlight />
        <InfoCell label="Unidad" value={item.unit.symbol} />
      </div>

      <InfoCell label="Producto" value={`${item.product.name} (${item.product.sku})`} />
      <InfoCell label="Descripción" value={item.description ?? '—'} />
    </div>
  )
}

function InfoCell({ label, value, highlight = false }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div>
      <p className="text-[10px] font-semibold uppercase text-slate-400">{label}</p>
      <p className={`font-mono ${highlight ? 'font-bold text-blue-600' : 'text-slate-800'}`}>{value}</p>
    </div>
  )
}
