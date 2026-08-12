import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getSessions, revokeSession } from '../api/session-api'
import { Alert } from '../components/common/Alert'
import { useSensitiveOperationGuard } from '../features/continuous-auth/hooks/useSensitiveOperationGuard'
import { useAuth } from '../hooks/useAuth'
import type { SessionSummary } from '../types/session'
import { getErrorMessage } from '../utils/errors'
import { formatRelativeTime } from '../utils/session-dates'
import { SessionsHeader } from '../components/sessions/SessionsHeader'
import { SecuritySummary } from '../components/sessions/SecuritySummary'
import { CurrentSessionCard } from '../components/sessions/CurrentSessionCard'
import { SessionsList } from '../components/sessions/SessionsList'
import { SessionsSkeleton } from '../components/sessions/SessionsSkeleton'
import { SessionsErrorState } from '../components/sessions/SessionsErrorState'
import { RevokeSessionDialog } from '../components/sessions/RevokeSessionDialog'
import { RevokeOtherSessionsDialog } from '../components/sessions/RevokeOtherSessionsDialog'

export function SessionsPage() {
  const { invalidateSession, logoutAll } = useAuth()
  const { guardSensitiveAction } = useSensitiveOperationGuard()
  const navigate = useNavigate()
  const [sessions, setSessions] = useState<SessionSummary[]>([])
  const [selectedSession, setSelectedSession] = useState<SessionSummary | null>(null)
  const [revokingIds, setRevokingIds] = useState<Set<string>>(new Set())
  const [isLoading, setIsLoading] = useState(true)
  const [isLogoutAllDialogOpen, setIsLogoutAllDialogOpen] = useState(false)
  const [isLoggingOutAll, setIsLoggingOutAll] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<string>('')

  const loadSessions = useCallback(async () => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await getSessions()
      setSessions(response.sessions)
      setLastUpdated('Actualizado hace unos segundos')
    } catch (caughtError: unknown) {
      setError(getErrorMessage(caughtError))
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadSessions()
  }, [loadSessions])

  // Update relative time label periodically
  useEffect(() => {
    if (isLoading) return undefined
    const interval = setInterval(() => {
      const oldestActivity = sessions
        .map((s) => new Date(s.last_activity_at).getTime())
        .sort((a, b) => b - a)[0]
      if (oldestActivity) {
        setLastUpdated(`Actualizado ${formatRelativeTime(new Date(oldestActivity).toISOString())}`)
      }
    }, 30000)
    return () => clearInterval(interval)
  }, [sessions, isLoading])

  const currentSession = useMemo(
    () => sessions.find((s) => s.is_current) ?? null,
    [sessions],
  )

  const otherSessions = useMemo(
    () => sessions.filter((s) => !s.is_current),
    [sessions],
  )

  const recognizedDevices = useMemo(() => {
    const devices = new Set(
      sessions
        .filter((s) => s.browser && s.operating_system)
        .map((s) => `${s.browser}-${s.operating_system}`),
    )
    return devices.size
  }, [sessions])

  const handleRevoke = async () => {
    if (!selectedSession || revokingIds.has(selectedSession.id)) return

    const target = selectedSession
    setRevokingIds((current) => new Set(current).add(target.id))
    setError(null)
    setSuccess(null)

    try {
      const executed = await guardSensitiveAction(async () => {
        await revokeSession(target.id)
      })
      if (!executed) return

      if (target.is_current) {
        invalidateSession('Esta sesión fue cerrada.')
        navigate('/login', {
          replace: true,
          state: { message: 'La sesión actual fue revocada.' },
        })
        return
      }

      setSessions((current) => current.filter((session) => session.id !== target.id))
      setSuccess('La sesión fue revocada correctamente.')
      setSelectedSession(null)
    } catch (caughtError: unknown) {
      setError(getErrorMessage(caughtError))
    } finally {
      setRevokingIds((current) => {
        const next = new Set(current)
        next.delete(target.id)
        return next
      })
    }
  }

  const handleLogoutAll = async () => {
    if (isLoggingOutAll) return

    setIsLoggingOutAll(true)
    setError(null)

    try {
      const executed = await guardSensitiveAction(async () => {
        await logoutAll()
      })
      if (!executed) return
      navigate('/login', {
        replace: true,
        state: { message: 'Todas las sesiones fueron cerradas correctamente.' },
      })
    } catch (caughtError: unknown) {
      setError(getErrorMessage(caughtError))
      setIsLogoutAllDialogOpen(false)
    } finally {
      setIsLoggingOutAll(false)
    }
  }

  const handleSessionRevoke = (session: SessionSummary) => {
    setSelectedSession(session)
  }

  return (
    <div className="flex flex-col gap-4 py-4 pb-28">
      <SessionsHeader
        onRefresh={() => void loadSessions()}
        onLogoutOthers={() => setIsLogoutAllDialogOpen(true)}
        isRefreshing={isLoading}
        otherSessionsCount={otherSessions.length}
      />

      {error && (
        <Alert variant="error" onDismiss={() => setError(null)}>
          {error}
        </Alert>
      )}
      {success && (
        <Alert variant="success" onDismiss={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      {isLoading ? (
        <SessionsSkeleton />
      ) : error && sessions.length === 0 ? (
        <SessionsErrorState onRetry={() => void loadSessions()} />
      ) : (
        <>
          {/* Security summary */}
          <SecuritySummary
            activeSessions={sessions.length}
            recognizedDevices={recognizedDevices}
            lastUpdated={lastUpdated}
          />

          {/* Current session */}
          {currentSession && (
            <CurrentSessionCard
              session={currentSession}
              onRevoke={() => setSelectedSession(currentSession)}
              isRevoking={revokingIds.has(currentSession.id)}
            />
          )}

          {/* Other sessions */}
          <SessionsList
            sessions={otherSessions}
            onRevoke={handleSessionRevoke}
            revokingIds={revokingIds}
          />

          {/* Security tip */}
          <aside className="flex items-start gap-2.5 rounded-lg border border-primary-light bg-primary-xlight p-3">
            <span className="inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary-light font-bold text-primary text-xs">
              i
            </span>
            <p className="text-2xs text-primary leading-relaxed">
              <strong>¿No reconoces un dispositivo?</strong> Revoca la sesión y
              cambia tu contraseña desde la pantalla de Seguridad.
            </p>
          </aside>
        </>
      )}

      <RevokeSessionDialog
        session={selectedSession}
        isOpen={selectedSession !== null}
        isLoading={selectedSession ? revokingIds.has(selectedSession.id) : false}
        onCancel={() => setSelectedSession(null)}
        onConfirm={() => void handleRevoke()}
      />

      <RevokeOtherSessionsDialog
        isOpen={isLogoutAllDialogOpen}
        sessions={otherSessions}
        isLoading={isLoggingOutAll}
        onCancel={() => setIsLogoutAllDialogOpen(false)}
        onConfirm={() => void handleLogoutAll()}
      />
    </div>
  )
}