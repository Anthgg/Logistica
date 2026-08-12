import {
  notifyUnauthorized,
  resetUnauthorizedNotification,
} from './auth-events'
import { API_ROOT } from './config'
import { clearCsrfToken, getCsrfToken } from './csrf'
export { clearCsrfToken, getCsrfToken }
import {
  getRequestLanguage,
  recordContentLanguage,
} from './locale'
import { ApiRequestError } from '../types/api'

type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'

export interface ApiRequestOptions {
  path: string
  method?: HttpMethod
  body?: unknown
  headers?: HeadersInit
  signal?: AbortSignal
  requiresCsrf?: boolean
  timeout?: number
  skipAuthRefresh?: boolean
}

interface RetryState {
  csrf: boolean
  authentication: boolean
  rateLimit: boolean
}

const MUTABLE_METHODS = new Set<HttpMethod>(['POST', 'PUT', 'PATCH', 'DELETE'])
const PUBLIC_AUTH_PATHS = new Set([
  '/auth/csrf',
  '/auth/login',
  '/auth/register',
  '/auth/refresh',
])
const CSRF_ERROR_CODES = new Set([
  'INVALID_CSRF_TOKEN',
  'CSRF_TOKEN_MISSING',
  'CSRF_VALIDATION_FAILED',
  'CSRF_ERROR',
  'INVALID_CSRF',
  'CSRF_EXPIRED',
])
const SESSION_ERROR_CODES = new Set([
  'SESSION_EXPIRED',
  'SESSION_REVOKED',
  'INVALID_SESSION',
  'SESSION_REQUIRED',
  'INVALID_REFRESH_TOKEN',
  'REFRESH_TOKEN_EXPIRED',
  'REFRESH_TOKEN_REUSED',
])

let refreshPromise: Promise<unknown> | null = null

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function extractError(payload: unknown, status: number): ApiRequestError {
  if (isRecord(payload) && isRecord(payload.error)) {
    const code =
      typeof payload.error.code === 'string'
        ? payload.error.code
        : `HTTP_${status}`
    const backendMessage =
      typeof payload.error.message === 'string'
        ? payload.error.message
        : 'La solicitud no pudo completarse.'
    const message =
      status === 500
        ? 'Ocurrió un error interno. Inténtalo más tarde.'
        : status === 429
          ? backendMessage ||
            'Demasiadas solicitudes. Inténtalo nuevamente en unos segundos.'
        : status === 503 && code === `HTTP_${status}`
          ? 'El servicio no está disponible temporalmente.'
          : backendMessage

    return new ApiRequestError(message, {
      code,
      status,
      details: status >= 500 ? null : payload.error.details,
    })
  }

  if (isRecord(payload) && Array.isArray(payload.detail)) {
    return new ApiRequestError('Revisa los datos ingresados.', {
      code: 'VALIDATION_ERROR',
      status,
      details: payload.detail,
    })
  }

  const message =
    status === 500
      ? 'Ocurrió un error interno. Inténtalo más tarde.'
      : status === 429
        ? 'Demasiadas solicitudes. Inténtalo nuevamente en unos segundos.'
      : status === 503
        ? 'El servicio no está disponible temporalmente.'
        : 'La solicitud no pudo completarse.'

  return new ApiRequestError(message, {
    code: status === 401 ? 'SESSION_REQUIRED' : `HTTP_${status}`,
    status,
  })
}

function getRetryDelayMs(retryAfter: string | null): number | null {
  if (!retryAfter) return null

  const seconds = Number(retryAfter)
  if (Number.isFinite(seconds) && seconds >= 0) {
    return Math.min(seconds * 1_000, 60_000)
  }

  const retryAt = Date.parse(retryAfter)
  if (Number.isNaN(retryAt)) return null
  return Math.min(Math.max(retryAt - Date.now(), 0), 60_000)
}

function waitForRetry(delayMs: number, signal: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal.aborted) {
      reject(new DOMException('Request aborted', 'AbortError'))
      return
    }

    const timerId = window.setTimeout(() => {
      signal.removeEventListener('abort', onAbort)
      resolve()
    }, delayMs)
    const onAbort = () => {
      window.clearTimeout(timerId)
      reject(new DOMException('Request aborted', 'AbortError'))
    }
    signal.addEventListener('abort', onAbort, { once: true })
  })
}

async function readPayload(response: Response): Promise<unknown> {
  if (response.status === 204) {
    return undefined
  }

  const text = await response.text()
  if (!text) {
    return undefined
  }

  const contentType = response.headers.get('content-type') ?? ''
  if (!contentType.includes('application/json')) {
    if (!response.ok) {
      return undefined
    }
    throw new ApiRequestError('El servidor devolvió una respuesta inesperada.', {
      code: 'INVALID_RESPONSE',
      status: response.status,
    })
  }

  try {
    return JSON.parse(text) as unknown
  } catch {
    throw new ApiRequestError('El servidor devolvió una respuesta inválida.', {
      code: 'INVALID_RESPONSE',
      status: response.status,
    })
  }
}

function buildUrl(path: string): string {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`

  if (
    normalizedPath === '/api' ||
    normalizedPath.startsWith('/api/')
  ) {
    throw new ApiRequestError(
      'La ruta de API no debe repetir el prefijo "/api".',
      { code: 'INVALID_API_PATH' },
    )
  }

  return `${API_ROOT}${normalizedPath}`
}

function shouldRefreshAuthentication(
  options: ApiRequestOptions,
  responseStatus: number,
  retryState: RetryState,
): boolean {
  return (
    responseStatus === 401 &&
    !options.skipAuthRefresh &&
    !retryState.authentication &&
    !PUBLIC_AUTH_PATHS.has(options.path)
  )
}

export function refreshAuthentication(): Promise<unknown> {
  if (!refreshPromise) {
    refreshPromise = apiRequest<unknown>({
      path: '/auth/refresh',
      method: 'POST',
      skipAuthRefresh: true,
    })
      .then((payload) => {
        clearCsrfToken()
        resetUnauthorizedNotification()
        return payload
      })
      .catch((error: unknown) => {
        const refreshError =
          error instanceof ApiRequestError && error.status !== null
            ? error
            : new ApiRequestError(
                'No fue posible renovar la sesión. Inicia sesión nuevamente.',
                {
                  code: 'SESSION_REFRESH_FAILED',
                  status: 401,
                  details: error,
                },
              )
        clearCsrfToken()
        notifyUnauthorized(refreshError)
        throw refreshError
      })
      .finally(() => {
        refreshPromise = null
      })
  }

  return refreshPromise
}

export async function apiRequest<T>(
  options: ApiRequestOptions,
): Promise<T> {
  const method = options.method ?? 'GET'
  const shouldUseCsrf =
    options.requiresCsrf ?? MUTABLE_METHODS.has(method)

  const execute = async (retryState: RetryState): Promise<T> => {
    const controller = new AbortController()
    const timeout = options.timeout ?? 15_000
    let didTimeout = false
    const timeoutId = window.setTimeout(() => {
      didTimeout = true
      controller.abort()
    }, timeout)
    const onExternalAbort = () => controller.abort()

    if (options.signal?.aborted) {
      controller.abort()
    } else {
      options.signal?.addEventListener('abort', onExternalAbort, { once: true })
    }

    try {
      const headers = new Headers(options.headers)
      headers.set('Accept', 'application/json')
      headers.set('Accept-Language', getRequestLanguage())

      const isMultipart = options.body instanceof FormData

      if (options.body !== undefined && !isMultipart) {
        headers.set('Content-Type', 'application/json')
      }

      if (shouldUseCsrf) {
        headers.set('X-CSRF-Token', await getCsrfToken())
      }

      const requestBody: BodyInit | undefined =
        options.body === undefined
          ? undefined
          : options.body instanceof FormData
            ? options.body
            : JSON.stringify(options.body)

      const response = await fetch(buildUrl(options.path), {
        method,
        credentials: 'include',
        headers,
        body: requestBody,
        signal: controller.signal,
      })
      recordContentLanguage(response.headers.get('Content-Language'))
      const payload = await readPayload(response)

      if (!response.ok) {
        const apiError = extractError(payload, response.status)

        const isCsrfError =
          CSRF_ERROR_CODES.has(apiError.code) ||
          apiError.message.toLowerCase().includes('csrf')

        if (
          shouldUseCsrf &&
          !retryState.csrf &&
          isCsrfError
        ) {
          clearCsrfToken()
          return execute({ ...retryState, csrf: true })
        }

        if (
          shouldRefreshAuthentication(options, response.status, retryState)
        ) {
          await refreshAuthentication()
          return execute({ ...retryState, authentication: true })
        }

        const retryDelayMs = getRetryDelayMs(
          response.headers.get('Retry-After'),
        )
        if (
          response.status === 429 &&
          method === 'GET' &&
          !retryState.rateLimit &&
          retryDelayMs !== null
        ) {
          await waitForRetry(retryDelayMs, controller.signal)
          return execute({ ...retryState, rateLimit: true })
        }

        if (
          response.status === 401 &&
          !options.skipAuthRefresh &&
          SESSION_ERROR_CODES.has(apiError.code)
        ) {
          clearCsrfToken()
          notifyUnauthorized(apiError)
        }

        throw apiError
      }

      return payload as T
    } catch (error: unknown) {
      if (error instanceof ApiRequestError) {
        throw error
      }

      if (error instanceof DOMException && error.name === 'AbortError') {
        throw new ApiRequestError(
          didTimeout
            ? 'La solicitud excedió el tiempo de espera.'
            : 'La solicitud fue cancelada.',
          {
            code: didTimeout ? 'TIMEOUT' : 'REQUEST_ABORTED',
          },
        )
      }

      throw new ApiRequestError('No se pudo conectar con el servidor.', {
        code: 'NETWORK_ERROR',
      })
    } finally {
      window.clearTimeout(timeoutId)
      options.signal?.removeEventListener('abort', onExternalAbort)
    }
  }

  return execute({ csrf: false, authentication: false, rateLimit: false })
}

export function authenticatedFetch<T>(
  path: string,
  options: Omit<ApiRequestOptions, 'path'> = {},
): Promise<T> {
  return apiRequest<T>({ ...options, path })
}
