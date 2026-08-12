import { Button } from '../common/Button'
import { DeviceIcon } from './DeviceIcon'
import { SessionStatusBadge } from './SessionStatusBadge'
import {
  formatRelativeTime,
  formatSessionDate,
  formatExpiry,
  isExpiringSoon,
} from '../../utils/session-dates'
import { maskIpAddress } from '../../utils/date'
import type { SessionSummary } from '../../types/session'

interface CurrentSessionCardProps {
  session: SessionSummary
  onRevoke: () => void
  isRevoking: boolean
}

function safeText(value: string | null, fallback = 'No identificado'): string {
  return value && value.trim() !== '' ? value : fallback
}

export function CurrentSessionCard({
  session,
  onRevoke,
  isRevoking,
}: CurrentSessionCardProps) {
  const expiringSoon = isExpiringSoon(session.expires_at)

  return (
    <section className="flex flex-col gap-2">
      <div className="flex items-center gap-2">
        <h2 className="text-sm font-semibold text-ink">Este dispositivo</h2>
        <span className="text-2xs text-muted">·</span>
        <span className="text-2xs text-muted">Sesión en uso</span>
      </div>

      <div
        className="relative overflow-hidden rounded-xl border border-emerald-200 bg-white shadow-sm"
        style={{ boxShadow: 'inset 3px 0 0 #28866B, 0 1px 2px rgba(21,34,53,0.05)' }}
      >
        <div className="flex flex-col gap-3 p-4 lg:flex-row lg:items-center">
          {/* Left: device info */}
          <div className="flex min-w-0 items-center gap-3 lg:w-[280px] shrink-0">
            <DeviceIcon deviceType={session.device_type} size={20} />
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-1.5">
                <span className="text-sm font-semibold text-ink truncate">
                  {safeText(session.browser)}
                </span>
              </div>
              <p className="text-2xs text-muted mt-0.5 truncate">
                {safeText(session.operating_system)} · {safeText(session.device_type, 'Equipo actual')}
              </p>
              <div className="flex flex-wrap items-center gap-1.5 mt-2">
                <SessionStatusBadge type="current" label="Sesión actual" />
                <SessionStatusBadge type="trusted" label="Protegida" />
              </div>
            </div>
          </div>

          {/* Center: details */}
          <div className="flex-1 grid grid-cols-2 gap-x-4 gap-y-2 lg:grid-cols-4">
            <div>
              <dt className="text-2xs font-semibold uppercase tracking-wide text-faint">IP</dt>
              <dd className="mt-0.5 font-mono text-2xs text-ink">
                {maskIpAddress(session.ip_address)}
              </dd>
            </div>
            <div>
              <dt className="text-2xs font-semibold uppercase tracking-wide text-faint">Inicio</dt>
              <dd className="mt-0.5 text-2xs text-ink" title={formatSessionDate(session.created_at)}>
                {formatSessionDate(session.created_at)}
              </dd>
            </div>
            <div>
              <dt className="text-2xs font-semibold uppercase tracking-wide text-faint">Última actividad</dt>
              <dd className="mt-0.5 text-2xs text-ink">
                {formatRelativeTime(session.last_activity_at)}
              </dd>
            </div>
            <div>
              <dt className="text-2xs font-semibold uppercase tracking-wide text-faint">Expiración</dt>
              <dd className="mt-0.5 text-2xs text-ink">
                {formatExpiry(session.expires_at)}
              </dd>
              {expiringSoon && (
                <span className="text-2xs text-orange mt-0.5 block">Próxima a expirar</span>
              )}
            </div>
          </div>

          {/* Right: action */}
          <div className="flex shrink-0 justify-end lg:w-auto">
            <Button
              type="button"
              variant="secondary"
              size="small"
              onClick={onRevoke}
              disabled={isRevoking}
              className="hover:border-danger hover:text-danger"
            >
              Cerrar sesión
            </Button>
          </div>
        </div>
      </div>
    </section>
  )
}