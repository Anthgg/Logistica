import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import App from '../App'
import { API_ROOT } from '../api/config'

const testUser = {
  id: 'user-1',
  email: 'test@example.com',
  full_name: 'Usuario de Prueba',
  role: 'admin',
  is_active: true,
  is_verified: true,
  created_at: '2026-01-01T00:00:00Z',
}

const testSession = {
  id: 'session-1',
  authentication_level: 'traditional',
  created_at: '2026-07-25T00:00:00Z',
  last_activity_at: '2026-07-25T00:00:00Z',
  expires_at: '2026-08-25T00:00:00Z',
  device_id: null,
}

const testCatalog = {
  locale: 'es',
  supported_locales: ['es', 'en', 'pt'],
  translations: {
    common: { cancel: 'Cancelar' },
    status: { pending_pickup: 'Pendiente de recojo' },
    priority: { normal: 'Normal' },
    event: { shipment_created: 'Envío creado' },
    resource: { shipment: 'Envío' },
    risk: { low: 'Bajo' },
    auth_level: { traditional: 'Tradicional' },
    continuous_auth_status: { active: 'Activo' },
    action: { allow: 'Permitir' },
  },
}

function jsonResponse(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

function createFetchMock(handlers: Record<string, () => Promise<Response>>) {
  return vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input)
    if (url === `${API_ROOT}/health`) {
      return jsonResponse({ status: 'ok', database: 'ok' })
    }
    const handler = handlers[url]
    if (handler) {
      return handler()
    }
    return jsonResponse({})
  })
}

function mockMissingSession() {
  const fetchMock = createFetchMock({
    [`${API_ROOT}/auth/csrf`]: async () => jsonResponse({ csrf_token: 'bootstrap-csrf' }),
    [`${API_ROOT}/i18n/catalog`]: async () => jsonResponse(testCatalog),
    [`${API_ROOT}/auth/me`]: async () => jsonResponse({ detail: 'Sin sesión' }, 401),
    [`${API_ROOT}/auth/refresh`]: async () => jsonResponse({ detail: 'Sin refresh' }, 401),
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

function mockAuthenticated() {
  const fetchMock = createFetchMock({
    [`${API_ROOT}/health`]: async () => jsonResponse({ status: 'ok', database: 'ok' }),
    [`${API_ROOT}/auth/csrf`]: async () => jsonResponse({ csrf_token: 'bootstrap-csrf' }),
    [`${API_ROOT}/i18n/catalog`]: async () => jsonResponse(testCatalog),
    [`${API_ROOT}/auth/me`]: async () => jsonResponse({ success: true, message: 'ok', user: testUser, session: testSession }),
    [`${API_ROOT}/auth/sessions`]: async () => jsonResponse({ items: [testSession] }),
    [`${API_ROOT}/logistics/me/permissions`]: async () =>
      jsonResponse({
        success: true,
        catalog_version: '2026.07.26',
        user_id: 'user-1',
        permissions: [],
        sensitive_permissions: [],
        step_up_permissions: [],
        roles: [],
      }),
    [`${API_ROOT}/logistics/me`]: async () =>
      jsonResponse({
        success: true,
        user: {
          id: 'user-1',
          display_name: 'Usuario de Prueba',
          email: 'test@example.com',
          platform_role: 'admin',
          is_active: true,
        },
        session: {
          id: 'session-1',
          device_id: null,
          expires_at: '2026-08-25T00:00:00Z',
          authentication_level: 'traditional',
          risk_score: null,
        },
        logistics: {
          enabled: false,
          roles: [],
          permissions: [],
          sensitive_permissions: [],
          step_up_permissions: [],
          organizations: [],
          branches: [],
          warehouses: [],
          default_organization_id: null,
          default_branch_id: null,
          default_warehouse_id: null,
        },
      }),
    [`${API_ROOT}/continuous-auth/status`]: async () =>
      jsonResponse({
        risk_level: 'low',
        authentication_level: 'traditional',
        recommended_action: 'allow',
        applied_action: 'allow',
        components: [],
        score: 0.95,
        updated_at: new Date().toISOString(),
      }),
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

describe('AppRouter y restauración de sesión', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    window.history.replaceState({}, '', '/profile')
  })

  it('inicializa health, CSRF, catálogo y sesión en ese orden', async () => {
    const fetchMock = mockMissingSession()
    render(<App />)

    await screen.findByRole('heading', { name: 'Inicia sesión' })
    expect(fetchMock.mock.calls.slice(0, 4).map((call) => call[0])).toEqual([
      `${API_ROOT}/health`,
      `${API_ROOT}/auth/csrf`,
      `${API_ROOT}/i18n/catalog`,
      `${API_ROOT}/auth/me`,
    ])
  })

  it('permite al usuario autenticado acceder al perfil', async () => {
    mockAuthenticated()
    render(<App />)

    expect(
      await screen.findByRole('heading', { name: 'Hola, Usuario' }, { timeout: 3000 }),
    ).toBeInTheDocument()
  })

  it('redirige una ruta privada a login sin sesión', async () => {
    mockMissingSession()
    render(<App />)

    expect(
      await screen.findByRole('heading', { name: 'Inicia sesión' }),
    ).toBeInTheDocument()
    expect(window.location.pathname).toBe('/login')
  })
})
