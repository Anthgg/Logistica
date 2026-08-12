import { NavLink } from 'react-router-dom'
import { LogisticsIcon } from '../../../components/common/LogisticsIcon'
import type { LogisticsIconName } from '../../../components/common/LogisticsIcon'

const ITEMS: Array<{ label: string; path: string; icon: LogisticsIconName; end?: boolean }> = [
  { label: 'Resumen', path: '/logistics/inventory/ledger', icon: 'dashboard', end: true },
  { label: 'Movimientos', path: '/logistics/inventory/ledger/movements', icon: 'list' },
  { label: 'Kardex', path: '/logistics/inventory/ledger/kardex', icon: 'timeline' },
  { label: 'Eventos', path: '/logistics/inventory/ledger/prepared-events', icon: 'activity' },
  { label: 'Particiones', path: '/logistics/inventory/ledger/partitions', icon: 'layers' },
  { label: 'Checkpoints', path: '/logistics/inventory/ledger/checkpoints', icon: 'shield' },
  { label: 'Reconciliación', path: '/logistics/inventory/ledger/reconciliation', icon: 'check-square' },
  { label: 'Exportar', path: '/logistics/inventory/ledger/exports', icon: 'arrow-down' },
]

export function InventoryLedgerPhaseNav() {
  return (
    <nav
      aria-label="Navegación del libro de inventario"
      className="overflow-x-auto rounded-2xl border border-slate-200 bg-white p-1.5 shadow-sm"
    >
      <div className="flex min-w-max items-center gap-1">
        {ITEMS.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.end}
            className={({ isActive }) =>
              `inline-flex min-h-10 items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 ${
                isActive
                  ? 'bg-slate-950 text-white shadow-sm'
                  : 'text-slate-600 hover:bg-slate-100 hover:text-slate-950'
              }`
            }
          >
            <LogisticsIcon name={item.icon} size={16} aria-hidden="true" />
            {item.label}
          </NavLink>
        ))}
      </div>
    </nav>
  )
}
