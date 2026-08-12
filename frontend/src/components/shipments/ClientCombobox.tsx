import * as React from 'react'
import type { Client } from '../../types/operations'
import { LogisticsIcon } from '../common/LogisticsIcon'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select'

interface ClientComboboxProps {
  clients: Client[]
  value: string
  onChange: (clientId: string) => void
  disabled?: boolean
  required?: boolean
  error?: string
}

export function ClientCombobox({
  clients,
  value,
  onChange,
  disabled = false,
  required = false,
  error,
}: ClientComboboxProps) {
  const [search, setSearch] = React.useState('')

  const filteredClients = React.useMemo(() => {
    if (!search.trim()) return clients
    const q = search.toLowerCase().trim()
    return clients.filter(
      (c) =>
        c.business_name.toLowerCase().includes(q) ||
        (c.document_number && c.document_number.includes(q))
    )
  }, [clients, search])

  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-xs font-semibold text-slate-700">
        Cliente {required && <span className="text-rose-500">*</span>}
      </label>
      <Select value={value || 'none'} onValueChange={(val) => onChange(val === 'none' ? '' : val)} disabled={disabled}>
        <SelectTrigger className="h-10 text-xs">
          <SelectValue placeholder="Seleccionar cliente..." />
        </SelectTrigger>
        <SelectContent>
          <div className="p-2 pb-1.5">
            <div className="relative">
              <div className="pointer-events-none absolute inset-y-0 left-2.5 flex items-center text-slate-400">
                <LogisticsIcon name="search" size={14} />
              </div>
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Buscar cliente por nombre o RUC..."
                className="h-8 w-full rounded-lg border border-slate-200 bg-slate-50 pl-8 pr-2.5 text-xs text-slate-800 placeholder:text-slate-400 focus:border-[#1F4E6D] focus:bg-white focus:outline-none"
                onClick={(e) => e.stopPropagation()}
                onKeyDown={(e) => e.stopPropagation()}
              />
            </div>
          </div>
          <SelectItem value="none">
            <span className="text-slate-400">Seleccionar cliente...</span>
          </SelectItem>
          {filteredClients.map((client) => (
            <SelectItem key={client.id} value={client.id}>
              <div className="flex items-center gap-2">
                <LogisticsIcon name="building" size={14} className="text-slate-400 shrink-0" />
                <span className="font-semibold">{client.business_name}</span>
                {client.document_number && (
                  <span className="text-[11px] text-slate-400">({client.document_number})</span>
                )}
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      {error && <p className="text-[11px] font-medium text-rose-500">{error}</p>}
    </div>
  )
}
