import { screen } from '@testing-library/react'
import { Route, Routes } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import {
  createAuthValue,
  renderWithAuth,
  testUser,
} from '../../test/test-utils'
import type { UserRole } from '../../types/user'
import { RoleRoute } from './RoleRoute'

function renderRole(role: UserRole) {
  renderWithAuth(
    <Routes>
      <Route element={<RoleRoute roles={['admin', 'supervisor']} />}>
        <Route path="/research/sessions" element={<h1>Sesiones permitidas</h1>} />
      </Route>
      <Route path="/unauthorized" element={<h1>Sin autorización</h1>} />
    </Routes>,
    {
      auth: createAuthValue({
        user: { ...testUser, role },
        isAuthenticated: true,
      }),
      initialEntries: ['/research/sessions'],
    },
  )
}

describe('RoleRoute', () => {
  it('permite sesiones de investigación a supervisor', () => {
    renderRole('supervisor')
    expect(screen.getByText('Sesiones permitidas')).toBeInTheDocument()
  })

  it('rechaza roles fuera de la lista', () => {
    renderRole('dispatcher')
    expect(screen.getByText('Sin autorización')).toBeInTheDocument()
  })
})
