import { useCallback, useEffect, useRef, useState } from 'react'
import { requestContinuousAuthEvaluation } from '../api/continuous-auth-api'
import { CONTINUOUS_AUTH_STATUS_INTERVAL_MS } from '../../../api/config'
import type {
  ContinuousAuthEvaluationResponse,
  ContinuousAuthStatus,
} from '../types/continuous-auth'

interface EvaluationSource {
  experimentalSessionId: string | null
  facialCaptureId: string | null
  behavioralWindowId: string | null
}

interface ContinuousAuthEvaluationOptions {
  enabled: boolean
  source: EvaluationSource
  status: ContinuousAuthStatus | null
  onSuccess: (
    response: ContinuousAuthEvaluationResponse,
  ) => Promise<void>
  onError: (error: unknown) => void
}

function canEvaluateAt(nextEvaluationAfter: string | null): boolean {
  if (!nextEvaluationAfter) {
    return true
  }

  const nextAt = new Date(nextEvaluationAfter).getTime()
  return Number.isNaN(nextAt) || nextAt <= Date.now()
}

export function useContinuousAuthEvaluation({
  enabled,
  source,
  status,
  onSuccess,
  onError,
}: ContinuousAuthEvaluationOptions) {
  const [isEvaluating, setIsEvaluating] = useState(false)
  const inFlightRef = useRef(false)
  const lastCombinationRef = useRef<string | null>(null)
  const controllerRef = useRef<AbortController | null>(null)
  const lastEvaluationAtRef = useRef<number | null>(null)

  const resetEvaluation = useCallback(() => {
    controllerRef.current?.abort()
    controllerRef.current = null
    inFlightRef.current = false
    lastCombinationRef.current = null
    lastEvaluationAtRef.current = null
    setIsEvaluating(false)
  }, [])

  useEffect(() => resetEvaluation, [resetEvaluation])

  const evaluate = useCallback(async () => {
    if (
      !enabled ||
      !status?.enabled ||
      status.authentication_level === 'terminated' ||
      !source.experimentalSessionId ||
      (!source.facialCaptureId && !source.behavioralWindowId) ||
      !canEvaluateAt(status.next_evaluation_after) ||
      (lastEvaluationAtRef.current !== null &&
        Date.now() - lastEvaluationAtRef.current <
          CONTINUOUS_AUTH_STATUS_INTERVAL_MS) ||
      inFlightRef.current
    ) {
      return null
    }

    const combination = [
      source.experimentalSessionId,
      source.facialCaptureId ?? 'no-facial-capture',
      source.behavioralWindowId ?? 'no-behavioral-window',
    ].join(':')

    if (lastCombinationRef.current === combination) {
      return null
    }

    inFlightRef.current = true
    setIsEvaluating(true)
    const controller = new AbortController()
    controllerRef.current = controller

    try {
      const response = await requestContinuousAuthEvaluation(
        {
          experimental_session_id: source.experimentalSessionId,
          facial_capture_id: source.facialCaptureId,
          behavioral_window_id: source.behavioralWindowId,
          evaluation_timestamp: new Date().toISOString(),
        },
        controller.signal,
      )
      lastCombinationRef.current = combination
      lastEvaluationAtRef.current = Date.now()
      await onSuccess(response)
      return response
    } catch (error: unknown) {
      if (!controller.signal.aborted) {
        onError(error)
      }
      throw error
    } finally {
      if (controllerRef.current === controller) {
        controllerRef.current = null
      }
      inFlightRef.current = false
      setIsEvaluating(false)
    }
  }, [enabled, onError, onSuccess, source, status])

  return {
    evaluate,
    isEvaluating,
    resetEvaluation,
  }
}
