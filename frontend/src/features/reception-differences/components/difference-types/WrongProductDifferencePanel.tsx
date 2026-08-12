import type { ReceptionDifferenceItem } from '../../types/reception-differences'

interface WrongProductDifferencePanelProps {
  item: ReceptionDifferenceItem
}

export function WrongProductDifferencePanel({ item }: WrongProductDifferencePanelProps) {
  return (
    <div className="space-y-3 text-xs">
      <div className="grid grid-cols-2 gap-4">
        <div className="rounded-lg border border-slate-200 p-3">
          <p className="mb-1 text-[10px] font-semibold uppercase text-slate-400">Esperado</p>
          <p className="font-semibold text-slate-800">{item.product.name}</p>
          <p className="text-slate-500">SKU: {item.product.sku}</p>
        </div>
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-3">
          <p className="mb-1 text-[10px] font-semibold uppercase text-rose-400">Observado</p>
          <p className="font-semibold text-rose-800">{item.product.name}</p>
          <p className="text-rose-600">SKU: {item.product.sku}</p>
          <p className="text-rose-600">Cantidad: {item.observed_quantity} {item.unit.symbol}</p>
        </div>
      </div>

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
