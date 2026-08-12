import { SessionRow } from './SessionRow'
import { LogisticsIcon } from '../common/LogisticsIcon'
import type { SessionSummary } from '../../types/session'

interface SessionsListProps {
  sessions: SessionSummary[]
  onRevoke: (session: SessionSummary) => void
  revokingIds: Set<string>
}

export function SessionsList({ sessions, onRevoke, revokingIds }: SessionsListProps) {
  if (sessions.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-2 py-8 px-4 text-center">
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-xlight text-emerald" aria-hidden="true">
          <LogisticsIcon name="shield" size={24} />
        </div>
        <h3 className="text-sm font-semibold text-ink">No hay otros dispositivos conectados</h3>
        <p className="text-2xs text-muted max-w-[280px]">
          Tu cuenta solo está abierta en este dispositivo.
        </p>
      </div>
    )
  }

  return (
    <section className="flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h2 className="text-sm font-semibold text-ink">Otros accesos</h2>
          <span className="text-2xs text-muted">
            Sesiones abiertas en otros navegadores o dispositivos
          </span>
        </div>
        <span className="rounded-full border border-border-subtle bg-slate-50 px-2 py-0.5 text-2xs font-semibold text-muted">
          {sessions.length} {sessions.length === 1 ? 'sesión' : 'sesiones'}
        </span>
      </div>

      <div className="flex flex-col gap-1.5">
        {sessions.map((session) => (
          <SessionRow
            key={session.id}
            session={session}
            onRevoke={onRevoke}
            isRevoking={revokingIds.has(session.id)}
          />
        ))}
      </div>
    </section>
  )
}