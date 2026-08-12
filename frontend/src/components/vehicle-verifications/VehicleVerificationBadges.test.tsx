import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { VehicleVerificationSourceBadge, VehicleVerificationMethodBadge } from './VehicleVerificationSourceBadge'
import { VehicleVerificationFreshnessIndicator } from './VehicleVerificationFreshnessIndicator'

describe('VehicleVerificationSourceBadge', () => {
  it('renderiza la etiqueta de fuente SUNARP', () => {
    render(<VehicleVerificationSourceBadge sourceType="SUNARP" />)
    expect(screen.getByText('SUNARP Registral')).toBeInTheDocument()
  })

  it('usa el sourceName cuando se proporciona', () => {
    render(<VehicleVerificationSourceBadge sourceType="MTC" sourceName="MTC Oficial" />)
    expect(screen.getByText('MTC Oficial')).toBeInTheDocument()
  })

  it('aplica clase accesible con borde', () => {
    const { container } = render(<VehicleVerificationSourceBadge sourceType="SBS" />)
    const badge = container.querySelector('.border')
    expect(badge).not.toBeNull()
  })
})

describe('VehicleVerificationMethodBadge', () => {
  it('renderiza método AUTHORIZED_API', () => {
    render(<VehicleVerificationMethodBadge method="AUTHORIZED_API" />)
    expect(screen.getByText('API Autorizada')).toBeInTheDocument()
  })

  it('no muestra "automática" para ASSISTED_MANUAL', () => {
    render(<VehicleVerificationMethodBadge method="ASSISTED_MANUAL" />)
    expect(screen.getByText('Validación Asistida')).toBeInTheDocument()
    expect(screen.queryByText(/automática/i)).toBeNull()
  })
})

describe('VehicleVerificationFreshnessIndicator', () => {
  it('muestra estado Vigente', () => {
    render(<VehicleVerificationFreshnessIndicator freshness="FRESH" />)
    expect(screen.getByText('Vigente')).toBeInTheDocument()
  })

  it('muestra fecha absoluta de fuente', () => {
    render(
      <VehicleVerificationFreshnessIndicator
        freshness="FRESH"
        sourceDate="2026-01-15T00:00:00Z"
      />,
    )
    expect(screen.getByText(/Fuente:/)).toBeInTheDocument()
  })

  it('muestra días restantes cuando se provee expirationDate', () => {
    render(
      <VehicleVerificationFreshnessIndicator
        freshness="AGING"
        sourceDate="2026-01-01T00:00:00Z"
        expirationDate="2026-02-01T00:00:00Z"
        daysUntilExpiration={15}
      />,
    )
    expect(screen.getByText(/en 15 días/)).toBeInTheDocument()
  })

  it('muestra vencida cuando daysUntilExpiration es negativo', () => {
    render(
      <VehicleVerificationFreshnessIndicator
        freshness="EXPIRED"
        expirationDate="2025-12-01T00:00:00Z"
        daysUntilExpiration={-30}
      />,
    )
    expect(screen.getByText(/hace 30 días/)).toBeInTheDocument()
  })

  it('no muestra "Actual", "Reciente" o "Hace tiempo"', () => {
    render(<VehicleVerificationFreshnessIndicator freshness="STALE" />)
    expect(screen.queryByText('Actual')).toBeNull()
    expect(screen.queryByText('Reciente')).toBeNull()
    expect(screen.queryByText('Hace tiempo')).toBeNull()
  })
})