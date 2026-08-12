import { useEffect, useState, type FormEvent } from 'react'
import { businessPartnersApi } from '../../api/business-partners-api'
import { productsCatalogApi } from '../../api/products-catalog-api'
import { Alert } from '../common/Alert'
import { Button } from '../common/Button'
import type { BusinessPartner } from '../../types/business-partners'
import type { Product } from '../../types/products-catalog'
import type {
  PurchaseOrderCreate,
  PurchaseOrderLineCreate,
} from '../../types/purchase-orders'

interface Props {
  isOpen: boolean
  isSubmitting: boolean
  error: string | null
  onSubmit: (data: PurchaseOrderCreate) => void
  onClose: () => void
}

type ProductOption = Product & { base_unit_code?: string }
type FormLine = PurchaseOrderLineCreate & { key: number }

let nextLineKey = 1

function emptyLine(): FormLine {
  return {
    key: nextLineKey++,
    product_id: '',
    description: '',
    unit_code: '',
    quantity: '1',
    unit_price: '0',
    tax_rate: '18',
  }
}

export function PurchaseOrderFormModal({
  isOpen,
  isSubmitting,
  error,
  onSubmit,
  onClose,
}: Props) {
  const [supplierId, setSupplierId] = useState('')
  const [currencyCode, setCurrencyCode] = useState('PEN')
  const [deliveryDate, setDeliveryDate] = useState('')
  const [notes, setNotes] = useState('')
  const [lines, setLines] = useState<FormLine[]>([emptyLine()])
  const [suppliers, setSuppliers] = useState<BusinessPartner[]>([])
  const [products, setProducts] = useState<ProductOption[]>([])
  const [optionsError, setOptionsError] = useState<string | null>(null)
  const [loadingOptions, setLoadingOptions] = useState(false)

  useEffect(() => {
    if (!isOpen) return
    setLoadingOptions(true)
    setOptionsError(null)
    Promise.all([
      businessPartnersApi.list({ role: 'SUPPLIER', status: 'ACTIVE' }),
      productsCatalogApi.list({ page: 1, page_size: 100, status: 'ACTIVE' }),
    ])
      .then(([supplierResponse, productResponse]) => {
        setSuppliers(supplierResponse.items)
        setProducts(productResponse.items as ProductOption[])
      })
      .catch(() => {
        setOptionsError('No se pudieron cargar proveedores y productos.')
      })
      .finally(() => setLoadingOptions(false))
  }, [isOpen])

  if (!isOpen) return null

  const updateLine = (key: number, patch: Partial<FormLine>) => {
    setLines((current) =>
      current.map((line) => (line.key === key ? { ...line, ...patch } : line)),
    )
  }

  const chooseProduct = (line: FormLine, productId: string) => {
    const product = products.find((item) => item.id === productId)
    updateLine(line.key, {
      product_id: productId,
      description: product?.name ?? '',
      unit_code: product?.base_unit_code ?? product?.base_unit ?? '',
    })
  }

  const resetAndClose = () => {
    if (isSubmitting) return
    setSupplierId('')
    setCurrencyCode('PEN')
    setDeliveryDate('')
    setNotes('')
    setLines([emptyLine()])
    onClose()
  }

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const validLines = lines.filter(
      (line) =>
        line.product_id &&
        Number(line.quantity) > 0 &&
        Number(line.unit_price) >= 0,
    )
    if (!supplierId || validLines.length === 0) return

    onSubmit({
      supplier_id: supplierId,
      currency_code: currencyCode.toUpperCase(),
      expected_delivery_date: deliveryDate || null,
      notes: notes.trim() || null,
      lines: validLines.map(({ key: _key, ...line }) => line),
    })
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/55 p-4">
      <section
        className="max-h-[92vh] w-full max-w-5xl overflow-y-auto rounded-2xl bg-white shadow-2xl"
        role="dialog"
        aria-modal="true"
        aria-labelledby="purchase-order-form-title"
      >
        <div className="sticky top-0 z-10 flex items-center justify-between border-b border-slate-200 bg-white px-6 py-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-orange">
              Compras
            </p>
            <h2 id="purchase-order-form-title" className="text-xl font-bold text-slate-900">
              Nueva orden de compra
            </h2>
          </div>
          <Button type="button" variant="ghost" onClick={resetAndClose}>
            Cerrar
          </Button>
        </div>

        <form className="space-y-6 p-6" onSubmit={handleSubmit}>
          {(error || optionsError) && (
            <Alert variant="error" title="No se pudo crear la orden">
              {error ?? optionsError}
            </Alert>
          )}

          <div className="grid gap-4 md:grid-cols-3">
            <label className="field md:col-span-2">
              <span className="field__label">Proveedor</span>
              <span className="field__control">
                <select
                  className="field__input"
                  value={supplierId}
                  onChange={(event) => setSupplierId(event.target.value)}
                  required
                  disabled={loadingOptions}
                >
                  <option value="">Selecciona un proveedor</option>
                  {suppliers.map((supplier) => (
                    <option key={supplier.id} value={supplier.id}>
                      {supplier.legal_name}
                    </option>
                  ))}
                </select>
              </span>
            </label>
            <label className="field">
              <span className="field__label">Moneda</span>
              <span className="field__control">
                <select
                  className="field__input"
                  value={currencyCode}
                  onChange={(event) => setCurrencyCode(event.target.value)}
                >
                  <option value="PEN">PEN · Sol</option>
                  <option value="USD">USD · Dólar</option>
                  <option value="EUR">EUR · Euro</option>
                </select>
              </span>
            </label>
            <label className="field">
              <span className="field__label">Entrega esperada</span>
              <span className="field__control">
                <input
                  className="field__input"
                  type="date"
                  value={deliveryDate}
                  onChange={(event) => setDeliveryDate(event.target.value)}
                />
              </span>
            </label>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-800">Productos</h3>
              <Button
                type="button"
                variant="secondary"
                size="small"
                onClick={() => setLines((current) => [...current, emptyLine()])}
              >
                Agregar línea
              </Button>
            </div>

            {lines.map((line, index) => (
              <div
                key={line.key}
                className="grid gap-3 rounded-xl border border-slate-200 bg-slate-50 p-4 md:grid-cols-12"
              >
                <label className="field md:col-span-4">
                  <span className="field__label">Producto {index + 1}</span>
                  <span className="field__control">
                    <select
                      className="field__input"
                      value={line.product_id}
                      onChange={(event) => chooseProduct(line, event.target.value)}
                      required
                    >
                      <option value="">Selecciona un producto</option>
                      {products.map((product) => (
                        <option key={product.id} value={product.id}>
                          {product.sku} · {product.name}
                        </option>
                      ))}
                    </select>
                  </span>
                </label>
                <label className="field md:col-span-2">
                  <span className="field__label">Unidad</span>
                  <span className="field__control">
                    <input
                      className="field__input"
                      value={line.unit_code ?? ''}
                      onChange={(event) =>
                        updateLine(line.key, { unit_code: event.target.value })
                      }
                      maxLength={20}
                    />
                  </span>
                </label>
                <label className="field md:col-span-2">
                  <span className="field__label">Cantidad</span>
                  <span className="field__control">
                    <input
                      className="field__input"
                      type="number"
                      min="0.0001"
                      step="0.0001"
                      value={line.quantity}
                      onChange={(event) =>
                        updateLine(line.key, { quantity: event.target.value })
                      }
                      required
                    />
                  </span>
                </label>
                <label className="field md:col-span-2">
                  <span className="field__label">Precio unitario</span>
                  <span className="field__control">
                    <input
                      className="field__input"
                      type="number"
                      min="0"
                      step="0.01"
                      value={line.unit_price}
                      onChange={(event) =>
                        updateLine(line.key, { unit_price: event.target.value })
                      }
                      required
                    />
                  </span>
                </label>
                <label className="field md:col-span-1">
                  <span className="field__label">IGV %</span>
                  <span className="field__control">
                    <input
                      className="field__input"
                      type="number"
                      min="0"
                      max="100"
                      step="0.01"
                      value={line.tax_rate}
                      onChange={(event) =>
                        updateLine(line.key, { tax_rate: event.target.value })
                      }
                    />
                  </span>
                </label>
                <div className="flex items-end md:col-span-1">
                  <Button
                    type="button"
                    variant="ghost"
                    size="small"
                    disabled={lines.length === 1}
                    onClick={() =>
                      setLines((current) =>
                        current.filter((item) => item.key !== line.key),
                      )
                    }
                  >
                    Quitar
                  </Button>
                </div>
              </div>
            ))}
          </div>

          <label className="field">
            <span className="field__label">Observaciones</span>
            <span className="field__control">
              <textarea
                className="field__input field__textarea"
                value={notes}
                onChange={(event) => setNotes(event.target.value)}
                maxLength={2000}
                rows={3}
              />
            </span>
          </label>

          <div className="flex justify-end gap-3 border-t border-slate-200 pt-4">
            <Button type="button" variant="secondary" onClick={resetAndClose}>
              Cancelar
            </Button>
            <Button
              type="submit"
              isLoading={isSubmitting}
              disabled={!supplierId || loadingOptions}
            >
              Crear orden
            </Button>
          </div>
        </form>
      </section>
    </div>
  )
}
