import { useState } from 'react'
import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import {
  createContinuousAuthValue,
  renderWithAuth,
  testContinuousAuthStatus,
} from '../../../test/test-utils'
import { useSensitiveOperationGuard } from './useSensitiveOperationGuard'

function GuardHarness({ action }: { action: () => Promise<void> }) {
  const { canProceed, guardSensitiveAction } =
    useSensitiveOperationGuard()
  const [result, setResult] = useState('sin ejecutar')

  return (
    <div>
      <span>{canProceed ? 'permitida' : 'restringida'}</span>
      <button
        type="button"
        onClick={() => {
          void guardSensitiveAction(action).then((executed) => {
            setResult(executed ? 'ejecutada' : 'bloqueada')
          })
        }}
      >
        Ejecutar
      </button>
      <span>{result}</span>
    </div>
  )
}

describe('useSensitiveOperationGuard', () => {
  it('permite la acción después de confirmar estado seguro', async () => {
    const action = vi.fn(async () => undefined)
    renderWithAuth(<GuardHarness action={action} />)

    await userEvent.click(screen.getByRole('button', { name: 'Ejecutar' }))

    expect(await screen.findByText('ejecutada')).toBeVisible()
    expect(action).toHaveBeenCalledOnce()
  })

  it('bloquea restricted y solicita reverificación', async () => {
    const action = vi.fn(async () => undefined)
    const requestReverification = vi.fn()
    const restricted = {
      ...testContinuousAuthStatus,
      risk_level: 'high' as const,
      authentication_level: 'restricted' as const,
    }
    renderWithAuth(<GuardHarness action={action} />, {
      continuousAuth: createContinuousAuthValue({
        status: restricted,
        riskLevel: 'high',
        authenticationLevel: 'restricted',
        refreshStatus: async () => restricted,
        requestReverification,
      }),
    })

    expect(screen.getByText('restringida')).toBeVisible()
    await userEvent.click(screen.getByRole('button', { name: 'Ejecutar' }))

    expect(await screen.findByText('bloqueada')).toBeVisible()
    expect(action).not.toHaveBeenCalled()
    expect(requestReverification).toHaveBeenCalledOnce()
  })

  it('no ejecuta automáticamente una acción al reverificar', async () => {
    const action = vi.fn(async () => undefined)
    const requestReverification = vi.fn()
    const restricted = {
      ...testContinuousAuthStatus,
      authentication_level: 'verification_required' as const,
    }
    renderWithAuth(<GuardHarness action={action} />, {
      continuousAuth: createContinuousAuthValue({
        status: restricted,
        authenticationLevel: 'verification_required',
        refreshStatus: async () => restricted,
        requestReverification,
      }),
    })

    await userEvent.click(screen.getByRole('button', { name: 'Ejecutar' }))

    expect(action).not.toHaveBeenCalled()
    expect(requestReverification).toHaveBeenCalledOnce()
  })
})
