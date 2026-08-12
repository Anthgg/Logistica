import { useState } from 'react'
import type { WarehouseLocationSummary } from '../types/putaway'

interface Props {
  locations: WarehouseLocationSummary[]
  selectedLocationId?: string
  onSelect?: (location: WarehouseLocationSummary) => void
  showCapacity?: boolean
  capacityMap?: Record<string, { used: string; total: string; percentage: string }>
}

interface TreeNode {
  code: string
  name: string
  location?: WarehouseLocationSummary
  children: Record<string, TreeNode>
}

function buildTree(locations: WarehouseLocationSummary[]): TreeNode {
  const root: TreeNode = { code: '', name: 'Almacén', children: {} }

  for (const loc of locations) {
    const zone = loc.zone || 'Sin zona'
    const aisle = loc.aisle || ''
    const level = loc.level || ''
    const rack = loc.rack || ''
    const position = loc.position || ''

    if (!root.children[zone]) {
      root.children[zone] = { code: zone, name: zone, children: {} }
    }
    const zoneNode = root.children[zone]

    const aisleKey = aisle || '_direct'
    if (!zoneNode.children[aisleKey]) {
      zoneNode.children[aisleKey] = { code: aisle || zone, name: aisle || zone, children: {} }
    }
    const aisleNode = zoneNode.children[aisleKey]

    const levelKey = level || '_direct'
    if (!aisleNode.children[levelKey]) {
      aisleNode.children[levelKey] = { code: level || aisle || zone, name: level || aisle || zone, children: {} }
    }
    const levelNode = aisleNode.children[levelKey]

    const rackKey = rack || '_direct'
    if (!levelNode.children[rackKey]) {
      levelNode.children[rackKey] = { code: rack || level || aisle || zone, name: rack || level || aisle || zone, children: {} }
    }
    const rackNode = levelNode.children[rackKey]

    const posKey = position || loc.code
    rackNode.children[posKey] = {
      code: loc.code,
      name: loc.name || loc.code,
      location: loc,
      children: {},
    }
  }

  return root
}

function TreeNodeComponent({
  node,
  depth,
  selectedLocationId,
  onSelect,
  capacityMap,
  expandedByDefault,
}: {
  node: TreeNode
  depth: number
  selectedLocationId?: string
  onSelect?: (location: WarehouseLocationSummary) => void
  capacityMap?: Record<string, { used: string; total: string; percentage: string }>
  expandedByDefault: boolean
}) {
  const [expanded, setExpanded] = useState(expandedByDefault)
  const hasChildren = Object.keys(node.children).length > 0
  const isLeaf = !!node.location
  const capacity = node.location ? capacityMap?.[node.location.location_id] : undefined

  const indent = depth * 16

  if (isLeaf && node.location) {
    const isSelected = selectedLocationId === node.location.location_id
    return (
      <div
        style={{ paddingLeft: indent }}
        className={`flex items-center justify-between px-2 py-1 cursor-pointer text-sm ${
          isSelected ? 'bg-blue-100 text-blue-700' : 'hover:bg-gray-50'
        }`}
        onClick={() => onSelect?.(node.location!)}
      >
        <div className="flex items-center gap-2">
          <span className="text-gray-400">•</span>
          <span className="font-medium">{node.location.code}</span>
          <span className="text-gray-500 text-xs">{node.location.name}</span>
          {node.location.is_pickable && <span className="text-xs bg-green-100 px-1 rounded">P</span>}
          {node.location.is_quarantine && <span className="text-xs bg-yellow-100 px-1 rounded">Q</span>}
          {node.location.is_damaged && <span className="text-xs bg-red-100 px-1 rounded">D</span>}
        </div>
        {capacity && (
          <span className={`text-xs ${
            parseFloat(capacity.percentage) >= 90 ? 'text-red-500' :
            parseFloat(capacity.percentage) >= 70 ? 'text-yellow-500' : 'text-green-500'
          }`}>
            {capacity.percentage}%
          </span>
        )}
      </div>
    )
  }

  return (
    <div>
      <div
        style={{ paddingLeft: indent }}
        className="flex items-center gap-2 px-2 py-1 cursor-pointer text-sm hover:bg-gray-50"
        onClick={() => setExpanded(!expanded)}
      >
        <span className="text-gray-400 text-xs">{expanded ? '▼' : '▶'}</span>
        <span className="font-medium">{node.name}</span>
        {hasChildren && (
          <span className="text-xs text-gray-400">({Object.keys(node.children).length})</span>
        )}
      </div>
      {expanded && hasChildren && (
        <div>
          {Object.values(node.children).map((child) => (
            <TreeNodeComponent
              key={child.code}
              node={child}
              depth={depth + 1}
              selectedLocationId={selectedLocationId}
              onSelect={onSelect}
              capacityMap={capacityMap}
              expandedByDefault={depth < 2}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export function LocationTree({ locations, selectedLocationId, onSelect, capacityMap }: Props) {
  const tree = buildTree(locations)

  return (
    <div className="bg-white rounded-lg border overflow-auto max-h-96">
      <div className="p-2 border-b bg-gray-50 text-xs font-medium text-gray-500">
        Árbol de ubicaciones ({locations.length})
      </div>
      {Object.values(tree.children).map((zoneNode) => (
        <TreeNodeComponent
          key={zoneNode.code}
          node={zoneNode}
          depth={0}
          selectedLocationId={selectedLocationId}
          onSelect={onSelect}
          capacityMap={capacityMap}
          expandedByDefault={true}
        />
      ))}
    </div>
  )
}
