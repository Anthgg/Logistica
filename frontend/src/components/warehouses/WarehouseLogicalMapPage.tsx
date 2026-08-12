import { useCallback, useEffect, useState } from 'react'
import { warehousesApi } from '../../api/warehouses-modeling-api'
import type { LogicalMapNode, LogicalMapResponse } from '../../types/warehouse-modeling'
import { getErrorMessage } from '../../utils/errors'

interface WarehouseLogicalMapPageProps {
  warehouseId: string
}

export function WarehouseLogicalMapPage({ warehouseId }: WarehouseLogicalMapPageProps) {
  const [mapData, setMapData] = useState<LogicalMapResponse | null>(null)
  const [selectedNode, setSelectedNode] = useState<LogicalMapNode | null>(null)
  const [currentFloor, setCurrentFloor] = useState<number>(1)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadMap = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      setMapData(await warehousesApi.getLogicalMap(warehouseId, currentFloor))
    } catch (err: unknown) {
      setError(getErrorMessage(err))
    } finally {
      setIsLoading(false)
    }
  }, [warehouseId, currentFloor])

  useEffect(() => {
    void loadMap()
  }, [loadMap])

  return (
    <div className="space-y-4 text-xs">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-bold text-slate-900">Mapa Lógico 2D del Almacén</h3>
          <p className="text-[11px] text-slate-500">
            Representación de maquetación de planta interna. No utiliza mapas ni coordenadas geográficas.
          </p>
        </div>

        {mapData && (
          <div className="flex items-center gap-2">
            <span className="font-semibold text-slate-500">Planta:</span>
            {mapData.floor_levels.map((fl) => (
              <button
                key={fl}
                type="button"
                className={`px-2.5 py-1 rounded-lg font-bold transition-colors ${
                  currentFloor === fl
                    ? 'bg-blue-700 text-white'
                    : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                }`}
                onClick={() => setCurrentFloor(fl)}
              >
                Piso {fl}
              </button>
            ))}
          </div>
        )}
      </div>

      {error && <p className="text-xs font-semibold text-rose-600">{error}</p>}

      {isLoading ? (
        <div className="loading-panel">
          <span className="spinner" />
          <p>Cargando mapa lógico de la planta…</p>
        </div>
      ) : mapData ? (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
          {/* Lienzo SVG Interactivo */}
          <div className="lg:col-span-3 rounded-xl border border-slate-200 bg-slate-900 p-4 min-h-[400px] flex items-center justify-center overflow-auto shadow-inner">
            <svg viewBox="0 0 1000 600" className="w-full h-auto max-h-[500px]">
              {/* Cuadrícula Guía */}
              <defs>
                <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                  <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1e293b" strokeWidth="1" />
                </pattern>
              </defs>
              <rect width="100%" height="100%" fill="url(#grid)" />

              {/* Nodos de Ubicación Renderizados */}
              {mapData.nodes.map((node) => {
                const isSelected = selectedNode?.id === node.id
                return (
                  <g
                    key={node.id}
                    transform={`translate(${node.x}, ${node.y}) rotate(${node.rotation})`}
                    className="cursor-pointer transition-transform"
                    onClick={() => setSelectedNode(node)}
                  >
                    <rect
                      width={node.width}
                      height={node.height}
                      rx="4"
                      fill={isSelected ? '#3b82f6' : '#334155'}
                      stroke={isSelected ? '#60a5fa' : '#475569'}
                      strokeWidth={isSelected ? '3' : '1.5'}
                    />
                    <text
                      x={node.width / 2}
                      y={node.height / 2}
                      fill="#f8fafc"
                      fontSize="10"
                      fontWeight="bold"
                      textAnchor="middle"
                      dominantBaseline="middle"
                    >
                      {node.full_code}
                    </text>
                  </g>
                )
              })}
            </svg>
          </div>

          {/* Panel Lateral de Nodo Seleccionado y Sin Mapear */}
          <div className="space-y-3">
            {selectedNode ? (
              <div className="rounded-xl border border-slate-200 bg-white p-3 space-y-2 shadow-xs">
                <span className="font-mono text-[10px] font-bold text-slate-400 uppercase">
                  Nodo Seleccionado en Canvas
                </span>
                <h4 className="font-mono text-sm font-bold text-slate-900">{selectedNode.full_code}</h4>
                <div className="text-[11px] text-slate-600 space-y-1">
                  <p>Tipo: {selectedNode.location_type}</p>
                  <p>Estado: {selectedNode.status}</p>
                  <p>
                    Posición Coordenadas: X={selectedNode.x}, Y={selectedNode.y}
                  </p>
                </div>
              </div>
            ) : (
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-center text-slate-400">
                <p>Haz clic en un bloque del mapa para ver sus coordenadas y metadatos.</p>
              </div>
            )}

            <div className="rounded-xl border border-slate-200 bg-white p-3 space-y-2 shadow-xs">
              <span className="font-mono text-[10px] font-bold text-slate-400 uppercase">
                Ubicaciones Pendientes por Mapear ({mapData.unmapped_locations.length})
              </span>
              <div className="space-y-1 max-h-[180px] overflow-y-auto">
                {mapData.unmapped_locations.map((u) => (
                  <div
                    key={u.id}
                    className="flex items-center justify-between p-1.5 rounded bg-slate-50 border border-slate-100 font-mono text-[10px]"
                  >
                    <span className="font-bold text-slate-800">{u.full_code}</span>
                    <span className="text-slate-400">{u.location_type}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  )
}
