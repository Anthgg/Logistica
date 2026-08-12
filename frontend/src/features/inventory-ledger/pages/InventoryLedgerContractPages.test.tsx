import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { ReactNode } from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { InventoryMovementsPage } from './InventoryMovementsPage'
import { InventoryLedgerCheckpointsPage } from './InventoryLedgerCheckpointsPage'
import { InventoryLedgerDashboardPage } from './InventoryLedgerDashboardPage'

const mocks = vi.hoisted(() => ({
  useQuery: vi.fn(),
  useLogisticsAccess: vi.fn(),
}))

vi.mock('../../inbound-docks/hooks/useQuery', () => ({
  useQuery: mocks.useQuery,
}))

vi.mock('../../logistics-me/hooks/useLogisticsAccess', () => ({
  useLogisticsAccess: mocks.useLogisticsAccess,
}))

vi.mock('../../logistics-permissions/hooks/useLogisticsPermissions', () => ({
  useLogisticsPermissions: () => ({ hasPermission: () => true }),
}))

vi.mock('../../../components/logistics/LogisticsContextSwitcher', () => ({
  LogisticsContextSwitcher: () => <button type="button">Seleccionar organización</button>,
}))

const idleQuery = {
  data: undefined,
  isLoading: false,
  isFetching: false,
  isError: false,
  error: null,
  errorCode: null,
  status: null,
  refetch: vi.fn(),
  setData: vi.fn(),
}

function renderWithRouter(ui: ReactNode) {
  return render(<MemoryRouter>{ui}</MemoryRouter>)
}

describe('contrato HTTP del libro de inventario', () => {
  beforeEach(() => {
    mocks.useQuery.mockReset()
    mocks.useQuery.mockReturnValue(idleQuery)
    mocks.useLogisticsAccess.mockReturnValue({
      currentContext: {
        organization_id: null,
        branch_id: null,
        warehouse_id: null,
      },
    })
  })

  it('no consulta movimientos sin organization_id', () => {
    renderWithRouter(<InventoryMovementsPage />)

    expect(screen.getByRole('heading', { name: 'Selecciona el ledger que deseas consultar' })).toBeInTheDocument()
    expect(mocks.useQuery).toHaveBeenCalledWith(
      expect.any(Array),
      '/logistics/inventory/movements',
      undefined,
      { enabled: false },
    )
  })

  it('usa el envelope real y filtros válidos del backend', async () => {
    mocks.useLogisticsAccess.mockReturnValue({
      currentContext: {
        organization_id: '11111111-1111-4111-8111-111111111111',
        branch_id: null,
        warehouse_id: null,
      },
    })
    mocks.useQuery.mockReturnValue({
      ...idleQuery,
      data: {
        items: [
          {
            id: '22222222-2222-4222-8222-222222222222',
            movement_code: 'MOV-0001',
            ledger_sequence: 1,
            movement_family: 'INBOUND',
            movement_type: 'INBOUND_RECEIPT_RECOGNIZED',
            status: 'POSTED',
            occurred_at: '2026-08-10T10:00:00Z',
            posted_at: '2026-08-10T10:00:01Z',
            warehouse_summary: null,
            product_count: 1,
            line_count: 1,
            integrity_status: 'OK',
          },
        ],
        total: 1,
        page: 1,
        page_size: 50,
      },
    })

    const user = userEvent.setup()
    renderWithRouter(<InventoryMovementsPage />)
    expect(screen.getByText('MOV-0001')).toBeInTheDocument()

    await user.click(screen.getByRole('tab', { name: 'Entradas' }))
    const lastCall = mocks.useQuery.mock.calls.at(-1)
    expect(lastCall?.[2]).toMatchObject({
      organization_id: '11111111-1111-4111-8111-111111111111',
      movement_family: 'INBOUND',
    })
    expect(lastCall?.[2]).not.toHaveProperty('movement_type', 'ENTRY')
  })

  it('reemplaza el listado inexistente de checkpoints por particiones', () => {
    mocks.useLogisticsAccess.mockReturnValue({
      currentContext: {
        organization_id: '11111111-1111-4111-8111-111111111111',
        branch_id: null,
        warehouse_id: null,
      },
    })
    mocks.useQuery.mockReturnValue({ ...idleQuery, data: [] })

    renderWithRouter(<InventoryLedgerCheckpointsPage />)

    expect(mocks.useQuery).toHaveBeenCalledWith(
      expect.any(Array),
      '/logistics/inventory/ledger/partitions',
      { organization_id: '11111111-1111-4111-8111-111111111111' },
      { enabled: true },
    )
    expect(
      mocks.useQuery.mock.calls.some((call) => call[1] === '/logistics/inventory/ledger/checkpoints'),
    ).toBe(false)
    expect(screen.getByText('Aún no hay particiones del libro')).toBeInTheDocument()
  })

  it('muestra un estado guiado cuando falta el contexto organizacional', () => {
    renderWithRouter(<InventoryLedgerCheckpointsPage />)

    expect(screen.getByRole('heading', { name: 'Elige dónde validar el libro' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Seleccionar organización' })).toBeInTheDocument()
    expect(screen.getByText('Cómo funciona')).toBeInTheDocument()
  })

  it('construye el tablero desde el listado real de movimientos', () => {
    mocks.useLogisticsAccess.mockReturnValue({
      currentContext: {
        organization_id: '11111111-1111-4111-8111-111111111111',
        branch_id: null,
        warehouse_id: null,
      },
    })
    mocks.useQuery.mockReturnValue({
      ...idleQuery,
      data: { items: [], total: 0, page: 1, page_size: 10 },
    })

    renderWithRouter(<InventoryLedgerDashboardPage />)

    expect(mocks.useQuery).toHaveBeenCalledWith(
      expect.any(Array),
      '/logistics/inventory/movements',
      expect.objectContaining({
        organization_id: '11111111-1111-4111-8111-111111111111',
        page_size: 10,
      }),
      { enabled: true },
    )
    expect(
      mocks.useQuery.mock.calls.some((call) => call[1] === '/logistics/inventory/movements/dashboard'),
    ).toBe(false)
  })
})
