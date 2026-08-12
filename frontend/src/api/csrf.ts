import { API_ROOT } from './config'
import {
  getRequestLanguage,
  recordContentLanguage,
} from './locale'
import { ApiRequestError } from '../types/api'

let csrfToken: string | null = null
let pendingRequest: Promise<string> | null = null

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function readCsrfToken(value: unknown): string {
  if (
    !isRecord(value) ||
    typeof value.csrf_token !== 'string' ||
    value.csrf_token.length === 0
  ) {
    throw new ApiRequestError('La respuesta CSRF no es válida.', {
      code: 'INVALID_RESPONSE',
    })
  }

  return value.csrf_token
}

async function requestCsrfToken(): Promise<string> {
  const controller = new AbortController()
  const timeoutId = window.setTimeout(() => controller.abort(), 15_000)
  let response: Response

  try {
    response = await fetch(`${API_ROOT}/auth/csrf`, {
      method: 'GET',
      credentials: 'include',
      signal: controller.signal,
      headers: {
        Accept: 'application/json',
        'Accept-Language': getRequestLanguage(),
      },
    })
  } catch (error: unknown) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiRequestError('La solicitud excedió el tiempo de espera.', {
        code: 'TIMEOUT',
      })
    }

    throw new ApiRequestError('No se pudo conectar con el servidor.', {
      code: 'NETWORK_ERROR',
    })
  } finally {
    window.clearTimeout(timeoutId)
  }

  recordContentLanguage(response.headers.get('Content-Language'))

  if (!response.ok) {
    throw new ApiRequestError('No fue posible preparar la solicitud segura.', {
      code: 'CSRF_FETCH_FAILED',
      status: response.status,
    })
  }

  const data: unknown = await response.json()
  csrfToken = readCsrfToken(data)
  return csrfToken
}

export function clearCsrfToken(): void {
  csrfToken = null
  pendingRequest = null
}

export async function getCsrfToken(): Promise<string> {
  if (csrfToken) {
    return csrfToken
  }

  if (!pendingRequest) {
    pendingRequest = requestCsrfToken().finally(() => {
      pendingRequest = null
    })
  }

  return pendingRequest
}

export async function refreshCsrfToken(): Promise<string> {
  clearCsrfToken()
  return getCsrfToken()
}
