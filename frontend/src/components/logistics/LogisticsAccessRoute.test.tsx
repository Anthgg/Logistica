import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { LogisticsAccessRoute } from './LogisticsAccessRoute'
import {
  createLogisticsAccessState,
} from '../../features/logistics-me/test/test-utils'
import { LogisticsAccessContext } from '../../features/logistics-me/contexts/logistics-access-context'
import { AuthContext, type AuthContextValue } from '../../contexts/auth-context'
import { LOGISTICS_PERMISSIONS } from '../../features/logistics-permissions/logistics-permissions-map'

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

function renderRoute(
  access: ReturnType<typeof createLogisticsAccessState>,
  initial = '/logistics/warehouses',
  permission?: string,
) {
  function Child() {
    return <div>página logística</div>
  }
  render(
    <AuthContext.Provider value={authedValue()}>
      <LogisticsAccessContext.Provider value={access}>
        <MemoryRouter initialEntries={[initial]}>
          <Routes>
            <Route
              element={
                <LogisticsAccessRoute
                  permission={permission ?? LOGISTICS_PERMISSIONS.warehouses.read}
                />
              }
            >
              <Route path="/logistics/warehouses" element={<Child />} />
            </Route>
            <Route path="/login" element={<div>login</div>} />
            <Route path="/logistics/unavailable" element={<div>unavailable</div>} />
          </Routes>
        </MemoryRouter>
      </LogisticsAccessContext.Provider>
    </AuthContext.Provider>,
  )
}

describe('LogisticsAccessRoute - autorizada', () => {
  it('renderiza la página cuando acceso habilitado y tiene permiso', () => {
    const access = createLogisticsAccessState({
      me: { permissions: [LOGISTICS_PERMISSIONS.warehouses.read] },
    })
    renderRoute(access)
    expect(screen.getByText('página logística')).toBeInTheDocument()
  })
})

describe('LogisticsAccessRoute - denegada', () => {
  it('muestra pantalla sin acceso cuando no tiene permiso', () => {
    const access = createLogisticsAccessState({
      me: { permissions: [] },
    })
    renderRoute(access)
    expect(screen.queryByText('página logística')).not.toBeInTheDocument()
    expect(screen.getByText('403')).toBeInTheDocument()
  })

  it('muestra pantalla sin acceso cuando acceso disabled', () => {
    const access = createLogisticsAccessState({
      accessStatus: 'disabled',
      me: { enabled: false },
    })
    renderRoute(access)
    expect(screen.getByText('Acceso logístico deshabilitado')).toBeInTheDocument()
  })

  it('muestra pantalla sin rol cuando no hay roles', () => {
    const access = createLogisticsAccessState({
      accessStatus: 'no_role',
      me: { roles: [], organizations: ['org-1'] },
    })
    renderRoute(access)
    expect(screen.getByText('No tienes un rol logístico asignado')).toBeInTheDocument()
  })

  it('muestra pantalla sin alcance cuando no hay organizaciones', () => {
    const access = createLogisticsAccessState({
      accessStatus: 'no_scope',
      me: { organizations: [], branches: [], warehouses: [] },
    })
    renderRoute(access)
    expect(screen.getByText('No tienes un alcance organizacional asignado')).toBeInTheDocument()
  })

  it('muestra pantalla de error cuando isError', () => {
    const access = createLogisticsAccessState({
      isError: true,
      error: 'fallo',
      accessStatus: 'error',
    })
    renderRoute(access)
    expect(screen.getByText('No se pudo verificar tu acceso logístico')).toBeInTheDocument()
  })

  it('distingue un timeout de una denegación de acceso', () => {
    const access = createLogisticsAccessState({
      isError: true,
      error: 'El servidor tardó demasiado en responder',
      errorCode: 'TIMEOUT',
      accessStatus: 'error',
    })
    renderRoute(access)
    expect(screen.getByText('504')).toBeInTheDocument()
    expect(
      screen.getByText('El servicio logístico tardó demasiado en responder'),
    ).toBeInTheDocument()
    expect(screen.queryByText('403')).not.toBeInTheDocument()
  })

  it('muestra scope denegado cuando el contexto no cubre la organización', () => {
    const access = createLogisticsAccessState({
      me: {
        permissions: [LOGISTICS_PERMISSIONS.warehouses.read],
        organizations: ['org-1'],
      },
    })
    render(
      <AuthContext.Provider value={authedValue()}>
        <LogisticsAccessContext.Provider value={access}>
          <MemoryRouter initialEntries={['/logistics/warehouses']}>
            <Routes>
              <Route
                element={
                  <LogisticsAccessRoute
                    permission={LOGISTICS_PERMISSIONS.warehouses.read}
                    scope={{ organization_id: 'org-2', branch_id: null, warehouse_id: null }}
                  />
                }
              >
                <Route path="/logistics/warehouses" element={<div>página logística</div>} />
              </Route>
            </Routes>
          </MemoryRouter>
        </LogisticsAccessContext.Provider>
      </AuthContext.Provider>,
    )
    expect(screen.queryByText('página logística')).not.toBeInTheDocument()
  })
})

describe('LogisticsAccessRoute - loading', () => {
  it('no muestra la página mientras carga', () => {
    const access = createLogisticsAccessState({
      isLoading: true,
      accessStatus: 'loading',
      me: { permissions: [LOGISTICS_PERMISSIONS.warehouses.read] },
    })
    renderRoute(access)
    expect(screen.queryByText('página logística')).not.toBeInTheDocument()
  })
})

describe('LogisticsAccessRoute - sesión ausente', () => {
  it('redirige a login cuando no hay sesión', () => {
    const access = createLogisticsAccessState({
      me: { permissions: [LOGISTICS_PERMISSIONS.warehouses.read] },
    })
    function NoSession() {
      const value = authedValue()
      value.isAuthenticated = false
      value.user = null
      return (
        <AuthContext.Provider value={value}>
          <LogisticsAccessContext.Provider value={access}>
            <MemoryRouter initialEntries={['/logistics/warehouses']}>
              <Routes>
                <Route
                  element={
                    <LogisticsAccessRoute
                      permission={LOGISTICS_PERMISSIONS.warehouses.read}
                    />
                  }
                >
                  <Route path="/logistics/warehouses" element={<div>página</div>} />
                </Route>
                <Route path="/login" element={<div>login page</div>} />
              </Routes>
            </MemoryRouter>
          </LogisticsAccessContext.Provider>
        </AuthContext.Provider>
      )
    }
    render(<NoSession />)
    expect(screen.getByText('login page')).toBeInTheDocument()
  })
})
