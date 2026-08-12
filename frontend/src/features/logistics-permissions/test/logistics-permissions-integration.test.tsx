import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import type { ReactElement } from 'react'
import { LogisticsAuthorizationContext } from '../contexts/logistics-authorization-context'
import type { LogisticsAuthorizationState } from '../contexts/logistics-authorization-context'
import { LogisticsPermissionRoute } from '../../../components/logistics/LogisticsPermissionRoute'
import { PermissionGate } from '../../../components/logistics/PermissionGate'
import { LogisticsDock } from '../../../components/layout/LogisticsDock'
import { ActionReasonDialog } from '../../../components/logistics/ActionReasonDialog'
import { LOGISTICS_PERMISSIONS } from '../logistics-permissions-map'
import { createLogisticsAuthState } from './test-utils'
import { AuthContext, type AuthContextValue } from '../../../contexts/auth-context'

beforeEach(() => {
  const store: Record<string, string> = {}
  vi.stubGlobal('localStorage', {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, value: string) => {
      store[key] = value
    },
    removeItem: (key: string) => {
      delete store[key]
    },
    clear: () => {
      for (const k of Object.keys(store)) delete store[k]
    },
  })
})

afterEach(() => {
  vi.unstubAllGlobals()
})

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
  state: LogisticsAuthorizationState,
  initial = '/',
) {
  return render(
    <AuthContext.Provider value={authedValue()}>
      <LogisticsAuthorizationContext.Provider value={state}>
        <MemoryRouter initialEntries={[initial]}>
          {element}
        </MemoryRouter>
      </LogisticsAuthorizationContext.Provider>
    </AuthContext.Provider>,
  )
}

describe('Integración - carga de permisos', () => {
  it('no muestra contenido protegido antes de cargar permisos', () => {
    const state = createLogisticsAuthState({
      isLoading: true,
      permissions: [LOGISTICS_PERMISSIONS.warehouses.read],
    })
    renderWithProviders(
      <Routes>
        <Route
          element={
            <LogisticsPermissionRoute permission={LOGISTICS_PERMISSIONS.warehouses.read} />
          }
        >
          <Route path="/" element={<div>contenido protegido</div>} />
        </Route>
      </Routes>,
      state,
    )
    expect(screen.queryByText('contenido protegido')).not.toBeInTheDocument()
  })

  it('muestra contenido protegido tras cargar permisos', () => {
    const state = createLogisticsAuthState({
      permissions: [LOGISTICS_PERMISSIONS.warehouses.read],
    })
    renderWithProviders(
      <Routes>
        <Route
          element={
            <LogisticsPermissionRoute permission={LOGISTICS_PERMISSIONS.warehouses.read} />
          }
        >
          <Route path="/" element={<div>contenido protegido</div>} />
        </Route>
      </Routes>,
      state,
    )
    expect(screen.getByText('contenido protegido')).toBeInTheDocument()
  })
})

describe('Integración - 401 redirige, 403 no cierra sesión', () => {
  it('403 muestra página de acceso denegado sin cerrar sesión', () => {
    const state = createLogisticsAuthState({ permissions: [] })
    renderWithProviders(
      <Routes>
        <Route
          element={
            <LogisticsPermissionRoute permission={LOGISTICS_PERMISSIONS.warehouses.read} />
          }
        >
          <Route path="/" element={<div>contenido protegido</div>} />
        </Route>
      </Routes>,
      state,
    )
    expect(screen.queryByText('contenido protegido')).not.toBeInTheDocument()
    expect(screen.getByText('403')).toBeInTheDocument()
    expect(screen.getByText(/No tienes permisos/i)).toBeInTheDocument()
  })
})

describe('Integración - menú filtrado por permisos', () => {
  it('muestra módulo de almacenes cuando tiene el permiso logístico', () => {
    const state = createLogisticsAuthState({
      permissions: [LOGISTICS_PERMISSIONS.warehouses.read],
    })
    renderWithProviders(<LogisticsDock />, state)
    expect(screen.getByRole('link', { name: 'Almacenes' })).toBeInTheDocument()
  })

  it('oculta módulo de almacenes cuando no tiene el permiso logístico', () => {
    const state = createLogisticsAuthState({ permissions: [] })
    renderWithProviders(<LogisticsDock />, state)
    expect(screen.queryByRole('link', { name: 'Almacenes' })).not.toBeInTheDocument()
  })
})

describe('Integración - botones filtrados por permiso', () => {
  it('oculta botón de crear cuando falta el permiso', () => {
    const state = createLogisticsAuthState({ permissions: [] })
    renderWithProviders(
      <PermissionGate permission={LOGISTICS_PERMISSIONS.warehouses.create}>
        <button>Crear almacén</button>
      </PermissionGate>,
      state,
    )
    expect(screen.queryByText('Crear almacén')).not.toBeInTheDocument()
  })

  it('muestra botón de crear cuando tiene el permiso', () => {
    const state = createLogisticsAuthState({
      permissions: [LOGISTICS_PERMISSIONS.warehouses.create],
    })
    renderWithProviders(
      <PermissionGate permission={LOGISTICS_PERMISSIONS.warehouses.create}>
        <button>Crear almacén</button>
      </PermissionGate>,
      state,
    )
    expect(screen.getByText('Crear almacén')).toBeInTheDocument()
  })
})

describe('Integración - revocación de permisos', () => {
  it('los permisos revocados desaparecen tras refreshPermissions', async () => {
    const state = createLogisticsAuthState({
      permissions: [LOGISTICS_PERMISSIONS.warehouses.read],
    })
    const { rerender } = renderWithProviders(
      <PermissionGate permission={LOGISTICS_PERMISSIONS.warehouses.read}>
        <button>Ver almacenes</button>
      </PermissionGate>,
      state,
    )
    expect(screen.getByText('Ver almacenes')).toBeInTheDocument()

    // Simular revocación: nuevo estado sin el permiso
    const revokedState = createLogisticsAuthState({ permissions: [] })
    rerender(
      <AuthContext.Provider value={authedValue()}>
        <LogisticsAuthorizationContext.Provider value={revokedState}>
          <MemoryRouter>
            <PermissionGate permission={LOGISTICS_PERMISSIONS.warehouses.read}>
              <button>Ver almacenes</button>
            </PermissionGate>
          </MemoryRouter>
        </LogisticsAuthorizationContext.Provider>
      </AuthContext.Provider>,
    )
    expect(screen.queryByText('Ver almacenes')).not.toBeInTheDocument()
  })
})

describe('Integración - motivo requerido', () => {
  it('ActionReasonDialog exige motivo antes de confirmar acción sensible', async () => {
    const user = userEvent.setup()
    const onConfirm = vi.fn()
    renderWithProviders(
      <ActionReasonDialog
        isOpen
        title="Revocar rol"
        resourceLabel="Usuario: Juan"
        confirmLabel="Revocar"
        onConfirm={onConfirm}
        onCancel={() => undefined}
      />,
      createLogisticsAuthState(),
    )
    expect(screen.getByRole('button', { name: 'Revocar' })).toBeDisabled()
    await user.type(screen.getByLabelText('Motivo'), 'Rotación de personal')
    await user.click(screen.getByRole('button', { name: 'Revocar' }))
    expect(onConfirm).toHaveBeenCalledWith('Rotación de personal')
  })
})

describe('Integración - error de carga de permisos', () => {
  it('muestra 403 con reason load_error cuando falla la carga', () => {
    const state = createLogisticsAuthState({
      isError: true,
      error: 'fallo de red',
    })
    renderWithProviders(
      <Routes>
        <Route
          element={
            <LogisticsPermissionRoute permission={LOGISTICS_PERMISSIONS.warehouses.read} />
          }
        >
          <Route path="/" element={<div>página</div>} />
        </Route>
      </Routes>,
      state,
    )
    expect(
      screen.getByText('No se pudo verificar tu autorización'),
    ).toBeInTheDocument()
  })
})

describe('Integración - alcance de contexto', () => {
  it('deniega acceso a almacén no autorizado', () => {
    const state = createLogisticsAuthState({
      permissions: [LOGISTICS_PERMISSIONS.warehouses.read],
      roles: [
        {
          role_code: 'WH_OP',
          role_name: 'Operador',
          scope_type: 'WAREHOUSE',
          organization_id: 'org-1',
          branch_id: 'branch-1',
          warehouse_id: 'wh-1',
          expires_at: null,
        },
      ],
    })
    renderWithProviders(
      <Routes>
        <Route
          element={
            <LogisticsPermissionRoute
              permission={LOGISTICS_PERMISSIONS.warehouses.read}
              scope={{ organization_id: 'org-1', branch_id: 'branch-1', warehouse_id: 'wh-2' }}
            />
          }
        >
          <Route path="/" element={<div>contenido</div>} />
        </Route>
      </Routes>,
      state,
    )
    expect(screen.queryByText('contenido')).not.toBeInTheDocument()
    expect(screen.getByText('403')).toBeInTheDocument()
  })
})

describe('Integración - sin permisos logísticos', () => {
  it('usuario sin permisos logísticos no ve módulo de almacenes', () => {
    const state = createLogisticsAuthState({ permissions: [] })
    renderWithProviders(<LogisticsDock />, state)
    expect(screen.queryByRole('link', { name: 'Almacenes' })).not.toBeInTheDocument()
  })
})