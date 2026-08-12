import { useCallback, useEffect, useState } from 'react'
import { productsCatalogApi } from '../../api/products-catalog-api'
import { Button } from '../../components/common/Button'
import { Input } from '../../components/common/Input'
import { StatusBadge } from '../../components/common/StatusBadge'
import { ResourceDialog } from '../../components/common/ResourceDialog'
import type { ProductIdentifier, ProductIdentifierCreate } from '../../types/products-catalog'
import { getErrorMessage } from '../../utils/errors'

interface ProductIdentifiersPanelProps {
  productId: string
  canManageIdentifiers: boolean
}

export function ProductIdentifiersPanel({ productId, canManageIdentifiers }: ProductIdentifiersPanelProps) {
  const [identifiers, setIdentifiers] = useState<ProductIdentifier[]>([])
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [form, setForm] = useState<ProductIdentifierCreate>({
    identifier_type: 'EAN13',
    value: '',
    symbology: 'EAN_13',
    is_primary: false,
  })

  const loadIdentifiers = useCallback(async () => {
    setIsLoading(true)
    try {
      setIdentifiers(await productsCatalogApi.listIdentifiers(productId))
    } catch (err: unknown) {
      setError(getErrorMessage(err))
    } finally {
      setIsLoading(false)
    }
  }, [productId])

  useEffect(() => {
    void loadIdentifiers()
  }, [loadIdentifiers])

  const handleCreate = async () => {
    setIsSaving(true)
    try {
      await productsCatalogApi.createIdentifier(productId, form)
      setIsDialogOpen(false)
      await loadIdentifiers()
    } catch (err: unknown) {
      setError(getErrorMessage(err))
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="space-y-4 text-xs">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-bold text-slate-900">Identificadores y Códigos de Barras</h3>
          <p className="text-[11px] text-slate-500">
            Mapeo de GTIN, EAN-13, SKU de fabricante y simbologías de lectura en escáner.
          </p>
        </div>
        {canManageIdentifiers && (
          <Button size="small" onClick={() => setIsDialogOpen(true)}>
            Añadir código de barras
          </Button>
        )}
      </div>

      {error && <p className="text-xs font-semibold text-rose-600">{error}</p>}

      {isLoading ? (
        <div className="loading-panel">
          <span className="spinner" />
          <p>Cargando identificadores del producto…</p>
        </div>
      ) : (
        <div className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-xs">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50 text-[10px] uppercase font-bold text-slate-400">
                <th className="p-3">Tipo</th>
                <th className="p-3">Valor del Código</th>
                <th className="p-3">Simbología</th>
                <th className="p-3">Principal</th>
                <th className="p-3">Estado</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {identifiers.map((row) => (
                <tr key={row.id} className="hover:bg-slate-50/50">
                  <td className="p-3 font-bold text-slate-900">{row.identifier_type}</td>
                  <td className="p-3 font-mono font-bold text-blue-700">{row.value}</td>
                  <td className="p-3">
                    <span className="font-mono text-[10px] bg-slate-100 px-1.5 py-0.5 rounded">
                      {row.symbology}
                    </span>
                  </td>
                  <td className="p-3">
                    {row.is_primary ? (
                      <span className="text-emerald-700 font-bold bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200">
                        Sí (Principal)
                      </span>
                    ) : (
                      'Secundario'
                    )}
                  </td>
                  <td className="p-3">
                    <StatusBadge value={row.is_active ? 'active' : 'inactive'}>
                      {row.is_active ? 'Activo' : 'Inactivo'}
                    </StatusBadge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <ResourceDialog
        isOpen={isDialogOpen}
        title="Añadir nuevo identificador de producto"
        submitLabel="Registrar código"
        isSubmitting={isSaving}
        onClose={() => setIsDialogOpen(false)}
        onSubmit={() => void handleCreate()}
      >
        <div className="space-y-3 text-xs">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="font-semibold text-slate-700 block mb-1">Tipo de Identificador</label>
              <select
                className="input-field"
                value={form.identifier_type}
                onChange={(e) =>
                  setForm((c) => ({
                    ...c,
                    identifier_type: e.target.value as ProductIdentifierCreate['identifier_type'],
                  }))
                }
              >
                <option value="EAN13">EAN-13</option>
                <option value="UPCA">UPC-A</option>
                <option value="CODE128">Code 128</option>
                <option value="GTIN14">GTIN-14</option>
                <option value="SKU">SKU Fabricante</option>
              </select>
            </div>

            <Input
              label="Valor numérico / alfanumérico"
              value={form.value}
              onChange={(e) => setForm((c) => ({ ...c, value: e.target.value }))}
              required
            />
          </div>
        </div>
      </ResourceDialog>
    </div>
  )
}
