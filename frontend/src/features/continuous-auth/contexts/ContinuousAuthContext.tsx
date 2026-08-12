import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react'
import { useNavigate } from 'react-router-dom'
import {
  getContinuousAuthStatus,
  getModelStatus,
  reverifyContinuousAuth,
} from '../api/continuous-auth-api'
import { useContinuousAuthEvaluation } from '../hooks/useContinuousAuthEvaluation'
import { useContinuousAuthPolling } from '../hooks/useContinuousAuthPolling'
import type {
  ContinuousAuthEvaluationResponse,
  ContinuousAuthStatus,
} from '../types/continuous-auth'
import {
  getContinuousAuthErrorCode,
  getContinuousAuthErrorMessage,
  isRestrictedSessionError,
  isTerminatedSessionError,
} from '../utils/continuous-auth-errors'
import {
  CONTINUOUS_AUTH_MAX_FAILURES,
  CONTINUOUS_AUTH_STATUS_INTERVAL_MS,
} from '../../../api/config'
import { useAuth } from '../../../hooks/useAuth'
import { useResearchSession } from '../../../hooks/useResearchSession'
import { ApiRequestError } from '../../../types/api'
import {
  ContinuousAuthContext,
  type ContinuousAuthContextValue,
} from './continuous-auth-context'

export function ContinuousAuthProvider({
  children,
}: {
  children: ReactNode
}) {
  const {
    isAuthenticated,
    isLoading: isAuthLoading,
    invalidateSession,
    refreshUser,
  } = useAuth()
  const {
    experimentalSessionId,
    latestAcceptedFacialCaptureId,
    latestBehavioralWindowId,
    isActive: isResearchSessionActive,
    stopForSecurity,
  } = useResearchSession()
  const navigate = useNavigate()
  const [status, setStatus] = useState<ContinuousAuthStatus | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isReverifying, setIsReverifying] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [errorCode, setErrorCode] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [lastUpdatedAt, setLastUpdatedAt] = useState<string | null>(null)
  const [isReverificationOpen, setIsReverificationOpen] = useState(false)
  const statusControllerRef = useRef<AbortController | null>(null)
  const redirectStartedRef = useRef(false)
  const unauthorizedHandledRef = useRef(false)

  const terminateSession = useCallback(() => {
    if (redirectStartedRef.current) {
      return
    }

    redirectStartedRef.current = true
    statusControllerRef.current?.abort()
    stopForSecurity()
    const message = 'Tu sesión fue finalizada por seguridad.'
    invalidateSession(message)
    navigate('/login', {
      replace: true,
      state: { message },
    })
  }, [invalidateSession, navigate, stopForSecurity])

  const handleSecurityError = useCallback(
    (caughtError: unknown) => {
      const code = getContinuousAuthErrorCode(caughtError)
      const message = getContinuousAuthErrorMessage(caughtError)
      setErrorCode(code)
      setError(message)

      if (
        caughtError instanceof ApiRequestError &&
        [409, 503].includes(caughtError.status ?? 0)
      ) {
        setStatus((current) =>
          current
            ? {
                ...current,
                degraded: true,
                degraded_reason: message,
              }
            : current,
        )
        void getModelStatus().catch(() => undefined)
      }

      if (isTerminatedSessionError(caughtError)) {
        terminateSession()
        return
      }

      if (isRestrictedSessionError(caughtError)) {
        setIsReverificationOpen(true)
      }
    },
    [terminateSession],
  )

  const loadStatus = useCallback(
    async (
      externalSignal?: AbortSignal,
      showLoading = false,
    ): Promise<ContinuousAuthStatus | null> => {
      if (!isAuthenticated || isAuthLoading) {
        return null
      }

      statusControllerRef.current?.abort()
      const controller = new AbortController()
      statusControllerRef.current = controller
      const abortFromOutside = () => controller.abort()
      externalSignal?.addEventListener('abort', abortFromOutside, {
        once: true,
      })

      if (showLoading) {
        setIsLoading(true)
      }

      try {
        const nextStatus = await getContinuousAuthStatus(controller.signal)
        setStatus(nextStatus)
        setLastUpdatedAt(new Date().toISOString())
        setError(null)
        setErrorCode(null)
        unauthorizedHandledRef.current = false

        if (
          nextStatus.authentication_level === 'verification_required' ||
          nextStatus.authentication_level === 'restricted' ||
          nextStatus.risk_level === 'critical'
        ) {
          setIsReverificationOpen(true)
        }

        if (nextStatus.authentication_level === 'terminated') {
          terminateSession()
        }

        return nextStatus
      } catch (caughtError: unknown) {
        if (
          caughtError instanceof ApiRequestError &&
          caughtError.code === 'REQUEST_ABORTED'
        ) {
          return null
        }

        handleSecurityError(caughtError)

        if (
          caughtError instanceof ApiRequestError &&
          caughtError.status === 401 &&
          !unauthorizedHandledRef.current
        ) {
          unauthorizedHandledRef.current = true
          await refreshUser().catch(() => undefined)
        }

        throw caughtError
      } finally {
        externalSignal?.removeEventListener(
          'abort',
          abortFromOutside,
        )
        if (statusControllerRef.current === controller) {
          statusControllerRef.current = null
        }
        if (showLoading) {
          setIsLoading(false)
        }
      }
    },
    [
      handleSecurityError,
      isAuthLoading,
      isAuthenticated,
      refreshUser,
      terminateSession,
    ],
  )

  const refreshStatus = useCallback(
    () => loadStatus(undefined, true),
    [loadStatus],
  )

  const handleEvaluationSuccess = useCallback(
    async (_response: ContinuousAuthEvaluationResponse) => {
      await loadStatus()
    },
    [loadStatus],
  )

  const evaluationSource = useMemo(
    () => ({
      experimentalSessionId,
      facialCaptureId: latestAcceptedFacialCaptureId,
      behavioralWindowId: latestBehavioralWindowId,
    }),
    [
      experimentalSessionId,
      latestAcceptedFacialCaptureId,
      latestBehavioralWindowId,
    ],
  )

  const { evaluate, isEvaluating, resetEvaluation } =
    useContinuousAuthEvaluation({
      enabled: isAuthenticated && isResearchSessionActive,
      source: evaluationSource,
      status,
      onSuccess: handleEvaluationSuccess,
      onError: handleSecurityError,
    })

  const handleFailureLimit = useCallback(() => {
    setErrorCode('POLLING_SUSPENDED')
    setError(
      'La actualización automática se pausó temporalmente. Puedes reintentar manualmente.',
    )
  }, [])

  const pollStatus = useCallback(
    async (signal: AbortSignal) => {
      await loadStatus(signal)
    },
    [loadStatus],
  )

  const { isPolling, startPolling, stopPolling } =
    useContinuousAuthPolling({
      enabled:
        isAuthenticated &&
        !isAuthLoading &&
        status?.enabled !== false,
      authenticationLevel:
        status?.authentication_level ?? 'traditional',
      nextEvaluationAfter: status?.next_evaluation_after ?? null,
      hasExperimentalSession: isResearchSessionActive,
      intervalMs: CONTINUOUS_AUTH_STATUS_INTERVAL_MS,
      maxFailures: CONTINUOUS_AUTH_MAX_FAILURES,
      onPoll: pollStatus,
      onFailureLimit: handleFailureLimit,
    })

  useEffect(() => {
    if (isAuthLoading) {
      return undefined
    }

    if (!isAuthenticated) {
      statusControllerRef.current?.abort()
      setStatus(null)
      setError(null)
      setErrorCode(null)
      setNotice(null)
      setLastUpdatedAt(null)
      setIsReverificationOpen(false)
      resetEvaluation()
      redirectStartedRef.current = false
      unauthorizedHandledRef.current = false
      return undefined
    }

    void loadStatus(undefined, true).catch(() => undefined)
    return () => {
      statusControllerRef.current?.abort()
    }
  }, [
    isAuthLoading,
    isAuthenticated,
    loadStatus,
    resetEvaluation,
  ])

  useEffect(() => {
    if (
      status?.authentication_level === 'terminated' ||
      status?.recommended_action === 'terminate_session'
    ) {
      stopPolling()
      terminateSession()
    }
  }, [status, stopPolling, terminateSession])

  useEffect(() => {
    if (
      !evaluationSource.experimentalSessionId ||
      (!evaluationSource.facialCaptureId &&
        !evaluationSource.behavioralWindowId)
    ) {
      return
    }

    void evaluate().catch(() => undefined)
  }, [evaluate, evaluationSource])

  const reverify = useCallback(
    async (password: string) => {
      if (status?.authentication_level === 'terminated') {
        throw new ApiRequestError(
          'Esta sesión fue finalizada.',
          {
            code: 'SESSION_TERMINATED',
            status: 403,
          },
        )
      }

      setIsReverifying(true)
      setError(null)
      setErrorCode(null)

      try {
        const response = await reverifyContinuousAuth({ password })
        setNotice('Tu identidad fue confirmada correctamente.')
        setIsReverificationOpen(false)
        await loadStatus()
        startPolling()
        return response
      } catch (caughtError: unknown) {
        handleSecurityError(caughtError)
        throw caughtError
      } finally {
        setIsReverifying(false)
      }
    },
    [
      handleSecurityError,
      loadStatus,
      startPolling,
      status?.authentication_level,
    ],
  )

  const clearError = useCallback(() => {
    setError(null)
    setErrorCode(null)
  }, [])

  const clearNotice = useCallback(() => {
    setNotice(null)
  }, [])

  const requestReverification = useCallback(() => {
    if (status?.authentication_level !== 'terminated') {
      setIsReverificationOpen(true)
    }
  }, [status?.authentication_level])

  const closeReverification = useCallback(() => {
    if (
      status?.authentication_level !== 'restricted' &&
      status?.risk_level !== 'critical'
    ) {
      setIsReverificationOpen(false)
    }
  }, [status?.authentication_level, status?.risk_level])

  const value = useMemo<ContinuousAuthContextValue>(
    () => ({
      status,
      riskLevel: status?.risk_level ?? 'unknown',
      authenticationLevel:
        status?.authentication_level ?? 'traditional',
      recommendedAction: status?.recommended_action ?? 'none',
      appliedAction: status?.applied_action ?? 'none',
      components: status?.components_available ?? [],
      isLoading,
      isEvaluating,
      isReverifying,
      isPolling,
      error,
      errorCode,
      notice,
      lastUpdatedAt,
      isReverificationOpen,
      refreshStatus,
      evaluate,
      reverify,
      clearError,
      clearNotice,
      stopPolling,
      startPolling,
      requestReverification,
      closeReverification,
      handleSecurityError,
    }),
    [
      clearError,
      clearNotice,
      closeReverification,
      error,
      errorCode,
      evaluate,
      handleSecurityError,
      isEvaluating,
      isLoading,
      isPolling,
      isReverificationOpen,
      isReverifying,
      lastUpdatedAt,
      notice,
      refreshStatus,
      requestReverification,
      reverify,
      startPolling,
      status,
      stopPolling,
    ],
  )

  return (
    <ContinuousAuthContext.Provider value={value}>
      {children}
    </ContinuousAuthContext.Provider>
  )
}
