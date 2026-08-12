import { Button } from '../common/Button'
import { LogisticsIcon } from '../common/LogisticsIcon'

interface SessionsHeaderProps {
  onRefresh: () => void
  onLogoutOthers: () => void
  isRefreshing: boolean
  otherSessionsCount: number
}

export function SessionsHeader({
  onRefresh,
  onLogoutOthers,
  isRefreshing,
  otherSessionsCount,
}: SessionsHeaderProps) {
  return (
    <header className="flex flex-col items-stretch justify-between gap-3 border-b border-border-subtle pt-3 pb-3 sm:flex-row sm:items-center">
      <div className="min-w-0">
        <p className="text-2xs font-bold uppercase tracking-widest text-orange mb-1">
          Seguridad de la cuenta
        </p>
        <h1 className="text-xl font-bold text-ink tracking-tight leading-none">
          Sesiones y dispositivos
        </h1>
        <p className="text-xs text-muted mt-1">
          Supervisa los accesos recientes y revoca cualquier sesión que no reconozcas.
        </p>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        <Button
          type="button"
          variant="secondary"
          size="small"
          onClick={onRefresh}
          disabled={isRefreshing}
          className="gap-1.5"
        >
          <LogisticsIcon name="check" size={13} className={isRefreshing ? 'animate-spin' : ''} />
          {isRefreshing ? 'Actualizando…' : 'Actualizar'}
        </Button>
        {otherSessionsCount > 0 && (
          <Button
            type="button"
            variant="danger"
            size="small"
            onClick={onLogoutOthers}
          >
            Cerrar otras sesiones
          </Button>
        )}
      </div>
    </header>
  )
}