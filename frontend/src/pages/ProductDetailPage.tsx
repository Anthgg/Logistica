import { useCallback, useEffect, useState } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import { productsCatalogApi } from '../api/products-catalog-api'
import { Alert } from '../components/common/Alert'
import { Button } from '../components/common/Button'
import { PageHeader } from '../components/common/PageHeader'
import { StatusBadge } from '../components/common/StatusBadge'
import { ProductIdentifiersPanel } from '../components/products/ProductIdentifiersPanel'
import { useSensitiveOperationGuard } from '../features/continuous-auth/hooks/useSensitiveOperationGuard'
import type { Product, ProductPhysicalProfile, ProductTrackingPolicy } from '../types/products-catalog'
import { getErrorMessage } from '../utils/errors'

type ProductTab =
  | 'summary'
  | 'identifiers'
  | 'physical'
  | 'tracking'
  | 'history'

export function ProductDetailPage() {
  const { productId } = useParams<{ productId: string }>()
  const [searchParams, setSearchParams] = useSearchParams()
  const activeTab: ProductTab = (searchParams.get('tab') as ProductTab) || 'summary'

  const { guardSensitiveAction } = useSensitiveOperationGuard()

  const [product, setProduct] = useState<Product | null>(null)
  const [physical, setPhysical] = useState<ProductPhysicalProfile | null>(null)
  const [tracking, setTracking] = useState<ProductTrackingPolicy | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadProduct = useCallback(async () => {
    if (!productId) return
    setIsLoading(true)
    setError(null)
    try {
      const prod = await productsCatalogApi.get(productId)
      setProduct(prod)
      setPhysical(await productsCatalogApi.getPhysicalProfile(productId))
      setTracking(await productsCatalogApi.getTrackingPolicy(productId))
    } catch (err: unknown) {
      setError(getErrorMessage(err))
    } finally {
      setIsLoading(false)
    }
  }, [productId])

  useEffect(() => {
    void loadProduct()
  }, [loadProduct])

  const setTab = (tab: ProductTab) => {
    setSearchParams({ tab })
  }

  const handleActivate = async () => {
    if (!productId) return
    setIsSaving(true)
    try {
      const executed = await guardSensitiveAction(async () => {
        await productsCatalogApi.activate(productId)
      })
      if (!executed) return
      await loadProduct()
    } catch (err: unknown) {
      setError(getErrorMessage(err))
    } finally {
      setIsSaving(false)
    }
  }

  if (!productId) return null

  return (
    <div className="page">
      {product && (
        <PageHeader
          eyebrow={`SKU: ${product.sku} · Tipo: ${product.product_type}`}
          title={product.name}
          description={product.description || 'Sin descripción adicional.'}
          actions={
            <div className="flex items-center gap-2">
              <StatusBadge value={product.status.toLowerCase()}>{product.status}</StatusBadge>
              {product.status === 'DRAFT' && product.capabilities.can_activate && (
                <Button size="small" onClick={() => void handleActivate()} isLoading={isSaving}>
                  Activar Producto
                </Button>
              )}
            </div>
          }
        />
      )}

      {/* Nota legal explícita de Cero Stock */}
      <div className="rounded-xl border border-blue-200 bg-blue-50 p-3.5 text-xs text-blue-900 flex items-start gap-2.5">
        <span className="font-bold text-blue-700">ℹ️ Ficha Técnica Logística:</span>
        <p className="leading-relaxed">
          El catálogo define las especificaciones maestras del producto. Las existencias físicas, lotes en stock y saldos disponibles
          se gestionan exclusivamente en el módulo de inventario operativo.
        </p>
      </div>

      {error && <Alert variant="error">{error}</Alert>}

      {isLoading ? (
        <div className="loading-panel">
          <span className="spinner" />
          <p>Cargando ficha del producto…</p>
        </div>
      ) : product ? (
        <section className="panel operations-section space-y-4">
          <div className="tabs border-b border-slate-200 pb-2">
            {[
              { id: 'summary', label: 'Resumen Ficha' },
              { id: 'identifiers', label: 'Identificadores & Barcode' },
              { id: 'physical', label: 'Perfil Físico & Cubaje' },
              { id: 'tracking', label: 'Trazabilidad & Vencimiento' },
            ].map((t) => (
              <button
                key={t.id}
                type="button"
                className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-colors ${
                  activeTab === t.id
                    ? 'bg-blue-700 text-white shadow-xs'
                    : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                }`}
                onClick={() => setTab(t.id as ProductTab)}
              >
                {t.label}
              </button>
            ))}
          </div>

          <div className="pt-2 text-xs">
            {activeTab === 'summary' && (
              <div className="grid grid-cols-2 gap-4 text-slate-700">
                <div>
                  <span className="font-semibold text-slate-400 block uppercase text-[10px]">Categoría:</span>
                  <span className="font-bold text-slate-900">{product.category_name || 'Sin categoría'}</span>
                </div>
                <div>
                  <span className="font-semibold text-slate-400 block uppercase text-[10px]">Marca:</span>
                  <span className="font-bold text-slate-900">{product.brand_name || 'Genérico'}</span>
                </div>
                <div>
                  <span className="font-semibold text-slate-400 block uppercase text-[10px]">Unidad Base:</span>
                  <span className="font-mono font-bold text-slate-900">{product.base_unit}</span>
                </div>
                <div>
                  <span className="font-semibold text-slate-400 block uppercase text-[10px]">Versión Activa:</span>
                  <span className="font-mono font-bold text-slate-900">v{product.active_version}</span>
                </div>
              </div>
            )}

            {activeTab === 'identifiers' && (
              <ProductIdentifiersPanel
                productId={product.id}
                canManageIdentifiers={product.capabilities.can_manage_identifiers}
              />
            )}

            {activeTab === 'physical' && physical && (
              <div className="space-y-3">
                <h4 className="font-bold text-slate-900 text-xs">Dimensiones y Cubaje Calculado</h4>
                <div className="grid grid-cols-3 gap-3 text-slate-700">
                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                    <span className="text-[10px] uppercase font-semibold text-slate-400 block">Peso Neto (KG)</span>
                    <span className="font-mono font-bold text-slate-900">{physical.net_weight_kg}</span>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                    <span className="text-[10px] uppercase font-semibold text-slate-400 block">Volumen Informado (M3)</span>
                    <span className="font-mono font-bold text-slate-900">{physical.reported_volume_m3}</span>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                    <span className="text-[10px] uppercase font-semibold text-slate-400 block">Volumen Calculado (M3)</span>
                    <span className="font-mono font-bold text-blue-700">{physical.calculated_volume_m3}</span>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'tracking' && tracking && (
              <div className="space-y-3">
                <h4 className="font-bold text-slate-900 text-xs">Política de Control por Lote y Serie</h4>
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                    <span className="text-[10px] uppercase font-semibold text-slate-400 block">Tipo de Trazabilidad</span>
                    <span className="font-mono font-bold text-slate-900">{tracking.tracking_type}</span>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                    <span className="text-[10px] uppercase font-semibold text-slate-400 block">Control de Vencimiento</span>
                    <span className="font-bold text-slate-900">{tracking.requires_expiration ? 'Sí' : 'No'}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </section>
      ) : null}
    </div>
  )
}
