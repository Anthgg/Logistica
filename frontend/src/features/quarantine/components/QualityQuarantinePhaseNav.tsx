import { NavLink } from 'react-router-dom'
import { LogisticsIcon } from '../../../components/common/LogisticsIcon'
import type { LogisticsIconName } from '../../../components/common/LogisticsIcon'

const ITEMS: Array<{ label: string; path: string; icon: LogisticsIconName; end?: boolean }> = [
  { label: 'Resumen', path: '/logistics/quality/quarantine', icon: 'dashboard', end: true },
  { label: 'Casos', path: '/logistics/quality/quarantine/cases', icon: 'archive' },
  { label: 'Inspecciones', path: '/logistics/quality/inspections', icon: 'search' },
  { label: 'Zonas', path: '/logistics/quality/quarantine-zones', icon: 'location' },
  { label: 'Disponibilidad', path: '/logistics/quality/availability', icon: 'package' },
]

export function QualityQuarantinePhaseNav() {
  return (
    <nav aria-label="Navegación de cuarentena y calidad" className="overflow-x-auto rounded-2xl border border-slate-200 bg-white p-1.5 shadow-sm">
      <div className="flex min-w-max items-center gap-1">
        {ITEMS.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.end}
            className={({ isActive }) => `inline-flex min-h-10 items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 ${isActive ? 'bg-slate-950 text-white shadow-sm' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-950'}`}
          >
            <LogisticsIcon name={item.icon} size={16} aria-hidden="true" />
            {item.label}
          </NavLink>
        ))}
      </div>
    </nav>
  )
}
