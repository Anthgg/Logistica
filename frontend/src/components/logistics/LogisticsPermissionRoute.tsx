import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import { useLogisticsPermissions } from '../../features/logistics-permissions/hooks/useLogisticsPermissions'
import type { LogisticsPermissionsContext } from '../../types/logistics-permissions'
import { LoadingScreen } from '../common/LoadingScreen'
import { ForbiddenPage } from '../../pages/ForbiddenPage'

export interface LogisticsPermissionRouteProps {
  permission?: string
  anyOf?: readonly string[]
  allOf?: readonly string[]
  scope?: LogisticsPermissionsContext
}

export function LogisticsPermissionRoute(
  props: LogisticsPermissionRouteProps,
) {
  const { isAuthenticated, isLoading: isAuthLoading } = useAuth()
  const location = useLocation()
  const auth = useLogisticsPermissions()

  if (isAuthLoading || auth.isLoading) {
    return <LoadingScreen />
  }

  if (!isAuthenticated) {
    return (
      <Navigate to="/login" replace state={{ from: location }} />
    )
  }

  if (auth.isError) {
    return <ForbiddenPage reason="load_error" />
  }

  if (props.permission && !auth.hasPermission(props.permission)) {
    return <ForbiddenPage reason="denied" />
  }

  if (props.allOf && props.allOf.length > 0) {
    if (!auth.hasAllPermissions(props.allOf)) {
      return <ForbiddenPage reason="denied" />
    }
  }

  if (props.anyOf && props.anyOf.length > 0) {
    if (!auth.hasAnyPermission(props.anyOf)) {
      return <ForbiddenPage reason="denied" />
    }
  }

  if (props.scope && !auth.canAccessScope(props.scope)) {
    return <ForbiddenPage reason="scope" />
  }

  return <Outlet />
}