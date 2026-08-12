import { useContext } from 'react'
import {
  LogisticsAuthorizationContext,
  defaultLogisticsAuthorizationState,
  type LogisticsAuthorizationState,
} from '../contexts/logistics-authorization-context'

export function useLogisticsPermissions(): LogisticsAuthorizationState {
  const context = useContext(LogisticsAuthorizationContext)
  if (context === undefined) {
    return defaultLogisticsAuthorizationState
  }
  return context
}

export type {
  LogisticsAuthorizationState as LogisticsPermissionsValue,
} from '../contexts/logistics-authorization-context'