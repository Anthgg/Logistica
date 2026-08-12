import { createContext } from 'react'
import type {
  LogisticsAccessStatus,
  LogisticsContextChangeRequest,
  LogisticsMeResponse,
} from '../../../types/logistics-me'

export interface LogisticsAccessState {
  isLoading: boolean
  isLogisticsEnabled: boolean
  accessStatus: LogisticsAccessStatus
  isError: boolean
  error: string | null
  errorCode: string | null
  logisticsUser: LogisticsMeResponse['user'] | null
  session: LogisticsMeResponse['session'] | null
  roles: string[]
  permissions: ReadonlySet<string>
  sensitivePermissions: ReadonlySet<string>
  stepUpPermissions: ReadonlySet<string>
  organizations: string[]
  branches: string[]
  warehouses: string[]
  currentContext: {
    organization_id: string | null
    branch_id: string | null
    warehouse_id: string | null
  }
  isChangingContext: boolean
  contextError: string | null
  refreshLogisticsSession: () => Promise<void>
  changeContext: (
    context: LogisticsContextChangeRequest,
  ) => Promise<boolean>
  clearLogisticsSession: () => void
  hasPermission: (code: string) => boolean
  hasAnyPermission: (codes: readonly string[]) => boolean
  hasAllPermissions: (codes: readonly string[]) => boolean
  canAccessOrganization: (id: string) => boolean
  canAccessBranch: (id: string) => boolean
  canAccessWarehouse: (id: string) => boolean
}

export const defaultLogisticsAccessState: LogisticsAccessState = {
  isLoading: true,
  isLogisticsEnabled: false,
  accessStatus: 'loading',
  isError: false,
  error: null,
  errorCode: null,
  logisticsUser: null,
  session: null,
  roles: [],
  permissions: new Set<string>(),
  sensitivePermissions: new Set<string>(),
  stepUpPermissions: new Set<string>(),
  organizations: [],
  branches: [],
  warehouses: [],
  currentContext: {
    organization_id: null,
    branch_id: null,
    warehouse_id: null,
  },
  isChangingContext: false,
  contextError: null,
  refreshLogisticsSession: async () => undefined,
  changeContext: async () => false,
  clearLogisticsSession: () => undefined,
  hasPermission: () => false,
  hasAnyPermission: () => false,
  hasAllPermissions: () => false,
  canAccessOrganization: () => false,
  canAccessBranch: () => false,
  canAccessWarehouse: () => false,
}

export const LogisticsAccessContext =
  createContext<LogisticsAccessState | undefined>(undefined)

export type { LogisticsMeResponse }
