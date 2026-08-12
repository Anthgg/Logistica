import { beforeEach, describe, expect, it, vi } from 'vitest'
import { clearCsrfToken } from '../../../api/csrf'
import {
  getContinuousAuthStatus,
  getEvaluationDetail,
  getModelStatus,
  requestContinuousAuthEvaluation,
  reverifyContinuousAuth,
} from './continuous-auth-api'

const statusPayload = {
  success: true,
  enabled: true,
  continuous_auth_status: 'active',
  risk_level: 'low',
  authentication_level: 'continuously_verified',
  last_evaluation_at: '2026-07-25T10:00:00Z',
  recommended_action: 'maintain_session',
  applied_action: 'maintain_session',
  components_available: {
    facial: true,
    pad: true,
    behavioral: false,
  },
  next_evaluation_after: '2026-07-25T10:01:00Z',
}

function jsonResponse(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

describe('continuous-auth-api', () => {
  beforeEach(() => {
    clearCsrfToken()
    vi.restoreAllMocks()
  })

  it('consulta el endpoint exacto de estado con cookies', async () => {
    const fetchMock = vi.fn(async () => jsonResponse(statusPayload))
    vi.stubGlobal('fetch', fetchMock)

    const status = await getContinuousAuthStatus()

    expect(status.risk_level).toBe('low')
    expect(status.components_available).toEqual([
      expect.objectContaining({ name: 'facial', available: true }),
      expect.objectContaining({ name: 'pad', available: true }),
      expect.objectContaining({ name: 'behavioral', available: false }),
    ])
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringMatching(/\/api\/continuous-auth\/status$/),
      expect.objectContaining({
        method: 'GET',
        credentials: 'include',
      }),
    )
  })

  it('rechaza una respuesta pública con campos obligatorios inválidos', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => jsonResponse({ ...statusPayload, enabled: 'yes' })),
    )

    await expect(getContinuousAuthStatus()).rejects.toMatchObject({
      code: 'INVALID_RESPONSE',
    })
  })

  it('evalúa con CSRF, cookies y únicamente identificadores confirmados', async () => {
    const evaluation = {
      id: 'evaluation-id',
      risk_score: 0.12,
      risk_level: 'low',
      authentication_level: 'continuously_verified',
      recommended_action: 'maintain_session',
      applied_action: 'maintain_session',
      evaluated_at: '2026-07-25T10:00:00Z',
      components: [],
    }
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ csrf_token: 'csrf-value' }))
      .mockResolvedValueOnce(
        jsonResponse({
          success: true,
          evaluation: {
            ...evaluation,
            components: {
              facial: { available: true, status: 'available' },
              pad: { available: true, status: 'available' },
              behavioral: { available: false, status: 'pending' },
            },
          },
        }),
      )
    vi.stubGlobal('fetch', fetchMock)

    const request = {
      experimental_session_id: 'research-id',
      facial_capture_id: 'capture-id',
      behavioral_window_id: 'window-id',
      evaluation_timestamp: '2026-07-25T10:00:00Z',
    }
    await requestContinuousAuthEvaluation(request)

    const [, options] = fetchMock.mock.calls[1] as [
      string,
      RequestInit,
    ]
    const body = JSON.parse(String(options.body)) as Record<
      string,
      unknown
    >
    const headers = options.headers as Headers

    expect(options.credentials).toBe('include')
    expect(headers.get('X-CSRF-Token')).toBe('csrf-value')
    expect(body).toEqual(request)
    expect(body).not.toHaveProperty('risk_score')
    expect(body).not.toHaveProperty('facial_score')
  })

  it('reverifica con contraseña y no la persiste fuera del cuerpo', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ csrf_token: 'csrf-value' }))
      .mockResolvedValueOnce(
        jsonResponse({
          success: true,
          authentication_level: 'continuously_verified',
          continuous_auth_status: 'active',
          reverified_at: '2026-07-25T10:00:00Z',
        }),
      )
    vi.stubGlobal('fetch', fetchMock)

    await reverifyContinuousAuth({ password: 'correcta-segura' })

    const [, options] = fetchMock.mock.calls[1] as [
      string,
      RequestInit,
    ]
    expect(options.body).toBe('{"password":"correcta-segura"}')
    expect(options.credentials).toBe('include')
  })

  it('adapta el detalle administrativo real sin biometría cruda', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        jsonResponse({
          id: 'evaluation-id',
          user_id: 'user-id',
          session_id: 'session-id',
          experimental_session_id: 'experimental-id',
          participant_id: null,
          facial_capture_id: 'capture-id',
          behavioral_window_id: null,
          facial_available: true,
          pad_available: true,
          behavioral_available: false,
          facial_score: 0.9,
          pad_score: 0.95,
          behavioral_score: null,
          facial_risk: 0.1,
          pad_risk: 0.05,
          behavioral_risk: null,
          combined_risk: 0.08,
          risk_level: 'low',
          authentication_level: 'continuously_verified',
          recommended_action: 'maintain_session',
          applied_action: 'maintain_session',
          model_versions: { facial: '1.0' },
          latency_ms: 12,
          latency_breakdown: { facial: 8, fusion: 4 },
          evaluated_at: '2026-07-25T10:00:00Z',
          created_at: '2026-07-25T10:00:00Z',
        }),
      ),
    )

    await expect(getEvaluationDetail('evaluation-id')).resolves.toMatchObject({
      user: { id: 'user-id' },
      session: { id: 'session-id' },
      participant: null,
      component_scores: { facial: 0.9, pad: 0.95 },
      component_risks: { facial: 0.1, pad: 0.05 },
      latency: { facial: 8, fusion: 4 },
    })
  })

  it('adapta la respuesta envuelta del estado de modelos', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        jsonResponse({
          success: true,
          models: {
            global_status: 'ready',
            facial: {
              available: true,
              loaded: true,
              checksum_valid: true,
              version: 'facial-v1',
              reason_code: null,
            },
            pad: {
              available: true,
              loaded: true,
              checksum_valid: true,
              version: 'pad-v1',
              reason_code: null,
            },
            behavioral_available: 2,
            behavioral_loaded: 1,
            behavioral_versions: ['behavior-v1'],
            device: 'cpu',
            loaded_at: '2026-07-25T10:00:00Z',
            registry_checksum_valid: true,
            fusion_loaded: true,
            normalization_loaded: true,
            errors: [],
          },
        }),
      ),
    )

    await expect(getModelStatus()).resolves.toMatchObject({
      overall_status: 'ready',
      facial_loaded: true,
      pad_loaded: true,
      behavioral_available_count: 2,
      behavioral_loaded_count: 1,
      normalization_loaded: true,
    })
  })
})
