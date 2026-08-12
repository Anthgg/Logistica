import { screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { AuthContext } from '../../../contexts/auth-context'
import {
  ResearchSessionContext,
  type ResearchSessionContextValue,
} from '../../../contexts/research-session-context'
import {
  createAuthValue,
  testContinuousAuthStatus,
  testSession,
  testUser,
} from '../../../test/test-utils'
import {
  getContinuousAuthStatus,
  getModelStatus,
  reverifyContinuousAuth,
} from '../api/continuous-auth-api'
import { ApiRequestError } from '../../../types/api'
import { ContinuousAuthProvider } from './ContinuousAuthContext'

vi.mock('../api/continuous-auth-api', () => ({
  getContinuousAuthStatus: vi.fn(),
  getModelStatus: vi.fn(),
  requestContinuousAuthEvaluation: vi.fn(),
  reverifyContinuousAuth: vi.fn(),
}))

function researchValue(
  overrides: Partial<ResearchSessionContextValue> = {},
): ResearchSessionContextValue {
  return {
    configuration: null,
    participantId: null,
    isActive: false,
    hasCamera: false,
    startedAtEpoch: null,
    experimentalSessionId: null,
    latestAcceptedFacialCaptureId: null,
    latestBehavioralWindowId: null,
    lastCaptureConfirmedAt: null,
    lastBehaviorBatchConfirmedAt: null,
    counters: {
      keyboard: 0,
      mouse: 0,
      captures: 0,
      batches: 0,
      errors: 0,
    },
    startSession: async () => undefined,
    finishSession: async () => undefined,
    cancelSession: async () => undefined,
    stopForSecurity: () => undefined,
    ...overrides,
  }
}

function renderProvider({
  authenticated,
  authOverrides = {},
  researchOverrides = {},
}: {
  authenticated: boolean
  authOverrides?: Parameters<typeof createAuthValue>[0]
  researchOverrides?: Partial<ResearchSessionContextValue>
}) {
  const auth = createAuthValue({
    user: authenticated ? testUser : null,
    session: authenticated ? testSession : null,
    currentSession: authenticated ? testSession : null,
    isAuthenticated: authenticated,
    ...authOverrides,
  })

  return {
    auth,
    view: (
      <AuthContext.Provider value={auth}>
        <ResearchSessionContext.Provider
          value={researchValue(researchOverrides)}
        >
          <MemoryRouter initialEntries={['/private']}>
            <Routes>
              <Route
                path="/private"
                element={
                  <ContinuousAuthProvider>
                    <div>Contenido privado</div>
                  </ContinuousAuthProvider>
                }
              />
              <Route path="/login" element={<div>Acceso</div>} />
            </Routes>
          </MemoryRouter>
        </ResearchSessionContext.Provider>
      </AuthContext.Provider>
    ),
  }
}

describe('ContinuousAuthProvider', () => {
  beforeEach(() => {
    vi.mocked(getContinuousAuthStatus).mockReset()
    vi.mocked(getModelStatus).mockReset()
    vi.mocked(reverifyContinuousAuth).mockReset()
    vi.mocked(getContinuousAuthStatus).mockResolvedValue(
      testContinuousAuthStatus,
    )
  })

  it('no consulta status cuando no hay autenticación', async () => {
    const { render } = await import('@testing-library/react')
    const { view } = renderProvider({ authenticated: false })
    render(view)

    expect(screen.getByText('Contenido privado')).toBeVisible()
    expect(getContinuousAuthStatus).not.toHaveBeenCalled()
  })

  it('consulta status al montar una ruta autenticada', async () => {
    const { render } = await import('@testing-library/react')
    const { view } = renderProvider({ authenticated: true })
    render(view)

    await vi.waitFor(() => {
      expect(getContinuousAuthStatus).toHaveBeenCalledOnce()
    })
  })

  it('detiene la recolección e invalida una sesión terminada', async () => {
    const stopForSecurity = vi.fn()
    const invalidateSession = vi.fn()
    vi.mocked(getContinuousAuthStatus).mockResolvedValue({
      ...testContinuousAuthStatus,
      risk_level: 'critical',
      authentication_level: 'terminated',
      recommended_action: 'terminate_session',
      applied_action: 'terminate_session',
    })
    const { render } = await import('@testing-library/react')
    const { view } = renderProvider({
      authenticated: true,
      authOverrides: { invalidateSession },
      researchOverrides: { stopForSecurity },
    })
    render(view)

    expect(await screen.findByText('Acceso')).toBeVisible()
    expect(stopForSecurity).toHaveBeenCalledOnce()
    expect(invalidateSession).toHaveBeenCalledWith(
      'Tu sesión fue finalizada por seguridad.',
    )
  })

  it.each([409, 503])(
    'mantiene la sesión y consulta modelos ante estado degradado %s',
    async (statusCode) => {
      const invalidateSession = vi.fn()
      vi.mocked(getContinuousAuthStatus).mockRejectedValue(
        new ApiRequestError('Model unavailable', {
          code: `HTTP_${statusCode}`,
          status: statusCode,
        }),
      )
      vi.mocked(getModelStatus).mockResolvedValue({
        overall_status: 'degraded',
        facial_loaded: false,
        pad_loaded: false,
        behavioral_available_count: 0,
        behavioral_loaded_count: 0,
        versions: {},
        device: 'cpu',
        loaded_at: null,
        checksums_valid: false,
        fusion_loaded: false,
        normalization_loaded: false,
        errors: [],
      })
      const { render } = await import('@testing-library/react')
      const { view } = renderProvider({
        authenticated: true,
        authOverrides: { invalidateSession },
      })
      render(view)

      await vi.waitFor(() => {
        expect(getModelStatus).toHaveBeenCalledOnce()
      })
      expect(invalidateSession).not.toHaveBeenCalled()
      expect(screen.getByText('Contenido privado')).toBeVisible()
    },
  )
})
