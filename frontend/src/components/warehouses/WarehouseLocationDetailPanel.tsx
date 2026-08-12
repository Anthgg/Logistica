import { useState } from 'react'
import { warehousesApi } from '../../api/warehouses-modeling-api'
import { Button } from '../../components/common/Button'
import { LogisticsIcon } from '../../components/common/LogisticsIcon'
import { SecurePdfViewer } from '../../components/common/SecurePdfViewer'
import { StatusBadge } from '../../components/common/StatusBadge'
import type { WarehouseLocationTreeNode } from '../../types/warehouse-modeling'

interface WarehouseLocationDetailPanelProps {
  locationNode: WarehouseLocationTreeNode | null
  onBlockLocation: (node: WarehouseLocationTreeNode) => void
}

export function WarehouseLocationDetailPanel({
  locationNode,
  onBlockLocation,
}: WarehouseLocationDetailPanelProps) {
  const [isPreviewOpen, setIsPreviewOpen] = useState(false)

  if (!locationNode) {
    return (
      <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50/50 p-6 text-center text-xs text-slate-400">
        <p className="font-semibold">Selecciona una ubicación en el árbol jerárquico para inspeccionar sus metadatos.</p>
      </div>
    )
  }

  return (
    <div className="space-y-4 text-xs">
      <div className="rounded-xl border border-slate-200 bg-white p-4 space-y-3 shadow-xs">
        <div className="flex items-center justify-between">
          <div>
            <span className="font-mono text-[10px] font-bold text-slate-400 uppercase">Ficha Técnica de Ubicación</span>
            <h3 className="font-mono text-base font-bold text-slate-900">{locationNode.full_code}</h3>
          </div>
          <StatusBadge value={locationNode.status.toLowerCase()}>{locationNode.status}</StatusBadge>
        </div>

        {/* Advertencia obligatoria de Cero Ocupación/Stock */}
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-2.5 text-[11px] text-amber-900">
          <p className="font-bold flex items-center gap-1.5"><LogisticsIcon name="alert" size={14} aria-hidden /> Nota de alcance operativo:</p>
          <p className="mt-0.5">
            La ocupación física y saldos en stock estarán disponibles únicamente cuando se active el módulo de inventario operativo.
          </p>
        </div>

        <div className="grid grid-cols-2 gap-3 text-slate-700 pt-2 border-t border-slate-100">
          <div>
            <span className="font-semibold text-slate-400 block text-[10px] uppercase">Código de Segmento:</span>
            <span className="font-mono font-bold text-slate-900">{locationNode.code_segment}</span>
          </div>

          <div>
            <span className="font-semibold text-slate-400 block text-[10px] uppercase">Tipo de Estructura:</span>
            <span className="font-bold text-slate-900">{locationNode.location_type}</span>
          </div>

          <div>
            <span className="font-semibold text-slate-400 block text-[10px] uppercase">Uso Operativo:</span>
            <span className="font-bold text-slate-900">{locationNode.usage_type}</span>
          </div>

          <div>
            <span className="font-semibold text-slate-400 block text-[10px] uppercase">Sub-elementos Hijos:</span>
            <span className="font-mono font-bold text-slate-900">{locationNode.children_count}</span>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2 pt-3 border-t border-slate-100 justify-end">
          <Button size="small" variant="secondary" onClick={() => setIsPreviewOpen(true)}>
            Ver Etiqueta QR PDF
          </Button>

          {locationNode.status === 'ACTIVE' && (
            <Button size="small" variant="ghost" onClick={() => onBlockLocation(locationNode)}>
              Bloquear Ubicación
            </Button>
          )}
        </div>
      </div>

      <SecurePdfViewer
        isOpen={isPreviewOpen}
        title={`Etiqueta QR Oficial — ${locationNode.full_code}`}
        code={locationNode.full_code}
        fetchBlobUrl={async () => warehousesApi.downloadLocationLabelPdfBlobUrl(locationNode.id)}
        onClose={() => setIsPreviewOpen(false)}
      />
    </div>
  )
}
