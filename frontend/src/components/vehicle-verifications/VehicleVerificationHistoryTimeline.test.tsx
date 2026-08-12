import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { VehicleVerificationHistoryTimeline } from './VehicleVerificationHistoryTimeline'
import type { VehicleVerificationHistoryEvent } from '../../types/vehicle-verifications'

function makeEvent(overrides: Partial<VehicleVerificationHistoryEvent> = {}): VehicleVerificationHistoryEvent {
  return {
    id: 'e1',
    event_type: 'COMPLETED',
    user_name: 'analyst1',
    source_name: 'SUNARP',
    domain_label: 'Identidad Registral',
    result_status: 'VALIDATED',
    reason: null,
    vehicle_version: null,
    correlation_id_prefix: 'corr-abc',
    created_at: '2026-01-01T12:00:00Z',
    ...overrides,
  }
}

describe('VehicleVerificationHistoryTimeline', () => {
  it('muestra mensaje vacío cuando no hay eventos', () => {
    render(<VehicleVerificationHistoryTimeline history={[]} />)
    expect(screen.getByText(/Sin eventos de historial/)).toBeInTheDocument()
  })

  it('renderiza evento COMPLETED', () => {
    render(<VehicleVerificationHistoryTimeline history={[makeEvent()]} />)
    expect(screen.getByText('Completada')).toBeInTheDocument()
  })

  it('renderiza evento FAILED con tono de error', () => {
    render(<VehicleVerificationHistoryTimeline history={[makeEvent({ event_type: 'FAILED' })]} />)
    expect(screen.getByText('Fallida')).toBeInTheDocument()
  })

  it('muestra usuario, fuente y dominio del evento', () => {
    render(<VehicleVerificationHistoryTimeline history={[makeEvent()]} />)
    expect(screen.getByText('analyst1')).toBeInTheDocument()
    expect(screen.getByText('SUNARP')).toBeInTheDocument()
    expect(screen.getByText('Identidad Registral')).toBeInTheDocument()
  })

  it('muestra correlation ID parcial cuando se provee', () => {
    render(<VehicleVerificationHistoryTimeline history={[makeEvent()]} />)
    expect(screen.getByText(/corr-abc/)).toBeInTheDocument()
  })

  it('renderiza eventos de evidencia, conflicto y aplicación', () => {
    const events = [
      makeEvent({ id: 'e1', event_type: 'EVIDENCE_ASSOCIATED' }),
      makeEvent({ id: 'e2', event_type: 'CONFLICT_DETECTED' }),
      makeEvent({ id: 'e3', event_type: 'DATA_APPLIED', vehicle_version: 3 }),
    ]
    render(<VehicleVerificationHistoryTimeline history={events} />)
    expect(screen.getByText('Evidencia asociada')).toBeInTheDocument()
    expect(screen.getByText('Conflicto detectado')).toBeInTheDocument()
    expect(screen.getByText('Datos aplicados al vehículo')).toBeInTheDocument()
    expect(screen.getByText('v3')).toBeInTheDocument()
  })
})