import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { GateControlDocumentPanel } from '../components/GateControlDocumentPanel'
import type { GateCheckInCapabilities, GateCpvDocumentResponse } from '../types/gate-control'

vi.mock('../../logistics-permissions/hooks/useSensitiveActionGuard', () => ({
  useSensitiveActionGuard: () => ({ isBlocked: false, run: (fn: () => Promise<void>) => fn().then(() => true) }),
}))

vi.mock('../../logistics-permissions/logistics-permissions-map', () => ({
  LOGISTICS_PERMISSIONS: { gateControl: { issueCPV: 'gate:issue_cpv' } },
}))

function baseCaps(overrides: Partial<GateCheckInCapabilities> = {}): GateCheckInCapabilities {
  return {
    check_in_id: 'ci-1',
    can_view: true, can_resolve_appointment: false, can_create_check_in: false,
    can_create_walk_in: false, can_record_arrival: false, can_start_verification: false,
    can_manage_vehicle_inspection: false, can_manage_driver_inspection: false,
    can_manage_documents: false, can_manage_seal: false, can_capture_photo: false,
    can_view_sensitive_photo: false, can_manage_checks: false, can_request_exception: false,
    can_approve_exception: false, can_hold: false, can_request_supervisor: false,
    can_authorize: false, can_authorize_with_observations: false, can_deny: false,
    can_complete: false, can_preview_CPV: false, can_issue_CPV: false,
    can_download_CPV: false, can_request_correction: false, can_view_history: false,
    can_view_integrity: false, can_view_dock_preparation: false,
    ...overrides,
  }
}

const issuedDoc: GateCpvDocumentResponse = {
  document_instance_id: 'doc-1',
  check_in_id: 'ci-1',
  document_code: 'CPV-0001',
  status: 'ISSUED',
  issued_at: '2026-08-01T12:00:00Z',
  snapshot_hash: 'abc123def456',
  download_url: '/api/logistics/gate-check-ins/ci-1/document/pdf',
  expires_at: null,
}

describe('GateControlDocumentPanel', () => {
  it('shows issue button when no document and can_issue_CPV is true', () => {
    render(
      <GateControlDocumentPanel
        checkInId="ci-1"
        cpvDocument={null}
        capabilities={baseCaps({ can_issue_CPV: true })}
        onChanged={() => {}}
      />,
    )

    expect(screen.getByRole('button', { name: /Emitir CPV/i })).toBeInTheDocument()
  })

  it('shows empty state without issue button when can_issue_CPV is false', () => {
    render(
      <GateControlDocumentPanel
        checkInId="ci-1"
        cpvDocument={null}
        capabilities={baseCaps({ can_issue_CPV: false })}
        onChanged={() => {}}
      />,
    )

    expect(screen.queryByRole('button', { name: /Emitir CPV/i })).not.toBeInTheDocument()
    expect(screen.getByText(/Sin acta CPV/i)).toBeInTheDocument()
  })

  it('shows document_code and status when document exists', () => {
    render(
      <GateControlDocumentPanel
        checkInId="ci-1"
        cpvDocument={issuedDoc}
        capabilities={baseCaps({ can_download_CPV: true })}
        onChanged={() => {}}
      />,
    )

    expect(screen.getByText('CPV-0001')).toBeInTheDocument()
    expect(screen.getByText('ISSUED')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Descargar acta/i })).toBeInTheDocument()
  })

  it('shows snapshot_hash truncated', () => {
    render(
      <GateControlDocumentPanel
        checkInId="ci-1"
        cpvDocument={issuedDoc}
        capabilities={baseCaps()}
        onChanged={() => {}}
      />,
    )

    expect(screen.getByText('abc123def456')).toBeInTheDocument()
  })

  it('does not show fabricated fields (version, reprints, corrections_count, integrity_ok)', () => {
    render(
      <GateControlDocumentPanel
        checkInId="ci-1"
        cpvDocument={issuedDoc}
        capabilities={baseCaps()}
        onChanged={() => {}}
      />,
    )

    expect(screen.queryByText(/Versión/)).not.toBeInTheDocument()
    expect(screen.queryByText(/Reimpresiones/)).not.toBeInTheDocument()
    expect(screen.queryByText(/Correcciones/)).not.toBeInTheDocument()
    expect(screen.queryByText(/Integridad/)).not.toBeInTheDocument()
  })
})
