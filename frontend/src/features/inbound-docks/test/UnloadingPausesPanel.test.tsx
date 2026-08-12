import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { UnloadingPausesPanel } from '../components/UnloadingPausesPanel'
import type { UnloadingPause } from '../types/inbound-docks'

const mockPauses: UnloadingPause[] = [
  {
    id: 'pause-1',
    operation_id: 'op-10',
    reason: 'Falla mecánica de montacargas',
    reason_label: 'Falla de Equipo',
    is_active: true,
    severity: 'CRITICAL',
    started_at: '2026-08-01T11:00:00Z',
    ended_at: null,
    comment: 'Se requiere soporte técnico urgente',
    evidence_file_id: 'ev-1',
    responsible_informed: { id: 'u-1', display_name: 'Carlos Pérez' },
    duration_seconds: 600,
    created_by: null,
  },
  {
    id: 'pause-2',
    operation_id: 'op-10',
    reason: 'Cambio de turno de personal',
    reason_label: 'Cambio de Turno',
    is_active: false,
    severity: 'LOW',
    started_at: '2026-08-01T10:00:00Z',
    ended_at: '2026-08-01T10:15:00Z',
    comment: null,
    evidence_file_id: null,
    responsible_informed: null,
    duration_seconds: 900,
    created_by: null,
  },
]

describe('UnloadingPausesPanel', () => {
  it('muestra esqueleto de carga cuando loading es true', () => {
    const { container } = render(<UnloadingPausesPanel pauses={undefined} loading={true} error={null} />)
    expect(screen.getByText('Pausas')).toBeInTheDocument()
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument()
  })

  it('muestra mensaje de error cuando error no es null', () => {
    render(<UnloadingPausesPanel pauses={undefined} loading={false} error="Error al obtener pausas" />)
    expect(screen.getByText('Error al obtener pausas')).toBeInTheDocument()
  })

  it('muestra panel vacío cuando la lista de pausas está vacía', () => {
    render(<UnloadingPausesPanel pauses={[]} loading={false} error={null} />)
    expect(screen.getByText('Sin pausas')).toBeInTheDocument()
  })

  it('renderiza la lista de pausas con sus tonos de severidad y pills de estado (Activa / Cerrada)', () => {
    render(<UnloadingPausesPanel pauses={mockPauses} loading={false} error={null} />)

    expect(screen.getByText('Falla de Equipo')).toBeInTheDocument()
    expect(screen.getByText('Motivo: Falla mecánica de montacargas')).toBeInTheDocument()
    expect(screen.getByText('Activa')).toBeInTheDocument()
    expect(screen.getByText('Crítica')).toBeInTheDocument()

    expect(screen.getByText('Cambio de Turno')).toBeInTheDocument()
    expect(screen.getByText('Cerrada')).toBeInTheDocument()
    expect(screen.getByText('Baja')).toBeInTheDocument()
  })
})
