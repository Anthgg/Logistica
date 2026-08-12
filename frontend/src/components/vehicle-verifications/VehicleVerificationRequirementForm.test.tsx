import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { VehicleVerificationRequirementForm } from './VehicleVerificationRequirementForm'
import type { VehicleVerificationRequirement } from '../../types/vehicle-verifications'

describe('VehicleVerificationRequirementForm', () => {
  it('crea requisito con datos mínimos', async () => {
    const onSubmit = vi.fn()
    const user = userEvent.setup()
    render(<VehicleVerificationRequirementForm onSubmit={onSubmit} />)

    await user.type(screen.getByLabelText(/Tipo de vehículo/), 'CAMION')
    await user.click(screen.getByRole('button', { name: /Crear Requisito/ }))

    expect(onSubmit).toHaveBeenCalledOnce()
    const data = onSubmit.mock.calls[0][0]
    expect(data.vehicle_type).toBe('CAMION')
    expect(data.domain).toBe('REGISTRO_PROPIEDAD')
    expect(data.is_mandatory).toBe(true)
  })

  it('bloquea edición cuando el requisito inicial está ACTIVE', () => {
    const active: VehicleVerificationRequirement = {
      id: 'r1',
      vehicle_type: 'CAMION',
      body_type: null,
      ownership_type: null,
      carrier_category: null,
      domain: 'SOAT',
      preferred_source: 'SBS',
      is_mandatory: true,
      is_blocking: false,
      max_age_days: 365,
      warning_days: 30,
      min_confidence_score: 0.8,
      allow_assisted_validation: true,
      evidence_required: false,
      status: 'ACTIVE',
      created_at: '2026-01-01T00:00:00Z',
    }
    render(<VehicleVerificationRequirementForm initial={active} onSubmit={vi.fn()} />)
    expect(screen.getByText(/está ACTIVE/)).toBeInTheDocument()
    expect(screen.getByRole('button')).toBeDisabled()
  })

  it('permite editar cuando el requisito está DRAFT', () => {
    const draft: VehicleVerificationRequirement = {
      id: 'r1',
      vehicle_type: 'CAMION',
      body_type: null,
      ownership_type: null,
      carrier_category: null,
      domain: 'SOAT',
      preferred_source: 'SBS',
      is_mandatory: true,
      is_blocking: false,
      max_age_days: 365,
      warning_days: 30,
      min_confidence_score: 0.8,
      allow_assisted_validation: true,
      evidence_required: false,
      status: 'DRAFT',
      created_at: '2026-01-01T00:00:00Z',
    }
    render(<VehicleVerificationRequirementForm initial={draft} onSubmit={vi.fn()} />)
    expect(screen.queryByText(/está ACTIVE/)).toBeNull()
    expect(screen.getByRole('button', { name: /Guardar Cambios/ })).not.toBeDisabled()
  })

  it('no codifica requisitos legales en el formulario', () => {
    render(<VehicleVerificationRequirementForm onSubmit={vi.fn()} />)
    expect(screen.getByText(/backend valida y activa/i)).toBeInTheDocument()
  })
})