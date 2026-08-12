import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { RequestVehicleVerificationDialog } from './RequestVehicleVerificationDialog'
import type { VehicleVerificationRequest } from '../../types/vehicle-verifications'

describe('RequestVehicleVerificationDialog', () => {
  const baseProps = {
    isOpen: true,
    isSubmitting: false,
    vehicleId: 'veh-1',
    plateNumber: 'ABC123',
    availableSources: [
      { source_type: 'SUNARP', source_name: 'SUNARP', method: 'AUTHORIZED_API', authorization_status: 'AUTHORIZED', available: true },
      { source_type: 'MTC', source_name: 'MTC', method: 'AUTHORIZED_API', authorization_status: 'AUTHORIZED', available: true },
    ] as const,
  }

  it('no renderiza cuando isOpen es false', () => {
    render(
      <RequestVehicleVerificationDialog
        {...baseProps}
        isOpen={false}
        onSubmit={vi.fn()}
        onClose={vi.fn()}
      />,
    )
    expect(screen.queryByText(/Solicitar Verificación Autorizada/)).toBeNull()
  })

  it('muestra fuentes disponibles', () => {
    render(
      <RequestVehicleVerificationDialog
        {...baseProps}
        onSubmit={vi.fn()}
        onClose={vi.fn()}
      />,
    )
    expect(screen.getByText('SUNARP')).toBeInTheDocument()
    expect(screen.getByText('MTC')).toBeInTheDocument()
  })

  it('describe los datos que serán consultados', () => {
    render(
      <RequestVehicleVerificationDialog
        {...baseProps}
        onSubmit={vi.fn()}
        onClose={vi.fn()}
      />,
    )
    expect(screen.getByText(/Datos que serán consultados/)).toBeInTheDocument()
  })

  it('no permite enviar sin motivo', async () => {
    const onSubmit = vi.fn<(data: VehicleVerificationRequest) => void>()
    render(
      <RequestVehicleVerificationDialog
        {...baseProps}
        onSubmit={onSubmit}
        onClose={vi.fn()}
      />,
    )
    const submitBtn = screen.getByRole('button', { name: /^Solicitar Verificación$/ })
    expect(submitBtn).toBeDisabled()
  })

  it('envía con motivo y dominio', async () => {
    const onSubmit = vi.fn<(data: VehicleVerificationRequest) => void>()
    const user = userEvent.setup()
    render(
      <RequestVehicleVerificationDialog
        {...baseProps}
        onSubmit={onSubmit}
        onClose={vi.fn()}
      />,
    )
    await user.type(screen.getByLabelText(/Motivo/), 'Verificación periódica')
    await user.click(screen.getByRole('button', { name: /^Solicitar Verificación$/ }))
    expect(onSubmit).toHaveBeenCalledOnce()
    const data = onSubmit.mock.calls[0][0]
    expect(data.reason).toBe('Verificación periódica')
    expect(data.vehicle_id).toBe('veh-1')
    expect(data.plate_number).toBe('ABC123')
  })

  it('advierte no ingresar URL, API keys, CAPTCHA, HTML', () => {
    render(
      <RequestVehicleVerificationDialog
        {...baseProps}
        onSubmit={vi.fn()}
        onClose={vi.fn()}
      />,
    )
    const warning = screen.getByText((content: string) =>
      content.includes('No incluyas') && content.includes('CAPTCHA') && content.includes('API keys'),
    )
    expect(warning).toBeInTheDocument()
  })
})
