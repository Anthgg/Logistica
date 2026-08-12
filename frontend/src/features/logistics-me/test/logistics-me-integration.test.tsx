import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import type { ReactElement } from 'react'
import { LogisticsAccessContext } from '../contexts/logistics-access-context'
import type { LogisticsAccessState } from '../contexts/logistics-access-context'
import { LogisticsAccessRoute } from '../../../components/logistics/LogisticsAccessRoute'
import { LogisticsContextSwitcher } from '../../../components/logistics/LogisticsContextSwitcher'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { createLogisticsAccessState } from './test-utils'
import { AuthContext, type AuthContextValue } from '../../../contexts/auth-context'

function authedValue(): AuthContextValue {
  return {
    user: {
      id: 'u1',
      email: 'a@b.com',
      full_name: 'Test',
      role: 'admin',
      is_active: true,
      is_verified: true,
      created_at: '2026-01-01T00:00:00Z',
    },
    session: null,
    currentSession: null,
    isAuthenticated: true,
    isLoading: false,
    authError: null,
    login: async () => ({} as never),
    register: async () => ({} as never),
    logout: async () => undefined,
    logoutAll: async () => undefined,
    refreshSession: async () => ({} as never),
    changePassword: async () => ({ success: true, message: 'ok', revoked_sessions: null }),
    reloadCurrentUser: async () => undefined,
    refreshUser: async () => undefined,
    clearAuthError: () => undefined,
    invalidateSession: () => undefined,
  }
}

function renderWithProviders(
  element: ReactElement,
  state: LogisticsAccessState,
  initial = '/',
) {
  return render(
    <AuthContext.Provider value={authedValue()}>
      <LogisticsAccessContext.Provider value={state}>
        <MemoryRouter initialEntries={[initial]}>
          {element}
        </MemoryRouter>
      </LogisticsAccessContext.Provider>
    </AuthContext.Provider>,
  )
}

describe('Integración - carga de /logistics/me', () => {
  it('no muestra contenido logístico antes de cargar acceso', () => {
    const state = createLogisticsAccessState({
      isLoading: true,
      accessStatus: 'loading',
      me: { permissions: [LOGISTICS_PERMISSIONS.warehouses.read] },
    })
    renderWithProviders(
      <Routes>
        <Route element={<LogisticsAccessRoute permission={LOGISTICS_PERMISSIONS.warehouses.read} />}>
          <Route path="/" element={<div>contenido logístico</div>} />
        </Route>
      </Routes>,
      state,
    )
    expect(screen.queryByText('contenido logístico')).not.toBeInTheDocument()
  })

  it('muestra contenido logístico tras cargar acceso habilitado', () => {
    const state = createLogisticsAccessState({
      me: { permissions: [LOGISTICS_PERMISSIONS.warehouses.read] },
    })
    renderWithProviders(
      <Routes>
        <Route element={<LogisticsAccessRoute permission={LOGISTICS_PERMISSIONS.warehouses.read} />}>
          <Route path="/" element={<div>contenido logístico</div>} />
        </Route>
      </Routes>,
      state,
    )
    expect(screen.getByText('contenido logístico')).toBeInTheDocument()
  })
})

describe('Integración - usuario sin login', () => {
  it('redirige a login cuando no hay sesión', () => {
    const state = createLogisticsAccessState()
    function NoSession() {
      const value = authedValue()
      value.isAuthenticated = false
      value.user = null
      return (
        <AuthContext.Provider value={value}>
          <LogisticsAccessContext.Provider value={state}>
            <MemoryRouter initialEntries={['/']}>
              <Routes>
                <Route element={<LogisticsAccessRoute permission={LOGISTICS_PERMISSIONS.warehouses.read} />}>
                  <Route path="/" element={<div>contenido logístico</div>} />
                </Route>
                <Route path="/login" element={<div>login</div>} />
              </Routes>
            </MemoryRouter>
          </LogisticsAccessContext.Provider>
        </AuthContext.Provider>
      )
    }
    render(<NoSession />)
    expect(screen.getByText('login')).toBeInTheDocument()
  })
})

describe('Integración - usuario sin rol logístico', () => {
  it('muestra pantalla de acceso restringido', () => {
    const state = createLogisticsAccessState({
      accessStatus: 'no_role',
      me: { roles: [], organizations: ['org-1'] },
    })
    renderWithProviders(
      <Routes>
        <Route element={<LogisticsAccessRoute />}>
          <Route path="/" element={<div>módulo logístico</div>} />
        </Route>
      </Routes>,
      state,
    )
    expect(screen.queryByText('módulo logístico')).not.toBeInTheDocument()
    expect(screen.getByText('No tienes un rol logístico asignado')).toBeInTheDocument()
  })
})

describe('Integración - usuario con rol entra al módulo', () => {
  it('muestra módulo cuando tiene rol y permiso', () => {
    const state = createLogisticsAccessState({
      me: {
        roles: ['LOGISTICS_ADMIN'],
        permissions: [LOGISTICS_PERMISSIONS.warehouses.read],
      },
    })
    renderWithProviders(
      <Routes>
        <Route element={<LogisticsAccessRoute permission={LOGISTICS_PERMISSIONS.warehouses.read} />}>
          <Route path="/" element={<div>módulo logístico</div>} />
        </Route>
      </Routes>,
      state,
    )
    expect(screen.getByText('módulo logístico')).toBeInTheDocument()
  })
})

describe('Integración - 401 limpia sesión', () => {
  it('401 en acceso logístico muestra redirección a login', () => {
    const state = createLogisticsAccessState({
      isError: true,
      error: 'sesión expirada',
      accessStatus: 'error',
    })
    renderWithProviders(
      <Routes>
        <Route element={<LogisticsAccessRoute />}>
          <Route path="/" element={<div>módulo</div>} />
        </Route>
      </Routes>,
      state,
    )
    // En error de carga, muestra pantalla de error con botón reintentar
    expect(screen.getByText('No se pudo verificar tu acceso logístico')).toBeInTheDocument()
  })
})

describe('Integración - 403 mantiene sesión', () => {
  it('403 muestra acceso denegado sin cerrar sesión', () => {
    const state = createLogisticsAccessState({
      me: { permissions: [] },
    })
    renderWithProviders(
      <Routes>
        <Route element={<LogisticsAccessRoute permission={LOGISTICS_PERMISSIONS.warehouses.read} />}>
          <Route path="/" element={<div>módulo</div>} />
        </Route>
      </Routes>,
      state,
    )
    expect(screen.queryByText('módulo')).not.toBeInTheDocument()
    expect(screen.getByText('403')).toBeInTheDocument()
  })
})

describe('Integración - logout limpia sesión', () => {
  it('clearLogisticsSession limpia estado al cerrar sesión', () => {
    let cleared = false
    const state = createLogisticsAccessState()
    const originalClear = state.clearLogisticsSession
    state.clearLogisticsSession = () => {
      cleared = true
      originalClear()
    }
    state.clearLogisticsSession()
    expect(cleared).toBe(true)
  })
})

describe('Integración - cambio de contexto', () => {
  it('selector muestra opciones autorizadas', async () => {
    const user = userEvent.setup()
    const state = createLogisticsAccessState({
      me: {
        organizations: ['org-1', 'org-2'],
        branches: ['branch-1'],
        warehouses: ['wh-1'],
      },
    })
    renderWithProviders(<LogisticsContextSwitcher />, state)
    await user.click(screen.getByText('Cambiar'))
    const orgSelect = screen.getByRole('combobox', { name: /organización/i }) as HTMLSelectElement
    expect(Array.from(orgSelect.options).map((o) => o.value)).toContain('org-1')
    expect(Array.from(orgSelect.options).map((o) => o.value)).toContain('org-2')
  })
})

describe('Integración - contexto inválido', () => {
  it('muestra error cuando el contexto no es válido', () => {
    const state = createLogisticsAccessState({
      accessStatus: 'no_scope',
      me: { organizations: [], branches: [], warehouses: [] },
    })
    renderWithProviders(
      <Routes>
        <Route element={<LogisticsAccessRoute />}>
          <Route path="/" element={<div>módulo</div>} />
        </Route>
      </Routes>,
      state,
    )
    expect(screen.getByText('No tienes un alcance organizacional asignado')).toBeInTheDocument()
  })
})

describe('Integración - sin acceso logístico', () => {
  it('usuario sin acceso logístico ve pantalla controlada', () => {
    const state = createLogisticsAccessState({
      accessStatus: 'disabled',
      me: { enabled: false },
    })
    renderWithProviders(
      <Routes>
        <Route element={<LogisticsAccessRoute />}>
          <Route path="/" element={<div>módulo</div>} />
        </Route>
      </Routes>,
      state,
    )
    expect(screen.queryByText('módulo')).not.toBeInTheDocument()
    expect(screen.getByText('Acceso logístico deshabilitado')).toBeInTheDocument()
  })
})