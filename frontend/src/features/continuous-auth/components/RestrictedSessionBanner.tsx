import { Link } from 'react-router-dom'
import { Button } from '../../../components/common/Button'
import { LogisticsIcon } from '../../../components/common/LogisticsIcon'

export function RestrictedSessionBanner({
  onReverify,
  onLogout,
  isLoggingOut,
}: {
  onReverify: () => void
  onLogout: () => void
  isLoggingOut: boolean
}) {
  return (
    <section
      className="border-b border-orange-300 bg-orange-50"
      role="alert"
      aria-labelledby="restricted-session-title"
    >
      <div className="w-full min-w-0 flex flex-col gap-3 px-4 sm:px-5 lg:px-6 xl:px-8 2xl:px-10 py-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <LogisticsIcon
            name="shield"
            size={20}
            className="mt-0.5 shrink-0 text-orange-700"
          />
          <div>
            <h2
              id="restricted-session-title"
              className="text-sm font-bold text-orange-950"
            >
              Tu sesión está restringida temporalmente
            </h2>
            <p className="text-xs text-orange-900">
              Las consultas siguen disponibles, pero debes reverificar tu
              identidad antes de iniciar una operación sensible.
            </p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Link
            to="/security/continuous-auth"
            className="px-2 py-2 text-xs font-semibold text-orange-900 underline underline-offset-2"
          >
            Ver estado
          </Link>
          <Button size="small" onClick={onReverify}>
            Reverificar
          </Button>
          <Button
            size="small"
            variant="secondary"
            onClick={onLogout}
            isLoading={isLoggingOut}
          >
            Cerrar sesión
          </Button>
        </div>
      </div>
    </section>
  )
}
