import { act, renderHook } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { requestContinuousAuthEvaluation } from '../api/continuous-auth-api'
import type {
  ContinuousAuthEvaluationResponse,
  ContinuousAuthStatus,
} from '../types/continuous-auth'
import { useContinuousAuthEvaluation } from './useContinuousAuthEvaluation'

vi.mock('../api/continuous-auth-api', () => ({
  requestContinuousAuthEvaluation: vi.fn(),
}))

const status: ContinuousAuthStatus = {
  enabled: true,
  continuous_auth_status: 'active',
  risk_level: 'low',
  authentication_level: 'continuously_verified',
  last_evaluation_at: null,
  recommended_action: 'maintain_session',
  applied_action: 'maintain_session',
  components_available: [],
  next_evaluation_after: null,
  degraded: false,
  degraded_reason: null,
}

const evaluation: ContinuousAuthEvaluationResponse = {
  id: 'evaluation-1',
  risk_score: 0.1,
  risk_level: 'low',
  authentication_level: 'continuously_verified',
  recommended_action: 'maintain_session',
  applied_action: 'maintain_session',
  evaluated_at: '2026-07-26T00:00:00Z',
  components: [],
}

describe('useContinuousAuthEvaluation', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(requestContinuousAuthEvaluation).mockResolvedValue(evaluation)
  })

  it('evalúa con una captura facial confirmada aunque no exista ventana conductual', async () => {
    const onSuccess = vi.fn(async () => undefined)
    const { result } = renderHook(() =>
      useContinuousAuthEvaluation({
        enabled: true,
        source: {
          experimentalSessionId: 'session-1',
          facialCaptureId: 'capture-1',
          behavioralWindowId: null,
        },
        status,
        onSuccess,
        onError: vi.fn(),
      }),
    )

    await act(async () => {
      await result.current.evaluate()
    })

    expect(requestContinuousAuthEvaluation).toHaveBeenCalledWith(
      expect.objectContaining({
        experimental_session_id: 'session-1',
        facial_capture_id: 'capture-1',
        behavioral_window_id: null,
      }),
      expect.any(AbortSignal),
    )
    expect(onSuccess).toHaveBeenCalledWith(evaluation)
  })

  it('no evalúa cuando el backend no confirmó ninguna fuente', async () => {
    const { result } = renderHook(() =>
      useContinuousAuthEvaluation({
        enabled: true,
        source: {
          experimentalSessionId: 'session-1',
          facialCaptureId: null,
          behavioralWindowId: null,
        },
        status,
        onSuccess: vi.fn(async () => undefined),
        onError: vi.fn(),
      }),
    )

    await act(async () => {
      await result.current.evaluate()
    })

    expect(requestContinuousAuthEvaluation).not.toHaveBeenCalled()
  })
})
