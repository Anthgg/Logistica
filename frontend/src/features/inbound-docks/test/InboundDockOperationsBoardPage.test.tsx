import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { InboundDockOperationsBoardPage } from '../pages/InboundDockOperationsBoardPage'
import { LogisticsAuthorizationContext } from '../../logistics-permissions/contexts/logistics-authorization-context'
import { createLogisticsAuthState } from '../../logistics-permissions/test/test-utils'

vi.mock('../../logistics-permissions/hooks/useSensitiveActionGuard', () => ({
  useSensitiveActionGuard: () => ({
    run: async (action: (reason: string) => Promise<void>) => {
      await action('Motivo valido test')
      return true
    },
    isPending: false,
    stepUpRequired: false,
    errorMessage: null,
  }),
}))

vi.mock('../hooks/useInboundDocksQueries', () => ({
  useInboundDockQueueSummary: vi.fn(() => ({
    data: {
      server_time: '2026-08-01T12:00:00Z',
      timezone: 'UTC',
      total_in_queue: 2,
      total_assigned: 1,
      total_unloading: 1,
      total_waiting: 2,
      docks_available: 4,
      docks_reserved: 1,
      docks_occupied: 2,
      total_paused: 0,
      total_completed_pending_release: 0,
      prolonged_waits: 0,
      operations_with_anomalies: 0,
      operations_with_incomplete_data: 0,
      avg_waiting_seconds: 300,
    },
    isLoading: false,
  })),
  useInboundDockQueue: vi.fn(() => ({
    data: {
      items: [
        {
          id: 'q-1',
          position: 1,
          priority: 'NORMAL',
          status: 'WAITING',
          cpv_code: 'CPV-001',
          vehicle_plate: 'ABC-123',
          supplier_name: 'Proveedor A',
          waiting_seconds: 120,
          alerts: [],
        },
      ],
      total: 1,
    },
    isLoading: false,
    isError: false,
    refetch: vi.fn(),
  })),
  useInboundDockAssignments: vi.fn(() => ({
    data: {
      items: [],
      total: 0,
    },
    isLoading: false,
    refetch: vi.fn(),
  })),
  useUnloadingOperationsList: vi.fn(() => ({
    data: {
      items: [],
      total: 0,
    },
    isLoading: false,
    refetch: vi.fn(),
  })),
}))

function renderPage(permissions: string[] = ['logistics.inbound_docks.view_queue']) {
  const authState = createLogisticsAuthState({ permissions })
  return render(
    <LogisticsAuthorizationContext.Provider value={authState}>
      <MemoryRouter>
        <InboundDockOperationsBoardPage />
      </MemoryRouter>
    </LogisticsAuthorizationContext.Provider>,
  )
}

describe('InboundDockOperationsBoardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('permite alternar entre vistas tablero, tabla y calendario', async () => {
    const user = userEvent.setup()
    renderPage()

    expect(screen.getByText('Tablero')).toBeInTheDocument()

    const tableBtn = screen.getByRole('button', { name: 'Tabla' })
    await user.click(tableBtn)
    expect(screen.getByText('Tabla de operaciones')).toBeInTheDocument()

    const calendarBtn = screen.getByRole('button', { name: 'Calendario' })
    await user.click(calendarBtn)
    expect(screen.getByText('Calendario operativo')).toBeInTheDocument()
  })

  it('muestra aviso cuando no se tiene permiso logistics.inbound_docks.view_queue', () => {
    renderPage([])
    expect(
      screen.getByText('No tienes capability para visualizar la cola de muelles.'),
    ).toBeInTheDocument()
  })

  it('no muestra advertencia cuando se cuenta con el permiso logistics.inbound_docks.view_queue', () => {
    renderPage(['logistics.inbound_docks.view_queue'])
    expect(
      screen.queryByText('No tienes capability para visualizar la cola de muelles.'),
    ).not.toBeInTheDocument()
  })

  it('renderiza elementos de la cola y permite abrir dialogo de cambio de prioridad', async () => {
    const user = userEvent.setup()
    renderPage(['logistics.inbound_docks.view_queue', 'logistics.inbound_docks.change_priority'])
    expect(screen.getByText(/CPV-001/)).toBeInTheDocument()

    const priorityBtn = screen.getByRole('button', { name: 'Prioridad' })
    await user.click(priorityBtn)
    expect(screen.getByText('Cambiar prioridad de cola')).toBeInTheDocument()
  })
})
