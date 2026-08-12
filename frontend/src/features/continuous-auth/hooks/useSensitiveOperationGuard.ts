import { useCallback } from 'react'
import { ApiRequestError } from '../../../types/api'
import type {
  AuthenticationLevel,
  ContinuousAuthStatus,
  RiskLevel,
} from '../types/continuous-auth'
import { useContinuousAuth } from './useContinuousAuth'

function requiresReverification(
  status: ContinuousAuthStatus | null,
): boolean {
  const authenticationLevel: AuthenticationLevel =
    status?.authentication_level ?? 'traditional'
  const riskLevel: RiskLevel = status?.risk_level ?? 'unknown'

  return (
    authenticationLevel === 'verification_required' ||
    authenticationLevel === 'restricted' ||
    authenticationLevel === 'terminated' ||
    riskLevel === 'high' ||
    riskLevel === 'critical'
  )
}

export function useSensitiveOperationGuard() {
  const {
    status,
    refreshStatus,
    requestReverification,
    handleSecurityError,
  } = useContinuousAuth()
  const blocked = requiresReverification(status)

  const guardSensitiveAction = useCallback(
    async (action: () => Promise<void>): Promise<boolean> => {
      let currentStatus = status

      try {
        currentStatus = await refreshStatus()
      } catch {
        return false
      }

      if (requiresReverification(currentStatus)) {
        requestReverification()
        return false
      }

      try {
        await action()
        return true
      } catch (error: unknown) {
        if (error instanceof ApiRequestError && error.status === 403) {
          handleSecurityError(error)
          await refreshStatus().catch(() => null)
        }
        throw error
      }
    },
    [
      handleSecurityError,
      refreshStatus,
      requestReverification,
      status,
    ],
  )

  return {
    canProceed: !blocked,
    requireReverification: blocked,
    guardSensitiveAction,
  }
}
