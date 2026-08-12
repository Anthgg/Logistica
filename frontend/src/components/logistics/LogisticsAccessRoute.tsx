import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import { useLogisticsAccess } from '../../features/logistics-me/hooks/useLogisticsAccess'
import type { LogisticsPermissionsContext } from '../../types/logistics-permissions'
import { LoadingScreen } from '../common/LoadingScreen'
import { LogisticsAccessUnavailablePage } from '../../pages/LogisticsAccessUnavailablePage'
import type { LogisticsAccessStatus } from '../../types/logistics-me'

export interface LogisticsAccessRouteProps {
  permission?: string
  anyOf?: readonly string[]
  allOf?: readonly string[]
  scope?: LogisticsPermissionsContext
}

export function LogisticsAccessRoute(props: LogisticsAccessRouteProps) {
  const { isAuthenticated, isLoading: isAuthLoading } = useAuth()
  const location = useLocation()
  const access = useLogisticsAccess()

  if (isAuthLoading || access.isLoading) {
    return <LoadingScreen message="Cargando acceso logístico…" />
  }

  if (!isAuthenticated) {
    return (
      <Navigate to="/login" replace state={{ from: location }} />
    )
  }

  if (access.isError) {
    return (
      <LogisticsAccessUnavailablePage
        reason={access.errorCode === 'TIMEOUT' ? 'timeout' : 'error'}
      />
    )
  }

  if (access.accessStatus === 'session_expired') {
    return (
      <Navigate to="/login" replace state={{ from: location }} />
    )
  }

  if (
    access.accessStatus === 'disabled' ||
    access.accessStatus === 'no_role' ||
    access.accessStatus === 'no_scope'
  ) {
    const reason = mapStatusToReason(access.accessStatus)
    return <LogisticsAccessUnavailablePage reason={reason} />
  }

  if (props.permission && !access.hasPermission(props.permission)) {
    return <LogisticsAccessUnavailablePage reason="forbidden" />
  }

  if (props.allOf && props.allOf.length > 0) {
    if (!access.hasAllPermissions(props.allOf)) {
      return <LogisticsAccessUnavailablePage reason="forbidden" />
    }
  }

  if (props.anyOf && props.anyOf.length > 0) {
    if (!access.hasAnyPermission(props.anyOf)) {
      return <LogisticsAccessUnavailablePage reason="forbidden" />
    }
  }

  if (props.scope) {
    if (
      (props.scope.organization_id &&
        !access.canAccessOrganization(props.scope.organization_id)) ||
      (props.scope.branch_id &&
        !access.canAccessBranch(props.scope.branch_id)) ||
      (props.scope.warehouse_id &&
        !access.canAccessWarehouse(props.scope.warehouse_id))
    ) {
      return <LogisticsAccessUnavailablePage reason="scope" />
    }
  }

  return <Outlet />
}

function mapStatusToReason(
  status: LogisticsAccessStatus,
): 'disabled' | 'no_role' | 'no_scope' {
  if (status === 'disabled') return 'disabled'
  if (status === 'no_role') return 'no_role'
  return 'no_scope'
}
