import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react'
import { useAuth } from '../../../hooks/useAuth'
import type {
  LogisticsAccessStatus,
  LogisticsContextChangeRequest,
  LogisticsMeResponse,
} from '../../../types/logistics-me'
import {
  isLogisticsMeError,
  isSessionExpiredError,
} from '../../../types/logistics-me'
import { getErrorMessage } from '../../../utils/errors'
import {
  getCachedLogisticsMe,
  getLogisticsMe,
  invalidateLogisticsMeCache,
  refreshLogisticsMe,
  setLogisticsContext,
} from '../api/logistics-me-api'
import {
  LogisticsAccessContext,
  type LogisticsAccessState,
} from './logistics-access-context'

interface LogisticsAccessProviderProps {
  children: ReactNode
}

function deriveAccessStatus(
  response: LogisticsMeResponse | null,
  isError: boolean,
  isAuthLoading: boolean,
): LogisticsAccessStatus {
  if (isAuthLoading) return 'loading'
  if (isError) return 'error'
  if (!response) return 'loading'
  if (!response.logistics.enabled) return 'disabled'
  if (response.logistics.roles.length === 0) return 'no_role'
  // Platform admins y usuarios con scope GLOBAL no necesitan
  // una organización/sede/almacén específica asignada.
  const isPlatformAdmin = response.user.platform_role === 'admin'
  const hasGlobalScope = response.logistics.roles.includes('LOGISTICS_ADMIN')
  if (
    !isPlatformAdmin &&
    !hasGlobalScope &&
    response.logistics.organizations.length === 0 &&
    response.logistics.branches.length === 0 &&
    response.logistics.warehouses.length === 0
  ) {
    return 'no_scope'
  }
  return 'enabled'
}

export function LogisticsAccessProvider({
  children,
}: LogisticsAccessProviderProps) {
  const { isAuthenticated, isLoading: isAuthLoading, invalidateSession } = useAuth()

  const [isLoading, setIsLoading] = useState(true)
  const [isError, setIsError] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [errorCode, setErrorCode] = useState<string | null>(null)
  const [response, setResponse] = useState<LogisticsMeResponse | null>(null)
  const [isChangingContext, setIsChangingContext] = useState(false)
  const [contextError, setContextError] = useState<string | null>(null)
  const [currentContext, setCurrentContext] = useState({
    organization_id: null as string | null,
    branch_id: null as string | null,
    warehouse_id: null as string | null,
  })

  const mountedRef = useRef(true)

  const loadLogisticsMe = useCallback(
    async (force: boolean): Promise<void> => {
      if (!mountedRef.current) return
      if (!force && getCachedLogisticsMe()) {
        setResponse(getCachedLogisticsMe()!)
        return
      }

      setIsLoading(true)
      setIsError(false)
      setError(null)
      setErrorCode(null)

      try {
        const data = await getLogisticsMe()
        if (!mountedRef.current) return
        setResponse(data)
        setCurrentContext({
          organization_id: data.logistics.default_organization_id,
          branch_id: data.logistics.default_branch_id,
          warehouse_id: data.logistics.default_warehouse_id,
        })
      } catch (caught: unknown) {
        if (!mountedRef.current) return
        setIsError(true)
        setError(getErrorMessage(caught))
        setErrorCode(isLogisticsMeError(caught) ? caught.code : null)
        if (isSessionExpiredError(caught)) {
          invalidateSession('Tu sesión expiró. Inicia sesión nuevamente.')
        }
      } finally {
        if (mountedRef.current) setIsLoading(false)
      }
    },
    [invalidateSession],
  )

  const refreshLogisticsSession = useCallback(async (): Promise<void> => {
    if (!mountedRef.current) return
    setIsLoading(true)
    setIsError(false)
    setError(null)
    setErrorCode(null)
    try {
      const data = await refreshLogisticsMe()
      if (!mountedRef.current) return
      setResponse(data)
      setCurrentContext({
        organization_id: data.logistics.default_organization_id,
        branch_id: data.logistics.default_branch_id,
        warehouse_id: data.logistics.default_warehouse_id,
      })
    } catch (caught: unknown) {
      if (!mountedRef.current) return
      setIsError(true)
      setError(getErrorMessage(caught))
      setErrorCode(isLogisticsMeError(caught) ? caught.code : null)
      if (isSessionExpiredError(caught)) {
        invalidateSession('Tu sesión expiró. Inicia sesión nuevamente.')
      }
    } finally {
      if (mountedRef.current) setIsLoading(false)
    }
  }, [invalidateSession])

  const changeContext = useCallback(
    async (context: LogisticsContextChangeRequest): Promise<boolean> => {
      if (!mountedRef.current) return false
      setIsChangingContext(true)
      setContextError(null)
      try {
        const result = await setLogisticsContext(context)
        if (!mountedRef.current) return false
        setResponse((prev) =>
          prev ? { ...prev, logistics: result.context } : prev,
        )
        setCurrentContext({
          organization_id: context.organization_id,
          branch_id: context.branch_id,
          warehouse_id: context.warehouse_id,
        })
        return true
      } catch (caught: unknown) {
        if (!mountedRef.current) return false
        setContextError(getErrorMessage(caught))
        if (isSessionExpiredError(caught)) {
          invalidateSession('Tu sesión expiró. Inicia sesión nuevamente.')
        }
        return false
      } finally {
        if (mountedRef.current) setIsChangingContext(false)
      }
    },
    [invalidateSession],
  )

  const clearLogisticsSession = useCallback(() => {
    invalidateLogisticsMeCache()
    setResponse(null)
    setIsLoading(false)
    setIsError(false)
    setError(null)
    setErrorCode(null)
    setCurrentContext({
      organization_id: null,
      branch_id: null,
      warehouse_id: null,
    })
    setContextError(null)
    setIsChangingContext(false)
  }, [])

  useEffect(() => {
    mountedRef.current = true
    return () => {
      mountedRef.current = false
      invalidateLogisticsMeCache()
    }
  }, [])

  useEffect(() => {
    if (!isAuthenticated) {
      clearLogisticsSession()
      return
    }
    void loadLogisticsMe(false)
  }, [isAuthenticated, clearLogisticsSession, loadLogisticsMe])

  const accessStatus = useMemo<LogisticsAccessStatus>(
    () => deriveAccessStatus(response, isError, isAuthLoading),
    [response, isError, isAuthLoading],
  )

  const isLogisticsEnabled = accessStatus === 'enabled'

  const permissionsSet = useMemo<ReadonlySet<string>>(
    () => new Set(response?.logistics.permissions ?? []),
    [response],
  )
  const sensitiveSet = useMemo<ReadonlySet<string>>(
    () => new Set(response?.logistics.sensitive_permissions ?? []),
    [response],
  )
  const stepUpSet = useMemo<ReadonlySet<string>>(
    () => new Set(response?.logistics.step_up_permissions ?? []),
    [response],
  )
  const organizationsSet = useMemo<ReadonlySet<string>>(
    () => new Set(response?.logistics.organizations ?? []),
    [response],
  )
  const branchesSet = useMemo<ReadonlySet<string>>(
    () => new Set(response?.logistics.branches ?? []),
    [response],
  )
  const warehousesSet = useMemo<ReadonlySet<string>>(
    () => new Set(response?.logistics.warehouses ?? []),
    [response],
  )

  const hasPermission = useCallback(
    (code: string): boolean => {
      if (isLoading || accessStatus !== 'enabled') return false
      return permissionsSet.has(code)
    },
    [isLoading, accessStatus, permissionsSet],
  )

  const hasAnyPermission = useCallback(
    (codes: readonly string[]): boolean => {
      if (isLoading || accessStatus !== 'enabled') return false
      for (const code of codes) {
        if (permissionsSet.has(code)) return true
      }
      return false
    },
    [isLoading, accessStatus, permissionsSet],
  )

  const hasAllPermissions = useCallback(
    (codes: readonly string[]): boolean => {
      if (isLoading || accessStatus !== 'enabled') return false
      for (const code of codes) {
        if (!permissionsSet.has(code)) return false
      }
      return true
    },
    [isLoading, accessStatus, permissionsSet],
  )

  const canAccessOrganization = useCallback(
    (id: string): boolean => organizationsSet.has(id),
    [organizationsSet],
  )
  const canAccessBranch = useCallback(
    (id: string): boolean => branchesSet.has(id),
    [branchesSet],
  )
  const canAccessWarehouse = useCallback(
    (id: string): boolean => warehousesSet.has(id),
    [warehousesSet],
  )

  const value = useMemo<LogisticsAccessState>(
    () => ({
      isLoading,
      isLogisticsEnabled,
      accessStatus,
      isError,
      error,
      errorCode,
      logisticsUser: response?.user ?? null,
      session: response?.session ?? null,
      roles: response?.logistics.roles ?? [],
      permissions: permissionsSet,
      sensitivePermissions: sensitiveSet,
      stepUpPermissions: stepUpSet,
      organizations: response?.logistics.organizations ?? [],
      branches: response?.logistics.branches ?? [],
      warehouses: response?.logistics.warehouses ?? [],
      currentContext,
      isChangingContext,
      contextError,
      refreshLogisticsSession,
      changeContext,
      clearLogisticsSession,
      hasPermission,
      hasAnyPermission,
      hasAllPermissions,
      canAccessOrganization,
      canAccessBranch,
      canAccessWarehouse,
    }),
    [
      isLoading,
      isLogisticsEnabled,
      accessStatus,
      isError,
      error,
      errorCode,
      response,
      permissionsSet,
      sensitiveSet,
      stepUpSet,
      currentContext,
      isChangingContext,
      contextError,
      refreshLogisticsSession,
      changeContext,
      clearLogisticsSession,
      hasPermission,
      hasAnyPermission,
      hasAllPermissions,
      canAccessOrganization,
      canAccessBranch,
      canAccessWarehouse,
    ],
  )

  return (
    <LogisticsAccessContext.Provider value={value}>
      {children}
    </LogisticsAccessContext.Provider>
  )
}
