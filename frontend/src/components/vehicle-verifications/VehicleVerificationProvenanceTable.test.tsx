import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { VehicleVerificationProvenanceTable } from './VehicleVerificationProvenanceTable'
import type { VehicleVerificationFieldProvenance } from '../../types/vehicle-verifications'

function makeField(overrides: Partial<VehicleVerificationFieldProvenance> = {}): VehicleVerificationFieldProvenance {
  return {
    field_name: 'make',
    field_label: 'Marca',
    master_value: 'VOLVO',
    verified_value: 'VOLVO',
    source_type: 'SUNARP',
    source_name: 'SUNARP',
    verification_date: '2026-01-01T00:00:00Z',
    confidence_score: 0.95,
    is_selected: false,
    has_conflict: false,
    ...overrides,
  }
}

describe('VehicleVerificationProvenanceTable', () => {
  it('muestra mensaje vacío cuando no hay campos', () => {
    render(<VehicleVerificationProvenanceTable provenanceFields={[]} />)
    expect(screen.getByText(/Sin desglose de procedencia/)).toBeInTheDocument()
  })

  it('renderiza campo, valor maestro y verificado', () => {
    render(<VehicleVerificationProvenanceTable provenanceFields={[makeField()]} />)
    expect(screen.getByText('Marca')).toBeInTheDocument()
    expect(screen.getAllByText('VOLVO').length).toBe(2)
  })

  it('muestra "Conflicto" cuando has_conflict es true', () => {
    render(<VehicleVerificationProvenanceTable provenanceFields={[makeField({ has_conflict: true, verified_value: 'SCANIA' })]} />)
    expect(screen.getByText(/Conflicto/)).toBeInTheDocument()
  })

  it('muestra "Coincide" cuando no hay conflicto', () => {
    render(<VehicleVerificationProvenanceTable provenanceFields={[makeField()]} />)
    expect(screen.getByText(/Coincide/)).toBeInTheDocument()
  })

  it('atribuye campo a la fuente correcta, no a una sola fuente', () => {
    const fields = [
      makeField({ field_name: 'make', field_label: 'Marca', source_type: 'SUNARP', source_name: 'SUNARP' }),
      makeField({ field_name: 'soat_status', field_label: 'Estado SOAT', source_type: 'SBS', source_name: 'SBS' }),
    ]
    render(<VehicleVerificationProvenanceTable provenanceFields={fields} />)
    expect(screen.getByText('SUNARP')).toBeInTheDocument()
    expect(screen.getByText('SBS')).toBeInTheDocument()
  })
})