export type InlinePermissionReason = 'denied' | 'scope' | 'loading' | 'error'

const MESSAGES: Record<InlinePermissionReason, string> = {
  denied: 'No tienes permisos para esta acción.',
  scope: 'Esta acción no está disponible para tu alcance actual.',
  loading: 'Verificando permisos…',
  error: 'No se pudo verificar tu autorización. Inténtalo nuevamente.',
}

export function InlinePermissionError({
  reason = 'denied',
}: {
  reason?: InlinePermissionReason
}) {
  return (
    <p
      className="inline-permission-error"
      role={reason === 'error' ? 'alert' : 'status'}
      aria-live="polite"
    >
      {MESSAGES[reason]}
    </p>
  )
}