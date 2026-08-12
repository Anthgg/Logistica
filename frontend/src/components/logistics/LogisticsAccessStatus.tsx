import { useLogisticsAccess } from '../../features/logistics-me/hooks/useLogisticsAccess'
import type { LogisticsAccessStatus } from '../../types/logistics-me'

const STATUS_LABELS: Record<LogisticsAccessStatus, string> = {
  loading: 'Cargando acceso logístico…',
  enabled: 'Acceso logístico activo',
  disabled: 'Acceso logístico deshabilitado',
  no_role: 'Sin rol logístico',
  no_scope: 'Sin alcance organizacional',
  session_expired: 'Sesión expirada',
  error: 'Error de acceso',
}

export function LogisticsAccessStatus({ inline = false }: { inline?: boolean }) {
  const { accessStatus, logisticsUser, currentContext } = useLogisticsAccess()

  if (accessStatus !== 'enabled') {
    return null
  }

  if (inline) {
    return (
      <span
        className="flex items-center gap-1.5 text-emerald-700"
        role="status"
        aria-live="polite"
      >
        <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-500" aria-hidden="true" />
        <span className="truncate">
          {logisticsUser ? logisticsUser.display_name : STATUS_LABELS[accessStatus]}
        </span>
      </span>
    )
  }

  return (
    <div
      className="flex items-center gap-3 rounded-lg border border-slate-200 bg-white px-4 py-2 text-xs"
      role="status"
      aria-live="polite"
    >
      <span className="flex h-2 w-2 rounded-full bg-emerald-500" aria-hidden="true" />
      <span className="font-medium text-slate-700">
        {STATUS_LABELS[accessStatus]}
      </span>
      {logisticsUser && (
        <span className="text-slate-500">· {logisticsUser.display_name}</span>
      )}
      {currentContext.organization_id && (
        <span className="text-slate-400">
          · Org: {currentContext.organization_id.slice(0, 8)}
        </span>
      )}
    </div>
  )
}