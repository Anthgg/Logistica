import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { useLogisticsAccess } from '../features/logistics-me/hooks/useLogisticsAccess'

export type LogisticsUnavailableReason =
  | 'disabled'
  | 'no_role'
  | 'no_scope'
  | 'forbidden'
  | 'scope'
  | 'timeout'
  | 'error'

const REASONS: Record<
  LogisticsUnavailableReason,
  { title: string; body: string }
> = {
  disabled: {
    title: 'Acceso logístico deshabilitado',
    body: 'Tu cuenta no tiene acceso al módulo logístico. Contacta con tu administrador si necesitas acceso.',
  },
  no_role: {
    title: 'No tienes un rol logístico asignado',
    body: 'Tu cuenta no tiene roles logísticos activos. Solicita la asignación correspondiente a tu administrador.',
  },
  no_scope: {
    title: 'No tienes un alcance organizacional asignado',
    body: 'Tu rol no cubre ninguna organización, sede o almacén. Contacta con tu administrador para definir tu alcance.',
  },
  forbidden: {
    title: 'No tienes permisos para esta sección',
    body: 'Tu cuenta no está autorizada para acceder a esta sección del módulo logístico.',
  },
  scope: {
    title: 'Esta sección no está disponible para tu alcance',
    body: 'Tu rol no cubre la organización, sede o almacén seleccionado. Cambia de contexto o contacta con tu administrador.',
  },
  timeout: {
    title: 'El servicio logístico tardó demasiado en responder',
    body: 'Tu sesión sigue activa. Reintenta cuando el servicio termine de iniciar.',
  },
  error: {
    title: 'No se pudo verificar tu acceso logístico',
    body: 'Ocurrió un problema al cargar tu acceso. Inténtalo nuevamente en unos momentos.',
  },
}

export function LogisticsAccessUnavailablePage({
  reason = 'disabled',
}: {
  reason?: LogisticsUnavailableReason
}) {
  const text = REASONS[reason]
  const isServiceTimeout = reason === 'timeout'
  const { logout } = useAuth()
  const { refreshLogisticsSession } = useLogisticsAccess()

  const handleLogout = async () => {
    await logout()
  }

  const handleRetry = async () => {
    await refreshLogisticsSession()
  }

  return (
    <main className="error-page" role="alert" aria-live="assertive">
      <div className="error-page__code">{isServiceTimeout ? '504' : '403'}</div>
      <p className="eyebrow">
        {isServiceTimeout
          ? 'Servicio logístico temporalmente lento'
          : 'Acceso logístico restringido'}
      </p>
      <h1>{text.title}</h1>
      <p>{text.body}</p>
      <div className="flex gap-3 mt-4">
        <Link className="button button--primary button--medium" to="/dashboard">
          Volver al inicio
        </Link>
        {(reason === 'error' || reason === 'timeout') && (
          <button
            type="button"
            className="button button--secondary button--medium"
            onClick={() => void handleRetry()}
          >
            Reintentar
          </button>
        )}
        <button
          type="button"
          className="button button--ghost button--medium"
          onClick={() => void handleLogout()}
        >
          Cerrar sesión
        </button>
      </div>
    </main>
  )
}
