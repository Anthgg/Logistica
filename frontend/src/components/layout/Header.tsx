import { useLocation } from 'react-router-dom'
import { UserMenu } from './UserMenu'
import {
  LogisticsIcon,
  type LogisticsIconName,
} from '../common/LogisticsIcon'
import { APP_NAME, COMPANY_NAME } from '../../api/config'
import { LanguageSwitcher } from '../common/LanguageSwitcher'
import { ContinuousAuthIndicator } from '../../features/continuous-auth/components/ContinuousAuthIndicator'
import { LogisticsContextSwitcher } from '../logistics/LogisticsContextSwitcher'
import { LogisticsAccessStatus } from '../logistics/LogisticsAccessStatus'

export function Header() {
  const location = useLocation()
  const section = location.pathname.split('/').filter(Boolean)[0] ?? 'dashboard'

  const sections: Record<string, { title: string; description: string; icon: LogisticsIconName }> = {
    dashboard:        { title: 'Centro de control',     description: 'Pulso operativo de la red',           icon: 'dashboard' },
    clients:          { title: 'Clientes',              description: 'Cartera y puntos de atención',        icon: 'clients'   },
    shipments:        { title: 'Envíos y despachos',    description: 'Trazabilidad de origen a destino',    icon: 'truck'     },
    warehouses:       { title: 'Red de almacenes',      description: 'Capacidad y centros operativos',      icon: 'building'  },
    inventory:        { title: 'Inventario',            description: 'Stock y movimientos de mercancía',    icon: 'box'       },
    routes:           { title: 'Rutas de transporte',   description: 'Planificación de recorridos',         icon: 'route'     },
    incidents:        { title: 'Incidencias',           description: 'Excepciones y respuesta operativa',   icon: 'alert'     },
    reports:          { title: 'Analítica logística',   description: 'Rendimiento y tendencias',            icon: 'reports'   },
    research:         { title: 'Biometría',             description: 'Entrenamiento y control seguro',      icon: 'research'  },
    profile:          { title: 'Perfil de usuario',     description: 'Datos y preferencias de cuenta',      icon: 'user'      },
    sessions:         { title: 'Dispositivos y accesos',description: 'Control de sesiones activas',         icon: 'sessions'  },
    'change-password':{ title: 'Seguridad',             description: 'Credenciales y protección',           icon: 'key'       },
    security:         { title: 'Estado de seguridad',   description: 'Autenticación continua de la sesión', icon: 'shield'    },
    admin:            { title: 'Control de seguridad',  description: 'Supervisión y estado de modelos',     icon: 'shield'    },
  }

  const currentSection = sections[section] ?? {
    title: section,
    description: 'Operación logística',
    icon: 'layers' as LogisticsIconName,
  }

  const currentDate = new Intl.DateTimeFormat('es-PE', {
    weekday: 'short',
    day: '2-digit',
    month: 'short',
  }).format(new Date())

  return (
    <header className="sticky top-0 z-40 w-full bg-white shadow-[0_1px_0_0_#f1f5f9]">
      {/* Nivel 1 — Identidad y cuenta (~48px) */}
      <div className="flex h-12 items-center justify-between px-4 sm:px-5 lg:px-6 xl:px-8">
        <div className="flex shrink-0 items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-900 text-white">
            <LogisticsIcon name="route" size={16} />
          </div>
          <span className="text-sm font-bold tracking-tight text-slate-900">
            {APP_NAME}
            <span className="mx-1.5 font-light text-slate-300">/</span>
            <span className="font-medium text-slate-400">{COMPANY_NAME}</span>
          </span>
        </div>

        <div className="flex shrink-0 items-center gap-1.5">
          <LanguageSwitcher compact ghost />
          <UserMenu />
        </div>
      </div>

      {/* Nivel 2 — Barra de estado (~36px) */}
      <div className="flex h-9 items-center justify-between border-t border-slate-100 bg-slate-50 px-4 sm:px-5 lg:px-6 xl:px-8">
        {/* Izquierda: sección activa */}
        <div className="flex min-w-0 items-center gap-1.5">
          <LogisticsIcon
            name={currentSection.icon}
            size={13}
            className="shrink-0 text-blue-500"
          />
          <span className="truncate text-[11px] font-semibold text-slate-700">
            {currentSection.title}
          </span>
          <span className="hidden text-[11px] text-slate-300 sm:inline" aria-hidden="true">·</span>
          <span className="hidden truncate text-[11px] text-slate-400 sm:inline">
            {currentSection.description}
          </span>
        </div>

        {/* Derecha: indicadores planos */}
        <div className="flex shrink-0 items-center gap-3 text-[11px] text-slate-400">
          <span className="hidden items-center gap-1.5 xl:flex">
            <span className="pulse-dot !h-1.5 !w-1.5" aria-hidden="true" />
            <span className="font-medium text-emerald-700">Operativo</span>
          </span>
          <span className="hidden h-3 w-px bg-slate-200 xl:block" aria-hidden="true" />

          <time className="hidden md:inline">{currentDate}</time>
          <span className="hidden h-3 w-px bg-slate-200 md:block" aria-hidden="true" />

          <ContinuousAuthIndicator inline />

          {section === 'logistics' && (
            <>
              <span className="h-3 w-px bg-slate-200" aria-hidden="true" />
              <LogisticsAccessStatus inline />
              <LogisticsContextSwitcher inline />
            </>
          )}
        </div>
      </div>
    </header>
  )
}
