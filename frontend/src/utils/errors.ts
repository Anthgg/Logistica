import { ApiRequestError } from '../types/api'

const ERROR_MESSAGES: Record<string, string> = {
  INVALID_CREDENTIALS: 'Correo o contraseña incorrectos.',
  ACCOUNT_DISABLED:
    'Esta cuenta está deshabilitada. Contacta al administrador.',
  ACCOUNT_TEMPORARILY_LOCKED:
    'La cuenta está bloqueada temporalmente. Inténtalo más tarde.',
  EMAIL_ALREADY_REGISTERED: 'Ya existe una cuenta con este correo.',
  SESSION_EXPIRED: 'Tu sesión expiró. Inicia sesión nuevamente.',
  SESSION_REVOKED: 'Esta sesión fue cerrada.',
  INVALID_SESSION: 'Tu sesión ya no es válida. Inicia sesión nuevamente.',
  SESSION_REQUIRED: 'Inicia sesión para continuar.',
  INVALID_REFRESH_TOKEN: 'Tu sesión venció. Inicia sesión nuevamente.',
  REFRESH_TOKEN_EXPIRED: 'Tu sesión venció. Inicia sesión nuevamente.',
  REFRESH_TOKEN_REUSED:
    'La sesión fue invalidada por seguridad. Inicia sesión nuevamente.',
  SESSION_REFRESH_FAILED:
    'No fue posible renovar la sesión. Inicia sesión nuevamente.',
  WEAK_PASSWORD:
    'La contraseña no cumple los requisitos mínimos de seguridad.',
  PASSWORD_MISMATCH: 'Las contraseñas no coinciden.',
  CURRENT_PASSWORD_INCORRECT: 'La contraseña actual es incorrecta.',
  INVALID_CSRF_TOKEN:
    'No se pudo validar la solicitud. Inténtalo nuevamente.',
  CSRF_TOKEN_MISSING:
    'No se pudo validar la solicitud. Inténtalo nuevamente.',
  CSRF_VALIDATION_FAILED:
    'No se pudo validar la solicitud. Inténtalo nuevamente.',
  RATE_LIMIT_EXCEEDED:
    'Se realizaron demasiados intentos. Espera unos minutos.',
  CSRF_FETCH_FAILED:
    'No fue posible preparar la solicitud segura. Inténtalo nuevamente.',
  NETWORK_ERROR: 'No se pudo conectar con el servidor.',
  TIMEOUT: 'El servidor tardó demasiado en responder.',
  REQUEST_ABORTED: 'La solicitud fue cancelada.',
  VALIDATION_ERROR: 'Revisa los datos ingresados.',
  INVALID_RESPONSE: 'El servidor devolvió una respuesta inesperada.',
  HTTP_401: 'Tu sesión expiró. Inicia sesión nuevamente.',
  HTTP_403: 'No tienes permisos para realizar esta acción.',
  PERMISSION_DENIED: 'No tienes permisos para realizar esta acción.',
  PERMISSION_SCOPE_DENIED:
    'Esta acción no está disponible para tu alcance actual.',
  STEP_UP_REQUIRED:
    'Esta acción requiere verificación adicional de tu identidad.',
  SENSITIVE_ACTION_REASON_REQUIRED:
    'Debes indicar un motivo para realizar esta acción sensible.',
  CROSS_ORGANIZATION_ACCESS_DENIED:
    'No tienes acceso a la organización seleccionada.',
  CROSS_BRANCH_ACCESS_DENIED:
    'No tienes acceso a la sede seleccionada.',
  CROSS_WAREHOUSE_ACCESS_DENIED:
    'No tienes acceso al almacén seleccionado.',
  AUTHENTICATION_REQUIRED: 'Debes iniciar sesión para continuar.',
  USER_INACTIVE: 'Esta cuenta está inactiva. Contacta al administrador.',
  LOGISTICS_ACCESS_DISABLED: 'El acceso logístico está deshabilitado.',
  LOGISTICS_ROLE_REQUIRED: 'Se requiere un rol logístico para esta acción.',
  LOGISTICS_SCOPE_REQUIRED: 'Se requiere un alcance logístico válido.',
  LOGISTICS_CONTEXT_INVALID: 'El contexto organizacional no es válido.',
  LOGISTICS_CONTEXT_DENIED: 'No tienes acceso al contexto seleccionado.',
  HTTP_409: 'La operación entra en conflicto con el estado actual.',
  HTTP_413: 'El archivo excede el tamaño permitido por el servidor.',
  HTTP_415: 'El formato del archivo no es compatible. Usa JPEG o WebP.',
  HTTP_422: 'Revisa los datos ingresados.',
  HTTP_429: 'Se alcanzó el límite de solicitudes. Espera y vuelve a intentar.',
  HTTP_500: 'Ocurrió un error interno. Inténtalo más tarde.',
  HTTP_503: 'El servicio no está disponible temporalmente.',
  INTERNAL_ERROR: 'Ocurrió un error interno. Inténtalo más tarde.',
}

export function getErrorMessage(error: unknown): string {
  if (error instanceof ApiRequestError) {
    if (error.status === 500) {
      return ERROR_MESSAGES.HTTP_500
    }

    if (error.status !== null && error.message) {
      return error.message
    }

    return (
      ERROR_MESSAGES[error.code] ??
      (error.status ? ERROR_MESSAGES[`HTTP_${error.status}`] : undefined) ??
      (error.status && error.status >= 500
        ? ERROR_MESSAGES.HTTP_500
        : error.message || 'No se pudo completar la operación.')
    )
  }

  return 'Ocurrió un error inesperado. Inténtalo nuevamente.'
}

export function isAuthenticationError(error: unknown): boolean {
  return (
    error instanceof ApiRequestError &&
    (error.status === 401 ||
      ['SESSION_EXPIRED', 'SESSION_REVOKED', 'INVALID_SESSION'].includes(
        error.code,
      ))
  )
}

export function isNetworkError(error: unknown): boolean {
  return (
    error instanceof ApiRequestError &&
    ['NETWORK_ERROR', 'TIMEOUT'].includes(error.code)
  )
}
