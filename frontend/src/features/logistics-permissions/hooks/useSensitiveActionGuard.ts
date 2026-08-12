import { useCallback, useState } from 'react'
import { useLogisticsPermissions } from '../hooks/useLogisticsPermissions'
import { useSensitiveOperationGuard } from '../../continuous-auth/hooks/useSensitiveOperationGuard'
import { ApiRequestError } from '../../../types/api'
import {
  extractStepUpDetails,
  isReasonRequired,
  isStepUpRequired,
} from '../../../types/logistics-permissions'

export interface SensitiveActionGuardOptions {
  permission: string
  resourceType?: string
  resourceId?: string
  requiresReason?: boolean
}

export interface SensitiveActionGuardResult {
  isAuthorized: boolean
  isBlocked: boolean
  requiresReason: boolean
  isPending: boolean
  errorMessage: string | null
  reasonDialogOpen: boolean
  stepUpRequired: boolean
  stepUpPermission: string | null
  openReasonDialog: () => void
  closeReasonDialog: () => void
  run: (action: (reason?: string) => Promise<void>) => Promise<boolean>
  confirmWithReason: (
    action: (reason: string) => Promise<void>,
    reason: string,
  ) => Promise<boolean>
}

export function useSensitiveActionGuard(
  options: SensitiveActionGuardOptions,
): SensitiveActionGuardResult {
  const auth = useLogisticsPermissions()
  const { guardSensitiveAction, requireReverification } =
    useSensitiveOperationGuard()

  const [isPending, setIsPending] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [reasonDialogOpen, setReasonDialogOpen] = useState(false)
  const [stepUpRequired, setStepUpRequired] = useState(false)
  const [stepUpPermission, setStepUpPermission] = useState<string | null>(
    null,
  )

  const isSensitive = auth.isSensitivePermission(options.permission)
  const requiresReason =
    options.requiresReason === true
      ? true
      : isSensitive && auth.requiresStepUp(options.permission)

  const executeUnderGuard = useCallback(
    async (
      action: (reason?: string) => Promise<void>,
      reason?: string,
    ): Promise<boolean> => {
      setIsPending(true)
      setErrorMessage(null)
      try {
        const executed = await guardSensitiveAction(async () => {
          await action(reason)
        })
        return executed
      } catch (error: unknown) {
        if (isStepUpRequired(error)) {
          const details = extractStepUpDetails(error)
          setStepUpRequired(true)
          setStepUpPermission(details?.permission ?? options.permission)
          return false
        }
        if (isReasonRequired(error)) {
          setReasonDialogOpen(true)
          return false
        }
        if (error instanceof ApiRequestError) {
          setErrorMessage(error.message)
        } else {
          setErrorMessage('No se pudo completar la acción.')
        }
        return false
      } finally {
        setIsPending(false)
      }
    },
    [guardSensitiveAction, options.permission],
  )

  const run = useCallback(
    async (action: (reason?: string) => Promise<void>): Promise<boolean> => {
      setErrorMessage(null)
      setStepUpRequired(false)

      if (!auth.hasPermission(options.permission)) {
        setErrorMessage('No tienes permisos para esta acción.')
        return false
      }

      if (requiresReason) {
        setReasonDialogOpen(true)
        return false
      }

      return executeUnderGuard(action)
    },
    [auth, executeUnderGuard, options.permission, requiresReason],
  )

  const confirmWithReason = useCallback(
    async (
      action: (reason: string) => Promise<void>,
      reason: string,
    ): Promise<boolean> => {
      setReasonDialogOpen(false)
      return executeUnderGuard(action as (reason?: string) => Promise<void>, reason)
    },
    [executeUnderGuard],
  )

  return {
    isAuthorized: auth.hasPermission(options.permission),
    isBlocked: requireReverification,
    requiresReason,
    isPending,
    errorMessage,
    reasonDialogOpen,
    stepUpRequired,
    stepUpPermission,
    openReasonDialog: () => setReasonDialogOpen(true),
    closeReasonDialog: () => setReasonDialogOpen(false),
    run,
    confirmWithReason,
  }
}