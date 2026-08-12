import { Button } from '../common/Button'
import { LogisticsIcon } from '../common/LogisticsIcon'

interface SessionsErrorStateProps {
  onRetry: () => void
}

export function SessionsErrorState({ onRetry }: SessionsErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-8 px-4 text-center">
      <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-danger-xlight text-danger" aria-hidden="true">
        <LogisticsIcon name="alert" size={24} />
      </div>
      <h3 className="text-sm font-semibold text-ink">No pudimos cargar las sesiones</h3>
      <p className="text-2xs text-muted max-w-[300px]">
        Verifica tu conexión e inténtalo nuevamente.
      </p>
      <Button type="button" variant="secondary" size="small" onClick={onRetry}>
        Intentar nuevamente
      </Button>
    </div>
  )
}