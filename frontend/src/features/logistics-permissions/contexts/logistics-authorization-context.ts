import { createContext } from 'react'
import type {
  LogisticsPermissionsContext,
  LogisticsPermissionsResponse,
  LogisticsRoleScope,
} from '../../../types/logistics-permissions'

export interface LogisticsAuthorizationState {
  isLoading: boolean
  isError: boolean
  error: string | null
  catalogVersion: string | null
  userId: string | null
  roles: LogisticsRoleScope[]
  permissions: ReadonlySet<string>
  sensitivePermissions: ReadonlySet<string>
  stepUpPermissions: ReadonlySet<string>
  context: LogisticsPermissionsContext
  lastUpdatedAt: string | null
  hasPermission: (code: string) => boolean
  hasAnyPermission: (codes: readonly string[]) => boolean
  hasAllPermissions: (codes: readonly string[]) => boolean
  isSensitivePermission: (code: string) => boolean
  requiresStepUp: (code: string) => boolean
  canAccessOrganization: (id: string) => boolean
  canAccessBranch: (id: string) => boolean
  canAccessWarehouse: (id: string) => boolean
  canAccessScope: (scope: LogisticsPermissionsContext) => boolean
  refreshPermissions: () => Promise<void>
  setContext: (
    context: Partial<LogisticsPermissionsContext>,
  ) => Promise<void>
  resetContext: () => void
}

export const defaultLogisticsAuthorizationState: LogisticsAuthorizationState = {
  isLoading: true,
  isError: false,
  error: null,
  catalogVersion: null,
  userId: null,
  roles: [],
  permissions: new Set<string>(),
  sensitivePermissions: new Set<string>(),
  stepUpPermissions: new Set<string>(),
  context: {
    organization_id: null,
    branch_id: null,
    warehouse_id: null,
  },
  lastUpdatedAt: null,
  hasPermission: () => false,
  hasAnyPermission: () => false,
  hasAllPermissions: () => false,
  isSensitivePermission: () => false,
  requiresStepUp: () => false,
  canAccessOrganization: () => false,
  canAccessBranch: () => false,
  canAccessWarehouse: () => false,
  canAccessScope: () => false,
  refreshPermissions: async () => undefined,
  setContext: async () => undefined,
  resetContext: () => undefined,
}

export const LogisticsAuthorizationContext =
  createContext<LogisticsAuthorizationState | undefined>(undefined)

export type { LogisticsPermissionsResponse }