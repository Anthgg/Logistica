import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { EmptyState, ErrorState, StatusPill, TableSkeleton } from '../components/ui/SharedState'

describe('SharedState', () => {
  it('StatusPill aplica tono y contenido accesible', () => {
    render(<StatusPill tone="success">Activo</StatusPill>)
    const pill = screen.getByText('Activo')
    expect(pill.className).toContain('emerald')
  })

  it('EmptyState muestra título y descripción', () => {
    render(<EmptyState title="Sin datos" description="No hay registros" />)
    expect(screen.getByText('Sin datos')).toBeTruthy()
    expect(screen.getByText('No hay registros')).toBeTruthy()
  })

  it('ErrorState expone role alert y mensaje', () => {
    render(<ErrorState message="Falló la carga" />)
    const alert = screen.getByRole('alert')
    expect(alert.textContent).toContain('Falló la carga')
  })

  it('TableSkeleton renderiza filas animadas', () => {
    const { container } = render(<TableSkeleton rows={4} />)
    const bars = container.querySelectorAll('.animate-pulse')
    expect(bars.length).toBe(4)
  })
})