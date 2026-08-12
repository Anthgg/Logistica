import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import {
  createAuthValue,
  renderWithAuth,
  testSession,
  testUser,
} from '../test/test-utils'
import { SecurityPage } from './SecurityPage'

function renderSecurity(options: {
  logoutAll?: ReturnType<typeof vi.fn<() => Promise<void>>>
  changePassword?: ReturnType<
    typeof vi.fn<
      () => Promise<{
        success: boolean
        message: string
        revoked_sessions: number | null
      }>
    >
  >
} = {}) {
  const logoutAll = options.logoutAll ?? vi.fn(async () => undefined)
  const changePassword =
    options.changePassword ??
    vi.fn(async () => ({
      success: true,
      message: 'Contraseña actualizada.',
      revoked_sessions: 1,
    }))
  const auth = createAuthValue({
    user: testUser,
    currentSession: testSession,
    isAuthenticated: true,
    logoutAll,
    changePassword,
  })
  renderWithAuth(
    <Routes>
      <Route path="/change-password" element={<SecurityPage />} />
      <Route path="/login" element={<div>Inicio de sesión</div>} />
    </Routes>,
    { auth, initialEntries: ['/change-password'] },
  )
  return { logoutAll, changePassword }
}

describe('SecurityPage', () => {
  it('valida la confirmación de la nueva contraseña', async () => {
    const user = userEvent.setup()
    const { changePassword } = renderSecurity()

    await user.type(
      screen.getByLabelText('Contraseña actual'),
      'ClaveAnterior2025',
    )
    await user.type(
      screen.getByLabelText('Nueva contraseña'),
      'ClaveNueva2026',
    )
    await user.type(
      screen.getByLabelText('Confirmar nueva contraseña'),
      'ClaveDistinta2026',
    )
    await user.click(
      screen.getByRole('button', { name: 'Actualizar contraseña' }),
    )

    expect(screen.getByText('Las contraseñas no coinciden.')).toBeInTheDocument()
    expect(changePassword).not.toHaveBeenCalled()
  })

  it('envía el cambio y elimina contraseñas del formulario', async () => {
    const user = userEvent.setup()
    const { changePassword } = renderSecurity()
    const current = screen.getByLabelText('Contraseña actual')
    const next = screen.getByLabelText('Nueva contraseña')
    const confirmation = screen.getByLabelText(
      'Confirmar nueva contraseña',
    )

    await user.type(current, 'ClaveAnterior2025')
    await user.type(next, 'ClaveNueva2026')
    await user.type(confirmation, 'ClaveNueva2026')
    await user.click(
      screen.getByRole('button', { name: 'Actualizar contraseña' }),
    )

    expect(changePassword).toHaveBeenCalledWith({
      current_password: 'ClaveAnterior2025',
      new_password: 'ClaveNueva2026',
      new_password_confirmation: 'ClaveNueva2026',
      logout_other_sessions: true,
    })
    expect(await screen.findByText('Contraseña actualizada.')).toBeInTheDocument()
    expect(current).toHaveValue('')
    expect(next).toHaveValue('')
    expect(confirmation).toHaveValue('')
  })

  it('confirma logout-all y limpia la autenticación mediante contexto', async () => {
    const user = userEvent.setup()
    const { logoutAll } = renderSecurity()

    await user.click(
      screen.getByRole('button', { name: 'Cerrar todas las sesiones' }),
    )
    const dialog = screen.getByRole('alertdialog', {
      name: '¿Cerrar todas las sesiones?',
    })
    expect(logoutAll).not.toHaveBeenCalled()

    await user.click(
      within(dialog).getByRole('button', { name: 'Cerrar todas' }),
    )

    expect(logoutAll).toHaveBeenCalledOnce()
    expect(await screen.findByText('Inicio de sesión')).toBeInTheDocument()
  })
})
