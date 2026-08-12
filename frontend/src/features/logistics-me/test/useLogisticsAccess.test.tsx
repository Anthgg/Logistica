import { describe, expect, it } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import type { ReactNode } from 'react'
import { useLogisticsAccess } from '../hooks/useLogisticsAccess'
import { LogisticsAccessContext } from '../contexts/logistics-access-context'
import { defaultLogisticsAccessState } from '../contexts/logistics-access-context'
import {
  createLogisticsAccessState,
  buildMockLogisticsMe,
} from './test-utils'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'

function wrapper(state: typeof defaultLogisticsAccessState) {
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <LogisticsAccessContext.Provider value={state}>
        {children}
      </LogisticsAccessContext.Provider>
    )
  }
}

describe('useLogisticsAccess - estado de acceso', () => {
  it('expone accessStatus enabled cuando hay rol y alcance', () => {
    const state = createLogisticsAccessState()
    const { result } = renderHook(() => useLogisticsAccess(), {
      wrapper: wrapper(state),
    })
    expect(result.current.accessStatus).toBe('enabled')
    expect(result.current.isLogisticsEnabled).toBe(true)
  })

  it('expone accessStatus disabled cuando enabled=false', () => {
    const state = createLogisticsAccessState({
      accessStatus: 'disabled',
      me: { enabled: false },
    })
    const { result } = renderHook(() => useLogisticsAccess(), {
      wrapper: wrapper(state),
    })
    expect(result.current.accessStatus).toBe('disabled')
    expect(result.current.isLogisticsEnabled).toBe(false)
  })

  it('expone accessStatus no_role cuando roles está vacío', () => {
    const state = createLogisticsAccessState({
      accessStatus: 'no_role',
      me: { roles: [], organizations: ['org-1'] },
    })
    const { result } = renderHook(() => useLogisticsAccess(), {
      wrapper: wrapper(state),
    })
    expect(result.current.accessStatus).toBe('no_role')
  })

  it('expone accessStatus no_scope cuando no hay organizations/branches/warehouses', () => {
    const state = createLogisticsAccessState({
      accessStatus: 'no_scope',
      me: { organizations: [], branches: [], warehouses: [] },
    })
    const { result } = renderHook(() => useLogisticsAccess(), {
      wrapper: wrapper(state),
    })
    expect(result.current.accessStatus).toBe('no_scope')
  })

  it('expone accessStatus loading mientras isLoading', () => {
    const state = createLogisticsAccessState({
      isLoading: true,
      accessStatus: 'loading',
    })
    const { result } = renderHook(() => useLogisticsAccess(), {
      wrapper: wrapper(state),
    })
    expect(result.current.accessStatus).toBe('loading')
  })

  it('expone accessStatus error cuando isError', () => {
    const state = createLogisticsAccessState({
      isError: true,
      error: 'fallo de red',
      accessStatus: 'error',
    })
    const { result } = renderHook(() => useLogisticsAccess(), {
      wrapper: wrapper(state),
    })
    expect(result.current.accessStatus).toBe('error')
    expect(result.current.isError).toBe(true)
    expect(result.current.error).toBe('fallo de red')
  })
})

describe('useLogisticsAccess - permisos', () => {
  it('hasPermission concede cuando tiene el permiso', () => {
    const state = createLogisticsAccessState({
      me: { permissions: [LOGISTICS_PERMISSIONS.warehouses.read] },
    })
    const { result } = renderHook(() => useLogisticsAccess(), {
      wrapper: wrapper(state),
    })
    expect(result.current.hasPermission(LOGISTICS_PERMISSIONS.warehouses.read)).toBe(true)
  })

  it('hasPermission deniega cuando no tiene el permiso', () => {
    const state = createLogisticsAccessState({ me: { permissions: [] } })
    const { result } = renderHook(() => useLogisticsAccess(), {
      wrapper: wrapper(state),
    })
    expect(result.current.hasPermission(LOGISTICS_PERMISSIONS.warehouses.read)).toBe(false)
  })

  it('hasPermission deniega cuando accessStatus no es enabled', () => {
    const state = createLogisticsAccessState({
      accessStatus: 'disabled',
      me: { permissions: [LOGISTICS_PERMISSIONS.warehouses.read] },
    })
    const { result } = renderHook(() => useLogisticsAccess(), {
      wrapper: wrapper(state),
    })
    expect(result.current.hasPermission(LOGISTICS_PERMISSIONS.warehouses.read)).toBe(false)
  })
})

describe('useLogisticsAccess - alcance', () => {
  it('canAccessOrganization concede para organización autorizada', () => {
    const state = createLogisticsAccessState({
      me: { organizations: ['org-1', 'org-2'] },
    })
    const { result } = renderHook(() => useLogisticsAccess(), {
      wrapper: wrapper(state),
    })
    expect(result.current.canAccessOrganization('org-1')).toBe(true)
    expect(result.current.canAccessOrganization('org-3')).toBe(false)
  })

  it('canAccessBranch concede para sede autorizada', () => {
    const state = createLogisticsAccessState({
      me: { branches: ['branch-1'] },
    })
    const { result } = renderHook(() => useLogisticsAccess(), {
      wrapper: wrapper(state),
    })
    expect(result.current.canAccessBranch('branch-1')).toBe(true)
    expect(result.current.canAccessBranch('branch-2')).toBe(false)
  })

  it('canAccessWarehouse concede para almacén autorizado', () => {
    const state = createLogisticsAccessState({
      me: { warehouses: ['wh-1'] },
    })
    const { result } = renderHook(() => useLogisticsAccess(), {
      wrapper: wrapper(state),
    })
    expect(result.current.canAccessWarehouse('wh-1')).toBe(true)
    expect(result.current.canAccessWarehouse('wh-2')).toBe(false)
  })
})

describe('useLogisticsAccess - contexto', () => {
  it('expone currentContext con valores predeterminados', () => {
    const state = createLogisticsAccessState({
      me: {
        defaultOrganizationId: 'org-default',
        defaultBranchId: 'branch-default',
        defaultWarehouseId: 'wh-default',
      },
    })
    const { result } = renderHook(() => useLogisticsAccess(), {
      wrapper: wrapper(state),
    })
    expect(result.current.currentContext.organization_id).toBe('org-default')
    expect(result.current.currentContext.branch_id).toBe('branch-default')
    expect(result.current.currentContext.warehouse_id).toBe('wh-default')
  })

  it('changeContext es invocable', async () => {
    const state = createLogisticsAccessState()
    const { result } = renderHook(() => useLogisticsAccess(), {
      wrapper: wrapper(state),
    })
    await act(async () => {
      const success = await result.current.changeContext({
        organization_id: 'org-1',
        branch_id: 'branch-1',
        warehouse_id: 'wh-1',
      })
      expect(success).toBe(true)
    })
  })

  it('clearLogisticsSession es invocable', () => {
    const state = createLogisticsAccessState()
    const { result } = renderHook(() => useLogisticsAccess(), {
      wrapper: wrapper(state),
    })
    act(() => {
      result.current.clearLogisticsSession()
    })
  })
})

describe('useLogisticsAccess - fuera del provider', () => {
  it('devuelve estado por defecto (denegación por defecto)', () => {
    const { result } = renderHook(() => useLogisticsAccess())
    expect(result.current.isLoading).toBe(true)
    expect(result.current.isLogisticsEnabled).toBe(false)
    expect(result.current.hasPermission('logistics.warehouses.read')).toBe(false)
  })
})

describe('useLogisticsAccess - usuario y sesión logística', () => {
  it('expone logisticsUser cuando está habilitado', () => {
    const state = createLogisticsAccessState({
      me: { displayName: 'Ana García', platformRole: 'admin' },
    })
    const { result } = renderHook(() => useLogisticsAccess(), {
      wrapper: wrapper(state),
    })
    expect(result.current.logisticsUser?.display_name).toBe('Ana García')
    expect(result.current.logisticsUser?.platform_role).toBe('admin')
  })

  it('expone session con authentication_level', () => {
    const state = createLogisticsAccessState()
    const { result } = renderHook(() => useLogisticsAccess(), {
      wrapper: wrapper(state),
    })
    expect(result.current.session?.authentication_level).toBe('traditional')
  })
})

describe('useLogisticsAccess - mock builder', () => {
  it('buildMockLogisticsMe construye respuesta válida', () => {
    const mock = buildMockLogisticsMe({
      enabled: true,
      roles: ['LOGISTICS_OPERATOR'],
      permissions: ['logistics.warehouses.read'],
      organizations: ['org-1'],
    })
    expect(mock.success).toBe(true)
    expect(mock.logistics.enabled).toBe(true)
    expect(mock.logistics.roles).toContain('LOGISTICS_OPERATOR')
    expect(mock.logistics.permissions).toContain('logistics.warehouses.read')
  })
})