import { useCallback, useEffect, useRef, useState } from 'react'
import type { AuthenticationLevel } from '../types/continuous-auth'

interface ContinuousAuthPollingOptions {
  enabled: boolean
  authenticationLevel: AuthenticationLevel
  nextEvaluationAfter: string | null
  hasExperimentalSession: boolean
  intervalMs: number
  maxFailures: number
  onPoll: (signal: AbortSignal) => Promise<void>
  onFailureLimit: () => void
}

function getNextDelay(
  intervalMs: number,
  nextEvaluationAfter: string | null,
  hasExperimentalSession: boolean,
  failureCount: number,
): number {
  const normalDelay = hasExperimentalSession
    ? intervalMs
    : intervalMs * 2
  const incrementalDelay =
    failureCount > 0
      ? Math.min(normalDelay * (failureCount + 1), 60_000)
      : normalDelay

  if (!nextEvaluationAfter) {
    return incrementalDelay
  }

  const nextAt = new Date(nextEvaluationAfter).getTime()
  if (Number.isNaN(nextAt)) {
    return incrementalDelay
  }

  return Math.max(incrementalDelay, nextAt - Date.now(), 1_000)
}

export function useContinuousAuthPolling({
  enabled,
  authenticationLevel,
  nextEvaluationAfter,
  hasExperimentalSession,
  intervalMs,
  maxFailures,
  onPoll,
  onFailureLimit,
}: ContinuousAuthPollingOptions) {
  const [isManuallyEnabled, setIsManuallyEnabled] = useState(true)
  const [isVisible, setIsVisible] = useState(
    () => document.visibilityState !== 'hidden',
  )
  const [failureLimitReached, setFailureLimitReached] = useState(false)
  const timerRef = useRef<number | null>(null)
  const controllerRef = useRef<AbortController | null>(null)
  const inFlightRef = useRef(false)
  const failureCountRef = useRef(0)
  const onPollRef = useRef(onPoll)
  const onFailureLimitRef = useRef(onFailureLimit)

  useEffect(() => {
    onPollRef.current = onPoll
  }, [onPoll])

  useEffect(() => {
    onFailureLimitRef.current = onFailureLimit
  }, [onFailureLimit])

  useEffect(() => {
    const handleVisibilityChange = () => {
      const visible = document.visibilityState !== 'hidden'
      setIsVisible(visible)

      if (!visible) {
        controllerRef.current?.abort()
        controllerRef.current = null
        inFlightRef.current = false
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => {
      document.removeEventListener(
        'visibilitychange',
        handleVisibilityChange,
      )
    }
  }, [])

  const stopPolling = useCallback(() => {
    setIsManuallyEnabled(false)
    if (timerRef.current !== null) {
      window.clearTimeout(timerRef.current)
      timerRef.current = null
    }
    controllerRef.current?.abort()
    controllerRef.current = null
    inFlightRef.current = false
  }, [])

  const startPolling = useCallback(() => {
    failureCountRef.current = 0
    setFailureLimitReached(false)
    setIsManuallyEnabled(true)
  }, [])

  const shouldPoll =
    enabled &&
    isManuallyEnabled &&
    isVisible &&
    !failureLimitReached &&
    authenticationLevel !== 'terminated'

  useEffect(() => {
    if (!shouldPoll) {
      return undefined
    }

    let disposed = false

    const schedule = () => {
      if (disposed) {
        return
      }

      const delay = getNextDelay(
        intervalMs,
        nextEvaluationAfter,
        hasExperimentalSession,
        failureCountRef.current,
      )

      timerRef.current = window.setTimeout(async () => {
        if (disposed || inFlightRef.current) {
          schedule()
          return
        }

        inFlightRef.current = true
        const controller = new AbortController()
        controllerRef.current = controller

        try {
          await onPollRef.current(controller.signal)
          failureCountRef.current = 0
        } catch {
          if (!controller.signal.aborted) {
            failureCountRef.current += 1
          }

          if (failureCountRef.current >= maxFailures) {
            setFailureLimitReached(true)
            onFailureLimitRef.current()
            return
          }
        } finally {
          if (controllerRef.current === controller) {
            controllerRef.current = null
          }
          inFlightRef.current = false
        }

        schedule()
      }, delay)
    }

    schedule()

    return () => {
      disposed = true
      if (timerRef.current !== null) {
        window.clearTimeout(timerRef.current)
        timerRef.current = null
      }
      controllerRef.current?.abort()
      controllerRef.current = null
      inFlightRef.current = false
    }
  }, [
    hasExperimentalSession,
    intervalMs,
    maxFailures,
    nextEvaluationAfter,
    shouldPoll,
  ])

  return {
    isPolling: shouldPoll,
    startPolling,
    stopPolling,
  }
}
