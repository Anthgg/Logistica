import { describe, expect, it } from 'vitest'
import {
  adminRole,
  branchRole,
  createLogisticsAuthState,
} from '../test/test-utils'
import { useLogisticsPermissions } from '../hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../logistics-permissions-map'
import { renderHook, act } from '@testing-library/react'
import type { ReactNode } from 'react'
import { LogisticsAuthorizationContext } from '../contexts/logistics-authorization-context'
import { defaultLogisticsAuthorizationState } from '../contexts/logistics-authorization-context'

function wrapper(state: typeof defaultLogisticsAuthorizationState) {
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <LogisticsAuthorizationContext.Provider value={state}>
        {children}
      </LogisticsAuthorizationContext.Provider>
    )
  }
}

describe('useLogisticsPermissions - hasPermission', () => {
  it('concede acceso cuando el permiso está en la lista', () => {
    const state = createLogisticsAuthState({
      permissions: [LOGISTICS_PERMISSIONS.warehouses.read],
    })
    const { result } = renderHook(() => useLogisticsPermissions(), {
      wrapper: wrapper(state),
    })
    expect(result.current.hasPermission(LOGISTICS_PERMISSIONS.warehouses.read)).toBe(true)
  })

  it('deniega por defecto cuando el permiso no está', () => {
    const state = createLogisticsAuthState({ permissions: [] })
    const { result } = renderHook(() => useLogisticsPermissions(), {
      wrapper: wrapper(state),
    })
    expect(result.current.hasPermission(LOGISTICS_PERMISSIONS.warehouses.read)).toBe(false)
  })

  it('deniega mientras isLoading es true', () => {
    const state = createLogisticsAuthState({
      isLoading: true,
      permissions: [LOGISTICS_PERMISSIONS.warehouses.read],
    })
    const { result } = renderHook(() => useLogisticsPermissions(), {
      wrapper: wrapper(state),
    })
    expect(result.current.hasPermission(LOGISTICS_PERMISSIONS.warehouses.read)).toBe(false)
  })
})

describe('useLogisticsPermissions - hasAnyPermission / hasAllPermissions', () => {
  it('hasAnyPermission concede si al menos uno existe', () => {
    const state = createLogisticsAuthState({
      permissions: [LOGISTICS_PERMISSIONS.warehouses.read],
    })
    const { result } = renderHook(() => useLogisticsPermissions(), {
      wrapper: wrapper(state),
    })
    expect(
      result.current.hasAnyPermission([
        LOGISTICS_PERMISSIONS.warehouses.read,
        LOGISTICS_PERMISSIONS.warehouses.create,
      ]),
    ).toBe(true)
  })

  it('hasAllPermissions deniega si falta uno', () => {
    const state = createLogisticsAuthState({
      permissions: [LOGISTICS_PERMISSIONS.warehouses.read],
    })
    const { result } = renderHook(() => useLogisticsPermissions(), {
      wrapper: wrapper(state),
    })
    expect(
      result.current.hasAllPermissions([
        LOGISTICS_PERMISSIONS.warehouses.read,
        LOGISTICS_PERMISSIONS.warehouses.create,
      ]),
    ).toBe(false)
  })
})

describe('useLogisticsPermissions - permiso sensible y step-up', () => {
  it('identifica permisos sensibles', () => {
    const state = createLogisticsAuthState({
      sensitivePermissions: [LOGISTICS_PERMISSIONS.documents.cancel],
    })
    const { result } = renderHook(() => useLogisticsPermissions(), {
      wrapper: wrapper(state),
    })
    expect(result.current.isSensitivePermission(LOGISTICS_PERMISSIONS.documents.cancel)).toBe(true)
    expect(result.current.isSensitivePermission(LOGISTICS_PERMISSIONS.warehouses.read)).toBe(false)
  })

  it('identifica permisos que requieren step-up', () => {
    const state = createLogisticsAuthState({
      stepUpPermissions: [LOGISTICS_PERMISSIONS.roleAssignments.revoke],
    })
    const { result } = renderHook(() => useLogisticsPermissions(), {
      wrapper: wrapper(state),
    })
    expect(result.current.requiresStepUp(LOGISTICS_PERMISSIONS.roleAssignments.revoke)).toBe(true)
  })
})

describe('useLogisticsPermissions - alcance', () => {
  it('GLOBAL permite cualquier organización/sede/almacén', () => {
    const state = createLogisticsAuthState({ roles: [adminRole] })
    const { result } = renderHook(() => useLogisticsPermissions(), {
      wrapper: wrapper(state),
    })
    expect(result.current.canAccessOrganization('cualquier-org')).toBe(true)
    expect(result.current.canAccessBranch('cualquier-branch')).toBe(true)
    expect(result.current.canAccessWarehouse('cualquier-wh')).toBe(true)
  })

  it('BRANCH permite solo su organización/sede/almacén', () => {
    const state = createLogisticsAuthState({ roles: [branchRole] })
    const { result } = renderHook(() => useLogisticsPermissions(), {
      wrapper: wrapper(state),
    })
    expect(result.current.canAccessOrganization('org-1')).toBe(true)
    expect(result.current.canAccessOrganization('org-2')).toBe(false)
    expect(result.current.canAccessBranch('branch-1')).toBe(true)
    expect(result.current.canAccessBranch('branch-2')).toBe(false)
    expect(result.current.canAccessWarehouse('wh-1')).toBe(true)
    expect(result.current.canAccessWarehouse('wh-2')).toBe(false)
  })

  it('deniega alcance mientras isLoading', () => {
    const state = createLogisticsAuthState({
      isLoading: true,
      roles: [adminRole],
    })
    const { result } = renderHook(() => useLogisticsPermissions(), {
      wrapper: wrapper(state),
    })
    expect(result.current.canAccessScope({ organization_id: 'x', branch_id: null, warehouse_id: null })).toBe(false)
  })
})

describe('useLogisticsPermissions - error de carga', () => {
  it('expone isError y error', () => {
    const state = createLogisticsAuthState({
      isError: true,
      error: 'No se pudo cargar',
    })
    const { result } = renderHook(() => useLogisticsPermissions(), {
      wrapper: wrapper(state),
    })
    expect(result.current.isError).toBe(true)
    expect(result.current.error).toBe('No se pudo cargar')
  })
})

describe('useLogisticsPermissions - fuera del provider', () => {
  it('devuelve estado por defecto (denegación por defecto)', () => {
    const { result } = renderHook(() => useLogisticsPermissions())
    expect(result.current.isLoading).toBe(true)
    expect(result.current.hasPermission('logistics.warehouses.read')).toBe(false)
  })
})

describe('useLogisticsPermissions - refresh/setContext', () => {
  it('refreshPermissions y setContext son funciones invocables', async () => {
    const state = createLogisticsAuthState()
    const { result } = renderHook(() => useLogisticsPermissions(), {
      wrapper: wrapper(state),
    })
    await act(async () => {
      await result.current.refreshPermissions()
      await result.current.setContext({ organization_id: 'org-1' })
    })
    expect(result.current.context.organization_id).toBe('org-1')
  })
})