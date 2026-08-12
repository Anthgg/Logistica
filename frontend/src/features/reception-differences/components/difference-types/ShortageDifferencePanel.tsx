import type { ReceptionDifferenceItem } from '../../types/reception-differences'

interface ShortageDifferencePanelProps {
  item: ReceptionDifferenceItem
}

export function ShortageDifferencePanel({ item }: ShortageDifferencePanelProps) {
  return (
    <div className="space-y-3 text-xs">
      <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-amber-800" role="alert">
        Una recepción parcial no equivale automáticamente a un faltante formal.
      </div>

      <div className="grid grid-cols-2 gap-3">
        <InfoCell label="Ordenado" value={item.expected_quantity} />
        <InfoCell label="Observado" value={item.observed_quantity} />
        <InfoCell label="Diferencia" value={item.difference_quantity} highlight />
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
      <p className={`font-mono ${highlight ? 'font-bold text-rose-600' : 'text-slate-800'}`}>{value}</p>
    </div>
  )
}
