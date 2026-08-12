import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { getSessions, revokeSession } from '../api/session-api'
import {
  createAuthValue,
  renderWithAuth,
  testSession,
  testUser,
} from '../test/test-utils'
import type { SessionSummary } from '../types/session'
import { SessionsPage } from './SessionsPage'

vi.mock('../api/session-api', () => ({
  getSessions: vi.fn(),
  revokeSession: vi.fn(),
}))

const currentSession: SessionSummary = {
  id: testSession.id,
  device_name: 'Equipo actual',
  browser: 'Chrome',
  operating_system: 'Windows',
  device_type: 'desktop',
  ip_address: '192.168.1.44',
  created_at: '2026-07-20T10:00:00Z',
  last_activity_at: '2026-07-23T10:00:00Z',
  expires_at: '2026-08-20T10:00:00Z',
  is_current: true,
}

const otherSession: SessionSummary = {
  ...currentSession,
  id: 'f7e105bb-23f8-4a31-9618-c0e96b286739',
  device_name: 'Teléfono personal',
  browser: 'Safari',
  operating_system: 'iOS',
  device_type: 'mobile',
  ip_address: '10.1.2.3',
  is_current: false,
}

function renderSessions(overrides = {}) {
  const auth = createAuthValue({
    user: testUser,
    currentSession: testSession,
    isAuthenticated: true,
    ...overrides,
  })
  return renderWithAuth(
    <Routes>
      <Route path="/sessions" element={<SessionsPage />} />
      <Route path="/login" element={<div>Pantalla de acceso</div>} />
    </Routes>,
    { auth, initialEntries: ['/sessions'] },
  )
}

describe('SessionsPage', () => {
  beforeEach(() => {
    vi.mocked(getSessions).mockReset()
    vi.mocked(revokeSession).mockReset()
    vi.mocked(getSessions).mockResolvedValue({
      success: true,
      sessions: [currentSession, otherSession],
    })
    vi.mocked(revokeSession).mockResolvedValue({
      success: true,
      message: 'Revocada',
      revoked_sessions: 1,
    })
  })

  it('carga las sesiones e identifica la actual', async () => {
    renderSessions()

    // The current session card shows the browser name
    expect(await screen.findByText('Chrome')).toBeInTheDocument()
    const safariEls = screen.getAllByText('Safari')
    expect(safariEls.length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText('Sesión actual')).toBeInTheDocument()
    expect(screen.getByText('192.168.***.***')).toBeInTheDocument()
  })

  it('pide confirmación antes de revocar una sesión', async () => {
    const user = userEvent.setup()
    renderSessions()
    // Wait for the other session row to appear (Safari appears in both desktop and mobile views)
    await screen.findAllByText('Safari')
    // Find the revoke button in the row (aria-label="Revocar sesión")
    const revokeButton = screen.getByLabelText('Revocar sesión')

    await user.click(revokeButton)

    expect(
      screen.getByRole('alertdialog', { name: '¿Revocar esta sesión?' }),
    ).toBeInTheDocument()
    expect(revokeSession).not.toHaveBeenCalled()
  })

  it('revoca únicamente un identificador obtenido del listado', async () => {
    const user = userEvent.setup()
    renderSessions()
    await screen.findAllByText('Safari')

    const revokeButton = screen.getByLabelText('Revocar sesión')
    await user.click(revokeButton)

    const dialog = screen.getByRole('alertdialog')
    await user.click(
      within(dialog).getByRole('button', { name: 'Revocar sesión' }),
    )

    expect(revokeSession).toHaveBeenCalledWith(otherSession.id)
    expect(await screen.findByText(/revocada correctamente/i))
      .toBeInTheDocument()
    expect(screen.queryByText('Safari')).not.toBeInTheDocument()
  })

  it('limpia el contexto si se revoca la sesión actual', async () => {
    const user = userEvent.setup()
    const invalidateSession = vi.fn()
    renderSessions({ invalidateSession })
    await screen.findByText('Chrome')
    // Click "Cerrar sesión" on the current session card
    const closeButton = screen.getByRole('button', { name: 'Cerrar sesión' })
    await user.click(closeButton)

    await user.click(
      within(screen.getByRole('alertdialog')).getByRole('button', {
        name: 'Cerrar sesión',
      }),
    )

    expect(revokeSession).toHaveBeenCalledWith(currentSession.id)
    expect(invalidateSession).toHaveBeenCalledWith('Esta sesión fue cerrada.')
    expect(await screen.findByText('Pantalla de acceso')).toBeInTheDocument()
  })

  it('muestra un estado vacío sin inventar sesiones', async () => {
    vi.mocked(getSessions).mockResolvedValue({
      success: true,
      sessions: [],
    })
    renderSessions()

    expect(
      await screen.findByText('No hay otros dispositivos conectados'),
    ).toBeInTheDocument()
  })

  it('permite cerrar todas las sesiones desde el listado', async () => {
    const user = userEvent.setup()
    const logoutAll = vi.fn(async () => undefined)
    renderSessions({ logoutAll })
    await screen.findByText('Chrome')

    await user.click(
      screen.getByRole('button', { name: 'Cerrar otras sesiones' }),
    )
    await user.click(
      within(screen.getByRole('alertdialog')).getByRole('button', {
        name: 'Cerrar otras sesiones',
      }),
    )

    expect(logoutAll).toHaveBeenCalledOnce()
    expect(await screen.findByText('Pantalla de acceso')).toBeInTheDocument()
  })
})