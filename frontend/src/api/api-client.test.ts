import { beforeEach, describe, expect, it, vi } from 'vitest'
import { apiRequest } from './api-client'
import { API_ROOT, API_URL } from './config'
import { clearCsrfToken } from './csrf'
import {
  resetUnauthorizedNotification,
  subscribeToUnauthorized,
} from './auth-events'
import { ApiRequestError } from '../types/api'
import {
  getLastContentLanguage,
  recordContentLanguage,
  setRequestLanguage,
} from './locale'

type FetchMock = ReturnType<
  typeof vi.fn<
    (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>
  >
>

function jsonResponse(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

function createFetchMock(): FetchMock {
  const fetchMock = vi.fn<
    (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>
  >()
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

describe('apiRequest', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    clearCsrfToken()
    resetUnauthorizedNotification()
    setRequestLanguage('es-PE')
    recordContentLanguage(null)
  })

  it('usa la URL central y credentials include en GET', async () => {
    const fetchMock = createFetchMock()
    fetchMock.mockResolvedValue(jsonResponse({ success: true }))

    await apiRequest({ path: '/auth/me' })

    expect(fetchMock).toHaveBeenCalledWith(
      `${API_ROOT}/auth/me`,
      expect.objectContaining({ credentials: 'include', method: 'GET' }),
    )
  })

  it('envía Accept-Language y registra Content-Language', async () => {
    const fetchMock = createFetchMock()
    setRequestLanguage('pt-BR')
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify({ success: true }), {
        status: 200,
        headers: {
          'Content-Type': 'application/json',
          'Content-Language': 'pt',
        },
      }),
    )

    await apiRequest({ path: '/auth/me' })

    const headers = new Headers(fetchMock.mock.calls[0]?.[1]?.headers)
    expect(headers.get('Accept-Language')).toBe('pt-BR')
    expect(getLastContentLanguage()).toBe('pt')
  })

  it('solicita CSRF antes de una operación mutable', async () => {
    const fetchMock = createFetchMock()
    fetchMock
      .mockResolvedValueOnce(jsonResponse({ csrf_token: 'csrf-test' }))
      .mockResolvedValueOnce(jsonResponse({ success: true }))

    await apiRequest({
      path: '/auth/login',
      method: 'POST',
      body: { email: 'usuario@example.com' },
    })

    expect(fetchMock.mock.calls[0]?.[0]).toBe(`${API_ROOT}/auth/csrf`)
    expect(fetchMock.mock.calls[1]?.[0]).toBe(`${API_ROOT}/auth/login`)
  })

  it('envía X-CSRF-Token y JSON sin exponerlo en la URL', async () => {
    const fetchMock = createFetchMock()
    fetchMock
      .mockResolvedValueOnce(jsonResponse({ csrf_token: 'csrf-test' }))
      .mockResolvedValueOnce(jsonResponse({ success: true }))

    await apiRequest({
      path: '/auth/login',
      method: 'POST',
      body: { email: 'usuario@example.com' },
    })

    const [url, init] = fetchMock.mock.calls[1] ?? []
    const headers = new Headers(init?.headers)
    expect(headers.get('X-CSRF-Token')).toBe('csrf-test')
    expect(headers.get('Content-Type')).toBe('application/json')
    expect(String(url)).not.toContain('csrf-test')
  })

  it.each(['POST', 'PATCH', 'DELETE'] as const)(
    'envía cookies y CSRF para %s',
    async (method) => {
      const fetchMock = createFetchMock()
      fetchMock
        .mockResolvedValueOnce(jsonResponse({ csrf_token: 'mutable-csrf' }))
        .mockResolvedValueOnce(jsonResponse({ success: true }))

      await apiRequest({
        path: '/shipments/shipment-1',
        method,
        body: method === 'DELETE' ? undefined : { status: 'in_transit' },
      })

      const [, init] = fetchMock.mock.calls[1] ?? []
      const headers = new Headers(init?.headers)
      expect(init?.credentials).toBe('include')
      expect(headers.get('X-CSRF-Token')).toBe('mutable-csrf')
    },
  )

  it('renueva una vez el CSRF inválido y repite la operación', async () => {
    const fetchMock = createFetchMock()
    fetchMock
      .mockResolvedValueOnce(jsonResponse({ csrf_token: 'old-token' }))
      .mockResolvedValueOnce(
        jsonResponse(
          {
            success: false,
            error: {
              code: 'INVALID_CSRF_TOKEN',
              message: 'Token inválido',
            },
          },
          403,
        ),
      )
      .mockResolvedValueOnce(jsonResponse({ csrf_token: 'new-token' }))
      .mockResolvedValueOnce(jsonResponse({ success: true }))

    await apiRequest({ path: '/auth/logout', method: 'POST' })

    expect(fetchMock).toHaveBeenCalledTimes(4)
    const retryHeaders = new Headers(fetchMock.mock.calls[3]?.[1]?.headers)
    expect(retryHeaders.get('X-CSRF-Token')).toBe('new-token')
  })

  it('diferencia un fallo de red de credenciales inválidas', async () => {
    const fetchMock = createFetchMock()
    fetchMock.mockRejectedValue(new TypeError('Failed to fetch'))

    await expect(apiRequest({ path: '/auth/me' })).rejects.toMatchObject({
      code: 'NETWORK_ERROR',
      status: null,
    })
  })

  it('maneja respuestas vacías', async () => {
    const fetchMock = createFetchMock()
    fetchMock.mockResolvedValue(new Response(null, { status: 204 }))

    await expect(
      apiRequest<undefined>({ path: '/auth/me' }),
    ).resolves.toBeUndefined()
  })

  it('respeta Retry-After y reintenta una sola vez los GET con 429', async () => {
    const fetchMock = createFetchMock()
    fetchMock
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            success: false,
            error: {
              code: 'RATE_LIMIT_EXCEEDED',
              message: 'Espera antes de volver a intentarlo.',
            },
          }),
          {
            status: 429,
            headers: {
              'Content-Type': 'application/json',
              'Retry-After': '0',
            },
          },
        ),
      )
      .mockResolvedValueOnce(jsonResponse({ success: true }))

    await expect(apiRequest({ path: '/auth/me' })).resolves.toEqual({
      success: true,
    })
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })

  it('no repite automáticamente un POST limitado por tasa', async () => {
    const fetchMock = createFetchMock()
    fetchMock
      .mockResolvedValueOnce(jsonResponse({ csrf_token: 'rate-csrf' }))
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            success: false,
            error: {
              code: 'RATE_LIMIT_EXCEEDED',
              message: 'Espera antes de volver a intentarlo.',
            },
          }),
          {
            status: 429,
            headers: {
              'Content-Type': 'application/json',
              'Retry-After': '1',
            },
          },
        ),
      )

    await expect(
      apiRequest({ path: '/auth/logout', method: 'POST' }),
    ).rejects.toMatchObject({
      code: 'RATE_LIMIT_EXCEEDED',
      status: 429,
    })
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })

  it('no muestra HTML de errores del servidor', async () => {
    const fetchMock = createFetchMock()
    fetchMock.mockResolvedValue(
      new Response('<h1>Cloud error detail</h1>', {
        status: 500,
        headers: { 'Content-Type': 'text/html' },
      }),
    )

    await expect(apiRequest({ path: '/auth/me' })).rejects.toMatchObject({
      message: 'Ocurrió un error interno. Inténtalo más tarde.',
      code: 'HTTP_500',
    })
  })

  it('sanitiza mensajes internos aunque el backend devuelva JSON', async () => {
    const fetchMock = createFetchMock()
    fetchMock.mockResolvedValue(
      jsonResponse(
        {
          success: false,
          error: {
            code: 'INTERNAL_ERROR',
            message: 'Traceback /app/service.py database password=secret',
            details: { stack: 'internal stack' },
          },
        },
        500,
      ),
    )

    await expect(apiRequest({ path: '/auth/me' })).rejects.toMatchObject({
      message: 'Ocurrió un error interno. Inténtalo más tarde.',
      code: 'INTERNAL_ERROR',
      details: null,
    })
  })

  it('notifica una sesión expirada sin navegar desde HTTP', async () => {
    const fetchMock = createFetchMock()
    const listener = vi.fn()
    const unsubscribe = subscribeToUnauthorized(listener)
    fetchMock.mockResolvedValue(
      jsonResponse(
        {
          success: false,
          error: {
            code: 'SESSION_EXPIRED',
            message: 'Expired',
          },
        },
        401,
      ),
    )

    await expect(apiRequest({ path: '/auth/me' })).rejects.toBeInstanceOf(
      ApiRequestError,
    )
    expect(listener).toHaveBeenCalledOnce()
    unsubscribe()
  })

  it('usa VITE_API_URL como base completa sin duplicar /api', () => {
    expect(API_URL).toBeTruthy()
    expect(API_URL.endsWith('/api')).toBe(true)
    expect(API_URL.endsWith('/')).toBe(false)
    expect(API_ROOT).toBe(API_URL)
  })

  it('rechaza rutas que vuelven a incluir el prefijo /api', async () => {
    await expect(
      apiRequest({ path: '/api/shipments' }),
    ).rejects.toMatchObject({
      code: 'INVALID_API_PATH',
    })
  })

  it('mantiene el token CSRF fuera de localStorage', async () => {
    const storageSpy = vi.spyOn(Storage.prototype, 'setItem')
    const fetchMock = createFetchMock()
    fetchMock
      .mockResolvedValueOnce(jsonResponse({ csrf_token: 'memory-only' }))
      .mockResolvedValueOnce(jsonResponse({ success: true }))

    await apiRequest({ path: '/auth/logout', method: 'POST' })

    expect(storageSpy).not.toHaveBeenCalled()
  })

  it('renueva la sesión tras 401 y repite la solicitud una sola vez', async () => {
    const fetchMock = createFetchMock()
    fetchMock
      .mockResolvedValueOnce(
        jsonResponse(
          {
            success: false,
            error: { code: 'SESSION_EXPIRED', message: 'Expired' },
          },
          401,
        ),
      )
      .mockResolvedValueOnce(jsonResponse({ csrf_token: 'refresh-csrf' }))
      .mockResolvedValueOnce(jsonResponse({ success: true }))
      .mockResolvedValueOnce(jsonResponse({ sessions: [] }))

    await expect(
      apiRequest({ path: '/auth/sessions' }),
    ).resolves.toEqual({ sessions: [] })

    expect(fetchMock.mock.calls.map((call) => call[0])).toEqual([
      `${API_ROOT}/auth/sessions`,
      `${API_ROOT}/auth/csrf`,
      `${API_ROOT}/auth/refresh`,
      `${API_ROOT}/auth/sessions`,
    ])
    const refreshHeaders = new Headers(fetchMock.mock.calls[2]?.[1]?.headers)
    expect(refreshHeaders.get('X-CSRF-Token')).toBe('refresh-csrf')
  })

  it('comparte un único refresh entre solicitudes 401 simultáneas', async () => {
    const fetchMock = createFetchMock()
    const attempts = new Map<string, number>()

    fetchMock.mockImplementation(async (input) => {
      const url = String(input)

      if (url === `${API_ROOT}/auth/csrf`) {
        return jsonResponse({ csrf_token: 'shared-csrf' })
      }

      if (url === `${API_ROOT}/auth/refresh`) {
        return jsonResponse({ success: true })
      }

      const currentAttempt = (attempts.get(url) ?? 0) + 1
      attempts.set(url, currentAttempt)

      return currentAttempt === 1
        ? jsonResponse(
            {
              success: false,
              error: { code: 'SESSION_EXPIRED', message: 'Expired' },
            },
            401,
          )
        : jsonResponse({ success: true, url })
    })

    await Promise.all([
      apiRequest({ path: '/auth/me' }),
      apiRequest({ path: '/auth/sessions' }),
    ])

    const refreshCalls = fetchMock.mock.calls.filter(
      ([input]) => String(input) === `${API_ROOT}/auth/refresh`,
    )
    expect(refreshCalls).toHaveLength(1)
  })

  it('invalida la sesión cuando también falla el refresh', async () => {
    const fetchMock = createFetchMock()
    const listener = vi.fn()
    const unsubscribe = subscribeToUnauthorized(listener)
    fetchMock
      .mockResolvedValueOnce(
        jsonResponse(
          {
            success: false,
            error: { code: 'SESSION_EXPIRED', message: 'Expired' },
          },
          401,
        ),
      )
      .mockResolvedValueOnce(jsonResponse({ csrf_token: 'refresh-csrf' }))
      .mockResolvedValueOnce(
        jsonResponse(
          {
            success: false,
            error: {
              code: 'REFRESH_TOKEN_EXPIRED',
              message: 'Refresh expired',
            },
          },
          401,
        ),
      )

    await expect(
      apiRequest({ path: '/auth/me' }),
    ).rejects.toMatchObject({
      code: 'REFRESH_TOKEN_EXPIRED',
      message: 'Refresh expired',
    })
    expect(listener).toHaveBeenCalledOnce()
    expect(fetchMock).toHaveBeenCalledTimes(3)
    unsubscribe()
  })

  it('invalida la sesión si el refresh falla por red', async () => {
    const fetchMock = createFetchMock()
    const listener = vi.fn()
    const unsubscribe = subscribeToUnauthorized(listener)
    fetchMock
      .mockResolvedValueOnce(
        jsonResponse(
          {
            success: false,
            error: { code: 'SESSION_EXPIRED', message: 'Expired' },
          },
          401,
        ),
      )
      .mockResolvedValueOnce(jsonResponse({ csrf_token: 'refresh-csrf' }))
      .mockRejectedValueOnce(new TypeError('Failed to fetch'))

    await expect(
      apiRequest({ path: '/auth/me' }),
    ).rejects.toMatchObject({
      code: 'SESSION_REFRESH_FAILED',
      status: 401,
    })
    expect(listener).toHaveBeenCalledOnce()
    unsubscribe()
  })

  it('no intenta refresh para credenciales inválidas en login', async () => {
    const fetchMock = createFetchMock()
    fetchMock
      .mockResolvedValueOnce(jsonResponse({ csrf_token: 'login-csrf' }))
      .mockResolvedValueOnce(
        jsonResponse(
          {
            success: false,
            error: {
              code: 'INVALID_CREDENTIALS',
              message: 'Invalid',
            },
          },
          401,
        ),
      )

    await expect(
      apiRequest({ path: '/auth/login', method: 'POST' }),
    ).rejects.toMatchObject({ code: 'INVALID_CREDENTIALS' })
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })
})
