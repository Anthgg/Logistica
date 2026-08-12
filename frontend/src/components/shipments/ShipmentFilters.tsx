import { LogisticsIcon } from '../common/LogisticsIcon'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../ui/select'
import { useTranslations } from '../../hooks/useTranslations'
import type { ShipmentPriority, ShipmentStatus } from '../../types/operations'

const statuses: ShipmentStatus[] = [
  'registered',
  'pending_pickup',
  'picked_up',
  'warehouse_received',
  'in_transit',
  'out_for_delivery',
  'delivered',
  'delayed',
  'cancelled',
  'returned',
]

const priorities: ShipmentPriority[] = ['low', 'normal', 'high', 'urgent']

interface ShipmentFiltersProps {
  search: string
  onSearchChange: (value: string) => void
  status: string
  onStatusChange: (value: string) => void
  priority: string
  onPriorityChange: (value: string) => void
  onClearFilters: () => void
  totalResults: number
}

export function ShipmentFilters({
  search,
  onSearchChange,
  status,
  onStatusChange,
  priority,
  onPriorityChange,
  onClearFilters,
  totalResults,
}: ShipmentFiltersProps) {
  const { translate } = useTranslations()
  const hasActiveFilters = Boolean(search || status || priority)

  return (
    <div className="flex flex-col gap-3 rounded-xl border border-slate-200/90 bg-white p-3.5 shadow-2xs sm:flex-row sm:items-center sm:justify-between">
      <div className="flex flex-1 flex-col gap-2.5 sm:flex-row sm:items-center">
        {/* Campo de búsqueda principal */}
        <div className="relative flex-1 min-w-[240px]">
          <div className="pointer-events-none absolute inset-y-0 left-3 flex items-center text-slate-400">
            <LogisticsIcon name="search" size={16} />
          </div>
          <input
            type="search"
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Buscar por código, cliente, origen o destino..."
            className="h-10 w-full rounded-lg border border-slate-200 bg-white pl-9 pr-3.5 text-xs text-slate-800 placeholder:text-slate-400 focus:border-[#1F4E6D] focus:outline-none focus:ring-1 focus:ring-[#1F4E6D]"
          />
        </div>

        {/* Selector de estado */}
        <div className="w-full sm:w-[190px]">
          <Select
            value={status || 'all'}
            onValueChange={(val) => onStatusChange(val === 'all' ? '' : val)}
          >
            <SelectTrigger className="h-10 text-xs">
              <SelectValue placeholder="Todos los estados" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos los estados</SelectItem>
              {statuses.map((st) => (
                <SelectItem key={st} value={st}>
                  {translate('status', st, st)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Selector de prioridad */}
        <div className="w-full sm:w-[170px]">
          <Select
            value={priority || 'all'}
            onValueChange={(val) => onPriorityChange(val === 'all' ? '' : val)}
          >
            <SelectTrigger className="h-10 text-xs">
              <SelectValue placeholder="Todas las prioridades" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todas las prioridades</SelectItem>
              {priorities.map((pr) => (
                <SelectItem key={pr} value={pr}>
                  {translate('priority', pr, pr)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Botón limpiar filtros */}
        {hasActiveFilters && (
          <button
            type="button"
            onClick={onClearFilters}
            className="inline-flex h-10 items-center justify-center gap-1.5 rounded-lg border border-slate-200 bg-slate-50 px-3 text-xs font-medium text-slate-600 transition-colors hover:bg-slate-100 hover:text-slate-900"
          >
            Limpiar filtros
          </button>
        )}
      </div>

      {/* Contador de resultados */}
      <div className="shrink-0 text-right text-xs font-medium text-slate-500">
        <span>{totalResults}</span> {totalResults === 1 ? 'resultado' : 'resultados'}
      </div>
    </div>
  )
}
