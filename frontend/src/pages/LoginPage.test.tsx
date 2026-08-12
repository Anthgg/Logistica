import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { ApiRequestError } from '../types/api'
import {
  createAuthValue,
  renderWithAuth,
  testAuthResponse,
} from '../test/test-utils'
import { LoginPage } from './LoginPage'

function renderLogin(login = vi.fn(async () => testAuthResponse)) {
  const auth = createAuthValue({ login })
  const result = renderWithAuth(
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/profile" element={<div>Perfil cargado</div>} />
      <Route path="/sessions" element={<div>Sesiones cargadas</div>} />
    </Routes>,
    { auth, initialEntries: ['/login'] },
  )
  return { ...result, login }
}

describe('LoginPage', () => {
  it('muestra los campos y controles de acceso', () => {
    renderLogin()

    expect(screen.getByLabelText('Correo electrónico')).toBeInTheDocument()
    expect(screen.getByLabelText('Contraseña')).toBeInTheDocument()
    expect(screen.getByLabelText('Mantener mi sesión')).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: 'Iniciar sesión' }),
    ).toBeInTheDocument()
  })

  it('normaliza el correo antes de enviarlo', async () => {
    const user = userEvent.setup()
    const { login } = renderLogin()

    await user.type(
      screen.getByLabelText('Correo electrónico'),
      '  USUARIO@Example.COM  ',
    )
    await user.type(screen.getByLabelText('Contraseña'), 'ClaveSegura2026')
    await user.click(screen.getByRole('button', { name: 'Iniciar sesión' }))

    expect(login).toHaveBeenCalledWith({
      email: 'usuario@example.com',
      password: 'ClaveSegura2026',
      remember_me: false,
    })
  })

  it('redirige al perfil después de un login exitoso', async () => {
    const user = userEvent.setup()
    renderLogin()

    await user.type(
      screen.getByLabelText('Correo electrónico'),
      'usuario@example.com',
    )
    await user.type(screen.getByLabelText('Contraseña'), 'ClaveSegura2026')
    await user.click(screen.getByRole('button', { name: 'Iniciar sesión' }))

    expect(await screen.findByText('Perfil cargado')).toBeInTheDocument()
  })

  it('regresa a la ruta privada solicitada', async () => {
    const user = userEvent.setup()
    const auth = createAuthValue({
      login: vi.fn(async () => testAuthResponse),
    })
    renderWithAuth(
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/sessions" element={<div>Sesiones cargadas</div>} />
      </Routes>,
      {
        auth,
        initialEntries: [
          {
            pathname: '/login',
            state: { from: { pathname: '/sessions' } },
          },
        ],
      },
    )

    await user.type(
      screen.getByLabelText('Correo electrónico'),
      'usuario@example.com',
    )
    await user.type(screen.getByLabelText('Contraseña'), 'ClaveSegura2026')
    await user.click(screen.getByRole('button', { name: 'Iniciar sesión' }))

    expect(await screen.findByText('Sesiones cargadas')).toBeInTheDocument()
  })

  it('muestra el mensaje de credenciales incorrectas', async () => {
    const user = userEvent.setup()
    const login = vi.fn(async () => {
      throw new ApiRequestError('Correo o contraseña incorrectos.', {
        code: 'INVALID_CREDENTIALS',
        status: 401,
      })
    })
    renderLogin(login)

    await user.type(
      screen.getByLabelText('Correo electrónico'),
      'usuario@example.com',
    )
    await user.type(screen.getByLabelText('Contraseña'), 'ClaveIncorrecta2026')
    await user.click(screen.getByRole('button', { name: 'Iniciar sesión' }))

    expect(
      await screen.findByText('Correo o contraseña incorrectos.'),
    ).toBeInTheDocument()
  })

  it('presenta el fallo de red como indisponibilidad del servicio', async () => {
    const user = userEvent.setup()
    const login = vi.fn(async () => {
      throw new ApiRequestError('Network', { code: 'NETWORK_ERROR' })
    })
    renderLogin(login)

    await user.type(
      screen.getByLabelText('Correo electrónico'),
      'usuario@example.com',
    )
    await user.type(screen.getByLabelText('Contraseña'), 'ClaveSegura2026')
    await user.click(screen.getByRole('button', { name: 'Iniciar sesión' }))

    expect(
      await screen.findByText(/servicio no está disponible/i),
    ).toBeInTheDocument()
    await waitFor(() => expect(login).toHaveBeenCalledOnce())
  })

  it('permite mostrar y ocultar la contraseña', async () => {
    const user = userEvent.setup()
    renderLogin()
    const passwordInput = screen.getByLabelText('Contraseña')

    expect(passwordInput).toHaveAttribute('type', 'password')
    await user.click(screen.getByRole('button', { name: 'Mostrar contraseña' }))
    expect(passwordInput).toHaveAttribute('type', 'text')
  })
})
