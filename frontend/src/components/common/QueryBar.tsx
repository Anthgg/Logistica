import type { ReactNode } from 'react'
import { Input } from './Input'

export function QueryBar({
  search,
  onSearch,
  children,
}: {
  search: string
  onSearch: (value: string) => void
  children?: ReactNode
}) {
  return (
    <div className="query-bar">
      <Input
        label="Buscar"
        type="search"
        value={search}
        placeholder="Nombre, código o documento…"
        onChange={(event) => onSearch(event.target.value)}
      />
      {children}
    </div>
  )
}
