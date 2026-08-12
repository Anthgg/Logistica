import type { PurchaseOrderLine } from '../../types/purchase-orders'

interface Props {
  lines: PurchaseOrderLine[]
  currency: string
}

function fmtDecimal(val: string, currency: string) {
  const n = parseFloat(val)
  return isNaN(n)
    ? val
    : n.toLocaleString('es-PE', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 4,
      }) +
        ' ' +
        currency
}

export function PurchaseOrderLineItemsTable({ lines, currency }: Props) {
  if (lines.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-slate-300 px-6 py-10 text-center text-sm text-slate-500">
        Sin líneas de detalle.
      </div>
    )
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 shadow-sm">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50">
          <tr>
            <th className="px-4 py-3 text-left font-semibold text-slate-600">#</th>
            <th className="px-4 py-3 text-left font-semibold text-slate-600">Producto</th>
            <th className="px-4 py-3 text-right font-semibold text-slate-600">Cantidad</th>
            <th className="px-4 py-3 text-right font-semibold text-slate-600">Precio unit.</th>
            <th className="px-4 py-3 text-right font-semibold text-slate-600">Impuesto</th>
            <th className="px-4 py-3 text-right font-semibold text-slate-600">Subtotal</th>
            <th className="px-4 py-3 text-right font-semibold text-slate-600">Total línea</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 bg-white">
          {lines.map((line) => (
            <tr key={line.id} className="transition-colors hover:bg-slate-50">
              <td className="px-4 py-3 text-slate-400">{line.line_number}</td>
              <td className="px-4 py-3">
                <p className="font-medium text-slate-800">{line.description}</p>
                <p className="text-xs text-slate-400">{line.unit_code}</p>
              </td>
              <td className="px-4 py-3 text-right tabular-nums text-slate-700">
                {parseFloat(line.quantity).toLocaleString('es-PE', { minimumFractionDigits: 2 })}
              </td>
              <td className="px-4 py-3 text-right tabular-nums text-slate-700">
                {fmtDecimal(line.unit_price, currency)}
              </td>
              <td className="px-4 py-3 text-right tabular-nums text-slate-500">
                {parseFloat(line.tax_rate).toFixed(2)}%
              </td>
              <td className="px-4 py-3 text-right tabular-nums text-slate-700">
                {fmtDecimal(line.subtotal_amount, currency)}
              </td>
              <td className="px-4 py-3 text-right tabular-nums font-semibold text-slate-800">
                {fmtDecimal(line.total_amount, currency)}
              </td>
            </tr>
          ))}
        </tbody>
        <tfoot className="bg-slate-50">
          <tr>
            <td colSpan={6} className="px-4 py-3 text-right text-sm font-semibold text-slate-600">
              Total OC
            </td>
            <td className="px-4 py-3 text-right text-sm font-bold text-slate-800 tabular-nums">
              {fmtDecimal(
                lines
                  .reduce((sum, l) => sum + parseFloat(l.total_amount || '0'), 0)
                  .toFixed(2),
                currency,
              )}
            </td>
          </tr>
        </tfoot>
      </table>
    </div>
  )
}
