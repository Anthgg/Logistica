import type { ReactElement, ReactNode } from 'react'
import { render } from '@testing-library/react'
import { MemoryRouter, type InitialEntry } from 'react-router-dom'
import {
  LogisticsAccessContext,
  type LogisticsAccessState,
} from '../contexts/logistics-access-context'
import type {
  LogisticsMeResponse,
  LogisticsContextChangeRequest,
} from '../../../types/logistics-me'

export interface MockLogisticsMeOptions {
  enabled?: boolean
  roles?: string[]
  permissions?: string[]
  sensitivePermissions?: string[]
  stepUpPermissions?: string[]
  organizations?: string[]
  branches?: string[]
  warehouses?: string[]
  defaultOrganizationId?: string | null
  defaultBranchId?: string | null
  defaultWarehouseId?: string | null
  userId?: string
  displayName?: string
  email?: string
  platformRole?: string
  isActive?: boolean
}

export function buildMockLogisticsMe(
  options: MockLogisticsMeOptions = {},
): LogisticsMeResponse {
  return {
    success: true,
    user: {
      id: options.userId ?? 'user-1',
      display_name: options.displayName ?? 'Usuario de Prueba',
      email: options.email ?? 'test@example.com',
      platform_role: options.platformRole ?? 'admin',
      is_active: options.isActive ?? true,
    },
    session: {
      id: 'session-1',
      device_id: null,
      expires_at: '2026-08-25T00:00:00Z',
      authentication_level: 'traditional',
      risk_score: null,
    },
    logistics: {
      enabled: options.enabled ?? true,
      roles: options.roles ?? ['LOGISTICS_ADMIN'],
      permissions: options.permissions ?? ['logistics.warehouses.read'],
      sensitive_permissions: options.sensitivePermissions ?? [],
      step_up_permissions: options.stepUpPermissions ?? [],
      organizations: options.organizations ?? ['org-1'],
      branches: options.branches ?? ['branch-1'],
      warehouses: options.warehouses ?? ['wh-1'],
      default_organization_id: options.defaultOrganizationId ?? 'org-1',
      default_branch_id: options.defaultBranchId ?? 'branch-1',
      default_warehouse_id: options.defaultWarehouseId ?? 'wh-1',
    },
  }
}

export function createLogisticsAccessState(
  options: {
    isLoading?: boolean
    isError?: boolean
    error?: string | null
    errorCode?: string | null
    accessStatus?: LogisticsAccessState['accessStatus']
    me?: MockLogisticsMeOptions
    currentContext?: {
      organization_id: string | null
      branch_id: string | null
      warehouse_id: string | null
    }
    isChangingContext?: boolean
    contextError?: string | null
  } = {},
): LogisticsAccessState {
  const me = buildMockLogisticsMe(options.me)
  const permissions = new Set(me.logistics.permissions)
  const sensitive = new Set(me.logistics.sensitive_permissions)
  const stepUp = new Set(me.logistics.step_up_permissions)
  const organizations = new Set(me.logistics.organizations)
  const branches = new Set(me.logistics.branches)
  const warehouses = new Set(me.logistics.warehouses)
  const currentContext = options.currentContext ?? {
    organization_id: me.logistics.default_organization_id,
    branch_id: me.logistics.default_branch_id,
    warehouse_id: me.logistics.default_warehouse_id,
  }
  const accessStatus = options.accessStatus ?? 'enabled'

  return {
    isLoading: options.isLoading ?? false,
    isLogisticsEnabled: accessStatus === 'enabled',
    accessStatus,
    isError: options.isError ?? false,
    error: options.error ?? null,
    errorCode: options.errorCode ?? null,
    logisticsUser: me.user,
    session: me.session,
    roles: me.logistics.roles,
    permissions,
    sensitivePermissions: sensitive,
    stepUpPermissions: stepUp,
    organizations: me.logistics.organizations,
    branches: me.logistics.branches,
    warehouses: me.logistics.warehouses,
    currentContext,
    isChangingContext: options.isChangingContext ?? false,
    contextError: options.contextError ?? null,
    refreshLogisticsSession: async () => undefined,
    changeContext: async (_context: LogisticsContextChangeRequest) => true,
    clearLogisticsSession: () => undefined,
    hasPermission: (code: string) =>
      accessStatus === 'enabled' && permissions.has(code),
    hasAnyPermission: (codes: readonly string[]) =>
      accessStatus === 'enabled' && codes.some((c) => permissions.has(c)),
    hasAllPermissions: (codes: readonly string[]) =>
      accessStatus === 'enabled' && codes.every((c) => permissions.has(c)),
    canAccessOrganization: (id: string) => organizations.has(id),
    canAccessBranch: (id: string) => branches.has(id),
    canAccessWarehouse: (id: string) => warehouses.has(id),
  }
}

export function renderWithLogisticsAccess(
  element: ReactElement,
  state: LogisticsAccessState,
  initialEntries: InitialEntry[] = ['/'],
): ReturnType<typeof render> {
  function Wrapper({ children }: { children: ReactNode }) {
    return (
      <MemoryRouter initialEntries={initialEntries}>
        <LogisticsAccessContext.Provider value={state}>
          {children}
        </LogisticsAccessContext.Provider>
      </MemoryRouter>
    )
  }
  return render(element, { wrapper: Wrapper })
}
