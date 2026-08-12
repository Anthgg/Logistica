import { useEffect, useState } from 'react'
import { productsCatalogApi } from '../../api/products-catalog-api'
import { Button } from '../common/Button'
import { DecimalQuantityInput } from './DecimalQuantityInput'
import type { Product } from '../../types/products-catalog'
import type { PurchaseRequisitionLineCreate } from '../../types/purchase-requisitions'

interface LinesEditorProps {
  lines: PurchaseRequisitionLineCreate[]
  onChange: (lines: PurchaseRequisitionLineCreate[]) => void
  defaultRequiredDate: string
  defaultWarehouseId: string
  disabled?: boolean
}

export function PurchaseRequisitionLinesEditor({
  lines,
  onChange,
  defaultRequiredDate,
  defaultWarehouseId,
  disabled = false,
}: LinesEditorProps) {
  const [products, setProducts] = useState<Product[]>([])
  const [loadingProducts, setLoadingProducts] = useState(false)

  // Search & Products
  useEffect(() => {
    setLoadingProducts(true)
    productsCatalogApi.list({ page_size: 100 })
      .then((res) => setProducts(res.items || []))
      .catch(() => setProducts([]))
      .finally(() => setLoadingProducts(false))
  }, [])

  const addLine = () => {
    if (products.length === 0) return
    const firstProd = products[0]
    const newLine: PurchaseRequisitionLineCreate = {
      product_id: firstProd.id,
      requested_quantity: '1',
      unit_of_measure_id: firstProd.base_unit,
      required_date: defaultRequiredDate || new Date().toISOString().split('T')[0],
      destination_warehouse_id: defaultWarehouseId,
      justification: '',
    }
    onChange([...lines, newLine])
  }

  const updateLine = (index: number, patch: Partial<PurchaseRequisitionLineCreate>) => {
    const next = [...lines]
    next[index] = { ...next[index], ...patch }
    onChange(next)
  }

  const removeLine = (index: number) => {
    onChange(lines.filter((_, idx) => idx !== index))
  }

  const duplicateLine = (index: number) => {
    const lineToCopy = lines[index]
    onChange([...lines, { ...lineToCopy }])
  }

  return (
    <div className="space-y-4 text-xs">
      <div className="flex items-center justify-between border-b border-slate-200 pb-3">
        <div>
          <h4 className="font-bold text-slate-800 text-sm">Líneas del Requerimiento ({lines.length})</h4>
          <p className="text-slate-500 text-[11px] mt-0.5">
            Agrega los artículos requeridos, las cantidades exactas y las fechas de entrega deseadas.
          </p>
        </div>
        {!disabled && (
          <Button size="small" type="button" onClick={addLine} disabled={loadingProducts || products.length === 0}>
            + Añadir Producto
          </Button>
        )}
      </div>

      {lines.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center space-y-3">
          <p className="text-slate-500 font-medium">El requerimiento no posee líneas agregadas.</p>
          {!disabled && (
            <Button size="small" type="button" onClick={addLine} disabled={loadingProducts}>
              + Añadir Primera Línea
            </Button>
          )}
        </div>
      ) : (
        <div className="space-y-3">
          {lines.map((line, idx) => {
            return (
              <div
                key={idx}
                className="rounded-2xl border border-slate-200 bg-white p-4 shadow-xs space-y-3"
              >
                <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                  <span className="font-bold text-slate-700">Línea N.º {idx + 1}</span>
                  {!disabled && (
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => duplicateLine(idx)}
                        className="font-semibold text-indigo-600 hover:underline"
                      >
                        Duplicar
                      </button>
                      <button
                        type="button"
                        onClick={() => removeLine(idx)}
                        className="font-semibold text-rose-600 hover:underline"
                      >
                        Eliminar
                      </button>
                    </div>
                  )}
                </div>

                <div className="grid grid-cols-1 gap-3 sm:grid-cols-4">
                  {/* Product */}
                  <div className="col-span-1 sm:col-span-2">
                    <label className="mb-1 block font-bold text-slate-700">Producto / SKU *</label>
                    <select
                      value={line.product_id}
                      onChange={(e) => {
                        const prod = products.find((p) => p.id === e.target.value)
                        updateLine(idx, {
                          product_id: e.target.value,
                          unit_of_measure_id: prod?.base_unit || line.unit_of_measure_id,
                        })
                      }}
                      disabled={disabled}
                      required
                      className="w-full rounded-lg border border-slate-300 px-3 py-2 bg-white font-medium text-slate-800"
                    >
                      {products.map((p) => (
                        <option key={p.id} value={p.id}>
                          [{p.sku}] {p.name} ({p.brand_name || 'Sin Marca'})
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Quantity */}
                  <div>
                    <label className="mb-1 block font-bold text-slate-700">Cantidad *</label>
                    <DecimalQuantityInput
                      value={line.requested_quantity}
                      onChange={(val) => updateLine(idx, { requested_quantity: val })}
                      disabled={disabled}
                      required
                    />
                  </div>

                  {/* Date */}
                  <div>
                    <label className="mb-1 block font-bold text-slate-700">Fecha Requerida *</label>
                    <input
                      type="date"
                      value={line.required_date}
                      onChange={(e) => updateLine(idx, { required_date: e.target.value })}
                      disabled={disabled}
                      required
                      className="w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-800"
                    />
                  </div>
                </div>

                {/* Justification Line */}
                <div>
                  <input
                    type="text"
                    value={line.justification || ''}
                    onChange={(e) => updateLine(idx, { justification: e.target.value })}
                    disabled={disabled}
                    placeholder="Justificación específica para esta línea (opcional)..."
                    className="w-full rounded-lg border border-slate-200 px-3 py-1.5 text-[11px]"
                  />
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
