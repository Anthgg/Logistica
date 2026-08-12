import type { ReactElement, ReactNode } from 'react'
import { render } from '@testing-library/react'
import { MemoryRouter, type InitialEntry } from 'react-router-dom'
import {
  LogisticsAuthorizationContext,
  type LogisticsAuthorizationState,
} from '../contexts/logistics-authorization-context'
import type { LogisticsRoleScope } from '../../../types/logistics-permissions'

export const adminRole: LogisticsRoleScope = {
  role_code: 'LOGISTICS_ADMIN',
  role_name: 'Administrador logístico global',
  scope_type: 'GLOBAL',
  organization_id: null,
  branch_id: null,
  warehouse_id: null,
  expires_at: null,
}

export const branchRole: LogisticsRoleScope = {
  role_code: 'WAREHOUSE_MANAGER',
  role_name: 'Responsable de sede',
  scope_type: 'BRANCH',
  organization_id: 'org-1',
  branch_id: 'branch-1',
  warehouse_id: 'wh-1',
  expires_at: null,
}

export interface CreateAuthStateOptions {
  isLoading?: boolean
  isError?: boolean
  error?: string | null
  permissions?: string[]
  sensitivePermissions?: string[]
  stepUpPermissions?: string[]
  roles?: LogisticsRoleScope[]
  organizationId?: string | null
  branchId?: string | null
  warehouseId?: string | null
}


export function createLogisticsAuthState(
  options: CreateAuthStateOptions = {},
): LogisticsAuthorizationState {
  const permissions = new Set(options.permissions ?? [])
  const sensitive = new Set(options.sensitivePermissions ?? [])
  const stepUp = new Set(options.stepUpPermissions ?? [])
  const roles = options.roles ?? []
  const hasGlobal = roles.some((role) => role.scope_type === 'GLOBAL')
  const isLoading = options.isLoading ?? false

  const base = {
    hasPermission: (code: string) =>
      !isLoading && permissions.has(code),
    hasAnyPermission: (codes: readonly string[]) =>
      !isLoading && codes.some((code) => permissions.has(code)),
    hasAllPermissions: (codes: readonly string[]) =>
      !isLoading && codes.every((code) => permissions.has(code)),
  }

  let contextSnapshot: LogisticsAuthorizationState['context'] = {
    organization_id: options.organizationId ?? null,
    branch_id: options.branchId ?? null,
    warehouse_id: options.warehouseId ?? null,
  }

  const state: LogisticsAuthorizationState = {
    isLoading,
    isError: options.isError ?? false,
    error: options.error ?? null,
    catalogVersion: '2026.07.26',
    userId: 'user-1',
    roles,
    permissions,
    sensitivePermissions: sensitive,
    stepUpPermissions: stepUp,
    context: contextSnapshot,
    lastUpdatedAt: '2026-07-26T10:00:00Z',
    hasPermission: base.hasPermission,
    hasAnyPermission: base.hasAnyPermission,
    hasAllPermissions: base.hasAllPermissions,
    isSensitivePermission: (code: string) => sensitive.has(code),
    requiresStepUp: (code: string) => stepUp.has(code),
    canAccessOrganization: (id: string) =>
      !isLoading && (hasGlobal || roles.some((role) => role.organization_id === id)),
    canAccessBranch: (id: string) =>
      !isLoading && (hasGlobal || roles.some((role) => role.branch_id === id)),
    canAccessWarehouse: (id: string) =>
      !isLoading && (hasGlobal || roles.some((role) => role.warehouse_id === id)),
    canAccessScope: (scope) =>
      !isLoading &&
      (hasGlobal ||
        roles.some((role) => {
          if (scope.organization_id && role.organization_id !== scope.organization_id)
            return false
          if (scope.branch_id && role.branch_id !== scope.branch_id) return false
          if (scope.warehouse_id && role.warehouse_id !== scope.warehouse_id)
            return false
          return true
        })),
    refreshPermissions: async () => undefined,
    setContext: async (next) => {
      contextSnapshot = { ...contextSnapshot, ...next }
      state.context = contextSnapshot
    },
    resetContext: () => {
      contextSnapshot = { organization_id: null, branch_id: null, warehouse_id: null }
      state.context = contextSnapshot
    },
  }

  return state
}

export function renderWithLogisticsAuth(
  element: ReactElement,
  state: LogisticsAuthorizationState,
  initialEntries: InitialEntry[] = ['/'],
): ReturnType<typeof render> {
  function Wrapper({ children }: { children: ReactNode }) {
    return (
      <MemoryRouter initialEntries={initialEntries}>
        <LogisticsAuthorizationContext.Provider value={state}>
          {children}
        </LogisticsAuthorizationContext.Provider>
      </MemoryRouter>
    )
  }

  return render(element, { wrapper: Wrapper })
}