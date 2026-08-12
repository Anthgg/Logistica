import { useState } from 'react'
import { StatusBadge } from '../../components/common/StatusBadge'
import { LogisticsIcon } from '../../components/common/LogisticsIcon'
import type { WarehouseLocationTreeNode } from '../../types/warehouse-modeling'

interface WarehouseLocationTreeProps {
  warehouseId: string
  selectedLocationId: string | null
  onSelectLocation: (node: WarehouseLocationTreeNode) => void
}

export function WarehouseLocationTree({
  warehouseId: _warehouseId,
  selectedLocationId,
  onSelectLocation,
}: WarehouseLocationTreeProps) {
  const [nodes] = useState<WarehouseLocationTreeNode[]>([
    {
      id: 'loc-z01',
      code_segment: 'Z01',
      full_code: 'ALM01-Z01',
      name: 'Zona Almacenamiento General',
      location_type: 'ZONE',
      status: 'ACTIVE',
      usage_type: 'STORAGE',
      has_children: true,
      children_count: 4,
      children: [
        {
          id: 'loc-a01',
          code_segment: 'A01',
          full_code: 'ALM01-Z01-A01',
          name: 'Pasillo 01',
          location_type: 'AISLE',
          status: 'ACTIVE',
          usage_type: 'PICKING',
          has_children: true,
          children_count: 10,
        },
      ],
    },
    {
      id: 'loc-z02',
      code_segment: 'Z02',
      full_code: 'ALM01-Z02',
      name: 'Zona Cuarentena Sanitaria',
      location_type: 'QUARANTINE',
      status: 'ACTIVE',
      usage_type: 'TRANSIT',
      has_children: false,
      children_count: 0,
    },
  ])

  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set(['loc-z01']))
  const [filterType, setFilterType] = useState<string>('ALL')

  const toggleExpand = (id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const renderNode = (node: WarehouseLocationTreeNode, depth = 0) => {
    const isExpanded = expandedIds.has(node.id)
    const isSelected = selectedLocationId === node.id

    if (filterType !== 'ALL' && node.location_type !== filterType) {
      return null
    }

    return (
      <div key={node.id} className="select-none text-xs">
        <div
          className={`flex items-center gap-2 px-2 py-1.5 rounded-lg cursor-pointer transition-colors ${
            isSelected
              ? 'bg-blue-100 text-blue-900 font-bold border border-blue-300'
              : 'hover:bg-slate-100 text-slate-700'
          }`}
          style={{ paddingLeft: `${depth * 16 + 8}px` }}
          onClick={() => onSelectLocation(node)}
        >
          {node.has_children ? (
            <button
              type="button"
              className="h-4 w-4 flex items-center justify-center text-slate-500 hover:text-slate-900"
              onClick={(e) => {
                e.stopPropagation()
                toggleExpand(node.id)
              }}
            >
              <LogisticsIcon
                name="chevron"
                size={12}
                className={`transition-transform ${isExpanded ? 'rotate-90' : ''}`}
              />
            </button>
          ) : (
            <span className="h-4 w-4 inline-block text-center text-slate-300">•</span>
          )}

          <span className="font-mono text-[11px] font-bold text-slate-900">{node.code_segment}</span>
          <span className="truncate flex-1">{node.name}</span>

          <span className="text-[9px] font-bold uppercase px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200">
            {node.location_type}
          </span>

          <StatusBadge value={node.status.toLowerCase()}>{node.status}</StatusBadge>

          {node.children_count > 0 && (
            <span className="text-[10px] text-slate-400 font-mono">({node.children_count})</span>
          )}
        </div>

        {isExpanded && node.children && (
          <div className="space-y-0.5 mt-0.5">
            {node.children.map((child) => renderNode(child, depth + 1))}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-3 text-xs">
      <div className="flex items-center justify-between">
        <span className="font-bold text-slate-900 uppercase text-[10px] tracking-wider">
          Estructura Jerárquica de Ubicaciones
        </span>
        <select
          className="text-[11px] rounded-lg border border-slate-200 px-2 py-1 bg-white text-slate-700 font-medium"
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
        >
          <option value="ALL">Todos los tipos</option>
          <option value="ZONE">Zonas</option>
          <option value="AISLE">Pasillos</option>
          <option value="RACK">Estantes</option>
          <option value="SHELF">Niveles</option>
          <option value="BIN">Posiciones (Bin)</option>
          <option value="QUARANTINE">Cuarentena</option>
        </select>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-2 max-h-[500px] overflow-y-auto space-y-1 shadow-xs">
        {nodes.map((node) => renderNode(node))}
      </div>
    </div>
  )
}
