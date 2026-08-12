import { useState } from 'react'
import { LogisticsIcon } from '../common/LogisticsIcon'
import { DeviceIcon } from './DeviceIcon'
import { SessionStatusBadge } from './SessionStatusBadge'
import {
  formatRelativeTime,
  formatSessionDate,
  formatExpiry,
  isExpiringSoon,
  isExpired,
} from '../../utils/session-dates'
import { maskIpAddress } from '../../utils/date'
import type { SessionSummary } from '../../types/session'

interface SessionRowProps {
  session: SessionSummary
  onRevoke: (session: SessionSummary) => void
  isRevoking: boolean
}

function safeText(value: string | null, fallback = 'No identificado'): string {
  return value && value.trim() !== '' ? value : fallback
}

function getTrustStatus(session: SessionSummary) {
  if (isExpired(session.expires_at)) {
    return { type: 'expired' as const, label: 'Expirada' }
  }
  if (isExpiringSoon(session.expires_at)) {
    return { type: 'expiring' as const, label: 'Próxima a expirar' }
  }
  if (session.browser && session.operating_system) {
    return { type: 'trusted' as const, label: 'Dispositivo conocido' }
  }
  return { type: 'unknown' as const, label: 'No reconocido' }
}

export function SessionRow({ session, onRevoke, isRevoking }: SessionRowProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const trustStatus = getTrustStatus(session)

  return (
    <div
      className="overflow-hidden rounded-lg border border-border-subtle bg-white shadow-xs transition-colors hover:border-border-strong"
    >
      {/* Desktop / tablet view */}
      <div className="hidden sm:grid grid-cols-[1.4fr_1fr_1fr_0.8fr_auto] items-center gap-3 p-3">
        {/* Device */}
        <div className="flex min-w-0 items-center gap-2.5">
          <DeviceIcon deviceType={session.device_type} size={16} />
          <div className="min-w-0">
            <p className="text-xs font-semibold text-ink truncate">
              {safeText(session.browser)}
            </p>
            <p className="text-2xs text-muted truncate">
              {safeText(session.operating_system)} · {safeText(session.device_type, 'Dispositivo')}
            </p>
          </div>
        </div>

        {/* IP */}
        <div className="min-w-0">
          <p className="font-mono text-2xs text-ink">
            {maskIpAddress(session.ip_address)}
          </p>
          <p className="text-2xs text-faint mt-0.5">Dirección IP</p>
        </div>

        {/* Activity */}
        <div className="min-w-0">
          <p className="text-2xs text-ink">
            {formatRelativeTime(session.last_activity_at)}
          </p>
          <p className="text-2xs text-faint mt-0.5" title={formatSessionDate(session.created_at)}>
            Inicio: {formatSessionDate(session.created_at)}
          </p>
        </div>

        {/* Expiry */}
        <div className="min-w-0">
          <p className="text-2xs text-ink">{formatExpiry(session.expires_at)}</p>
          <div className="mt-1">
            <SessionStatusBadge type={trustStatus.type} label={trustStatus.label} />
          </div>
        </div>

        {/* Action */}
        <div className="flex justify-end">
          <button
            type="button"
            onClick={() => onRevoke(session)}
            disabled={isRevoking}
            aria-label="Revocar sesión"
            title="Revocar sesión"
            className="group inline-flex h-8 w-8 cursor-pointer items-center justify-center rounded-lg border border-transparent bg-transparent text-muted transition-colors hover:border-danger hover:bg-danger-xlight hover:text-danger disabled:opacity-50"
          >
            <LogisticsIcon name="chevron" size={16} className="rotate-180" />
          </button>
        </div>
      </div>

      {/* Mobile view */}
      <div className="sm:hidden">
        <button
          type="button"
          onClick={() => setIsExpanded((v) => !v)}
          className="flex w-full items-center gap-2.5 p-3 text-left"
          aria-expanded={isExpanded}
        >
          <DeviceIcon deviceType={session.device_type} size={16} />
          <div className="min-w-0 flex-1">
            <p className="text-xs font-semibold text-ink truncate">
              {safeText(session.browser)}
            </p>
            <p className="text-2xs text-muted truncate">
              {formatRelativeTime(session.last_activity_at)}
            </p>
          </div>
          <div className="shrink-0">
            <SessionStatusBadge type={trustStatus.type} label={trustStatus.label} />
          </div>
          <LogisticsIcon
            name="chevron"
            size={14}
            className={`text-faint transition-transform ${isExpanded ? 'rotate-90' : ''}`}
          />
        </button>

        {isExpanded && (
          <div className="border-t border-border-subtle p-3 space-y-2.5">
            <div className="flex justify-between">
              <span className="text-2xs text-faint">Sistema operativo</span>
              <span className="text-2xs text-ink">{safeText(session.operating_system)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-2xs text-faint">Tipo</span>
              <span className="text-2xs text-ink">{safeText(session.device_type, 'Dispositivo')}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-2xs text-faint">Dirección IP</span>
              <span className="font-mono text-2xs text-ink">{maskIpAddress(session.ip_address)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-2xs text-faint">Inicio de sesión</span>
              <span className="text-2xs text-ink">{formatSessionDate(session.created_at)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-2xs text-faint">Expiración</span>
              <span className="text-2xs text-ink">{formatExpiry(session.expires_at)}</span>
            </div>
            <button
              type="button"
              onClick={() => onRevoke(session)}
              disabled={isRevoking}
              className="mt-2 w-full rounded-lg border border-border py-2.5 text-xs font-semibold text-danger transition-colors hover:bg-danger-xlight disabled:opacity-50"
            >
              Revocar sesión
            </button>
          </div>
        )}
      </div>
    </div>
  )
}