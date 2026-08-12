import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type Dispatch,
  type ReactNode,
  type SetStateAction,
} from 'react'
import { useAuth } from '../../../hooks/useAuth'
import { useLogisticsAccess } from '../../logistics-me/hooks/useLogisticsAccess'
import type {
  LogisticsPermissionsContext,
  LogisticsPermissionsResponse,
  LogisticsRoleScope,
} from '../../../types/logistics-permissions'
import { getErrorMessage } from '../../../utils/errors'
import {
  getCachedPermissions,
  getMyLogisticsPermissions,
  invalidatePermissionsCache,
  refreshMyLogisticsPermissions,
} from '../api/logistics-permissions-api'
import {
  LogisticsAuthorizationContext,
  type LogisticsAuthorizationState,
} from './logistics-authorization-context'

interface LogisticsAuthorizationProviderProps {
  children: ReactNode
}

const PERMISSIONS_TTL_MS = 5 * 60 * 1000

function hasGlobalScope(roles: LogisticsRoleScope[]): boolean {
  return roles.some((role) => role.scope_type === 'GLOBAL')
}

function isSameId(a: string | null, b: string | null): boolean {
  return a !== null && a === b
}

interface ApplyHandlers {
  setCatalogVersion: Dispatch<SetStateAction<string | null>>
  setUserId: Dispatch<SetStateAction<string | null>>
  setRoles: Dispatch<SetStateAction<LogisticsRoleScope[]>>
  setPermissions: Dispatch<SetStateAction<ReadonlySet<string>>>
  setSensitivePermissions: Dispatch<SetStateAction<ReadonlySet<string>>>
  setStepUpPermissions: Dispatch<SetStateAction<ReadonlySet<string>>>
  setLastUpdatedAt: Dispatch<SetStateAction<string | null>>
  lastFetchRef: React.MutableRefObject<number>
}

function applyPermissions(
  response: LogisticsPermissionsResponse,
  handlers: ApplyHandlers,
): void {
  handlers.setCatalogVersion(response.catalog_version)
  handlers.setUserId(response.user_id)
  handlers.setRoles(response.roles)
  handlers.setPermissions(new Set(response.permissions))
  handlers.setSensitivePermissions(new Set(response.sensitive_permissions))
  handlers.setStepUpPermissions(new Set(response.step_up_permissions))
  handlers.setLastUpdatedAt(new Date().toISOString())
  handlers.lastFetchRef.current = Date.now()
}

export function LogisticsAuthorizationProvider({
  children,
}: LogisticsAuthorizationProviderProps) {
  const { isAuthenticated, user } = useAuth()
  const logisticsAccess = useLogisticsAccess()
  const [isLoading, setIsLoading] = useState(true)
  const [isError, setIsError] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [catalogVersion, setCatalogVersion] = useState<string | null>(null)
  const [userId, setUserId] = useState<string | null>(null)
  const [roles, setRoles] = useState<LogisticsRoleScope[]>([])
  const [permissions, setPermissions] = useState<ReadonlySet<string>>(
    new Set<string>(),
  )
  const [sensitivePermissions, setSensitivePermissions] = useState<
    ReadonlySet<string>
  >(new Set<string>())
  const [stepUpPermissions, setStepUpPermissions] = useState<
    ReadonlySet<string>
  >(new Set<string>())
  const [context, setContextState] = useState<LogisticsPermissionsContext>({
    organization_id: null,
    branch_id: null,
    warehouse_id: null,
  })
  const [lastUpdatedAt, setLastUpdatedAt] = useState<string | null>(null)

  const lastFetchRef = useRef(0)
  const mountedRef = useRef(true)

  const handlers: ApplyHandlers = {
    setCatalogVersion,
    setUserId,
    setRoles,
    setPermissions,
    setSensitivePermissions,
    setStepUpPermissions,
    setLastUpdatedAt,
    lastFetchRef,
  }

  const loadPermissions = useCallback(
    async (force: boolean): Promise<void> => {
      if (!mountedRef.current) return
      if (!force && getCachedPermissions()) {
        applyPermissions(getCachedPermissions()!, handlers)
        return
      }

      const now = Date.now()
      if (
        !force &&
        lastFetchRef.current > 0 &&
        now - lastFetchRef.current < PERMISSIONS_TTL_MS
      ) {
        return
      }

      setIsLoading(true)
      setIsError(false)
      setError(null)

      try {
        const response = await getMyLogisticsPermissions()
        if (!mountedRef.current) return
        applyPermissions(response, handlers)
      } catch (caught: unknown) {
        if (!mountedRef.current) return
        setIsError(true)
        setError(getErrorMessage(caught))
      } finally {
        if (mountedRef.current) setIsLoading(false)
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  )

  const refreshPermissions = useCallback(async (): Promise<void> => {
    if (!mountedRef.current) return
    setIsLoading(true)
    setIsError(false)
    setError(null)
    try {
      const response = await refreshMyLogisticsPermissions()
      if (!mountedRef.current) return
      applyPermissions(response, handlers)
    } catch (caught: unknown) {
      if (!mountedRef.current) return
      setIsError(true)
      setError(getErrorMessage(caught))
    } finally {
      if (mountedRef.current) setIsLoading(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const setContext = useCallback(
    async (next: Partial<LogisticsPermissionsContext>): Promise<void> => {
      setContextState((current) => ({ ...current, ...next }))
      await refreshPermissions()
    },
    [refreshPermissions],
  )

  const resetContext = useCallback(() => {
    setContextState({
      organization_id: null,
      branch_id: null,
      warehouse_id: null,
    })
  }, [])

  useEffect(() => {
    mountedRef.current = true
    return () => {
      mountedRef.current = false
      invalidatePermissionsCache()
    }
  }, [])

  useEffect(() => {
    if (!isAuthenticated || !user) {
      invalidatePermissionsCache()
      setPermissions(new Set<string>())
      setSensitivePermissions(new Set<string>())
      setStepUpPermissions(new Set<string>())
      setRoles([])
      setCatalogVersion(null)
      setUserId(null)
      setLastUpdatedAt(null)
      setIsLoading(false)
      setIsError(false)
      setError(null)
      return
    }

    if (logisticsAccess.isLoading) {
      setIsLoading(true)
      return
    }

    if (logisticsAccess.isError || logisticsAccess.accessStatus !== 'enabled') {
      setIsLoading(false)
      return
    }

    void loadPermissions(false)
  }, [
    isAuthenticated,
    user,
    logisticsAccess.isLoading,
    logisticsAccess.isError,
    logisticsAccess.accessStatus,
    loadPermissions,
  ])

  const hasGlobal = useMemo(() => hasGlobalScope(roles), [roles])

  const checkPermissionMatch = useCallback(
    (code: string): boolean => {
      if (hasGlobal || permissions.has('*') || permissions.has('admin') || permissions.has('ALL')) return true
      if (permissions.has(code)) return true
      const parts = code.split('.')
      while (parts.length > 1) {
        parts.pop()
        if (permissions.has(`${parts.join('.')}.*`)) return true
      }
      return false
    },
    [hasGlobal, permissions],
  )

  const hasPermission = useCallback(
    (code: string): boolean => {
      if (isLoading) return false
      return checkPermissionMatch(code)
    },
    [isLoading, checkPermissionMatch],
  )

  const hasAnyPermission = useCallback(
    (codes: readonly string[]): boolean => {
      if (isLoading) return false
      for (const code of codes) {
        if (checkPermissionMatch(code)) return true
      }
      return false
    },
    [isLoading, checkPermissionMatch],
  )

  const hasAllPermissions = useCallback(
    (codes: readonly string[]): boolean => {
      if (isLoading) return false
      for (const code of codes) {
        if (!checkPermissionMatch(code)) return false
      }
      return true
    },
    [isLoading, checkPermissionMatch],
  )

  const isSensitivePermission = useCallback(
    (code: string): boolean => sensitivePermissions.has(code),
    [sensitivePermissions],
  )

  const requiresStepUp = useCallback(
    (code: string): boolean => stepUpPermissions.has(code),
    [stepUpPermissions],
  )

  const canAccessOrganization = useCallback(
    (id: string): boolean => {
      if (isLoading) return false
      if (hasGlobal) return true
      return roles.some((role) => isSameId(role.organization_id, id))
    },
    [isLoading, hasGlobal, roles],
  )

  const canAccessBranch = useCallback(
    (id: string): boolean => {
      if (isLoading) return false
      if (hasGlobal) return true
      return roles.some((role) => isSameId(role.branch_id, id))
    },
    [isLoading, hasGlobal, roles],
  )

  const canAccessWarehouse = useCallback(
    (id: string): boolean => {
      if (isLoading) return false
      if (hasGlobal) return true
      return roles.some((role) => isSameId(role.warehouse_id, id))
    },
    [isLoading, hasGlobal, roles],
  )

  const canAccessScope = useCallback(
    (scope: LogisticsPermissionsContext): boolean => {
      if (isLoading) return false
      if (hasGlobal) return true
      return roles.some((role) => {
        if (
          scope.organization_id &&
          role.organization_id !== scope.organization_id
        )
          return false
        if (scope.branch_id && role.branch_id !== scope.branch_id)
          return false
        if (scope.warehouse_id && role.warehouse_id !== scope.warehouse_id)
          return false
        return true
      })
    },
    [isLoading, hasGlobal, roles],
  )

  const value = useMemo<LogisticsAuthorizationState>(
    () => ({
      isLoading,
      isError,
      error,
      catalogVersion,
      userId,
      roles,
      permissions,
      sensitivePermissions,
      stepUpPermissions,
      context,
      lastUpdatedAt,
      hasPermission,
      hasAnyPermission,
      hasAllPermissions,
      isSensitivePermission,
      requiresStepUp,
      canAccessOrganization,
      canAccessBranch,
      canAccessWarehouse,
      canAccessScope,
      refreshPermissions,
      setContext,
      resetContext,
    }),
    [
      isLoading,
      isError,
      error,
      catalogVersion,
      userId,
      roles,
      permissions,
      sensitivePermissions,
      stepUpPermissions,
      context,
      lastUpdatedAt,
      hasPermission,
      hasAnyPermission,
      hasAllPermissions,
      isSensitivePermission,
      requiresStepUp,
      canAccessOrganization,
      canAccessBranch,
      canAccessWarehouse,
      canAccessScope,
      refreshPermissions,
      setContext,
      resetContext,
    ],
  )

  return (
    <LogisticsAuthorizationContext.Provider value={value}>
      {children}
    </LogisticsAuthorizationContext.Provider>
  )
}
