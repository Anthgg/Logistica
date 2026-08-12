import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import { Button } from '../common/Button'
import { RestrictedSessionBanner } from '../../features/continuous-auth/components/RestrictedSessionBanner'
import { ReverificationDialog } from '../../features/continuous-auth/components/ReverificationDialog'
import { useContinuousAuth } from '../../features/continuous-auth/hooks/useContinuousAuth'
import { useAuth } from '../../hooks/useAuth'
import { Header } from './Header'
import { FloatingNavigationBar } from '../navigation/FloatingNavigationBar'

export function DashboardLayout() {
  const { logout } = useAuth()
  const {
    authenticationLevel,
    riskLevel,
    requestReverification,
    notice,
  } = useContinuousAuth()
  const [isLoggingOut, setIsLoggingOut] = useState(false)
  const isRestricted = authenticationLevel === 'restricted'
  const needsAttention =
    !isRestricted &&
    (authenticationLevel === 'verification_required' ||
      riskLevel === 'high' ||
      riskLevel === 'critical')

  const handleLogout = async () => {
    setIsLoggingOut(true)
    try {
      await logout()
    } finally {
      setIsLoggingOut(false)
    }
  }

  return (
    <div className="relative flex min-h-screen w-full flex-col overflow-x-hidden bg-[linear-gradient(135deg,_#f8fbff_0%,_#f4f7fb_42%,_#f8fafc_100%)] text-slate-900">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-64 bg-gradient-to-b from-sky-100/70 via-sky-50/20 to-transparent" />
      <Header />
      <div className="flex w-full flex-col px-4 pt-4 sm:px-6 lg:px-8">
        {isRestricted && (
          <div className="mb-4">
            <RestrictedSessionBanner
              onReverify={requestReverification}
              onLogout={() => void handleLogout().catch(() => undefined)}
              isLoggingOut={isLoggingOut}
            />
          </div>
        )}
        {needsAttention && (
          <section
            className={`mb-4 rounded-2xl border px-4 py-4 shadow-[0_10px_30px_-18px_rgba(15,23,42,0.35)] sm:px-6 ${
              riskLevel === 'critical'
                ? 'border-rose-200 bg-rose-50/90 text-rose-950'
                : 'border-amber-200 bg-amber-50/90 text-amber-950'
            }`}
            role={riskLevel === 'critical' ? 'alert' : 'status'}
          >
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-sm font-semibold leading-6">
                {riskLevel === 'critical'
                  ? 'Se requiere reverificación inmediata antes de continuar con operaciones sensibles.'
                  : 'Reverifica tu identidad antes de iniciar una operación sensible.'}
              </p>
              <Button size="small" onClick={requestReverification}>
                Reverificar identidad
              </Button>
            </div>
          </section>
        )}
      </div>
      <main className="relative flex w-full flex-1 flex-col px-4 pb-32 pt-2 sm:px-6 lg:px-8 lg:pt-3">
        <Outlet />
      </main>
      <FloatingNavigationBar />
      <ReverificationDialog />
      <span className="sr-only" aria-live="polite" aria-atomic="true">
        {notice}
      </span>
    </div>
  )
}