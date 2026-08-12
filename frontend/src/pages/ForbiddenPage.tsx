import { Link } from 'react-router-dom'

export type ForbiddenReason = 'denied' | 'scope' | 'load_error'

const REASONS: Record<ForbiddenReason, { title: string; body: string }> = {
  denied: {
    title: 'No tienes permisos para esta sección',
    body: 'Tu cuenta no está autorizada para acceder a esta sección. Contacta con tu administrador si necesitas acceso.',
  },
  scope: {
    title: 'Esta sección no está disponible para tu alcance',
    body: 'Tu rol no cubre la organización, sede o almacén seleccionado. Cambia de contexto o contacta con tu administrador.',
  },
  load_error: {
    title: 'No se pudo verificar tu autorización',
    body: 'Ocurrió un problema al cargar tus permisos. Inténtalo nuevamente en unos momentos.',
  },
}

export function ForbiddenPage({
  reason = 'denied',
}: {
  reason?: ForbiddenReason
}) {
  const text = REASONS[reason]
  return (
    <main className="error-page" role="alert" aria-live="assertive">
      <div className="error-page__code">403</div>
      <p className="eyebrow">Acceso restringido</p>
      <h1>{text.title}</h1>
      <p>{text.body}</p>
      <Link
        className="button button--primary button--medium"
        to="/dashboard"
      >
        Volver al inicio
      </Link>
    </main>
  )
}