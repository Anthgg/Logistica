import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { VehicleVerificationDomainsGrid } from './VehicleVerificationDomainsGrid'
import type { VehicleVerification } from '../../types/vehicle-verifications'

function makeVerification(overrides: Partial<VehicleVerification> = {}): VehicleVerification {
  return {
    id: 'v1',
    vehicle_id: 'veh-1',
    vehicle_internal_code: 'COD-1',
    plate_number: 'ABC123',
    domain: 'REGISTRO_PROPIEDAD',
    domain_label: 'Identidad Registral',
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
    provenance_fields: [],
    evidences: [],
    conflicts_count: 0,
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
    ...overrides,
  }
}

describe('VehicleVerificationDomainsGrid', () => {
  it('renderiza todos los dominios normativos', () => {
    render(<VehicleVerificationDomainsGrid verifications={[]} />)
    expect(screen.getByText('Identidad Registral')).toBeInTheDocument()
    expect(screen.getByText('Revisión Técnica (CITV)')).toBeInTheDocument()
    expect(screen.getByText('SOAT Obligatorio')).toBeInTheDocument()
  })

  it('muestra "Pendiente" para dominios sin verificación', () => {
    render(<VehicleVerificationDomainsGrid verifications={[]} />)
    const pendientes = screen.getAllByText('Pendiente')
    expect(pendientes.length).toBeGreaterThan(0)
  })

  it('muestra resultado validado para dominio verificado', () => {
    const v = makeVerification()
    render(<VehicleVerificationDomainsGrid verifications={[v]} />)
    expect(screen.getAllByText('VALIDATED').length).toBeGreaterThan(0)
  })

  it('no muestra un único badge "Vehículo verificado"', () => {
    render(<VehicleVerificationDomainsGrid verifications={[makeVerification()]} />)
    expect(screen.queryByText(/Vehículo verificado/i)).toBeNull()
  })

  it('muestra contador de conflictos cuando existe', () => {
    const v = makeVerification({ conflicts_count: 2, domain: 'SOAT' })
    render(<VehicleVerificationDomainsGrid verifications={[v]} />)
    expect(screen.getByText(/2/, { selector: 'span' })).toBeInTheDocument()
  })

  it('llama a onRequestDomain al solicitar', () => {
    const onRequestDomain = vi.fn()
    render(
      <VehicleVerificationDomainsGrid
        verifications={[]}
        onRequestDomain={onRequestDomain}
        canRequest
      />,
    )
    const buttons = screen.getAllByText('Solicitar')
    buttons[0].click()
    expect(onRequestDomain).toHaveBeenCalled()
  })
})