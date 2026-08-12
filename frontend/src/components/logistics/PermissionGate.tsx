import type { ReactNode } from 'react'
import type { LogisticsPermissionsContext } from '../../types/logistics-permissions'
import { useLogisticsPermissions } from '../../features/logistics-permissions/hooks/useLogisticsPermissions'

export interface PermissionGateProps {
  permission?: string
  anyOf?: readonly string[]
  allOf?: readonly string[]
  scope?: LogisticsPermissionsContext
  fallback?: ReactNode
  mode?: 'hide' | 'disable'
  showDisabled?: boolean
  disabledReason?: string
  children: ReactNode
}

interface GateDecision {
  authorized: boolean
  reason: 'loading' | 'denied' | 'scope' | 'authorized'
}

function useGateDecision(props: PermissionGateProps): GateDecision {
  const auth = useLogisticsPermissions()

  if (auth.isLoading) {
    return { authorized: false, reason: 'loading' }
  }

  if (props.permission) {
    if (!auth.hasPermission(props.permission)) {
      return { authorized: false, reason: 'denied' }
    }
  }

  if (props.allOf && props.allOf.length > 0) {
    if (!auth.hasAllPermissions(props.allOf)) {
      return { authorized: false, reason: 'denied' }
    }
  }

  if (props.anyOf && props.anyOf.length > 0) {
    if (!auth.hasAnyPermission(props.anyOf)) {
      return { authorized: false, reason: 'denied' }
    }
  }

  if (props.scope && !auth.canAccessScope(props.scope)) {
    return { authorized: false, reason: 'scope' }
  }

  return { authorized: true, reason: 'authorized' }
}

export function PermissionGate(props: PermissionGateProps) {
  const decision = useGateDecision(props)

  if (decision.authorized) {
    return <>{props.children}</>
  }

  if (decision.reason === 'loading') {
    return null
  }

  if (props.mode === 'disable' || props.showDisabled) {
    return (
      <div
        aria-disabled="true"
        aria-describedby={props.disabledReason ? 'permission-gate-reason' : undefined}
        className="permission-gate-disabled"
      >
        {props.children}
        {props.disabledReason && (
          <span
            id="permission-gate-reason"
            className="sr-only"
            role="status"
          >
            {props.disabledReason}
          </span>
        )}
      </div>
    )
  }

  return <>{props.fallback ?? null}</>
}