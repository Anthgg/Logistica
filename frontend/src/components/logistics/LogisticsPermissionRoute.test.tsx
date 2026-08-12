import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import {
  adminRole,
  createLogisticsAuthState,
} from '../../features/logistics-permissions/test/test-utils'
import { LogisticsAuthorizationContext } from '../../features/logistics-permissions/contexts/logistics-authorization-context'
import { LogisticsPermissionRoute } from './LogisticsPermissionRoute'
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
  auth: ReturnType<typeof createLogisticsAuthState>,
  initial = '/warehouses',
) {
  function Child() {
    return <div>página protegida</div>
  }
  render(
    <AuthContext.Provider value={authedValue()}>
      <LogisticsAuthorizationContext.Provider value={auth}>
        <MemoryRouter initialEntries={[initial]}>
          <Routes>
            <Route
              element={
                <LogisticsPermissionRoute permission={LOGISTICS_PERMISSIONS.warehouses.read} />
              }
            >
              <Route path="/warehouses" element={<Child />} />
            </Route>
            <Route path="/login" element={<div>login</div>} />
            <Route path="/unauthorized" element={<div>unauthorized</div>} />
            <Route path="/forbidden" element={<div>forbidden</div>} />
          </Routes>
        </MemoryRouter>
      </LogisticsAuthorizationContext.Provider>
    </AuthContext.Provider>,
  )
}

describe('LogisticsPermissionRoute - autorizada', () => {
  it('renderiza la página cuando tiene el permiso', () => {
    const auth = createLogisticsAuthState({
      permissions: [LOGISTICS_PERMISSIONS.warehouses.read],
    })
    renderRoute(auth)
    expect(screen.getByText('página protegida')).toBeInTheDocument()
  })
})

describe('LogisticsPermissionRoute - denegada', () => {
  it('muestra 403 cuando no tiene el permiso', () => {
    const auth = createLogisticsAuthState({ permissions: [] })
    renderRoute(auth)
    expect(screen.queryByText('página protegida')).not.toBeInTheDocument()
    expect(screen.getByText('403')).toBeInTheDocument()
  })

  it('muestra 403 cuando el scope no coincide', () => {
    const auth = createLogisticsAuthState({
      permissions: [LOGISTICS_PERMISSIONS.warehouses.read],
      organizationId: 'org-otra',
    })
    render(
      <AuthContext.Provider value={authedValue()}>
        <LogisticsAuthorizationContext.Provider value={auth}>
          <MemoryRouter initialEntries={['/warehouses']}>
            <Routes>
              <Route
                element={
                  <LogisticsPermissionRoute
                    permission={LOGISTICS_PERMISSIONS.warehouses.read}
                    scope={{ organization_id: 'org-1', branch_id: null, warehouse_id: null }}
                  />
                }
              >
                <Route path="/warehouses" element={<div>página protegida</div>} />
              </Route>
            </Routes>
          </MemoryRouter>
        </LogisticsAuthorizationContext.Provider>
      </AuthContext.Provider>,
    )
    expect(screen.queryByText('página protegida')).not.toBeInTheDocument()
    expect(screen.getByText('403')).toBeInTheDocument()
  })
})

describe('LogisticsPermissionRoute - loading', () => {
  it('no muestra la página protegida mientras carga permisos', () => {
    const auth = createLogisticsAuthState({
      isLoading: true,
      permissions: [LOGISTICS_PERMISSIONS.warehouses.read],
    })
    renderRoute(auth)
    expect(screen.queryByText('página protegida')).not.toBeInTheDocument()
  })
})

describe('LogisticsPermissionRoute - error de carga', () => {
  it('muestra 403 con reason load_error', () => {
    const auth = createLogisticsAuthState({
      isError: true,
      error: 'fallo de red',
    })
    renderRoute(auth)
    expect(screen.getByText('No se pudo verificar tu autorización')).toBeInTheDocument()
  })
})

describe('LogisticsPermissionRoute - sesión ausente', () => {
  it('redirige a login cuando no hay sesión', () => {
    const auth = createLogisticsAuthState({
      permissions: [LOGISTICS_PERMISSIONS.warehouses.read],
      roles: [adminRole],
    })
    function NoSession() {
      const value = authedValue()
      value.isAuthenticated = false
      value.user = null
      return (
        <AuthContext.Provider value={value}>
          <LogisticsAuthorizationContext.Provider value={auth}>
            <MemoryRouter initialEntries={['/warehouses']}>
              <Routes>
                <Route
                  element={
                    <LogisticsPermissionRoute permission={LOGISTICS_PERMISSIONS.warehouses.read} />
                  }
                >
                  <Route path="/warehouses" element={<div>página protegida</div>} />
                </Route>
                <Route path="/login" element={<div>login page</div>} />
              </Routes>
            </MemoryRouter>
          </LogisticsAuthorizationContext.Provider>
        </AuthContext.Provider>
      )
    }
    render(<NoSession />)
    expect(screen.getByText('login page')).toBeInTheDocument()
  })
})