import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ServerBasedOperationTimer } from '../components/ui/ServerBasedOperationTimer'

describe('ServerBasedOperationTimer', () => {
  it('calcula y muestra duraciones bruta, neta y pausada en estado ACTIVE', () => {
    const serverTime = '2026-08-01T12:30:00Z'
    const startedAt = '2026-08-01T12:00:00Z' // 30 min ago (1800s gross)
    
    render(
      <ServerBasedOperationTimer
        serverTimeIso={serverTime}
        startedAt={startedAt}
        activePauseStartedAt={null}
        accumulatedPauseSeconds={300} // 5 min paused
        status="ACTIVE"
      />,
    )

    expect(screen.getByText('En curso')).toBeInTheDocument()
    expect(screen.getByText('Bruto (aprox.)')).toBeInTheDocument()
    expect(screen.getByText('Neto (aprox.)')).toBeInTheDocument()
    expect(screen.getByText('Pausado (aprox.)')).toBeInTheDocument()
  })

  it('muestra estado Pausado cuando la operación está en PAUSED o UNLOADING_PAUSED', () => {
    const serverTime = '2026-08-01T12:30:00Z'
    const startedAt = '2026-08-01T12:00:00Z'

    render(
      <ServerBasedOperationTimer
        serverTimeIso={serverTime}
        startedAt={startedAt}
        activePauseStartedAt="2026-08-01T12:20:00Z"
        accumulatedPauseSeconds={120}
        status="UNLOADING_PAUSED"
      />,
    )

    expect(screen.getByText('Pausado')).toBeInTheDocument()
  })

  it('muestra estado Finalizado y duración oficial cuando status es COMPLETED', () => {
    render(
      <ServerBasedOperationTimer
        serverTimeIso="2026-08-01T13:00:00Z"
        startedAt="2026-08-01T12:00:00Z"
        activePauseStartedAt={null}
        accumulatedPauseSeconds={60}
        status="COMPLETED"
        officialDurationSeconds={3540}
      />,
    )

    expect(screen.getByText('Finalizado')).toBeInTheDocument()
    expect(screen.getByText(/Duración oficial:/i)).toBeInTheDocument()
  })

  it('muestra Inactivo para estados iniciales sin inicio', () => {
    render(
      <ServerBasedOperationTimer
        serverTimeIso="2026-08-01T12:00:00Z"
        startedAt={null}
        activePauseStartedAt={null}
        accumulatedPauseSeconds={0}
        status="PENDING"
      />,
    )

    expect(screen.getByText('Inactivo')).toBeInTheDocument()
  })
})
