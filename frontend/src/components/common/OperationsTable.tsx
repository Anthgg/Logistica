import type { ReactNode } from 'react'
import { EmptyState } from './EmptyState'

export interface TableColumn<T> {
  key: string
  label: string
  render: (row: T) => ReactNode
  align?: 'left' | 'right'
}

export function OperationsTable<T>({
  rows,
  columns,
  getRowKey,
  emptyMessage = 'No hay registros para mostrar.',
}: {
  rows?: T[]
  columns: TableColumn<T>[]
  getRowKey: (row: T) => string
  emptyMessage?: string
}) {
  const safeRows = rows ?? []
  if (safeRows.length === 0) {
    return (
      <div className="p-6">
        <EmptyState
          title="Sin registros operativos"
          description={emptyMessage}
          icon="archive"
        />
      </div>
    )
  }

  return (
    <div className="operations-table overflow-x-auto [webkit-overflow-scrolling:touch]">
      <table className="w-full border-collapse text-left text-xs">
        <thead>
          <tr>
            {columns.map((column) => (
              <th
                key={column.key}
                className={`bg-[#F0F4F7] text-faint font-semibold text-[10px] uppercase tracking-[0.05em] px-3.5 py-2.5 border-b border-[#DDE4E8] whitespace-nowrap ${
                  column.align === 'right' ? 'text-right' : 'text-left'
                }`}
              >
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {safeRows.map((row) => (
            <tr key={getRowKey(row)} className="group">
              {columns.map((column) => (
                <td
                  key={column.key}
                  data-label={column.label || 'Acciones'}
                  className={`px-3.5 py-2.5 border-b border-[#EEF2F5] text-ink align-middle group-last:border-b-0 group-hover:bg-[#FAFBFC] ${
                    column.align === 'right' ? 'text-right' : ''
                  }`}
                >
                  {column.render(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
