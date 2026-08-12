import { beforeEach, describe, expect, it, vi } from 'vitest'
import {
  getCurrentUser,
  login,
  logout,
  refreshSession,
  register,
} from './auth-api'
import { revokeSession } from './session-api'
import { API_ROOT } from './config'
import { clearCsrfToken } from './csrf'
import { testAuthResponse } from '../test/test-utils'

function jsonResponse(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

describe('servicios de autenticación', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    clearCsrfToken()
  })

  it('registro solicita CSRF y usa el endpoint oficial', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ csrf_token: 'register-csrf' }))
      .mockResolvedValueOnce(jsonResponse(testAuthResponse))
    vi.stubGlobal('fetch', fetchMock)

    await register({
      full_name: 'Usuario de Prueba',
      email: 'usuario@example.com',
      password: 'ClaveSegura2026',
      password_confirmation: 'ClaveSegura2026',
      accept_terms: true,
    })

    expect(fetchMock.mock.calls[0]?.[0]).toBe(`${API_ROOT}/auth/csrf`)
    expect(fetchMock.mock.calls[1]?.[0]).toBe(`${API_ROOT}/auth/register`)
    const init = fetchMock.mock.calls[1]?.[1] as RequestInit
    expect(new Headers(init.headers).get('X-CSRF-Token')).toBe('register-csrf')
    expect(init.credentials).toBe('include')
  })

  it('login envía el contrato requerido', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ csrf_token: 'login-csrf' }))
      .mockResolvedValueOnce(jsonResponse(testAuthResponse))
    vi.stubGlobal('fetch', fetchMock)

    await expect(login({
      email: 'usuario@example.com',
      password: 'ClaveSegura2026',
      remember_me: false,
    })).resolves.toEqual(testAuthResponse)

    const init = fetchMock.mock.calls[1]?.[1] as RequestInit
    expect(JSON.parse(String(init.body))).toEqual({
      email: 'usuario@example.com',
      password: 'ClaveSegura2026',
      remember_me: false,
    })
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })

  it('/auth/me no solicita CSRF', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(testAuthResponse))
    vi.stubGlobal('fetch', fetchMock)

    await getCurrentUser()

    expect(fetchMock).toHaveBeenCalledOnce()
    expect(fetchMock.mock.calls[0]?.[0]).toBe(`${API_ROOT}/auth/me`)
  })

  it('refresh solicita CSRF y devuelve usuario y sesión públicos', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ csrf_token: 'refresh-csrf' }))
      .mockResolvedValueOnce(jsonResponse(testAuthResponse))
    vi.stubGlobal('fetch', fetchMock)

    await expect(refreshSession()).resolves.toEqual(testAuthResponse)

    expect(fetchMock.mock.calls[1]?.[0]).toBe(`${API_ROOT}/auth/refresh`)
    expect(fetchMock.mock.calls[1]?.[1]).toEqual(
      expect.objectContaining({ method: 'POST', credentials: 'include' }),
    )
  })

  it('logout solicita CSRF antes de revocar la sesión', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ csrf_token: 'logout-csrf' }))
      .mockResolvedValueOnce(
        jsonResponse({
          success: true,
          message: 'Sesión cerrada',
          revoked_sessions: 1,
        }),
      )
    vi.stubGlobal('fetch', fetchMock)

    await logout()

    expect(fetchMock.mock.calls[1]?.[0]).toBe(`${API_ROOT}/auth/logout`)
    expect(fetchMock.mock.calls[1]?.[1]).toEqual(
      expect.objectContaining({ method: 'POST', credentials: 'include' }),
    )
  })

  it('la revocación usa DELETE, CSRF y solo el id recibido', async () => {
    const sessionId = 'f7e105bb-23f8-4a31-9618-c0e96b286739'
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ csrf_token: 'delete-csrf' }))
      .mockResolvedValueOnce(
        jsonResponse({
          success: true,
          message: 'Sesión revocada',
          revoked_sessions: 1,
        }),
      )
    vi.stubGlobal('fetch', fetchMock)

    await revokeSession(sessionId)

    expect(fetchMock.mock.calls[1]?.[0]).toBe(
      `${API_ROOT}/auth/sessions/${sessionId}`,
    )
    expect(fetchMock.mock.calls[1]?.[1]).toEqual(
      expect.objectContaining({ method: 'DELETE', credentials: 'include' }),
    )
    expect(
      new Headers(fetchMock.mock.calls[1]?.[1]?.headers).get('X-CSRF-Token'),
    ).toBe('delete-csrf')
  })
})
