import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import {
  createContinuousAuthValue,
  renderWithAuth,
  testContinuousAuthStatus,
} from '../../../test/test-utils'
import { ContinuousAuthIndicator } from './ContinuousAuthIndicator'
import { ReverificationDialog } from './ReverificationDialog'
import { RiskLevelBadge } from './RiskLevelBadge'

describe('componentes de autenticación continua', () => {
  it.each([
    ['low', 'Riesgo bajo'],
    ['medium', 'Riesgo moderado'],
    ['high', 'Riesgo alto'],
    ['critical', 'Riesgo crítico'],
  ] as const)('muestra %s con texto además de color', (level, label) => {
    renderWithAuth(<RiskLevelBadge level={level} />)
    expect(screen.getByText(label)).toBeVisible()
  })

  it('el indicador anuncia el estado y navega a seguridad', () => {
    renderWithAuth(<ContinuousAuthIndicator />, {
      continuousAuth: createContinuousAuthValue(),
    })

    const link = screen.getByRole('link', {
      name: /abrir estado de seguridad/i,
    })
    expect(link).toHaveAttribute('href', '/security/continuous-auth')
    expect(screen.getAllByText(/riesgo bajo/i).length).toBeGreaterThan(0)
  })

  it('muestra sin conexión sin convertir el fallo en riesgo crítico', () => {
    renderWithAuth(<ContinuousAuthIndicator />, {
      continuousAuth: createContinuousAuthValue({
        status: null,
        riskLevel: 'unknown',
        error: 'Sin conexión',
      }),
    })

    expect(
      screen.getByRole('link', { name: /sin conexión/i }),
    ).toBeVisible()
    expect(screen.queryByText('Riesgo crítico')).not.toBeInTheDocument()
  })

  it('el diálogo accesible limpia la contraseña después de fallar', async () => {
    const reverify = vi.fn(async () => {
      throw new Error('fallo')
    })
    renderWithAuth(<ReverificationDialog />, {
      continuousAuth: createContinuousAuthValue({
        status: {
          ...testContinuousAuthStatus,
          risk_level: 'high',
          authentication_level: 'verification_required',
        },
        riskLevel: 'high',
        authenticationLevel: 'verification_required',
        isReverificationOpen: true,
        reverify,
      }),
    })
    const user = userEvent.setup()
    const input = screen.getByLabelText('Contraseña actual')

    expect(screen.getByRole('dialog')).toHaveAttribute(
      'aria-modal',
      'true',
    )
    await user.type(input, 'secreto')
    await user.click(
      screen.getByRole('button', { name: 'Verificar identidad' }),
    )

    expect(reverify).toHaveBeenCalledWith('secreto')
    expect(input).toHaveValue('')
  })
})
