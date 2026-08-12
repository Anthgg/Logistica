import { useState } from 'react'
import { purchaseOrderLinesApi } from '../api/purchaseOrderLinesApi'
import type {
  PurchaseOrderCapabilities,
  PurchaseOrderLine,
} from '../types/purchase-orders-v2'
import { isDecimalString } from '../format'
import { EmptyState, StatusPill } from './ui'
import { Modal, DecimalInput } from './ui'

export function PurchaseOrderLinesEditor({
  purchaseOrderId,
  lines,
  currency,
  capabilities,
  onChanged,
}: {
  purchaseOrderId: string
  lines: PurchaseOrderLine[]
  currency: string
  capabilities: PurchaseOrderCapabilities
  onChanged: () => void
}) {
  const [editing, setEditing] = useState<PurchaseOrderLine | null>(null)

  const readOnly = !capabilities.can_manage_lines

  return (
    <div className="space-y-3">
      <p className="text-xs text-slate-500">
        Producto y proveedor solo lectura. Cantidades y precios como strings. No se usa Number. No se supera la cantidad adjudicada. Backend recalcula.
      </p>

      {lines.length === 0 ? (
        <EmptyState title="Sin líneas" description="Las líneas se generan desde la decisión." />
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200">
          <table className="min-w-full divide-y divide-slate-200 text-xs">
            <thead className="bg-slate-50/60 font-semibold uppercase text-slate-500">
              <tr>
                <th className="px-2 py-2.5 text-left">N.º</th>
                <th className="px-3 py-2.5 text-left">SKU</th>
                <th className="px-3 py-2.5 text-left">Producto</th>
                <th className="px-3 py-2.5 text-right">Adjudicado</th>
                <th className="px-3 py-2.5 text-right">Ordenado</th>
                <th className="px-3 py-2.5 text-left">Unidad</th>
                <th className="px-3 py-2.5 text-right">Precio oferta</th>
                <th className="px-3 py-2.5 text-right">Precio OC</th>
                <th className="px-3 py-2.5 text-right">Descuento</th>
                <th className="px-3 py-2.5 text-right">Flete</th>
                <th className="px-3 py-2.5 text-right">Total</th>
                <th className="px-3 py-2.5 text-center">Variación</th>
                <th className="px-3 py-2.5 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {lines.map((l) => (
                <tr key={l.id} className="hover:bg-slate-50/60">
                  <td className="px-2 py-2 font-mono">{l.line_number}</td>
                  <td className="px-3 py-2 font-mono">{l.sku ?? '—'}</td>
                  <td className="px-3 py-2">{l.product_name}</td>
                  <td className="px-3 py-2 text-right font-mono">{l.awarded_quantity}</td>
                  <td className="px-3 py-2 text-right font-mono">{l.ordered_quantity}</td>
                  <td className="px-3 py-2">{l.unit}</td>
                  <td className="px-3 py-2 text-right font-mono">{l.offer_unit_price}</td>
                  <td className="px-3 py-2 text-right font-mono">{l.unit_price}</td>
                  <td className="px-3 py-2 text-right font-mono">
                    {l.discount_type && l.discount_type !== 'NONE' ? `${l.discount_value} (${l.discount_type})` : '—'}
                  </td>
                  <td className="px-3 py-2 text-right font-mono">{l.freight_amount ?? '—'}</td>
                  <td className="px-3 py-2 text-right font-mono">{l.line_total ?? '—'}</td>
                  <td className="px-3 py-2 text-center">
                    {l.has_variance ? <StatusPill tone="warning">Sí</StatusPill> : '—'}
                  </td>
                  <td className="px-3 py-2 text-right">
                    {!readOnly && !l.is_readonly && (
                      <button type="button" onClick={() => setEditing(l)} className="rounded border border-slate-200 px-2 py-0.5 text-[11px] font-semibold hover:bg-slate-50">Editar</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {editing && (
        <LineEditorDialog
          purchaseOrderId={purchaseOrderId}
          line={editing}
          currency={currency}
          onClose={() => setEditing(null)}
          onSaved={() => { setEditing(null); onChanged() }}
        />
      )}
    </div>
  )
}

function LineEditorDialog({
  purchaseOrderId,
  line,
  currency,
  onClose,
  onSaved,
}: {
  purchaseOrderId: string
  line: PurchaseOrderLine
  currency: string
  onClose: () => void
  onSaved: () => void
}) {
  const [quantity, setQuantity] = useState(line.ordered_quantity)
  const [price, setPrice] = useState(line.unit_price)
  const [discountType, setDiscountType] = useState<'NONE' | 'PERCENTAGE' | 'AMOUNT'>(line.discount_type ?? 'NONE')
  const [discountValue, setDiscountValue] = useState(line.discount_value ?? '')
  const [freight, setFreight] = useState(line.freight_amount ?? '')
  const [deliveryDate, setDeliveryDate] = useState(line.delivery_date ?? '')
  const [varianceReason, setVarianceReason] = useState(line.variance_reason ?? '')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const qValid = isDecimalString(quantity)
  const pValid = isDecimalString(price)
  const needsVariance = price !== line.offer_unit_price

  const handleSave = async () => {
    if (!qValid || !pValid) { setError('Cantidad o precio inválidos.'); return }
    if (needsVariance && !varianceReason.trim()) { setError('Cambio de precio requiere motivo de variación.'); return }
    setSubmitting(true)
    setError(null)
    try {
      await purchaseOrderLinesApi.update(purchaseOrderId, line.id, {
        ordered_quantity: quantity,
        unit_price: price,
        discount_type: discountType,
        discount_value: discountValue || null,
        freight_amount: freight || null,
        delivery_date: deliveryDate || null,
        variance_reason: varianceReason || null,
        row_version: line.row_version,
      })
      onSaved()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'No se pudo guardar la línea.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Modal
      open
      onOpenChange={(o) => !o && onClose()}
      title={`Línea ${line.line_number} · ${line.product_name}`}
      size="lg"
      footer={
        <>
          <button type="button" onClick={onClose} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50">Cancelar</button>
          <button type="button" disabled={submitting} onClick={handleSave} className="rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#173a55] disabled:opacity-50">{submitting ? 'Guardando…' : 'Guardar'}</button>
        </>
      }
    >
      <div className="space-y-3">
        {error && <p role="alert" className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700">{error}</p>}
        <div className="grid grid-cols-2 gap-3 text-xs">
          <div>
            <div className="text-slate-500">Cantidad adjudicada</div>
            <div className="font-mono font-semibold">{line.awarded_quantity} {line.unit}</div>
          </div>
          <div>
            <div className="text-slate-500">Precio oferta</div>
            <div className="font-mono font-semibold">{line.offer_unit_price} {currency}</div>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <DecimalInput label="Cantidad ordenada" value={quantity} onChange={setQuantity} invalid={!qValid} maxDecimals={6} />
          <DecimalInput label="Precio OC" value={price} onChange={setPrice} invalid={!pValid} maxDecimals={6} />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="mb-1 block text-xs font-bold text-slate-700">Tipo descuento</label>
            <select value={discountType} onChange={(e) => setDiscountType(e.target.value as 'NONE' | 'PERCENTAGE' | 'AMOUNT')} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm">
              <option value="NONE">Sin descuento</option>
              <option value="PERCENTAGE">Porcentaje</option>
              <option value="AMOUNT">Monto fijo</option>
            </select>
          </div>
          <DecimalInput label="Valor descuento" value={discountValue} onChange={setDiscountValue} maxDecimals={6} />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <DecimalInput label="Flete" value={freight} onChange={setFreight} maxDecimals={6} />
          <div>
            <label className="mb-1 block text-xs font-bold text-slate-700">Fecha entrega</label>
            <input type="date" value={deliveryDate} onChange={(e) => setDeliveryDate(e.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
          </div>
        </div>
        {needsVariance && (
          <div>
            <label className="mb-1 block text-xs font-bold text-slate-700">Motivo de variación <span className="text-rose-500">*</span></label>
            <textarea value={varianceReason} onChange={(e) => setVarianceReason(e.target.value)} rows={2} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
          </div>
        )}
        <p className="text-[11px] text-slate-500">El total lo recalcula el backend. No se supera la cantidad adjudicada.</p>
      </div>
    </Modal>
  )
}