import { ApiRequestError } from '../../../types/api'

const CONTINUOUS_AUTH_ERROR_MESSAGES: Record<string, string> = {
  CONTINUOUS_AUTH_DISABLED:
    'La autenticación continua no está habilitada.',
  MODEL_REGISTRY_UNAVAILABLE:
    'Los modelos de verificación no están disponibles temporalmente.',
  FACIAL_MODEL_UNAVAILABLE:
    'La verificación facial no está disponible temporalmente.',
  PAD_MODEL_UNAVAILABLE:
    'La validación de presencia no está disponible temporalmente.',
  BEHAVIORAL_MODEL_UNAVAILABLE:
    'La validación conductual aún no está disponible.',
  FACIAL_TEMPLATE_NOT_FOUND:
    'No existe una plantilla facial habilitada para este participante.',
  FEATURE_SCHEMA_MISMATCH:
    'No se pudo procesar la información conductual.',
  INVALID_CAPTURE: 'La captura facial no pudo utilizarse.',
  INSUFFICIENT_COMPONENTS:
    'No existen suficientes componentes para completar la evaluación.',
  INFERENCE_TIMEOUT:
    'La evaluación tardó demasiado. Se intentará nuevamente.',
  INVALID_CREDENTIALS: 'No se pudo confirmar la contraseña.',
  REVERIFICATION_REQUIRED: 'Debes verificar nuevamente tu identidad.',
  SESSION_RESTRICTED: 'Tu sesión está restringida temporalmente.',
  SESSION_TERMINATED: 'Tu sesión fue finalizada por seguridad.',
  TOO_MANY_ATTEMPTS:
    'Se realizaron demasiados intentos. Espera antes de volver a intentarlo.',
  NETWORK_ERROR: 'No se pudo conectar con el servicio de verificación.',
  TIMEOUT: 'El servicio de verificación tardó demasiado en responder.',
  INVALID_RESPONSE:
    'El servicio de verificación devolvió una respuesta inesperada.',
}

export function getContinuousAuthErrorMessage(error: unknown): string {
  if (error instanceof ApiRequestError) {
    if (error.status === 503) {
      return 'Modelos no disponibles. La autenticación funciona en modo degradado.'
    }

    if (error.status === 409) {
      return 'Autenticación degradada. La evaluación no está disponible temporalmente.'
    }

    return (
      CONTINUOUS_AUTH_ERROR_MESSAGES[error.code] ??
      (error.status === 403
        ? 'La operación no está disponible con el estado actual de tu sesión.'
        : 'No se pudo actualizar el estado de seguridad.')
    )
  }

  return 'No se pudo actualizar el estado de seguridad.'
}

export function getContinuousAuthErrorCode(error: unknown): string | null {
  return error instanceof ApiRequestError ? error.code : null
}

export function isTerminatedSessionError(error: unknown): boolean {
  return (
    error instanceof ApiRequestError &&
    error.code === 'SESSION_TERMINATED'
  )
}

export function isRestrictedSessionError(error: unknown): boolean {
  return (
    error instanceof ApiRequestError &&
    ['SESSION_RESTRICTED', 'REVERIFICATION_REQUIRED'].includes(error.code)
  )
}
