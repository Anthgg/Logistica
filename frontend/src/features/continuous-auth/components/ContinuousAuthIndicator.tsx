import { Link } from 'react-router-dom'
import { LogisticsIcon } from '../../../components/common/LogisticsIcon'
import { useTranslations } from '../../../hooks/useTranslations'
import { formatDateTime } from '../../../utils/date'
import { useContinuousAuth } from '../hooks/useContinuousAuth'

const stateStyles = {
  safe: 'border-emerald-200 bg-emerald-50 text-emerald-800',
  attention: 'border-amber-200 bg-amber-50 text-amber-900',
  restricted: 'border-orange-200 bg-orange-50 text-orange-900',
  offline: 'border-slate-300 bg-slate-100 text-slate-700',
}

export function ContinuousAuthIndicator({ inline = false }: { inline?: boolean }) {
  const { translate } = useTranslations()
  const {
    status,
    riskLevel,
    authenticationLevel,
    error,
    isLoading,
  } = useContinuousAuth()

  const visualState =
    error && !status
      ? 'offline'
      : authenticationLevel === 'restricted' ||
          authenticationLevel === 'terminated' ||
          riskLevel === 'critical'
        ? 'restricted'
        : authenticationLevel === 'verification_required' ||
            riskLevel === 'medium' ||
            riskLevel === 'high' ||
            status?.degraded
          ? 'attention'
          : 'safe'

  const title = error && !status
      ? 'Estado de seguridad sin conexión'
      : status && !status.enabled
        ? 'Autenticación continua desactivada'
      : translate('risk', riskLevel, riskLevel)
  const authenticationLabel = translate(
    'auth_level',
    authenticationLevel,
    authenticationLevel,
  )

  const inlineDotColor = {
    safe: 'bg-emerald-500',
    attention: 'bg-amber-500',
    restricted: 'bg-orange-500',
    offline: 'bg-slate-400',
  }[visualState]

  const inlineTextColor = {
    safe: 'text-emerald-700',
    attention: 'text-amber-700',
    restricted: 'text-orange-700',
    offline: 'text-slate-500',
  }[visualState]

  if (inline) {
    return (
      <>
        <Link
          to="/security/continuous-auth"
          className={`flex items-center gap-1.5 no-underline transition-opacity hover:opacity-80 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 ${inlineTextColor}`}
          aria-label={`${title}. ${authenticationLabel}. Abrir estado de seguridad.`}
        >
          <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${inlineDotColor}`} aria-hidden="true" />
          <span className="truncate">{isLoading ? '…' : title}</span>
        </Link>
        <span className="sr-only" aria-live="polite" aria-atomic="true">
          {title}. {authenticationLabel}.
        </span>
      </>
    )
  }

  return (
    <>
      <Link
        to="/security/continuous-auth"
        className={`flex min-h-11 items-center gap-2 rounded-xl border px-2.5 py-1.5 no-underline transition hover:brightness-95 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 ${stateStyles[visualState]}`}
        aria-label={`${title}. ${authenticationLabel}. Abrir estado de seguridad.`}
      >
        <LogisticsIcon name="shield" size={17} />
        <span className="hidden min-w-0 lg:block">
          <span className="block truncate text-[11px] font-bold">
            {isLoading ? 'Actualizando seguridad…' : title}
          </span>
          <span className="block truncate text-[10px] opacity-75">
            {status?.last_evaluation_at
              ? `Verificado ${formatDateTime(status.last_evaluation_at)}`
              : authenticationLabel}
          </span>
        </span>
        {(authenticationLevel === 'verification_required' ||
          authenticationLevel === 'restricted') && (
          <span
            className="h-2 w-2 shrink-0 rounded-full bg-current"
            aria-hidden="true"
          />
        )}
      </Link>
      <span className="sr-only" aria-live="polite" aria-atomic="true">
        {title}. {authenticationLabel}.
      </span>
    </>
  )
}
