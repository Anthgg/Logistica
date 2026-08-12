import { useState, useCallback, useMemo } from 'react'
import { useQuery } from '../../inbound-docks/hooks/useQuery'
import type { ProductCategorySummary } from '../types/quality-inspection-plans'

interface ProductCategoryTreeSelectorProps {
  selectedIds: string[]
  onSelect: (ids: string[]) => void
  includeDescendants?: boolean
}

interface CategoryTreeNode extends ProductCategorySummary {
  children: CategoryTreeNode[]
}

const STATUS_COLORS: Record<string, string> = {
  ACTIVE: 'bg-emerald-100 text-emerald-700',
  INACTIVE: 'bg-slate-100 text-slate-500',
}

export function ProductCategoryTreeSelector({
  selectedIds,
  onSelect,
  includeDescendants = false,
}: ProductCategoryTreeSelectorProps) {
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set())

  const query = useQuery<ProductCategorySummary[]>(
    ['product-categories-tree'],
    '/logistics/product-categories',
    undefined,
  )

  const categories = query.data ?? []
  const isLoading = query.isLoading
  const isError = query.isError

  const tree = useMemo(() => buildTree(categories), [categories])

  const toggleExpand = useCallback((id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }, [])

  const toggleSelect = useCallback(
    (id: string) => {
      if (selectedIds.includes(id)) {
        onSelect(selectedIds.filter((sid) => sid !== id))
      } else {
        onSelect([...selectedIds, id])
      }
    },
    [selectedIds, onSelect],
  )

  const expandAll = useCallback(() => {
    const allIds = categories.map((c) => c.category_id)
    setExpandedIds(new Set(allIds))
  }, [categories])

  const collapseAll = useCallback(() => {
    setExpandedIds(new Set())
  }, [])

  if (isLoading) {
    return (
      <div className="space-y-3">
        <h3 className="text-sm font-bold text-slate-800">Selector de categorías</h3>
        <p className="text-xs text-slate-400">Cargando categorías…</p>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="space-y-3">
        <h3 className="text-sm font-bold text-slate-800">Selector de categorías</h3>
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800">
          {query.error || 'Error al cargar las categorías.'}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold text-slate-800">Selector de categorías</h3>
        <div className="flex gap-1.5">
          <button
            type="button"
            onClick={expandAll}
            className="rounded border border-slate-200 bg-white px-2 py-1 text-[10px] text-slate-600 hover:bg-slate-50"
          >
            Expandir todo
          </button>
          <button
            type="button"
            onClick={collapseAll}
            className="rounded border border-slate-200 bg-white px-2 py-1 text-[10px] text-slate-600 hover:bg-slate-50"
          >
            Colapsar todo
          </button>
        </div>
      </div>

      {selectedIds.length > 0 && (
        <p className="text-xs text-slate-500">
          {selectedIds.length} categoría{selectedIds.length !== 1 ? 's' : ''} seleccionada{selectedIds.length !== 1 ? 's' : ''}
          {includeDescendants && ' (incluyendo descendientes)'}
        </p>
      )}

      {tree.length === 0 ? (
        <p className="text-xs text-slate-400">No hay categorías disponibles.</p>
      ) : (
        <div className="space-y-0.5">
          {tree.map((node) => (
            <CategoryNode
              key={node.category_id}
              node={node}
              depth={0}
              selectedIds={selectedIds}
              expandedIds={expandedIds}
              onToggleExpand={toggleExpand}
              onToggleSelect={toggleSelect}
            />
          ))}
        </div>
      )}
    </div>
  )
}

interface CategoryNodeProps {
  node: CategoryTreeNode
  depth: number
  selectedIds: string[]
  expandedIds: Set<string>
  onToggleExpand: (id: string) => void
  onToggleSelect: (id: string) => void
}

function CategoryNode({
  node,
  depth,
  selectedIds,
  expandedIds,
  onToggleExpand,
  onToggleSelect,
}: CategoryNodeProps) {
  const hasChildren = node.children.length > 0
  const isExpanded = expandedIds.has(node.category_id)
  const isSelected = selectedIds.includes(node.category_id)
  const indent = depth * 16

  return (
    <div>
      <div
        className={`flex items-center gap-2 rounded-lg px-2 py-1.5 text-xs transition-colors ${
          isSelected ? 'bg-indigo-50 ring-1 ring-indigo-200' : 'hover:bg-slate-50'
        }`}
        style={{ paddingLeft: `${indent + 8}px` }}
      >
        <button
          type="button"
          onClick={() => onToggleExpand(node.category_id)}
          className="flex h-4 w-4 flex-shrink-0 items-center justify-center text-slate-400 hover:text-slate-600"
          aria-label={isExpanded ? 'Colapsar' : 'Expandir'}
        >
          {hasChildren ? (
            <svg
              className={`h-3 w-3 transition-transform ${isExpanded ? 'rotate-90' : ''}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
            </svg>
          ) : (
            <span className="h-3 w-3" />
          )}
        </button>

        <input
          type="checkbox"
          checked={isSelected}
          onChange={() => onToggleSelect(node.category_id)}
          className="h-3.5 w-3.5 flex-shrink-0 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
        />

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-mono text-[10px] text-slate-500">{node.code}</span>
            <span className="truncate font-medium text-slate-800">{node.name}</span>
            <span className={`rounded px-1.5 py-0.5 text-[10px] font-bold ${STATUS_COLORS[node.status] ?? 'bg-slate-100 text-slate-500'}`}>
              {node.status}
            </span>
          </div>
          <div className="flex gap-3 text-[10px] text-slate-500">
            <span>{node.product_count} producto{node.product_count !== 1 ? 's' : ''}</span>
            {node.children_count > 0 && (
              <span>{node.children_count} descendiente{node.children_count !== 1 ? 's' : ''}</span>
            )}
          </div>
        </div>
      </div>

      {isExpanded && hasChildren && (
        <div>
          {node.children.map((child) => (
            <CategoryNode
              key={child.category_id}
              node={child}
              depth={depth + 1}
              selectedIds={selectedIds}
              expandedIds={expandedIds}
              onToggleExpand={onToggleExpand}
              onToggleSelect={onToggleSelect}
            />
          ))}
        </div>
      )}
    </div>
  )
}

function buildTree(categories: ProductCategorySummary[]): CategoryTreeNode[] {
  const map = new Map<string, CategoryTreeNode>()
  const roots: CategoryTreeNode[] = []

  for (const cat of categories) {
    map.set(cat.category_id, { ...cat, children: [] })
  }

  for (const cat of categories) {
    const node = map.get(cat.category_id)!
    if (cat.parent_id && map.has(cat.parent_id)) {
      map.get(cat.parent_id)!.children.push(node)
    } else {
      roots.push(node)
    }
  }

  const sortNodes = (nodes: CategoryTreeNode[]) => {
    nodes.sort((a, b) => a.code.localeCompare(b.code))
    for (const node of nodes) sortNodes(node.children)
  }
  sortNodes(roots)

  return roots
}
