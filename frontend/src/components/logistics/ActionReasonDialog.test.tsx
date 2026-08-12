import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ActionReasonDialog } from './ActionReasonDialog'

function renderDialog(overrides: Partial<React.ComponentProps<typeof ActionReasonDialog>> = {}) {
  const props: React.ComponentProps<typeof ActionReasonDialog> = {
    isOpen: true,
    title: 'Revocar rol',
    resourceLabel: 'Usuario: Juan Pérez',
    consequence: 'El usuario perderá el rol inmediatamente.',
    confirmLabel: 'Revocar',
    onConfirm: () => undefined,
    onCancel: () => undefined,
    ...overrides,
  }
  return render(<ActionReasonDialog {...props} />)
}

describe('ActionReasonDialog - motivo obligatorio', () => {
  it('no renderiza cuando isOpen es false', () => {
    renderDialog({ isOpen: false })
    expect(screen.queryByText('Revocar rol')).not.toBeInTheDocument()
  })

  it('muestra título, recurso y consecuencia', () => {
    renderDialog()
    expect(screen.getByText('Revocar rol')).toBeInTheDocument()
    expect(screen.getByText('Usuario: Juan Pérez')).toBeInTheDocument()
    expect(screen.getByText('El usuario perderá el rol inmediatamente.')).toBeInTheDocument()
  })

  it('deshabilita confirmar con motivo vacío', () => {
    renderDialog()
    const confirm = screen.getByRole('button', { name: 'Revocar' })
    expect(confirm).toBeDisabled()
  })

  it('habilita confirmar al ingresar un motivo válido', async () => {
    const user = userEvent.setup()
    renderDialog()
    const input = screen.getByLabelText('Motivo')
    const confirm = screen.getByRole('button', { name: 'Revocar' })
    await user.type(input, 'Cambio de puesto')
    expect(confirm).toBeEnabled()
  })

  it('muestra error de validación si se intenta confirmar vacío tras tocar', async () => {
    const user = userEvent.setup()
    renderDialog()
    const input = screen.getByLabelText('Motivo')
    await user.click(input)
    await user.tab()
    expect(await screen.findByText('Debes ingresar un motivo para continuar.')).toBeInTheDocument()
  })

  it('llama onConfirm con el motivo recortado', async () => {
    const user = userEvent.setup()
    const onConfirm = vi.fn()
    renderDialog({ onConfirm })
    await user.type(screen.getByLabelText('Motivo'), '  Motivo válido  ')
    await user.click(screen.getByRole('button', { name: 'Revocar' }))
    expect(onConfirm).toHaveBeenCalledWith('Motivo válido')
  })

  it('muestra errorMessage del backend', () => {
    renderDialog({ errorMessage: 'El backend rechazó la operación.' })
    expect(screen.getByText('El backend rechazó la operación.')).toBeInTheDocument()
  })

  it('cancela con Escape', async () => {
    const user = userEvent.setup()
    const onCancel = vi.fn()
    renderDialog({ onCancel })
    await user.keyboard('{Escape}')
    expect(onCancel).toHaveBeenCalled()
  })
})