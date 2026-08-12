import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { WarehouseDocksBoard } from '../components/WarehouseDocksBoard'
import type { WarehouseDockSummary } from '../types/inbound-docks'

const mockDocks: WarehouseDockSummary[] = [
  {
    id: 'dock-1',
    code: 'M-01',
    name: 'Muelle 1',
    warehouse_id: 'wh-1',
    warehouse_name: 'Almacén Central',
    type: 'STANDARD',
    direction: 'INBOUND',
    status: 'ACTIVE',
    operational_status: 'AVAILABLE',
    active_assignment_id: null,
    active_assignment_vehicle_plate: null,
    occupied_since: null,
  },
  {
    id: 'dock-2',
    code: 'M-02',
    name: 'Muelle 2',
    warehouse_id: 'wh-1',
    warehouse_name: 'Almacén Central',
    type: 'REFRIGERATED',
    direction: 'INBOUND',
    status: 'ACTIVE',
    operational_status: 'OCCUPIED',
    active_assignment_id: 'assign-1',
    active_assignment_vehicle_plate: 'XYZ-789',
    occupied_since: new Date(Date.now() - 600000).toISOString(),
  },
  {
    id: 'dock-3',
    code: 'M-03',
    name: 'Muelle 3',
    warehouse_id: 'wh-1',
    warehouse_name: 'Almacén Central',
    type: 'HAZMAT',
    direction: 'INBOUND',
    status: 'ACTIVE',
    operational_status: 'MAINTENANCE',
    active_assignment_id: null,
    active_assignment_vehicle_plate: null,
    occupied_since: null,
  },
  {
    id: 'dock-4',
    code: 'M-04',
    name: 'Muelle 4',
    warehouse_id: 'wh-1',
    warehouse_name: 'Almacén Central',
    type: 'OVERSIZED',
    direction: 'INBOUND',
    status: 'INACTIVE',
    operational_status: 'INACTIVE',
    active_assignment_id: null,
    active_assignment_vehicle_plate: null,
    occupied_since: null,
  },
]

describe('WarehouseDocksBoard', () => {
  it('renderiza mensaje vacío cuando no hay muelles', () => {
    render(<WarehouseDocksBoard docks={[]} emptyMessage="No hay muelles disponibles." />)
    expect(screen.getByText('No hay muelles disponibles.')).toBeInTheDocument()
  })

  it('renderiza correctamente los pills de estado para AVAILABLE, OCCUPIED, MAINTENANCE, INACTIVE', () => {
    render(<WarehouseDocksBoard docks={mockDocks} />)

    expect(screen.getByText('M-01')).toBeInTheDocument()
    expect(screen.getByText('M-02')).toBeInTheDocument()
    expect(screen.getByText('M-03')).toBeInTheDocument()
    expect(screen.getByText('M-04')).toBeInTheDocument()

    expect(screen.getByText('Disponible')).toBeInTheDocument()
    expect(screen.getByText('Ocupado')).toBeInTheDocument()
    expect(screen.getByText('Mantenimiento')).toBeInTheDocument()
    expect(screen.getByText('Inactivo')).toBeInTheDocument()
  })

  it('muestra banner de vehículo ocupado y tiempo transcurrido cuando un muelle está ocupado', () => {
    render(<WarehouseDocksBoard docks={mockDocks} />)

    expect(screen.getByText(/Ocupado — XYZ-789/i)).toBeInTheDocument()
    expect(screen.getByText(/Desde/i)).toBeInTheDocument()
  })

  it('ejecuta callback onSelect al hacer click sobre una tarjeta de muelle', async () => {
    const user = userEvent.setup()
    const onSelect = vi.fn()
    render(<WarehouseDocksBoard docks={mockDocks} onSelect={onSelect} selectedId="dock-1" />)

    const dock2Btn = screen.getByRole('button', { name: /M-02/i })
    await user.click(dock2Btn)

    expect(onSelect).toHaveBeenCalledTimes(1)
    expect(onSelect).toHaveBeenCalledWith(mockDocks[1])
  })
})
