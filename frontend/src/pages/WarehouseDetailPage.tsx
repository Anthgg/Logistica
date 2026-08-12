import { useCallback, useEffect, useState } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import { warehousesApi } from '../api/warehouses-modeling-api'
import { Alert } from '../components/common/Alert'
import { Button } from '../components/common/Button'
import { PageHeader } from '../components/common/PageHeader'
import { StatusBadge } from '../components/common/StatusBadge'
import { WarehouseLocationTree } from '../components/warehouses/WarehouseLocationTree'
import { WarehouseLocationDetailPanel } from '../components/warehouses/WarehouseLocationDetailPanel'
import { WarehouseLocationGenerationWizard } from '../components/warehouses/WarehouseLocationGenerationWizard'
import { WarehouseLogicalMapPage } from '../components/warehouses/WarehouseLogicalMapPage'
import type { Warehouse, WarehouseLocationTreeNode } from '../types/warehouse-modeling'
import { getErrorMessage } from '../utils/errors'

type DetailTab =
  | 'summary'
  | 'locations'
  | 'map'
  | 'history'

export function WarehouseDetailPage() {
  const { warehouseId } = useParams<{ warehouseId: string }>()
  const [searchParams, setSearchParams] = useSearchParams()
  const activeTab: DetailTab = (searchParams.get('tab') as DetailTab) || 'locations'

  const [warehouse, setWarehouse] = useState<Warehouse | null>(null)
  const [selectedLocation, setSelectedLocation] = useState<WarehouseLocationTreeNode | null>(null)
  const [isWizardOpen, setIsWizardOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadWarehouse = useCallback(async () => {
    if (!warehouseId) return
    setIsLoading(true)
    setError(null)
    try {
      setWarehouse(await warehousesApi.get(warehouseId))
    } catch (err: unknown) {
      setError(getErrorMessage(err))
    } finally {
      setIsLoading(false)
    }
  }, [warehouseId])

  useEffect(() => {
    void loadWarehouse()
  }, [loadWarehouse])

  const setTab = (tab: DetailTab) => {
    setSearchParams({ tab })
  }

  const handleBlockLocation = async (node: WarehouseLocationTreeNode) => {
    const reason = window.prompt(`Ingresa el motivo obligatorio para bloquear ${node.full_code}:`)
    if (!reason || reason.trim().length < 5) return
    try {
      await warehousesApi.blockLocation(node.id, reason.trim())
      await loadWarehouse()
    } catch (err: unknown) {
      setError(getErrorMessage(err))
    }
  }

  if (!warehouseId) return null

  return (
    <div className="page">
      {warehouse && (
        <PageHeader
          eyebrow={`Sede: ${warehouse.branch_name || 'Principal'} · Tipo: ${warehouse.warehouse_type}`}
          title={`${warehouse.name} (${warehouse.code})`}
          description={warehouse.address_text}
          actions={
            <div className="flex items-center gap-2">
              <StatusBadge value={warehouse.status.toLowerCase()}>{warehouse.status}</StatusBadge>
              {warehouse.capabilities.can_bulk_create && (
                <Button size="small" onClick={() => setIsWizardOpen(true)}>
                  Generación Masiva
                </Button>
              )}
            </div>
          }
        />
      )}

      {error && <Alert variant="error">{error}</Alert>}

      {isLoading ? (
        <div className="loading-panel">
          <span className="spinner" />
          <p>Cargando detalles y estructura del almacén…</p>
        </div>
      ) : warehouse ? (
        <section className="panel operations-section space-y-4">
          {/* Métricas sin Ocupación o Stock Falso */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
              <span className="font-semibold text-slate-400 text-[10px] uppercase block">Ubicaciones Totales</span>
              <span className="font-mono text-lg font-bold text-slate-900">{warehouse.total_locations}</span>
            </div>
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
              <span className="font-semibold text-slate-400 text-[10px] uppercase block">Ubicaciones Activas</span>
              <span className="font-mono text-lg font-bold text-emerald-700">{warehouse.active_locations}</span>
            </div>
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
              <span className="font-semibold text-slate-400 text-[10px] uppercase block">Ubicaciones Bloqueadas</span>
              <span className="font-mono text-lg font-bold text-rose-700">{warehouse.blocked_locations}</span>
            </div>
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
              <span className="font-semibold text-slate-400 text-[10px] uppercase block">Versión Layout Activo</span>
              <span className="font-mono text-lg font-bold text-blue-700">
                {warehouse.active_layout_version ? `v${warehouse.active_layout_version}` : 'DRAFT'}
              </span>
            </div>
          </div>

          {/* Navegación por pestañas */}
          <div className="tabs border-b border-slate-200 pb-2">
            {[
              { id: 'locations', label: 'Estructura & Ubicaciones' },
              { id: 'map', label: 'Mapa Lógico 2D' },
              { id: 'summary', label: 'Ficha Resumen' },
            ].map((t) => (
              <button
                key={t.id}
                type="button"
                className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-colors ${
                  activeTab === t.id
                    ? 'bg-blue-700 text-white shadow-xs'
                    : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                }`}
                onClick={() => setTab(t.id as DetailTab)}
              >
                {t.label}
              </button>
            ))}
          </div>

          {/* Contenido activo */}
          <div className="pt-2">
            {activeTab === 'locations' && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <WarehouseLocationTree
                  warehouseId={warehouse.id}
                  selectedLocationId={selectedLocation?.id || null}
                  onSelectLocation={setSelectedLocation}
                />
                <WarehouseLocationDetailPanel
                  locationNode={selectedLocation}
                  onBlockLocation={handleBlockLocation}
                />
              </div>
            )}

            {activeTab === 'map' && <WarehouseLogicalMapPage warehouseId={warehouse.id} />}

            {activeTab === 'summary' && (
              <div className="space-y-3 text-xs text-slate-700">
                <p>
                  <strong>Cross-docking:</strong> {warehouse.is_inventory_enabled ? 'Habilitado' : 'No'}
                </p>
                <p>
                  <strong>Control de Temperatura:</strong> {warehouse.has_temperature_control ? 'Sí' : 'No'}
                </p>
                <p>
                  <strong>Materiales Peligrosos (HAZMAT):</strong> {warehouse.has_hazmat ? 'Sí' : 'No'}
                </p>
              </div>
            )}
          </div>
        </section>
      ) : null}

      <WarehouseLocationGenerationWizard
        warehouseId={warehouseId}
        isOpen={isWizardOpen}
        onClose={() => setIsWizardOpen(false)}
        onSuccess={loadWarehouse}
      />
    </div>
  )
}
