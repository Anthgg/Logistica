import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import {
  createAuthValue,
  renderWithAuth,
  testAuthResponse,
} from '../test/test-utils'
import { RegisterPage } from './RegisterPage'

function renderRegister(register = vi.fn(async () => testAuthResponse)) {
  const auth = createAuthValue({ register })
  renderWithAuth(
    <Routes>
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/login" element={<div>Acceso disponible</div>} />
    </Routes>,
    { auth, initialEntries: ['/register'] },
  )
  return register
}

async function fillValidForm(user: ReturnType<typeof userEvent.setup>) {
  await user.type(screen.getByLabelText('Nombre completo'), 'Usuario Prueba')
  await user.type(
    screen.getByLabelText('Correo electrónico'),
    'USUARIO@EXAMPLE.COM',
  )
  await user.type(screen.getByLabelText(/^Contraseña$/), 'ClaveSegura2026')
  await user.type(
    screen.getByLabelText('Confirmar contraseña'),
    'ClaveSegura2026',
  )
}

describe('RegisterPage', () => {
  it('exige aceptar los términos', async () => {
    // delay: null → eventos instantáneos, evita timeout en suite completa bajo carga
    const user = userEvent.setup({ delay: null })
    const register = renderRegister()
    await fillValidForm(user)

    await user.click(screen.getByRole('button', { name: 'Crear cuenta' }))

    expect(
      screen.getByText('Debes aceptar los términos para continuar.'),
    ).toBeInTheDocument()
    expect(register).not.toHaveBeenCalled()
  })

  it('valida que ambas contraseñas coincidan', async () => {
    const user = userEvent.setup({ delay: null })
    const register = renderRegister()
    await user.type(screen.getByLabelText('Nombre completo'), 'Usuario Prueba')
    await user.type(
      screen.getByLabelText('Correo electrónico'),
      'usuario@example.com',
    )
    await user.type(screen.getByLabelText(/^Contraseña$/), 'ClaveSegura2026')
    await user.type(
      screen.getByLabelText('Confirmar contraseña'),
      'OtraClave2026',
    )
    await user.click(
      screen.getByLabelText(/Acepto los términos/i),
    )
    await user.click(screen.getByRole('button', { name: 'Crear cuenta' }))

    expect(screen.getByText('Las contraseñas no coinciden.')).toBeInTheDocument()
    expect(register).not.toHaveBeenCalled()
  })

  it('muestra los requisitos de contraseña', () => {
    renderRegister()

    expect(screen.getByText('12 caracteres')).toBeInTheDocument()
    expect(screen.getByText('Una mayúscula')).toBeInTheDocument()
    expect(screen.getByText('Una minúscula')).toBeInTheDocument()
    expect(screen.getByText('Un número')).toBeInTheDocument()
  })

  it('envía datos normalizados y redirige a login', async () => {
    const user = userEvent.setup({ delay: null })
    const register = renderRegister()
    await fillValidForm(user)
    await user.click(screen.getByLabelText(/Acepto los términos/i))
    await user.click(screen.getByRole('button', { name: 'Crear cuenta' }))

    expect(register).toHaveBeenCalledWith({
      full_name: 'Usuario Prueba',
      email: 'usuario@example.com',
      password: 'ClaveSegura2026',
      password_confirmation: 'ClaveSegura2026',
      accept_terms: true,
    })
    expect(await screen.findByText('Acceso disponible')).toBeInTheDocument()
  })

  it('no envía un formulario vacío', async () => {
    const user = userEvent.setup({ delay: null })
    const register = renderRegister()
    await user.click(screen.getByRole('button', { name: 'Crear cuenta' }))

    expect(register).not.toHaveBeenCalled()
    expect(screen.getByText('Ingresa tu nombre completo.')).toBeInTheDocument()
    expect(screen.getByText('Ingresa tu correo.')).toBeInTheDocument()
  })
})

