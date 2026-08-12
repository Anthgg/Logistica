import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ApproveAssistedVehicleVerificationDialog } from './ApproveAssistedVehicleVerificationDialog'
import type { AssistedVehicleVerification } from '../../types/vehicle-verifications'

function makeAssisted(): AssistedVehicleVerification {
  return {
    id: 'a1',
    vehicle_id: 'veh-1',
    plate_number: 'ABC123',
    domain: 'REGISTRO_PROPIEDAD',
    source_type: 'SUNARP',
    official_reference_number: 'SUNARP-2026-99482',
    observation_timestamp: '2026-01-01T10:00:00Z',
    observed_plate: 'ABC123',
    observed_owner_name: 'Transportes Ejemplo SAC',
    observed_make_name: 'VOLVO',
    observed_model_name: 'FH16',
    observed_year: 2023,
    observed_status: 'VIGENTE',
    observed_expiration_date: '2027-01-01',
    result_status: 'VALIDATED',
    notes: 'Observación conforme',
    created_by_user_name: 'creator1',
    review_status: 'PENDING_APPROVAL',
    approved_by_user_name: null,
    approved_at: null,
    created_at: '2026-01-01T10:05:00Z',
  }
}

describe('ApproveAssistedVehicleVerificationDialog', () => {
  const baseProps = {
    isOpen: true,
    isSubmitting: false,
    verification: makeAssisted(),
    proposedConfidence: null,
    warnings: [],
    differences: [],
    canSelfApprove: true,
    onApprove: vi.fn(),
    onReject: vi.fn(),
    onClose: vi.fn(),
  }

  it('muestra creador, fecha y fuente', () => {
    render(<ApproveAssistedVehicleVerificationDialog {...baseProps} />)
    expect(screen.getByText('creator1')).toBeInTheDocument()
    expect(screen.getByText('SUNARP')).toBeInTheDocument()
  })

  it('enmascara propietario observado', () => {
    render(<ApproveAssistedVehicleVerificationDialog {...baseProps} />)
    expect(screen.queryByText('Transportes Ejemplo SAC')).toBeNull()
  })

  it('no muestra JSON completo, API key ni endpoint', () => {
    render(<ApproveAssistedVehicleVerificationDialog {...baseProps} />)
    expect(screen.queryByText(/api[_-]?key/i)).toBeNull()
    expect(screen.queryByText(/endpoint/i)).toBeNull()
  })

  it('bloquea aprobación cuando canSelfApprove es false', () => {
    render(<ApproveAssistedVehicleVerificationDialog {...baseProps} canSelfApprove={false} />)
    expect(screen.getByText(/prohíbe aprobar tu propia validación/i)).toBeInTheDocument()
  })

  it('muestra advertencias cuando existen', () => {
    render(
      <ApproveAssistedVehicleVerificationDialog
        {...baseProps}
        warnings={['Conflicto de marca detectado']}
      />,
    )
    expect(screen.getByText('Conflicto de marca detectado')).toBeInTheDocument()
  })

  it('muestra confianza propuesta por el backend', () => {
    render(
      <ApproveAssistedVehicleVerificationDialog
        {...baseProps}
        proposedConfidence={0.87}
      />,
    )
    expect(screen.getByText(/87%/)).toBeInTheDocument()
  })
})