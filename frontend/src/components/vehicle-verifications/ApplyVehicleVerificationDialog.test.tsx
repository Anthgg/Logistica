import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ApplyVehicleVerificationDialog } from './ApplyVehicleVerificationDialog'
import type { VehicleVerification } from '../../types/vehicle-verifications'

function makeVerification(): VehicleVerification {
  return {
    id: 'v1',
    vehicle_id: 'veh-1',
    vehicle_internal_code: 'COD-1',
    plate_number: 'ABC123',
    domain: 'CARACTERISTICAS',
    domain_label: 'Ficha Físico-Técnica',
    status: 'COMPLETED',
    result_status: 'VALIDATED',
    source_type: 'SUNARP',
    source_name: 'SUNARP',
    method: 'AUTHORIZED_API',
    source_date: '2026-01-01T00:00:00Z',
    requested_at: '2026-01-01T00:00:00Z',
    completed_at: '2026-01-01T00:05:00Z',
    expires_at: '2027-01-01T00:00:00Z',
    freshness: 'FRESH',
    days_until_expiration: 300,
    confidence_score: 0.95,
    provenance_fields: [
      { field_name: 'make', field_label: 'Marca', master_value: 'VOLVO', verified_value: 'SCANIA', source_type: 'SUNARP', source_name: 'SUNARP', verification_date: '2026-01-01T00:00:00Z', confidence_score: 0.95, is_selected: false, has_conflict: true },
      { field_name: 'model', field_label: 'Modelo', master_value: 'FH', verified_value: 'FH', source_type: 'SUNARP', source_name: 'SUNARP', verification_date: '2026-01-01T00:00:00Z', confidence_score: 0.9, is_selected: false, has_conflict: false },
    ],
    evidences: [],
    conflicts_count: 1,
    warnings: [],
    requested_by_user_name: 'tester',
    capabilities: {
      can_view_verifications: true,
      can_request_verification: true,
      can_retry_verification: true,
      can_revoke_verification: true,
      can_view_sensitive_result: true,
      can_create_assisted_verification: true,
      can_approve_assisted_verification: true,
      can_apply_result: true,
      can_resolve_conflict: true,
      can_view_evidence: true,
      can_manage_evidence: true,
      can_view_sources: true,
      can_manage_sources: true,
      can_view_requirements: true,
      can_manage_requirements: true,
      can_activate_requirements: true,
      can_view_review_tasks: true,
    },
    history: [],
  }
}

describe('ApplyVehicleVerificationDialog', () => {
  const baseProps = {
    isOpen: true,
    isSubmitting: false,
    verification: makeVerification(),
    currentVehicleVersion: 2,
    onApply: vi.fn<(selectedFields: string[], reason: string, expectedVersion: number) => void>(),
    onClose: vi.fn(),
  }

  it('muestra lista de campos verificados con valores actual y verificado', () => {
    render(<ApplyVehicleVerificationDialog {...baseProps} />)
    expect(screen.getByText('Marca')).toBeInTheDocument()
    expect(screen.getByText('Modelo')).toBeInTheDocument()
    expect(screen.getByText('VOLVO')).toBeInTheDocument()
    expect(screen.getByText('SCANIA')).toBeInTheDocument()
  })

  it('no selecciona ningún campo por defecto', () => {
    render(<ApplyVehicleVerificationDialog {...baseProps} />)
    const checkboxes = screen.getAllByRole('checkbox')
    checkboxes.forEach((cb) => expect(cb).not.toBeChecked())
  })

  it('requiere motivo para aplicar', () => {
    render(<ApplyVehicleVerificationDialog {...baseProps} />)
    const btn = screen.getByRole('button', { name: /Aplicar.*Step-Up/ })
    expect(btn).toBeDisabled()
  })

  it('advierte que el cambio de placa NO se hace aquí', () => {
    render(<ApplyVehicleVerificationDialog {...baseProps} />)
    expect(screen.getByText(/cambio de placa.*NO se realiza desde este diálogo/i)).toBeInTheDocument()
  })

  it('indica que creará una nueva versión', () => {
    render(<ApplyVehicleVerificationDialog {...baseProps} />)
    expect(screen.getByText(/nueva versión inmutable/i)).toBeInTheDocument()
  })
})