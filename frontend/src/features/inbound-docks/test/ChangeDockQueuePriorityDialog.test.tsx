import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ChangeDockQueuePriorityDialog } from '../components/dialogs/ChangeDockQueuePriorityDialog'
import { inboundDockQueueApi } from '../api/inboundDockQueueApi'
import { LogisticsAuthorizationContext } from '../../logistics-permissions/contexts/logistics-authorization-context'
import { createLogisticsAuthState } from '../../logistics-permissions/test/test-utils'
import type { InboundDockQueueEntry } from '../types/inbound-docks'

vi.mock('../api/inboundDockQueueApi', () => ({
  inboundDockQueueApi: {
    changePriority: vi.fn(),
  },
}))

vi.mock('../../logistics-permissions/hooks/useSensitiveActionGuard', () => ({
  useSensitiveActionGuard: () => ({
    run: async (action: (reason: string) => Promise<void>) => {
      await action('Motivo con longitud suficiente')
      return true
    },
    isPending: false,
    stepUpRequired: false,
    errorMessage: null,
  }),
}))

const mockEntry: InboundDockQueueEntry = {
  id: 'q-101',
  position: 3,
  priority: 'NORMAL',
  status: 'WAITING',
  check_in_id: 'chk-1',
  cpv_code: 'CPV-100',
  cit_code: null,
  warehouse_id: 'wh-1',
  warehouse_name: 'Almacén 1',
  supplier_id: 'sup-1',
  supplier_name: 'Proveedor Test',
  carrier_id: null,
  carrier_name: null,
  vehicle_id: null,
  vehicle_plate: 'ABC-123',
  vehicle_type: null,
  driver_name_redacted: null,
  gate_clearance_at: null,
  entered_queue_at: '2026-08-01T10:00:00Z',
  assigned_dock_id: null,
  assigned_dock_code: null,
  assigned_dock_name: null,
  cit_window_start: null,
  cit_window_end: null,
  pallets: null,
  packages: null,
  weight: null,
  special_requirements: [],
  compatible_dock_ids: [],
  alerts: [],
  waiting_seconds: 450,
  server_time: '2026-08-01T10:07:30Z',
}

function renderDialog(
  open = true,
  permissions = ['logistics.inbound_docks.change_priority'],
  onChanged = vi.fn(),
  onOpenChange = vi.fn(),
) {
  const authState = createLogisticsAuthState({ permissions })
  return render(
    <LogisticsAuthorizationContext.Provider value={authState}>
      <ChangeDockQueuePriorityDialog
        open={open}
        entry={mockEntry}
        onOpenChange={onOpenChange}
        onChanged={onChanged}
      />
    </LogisticsAuthorizationContext.Provider>,
  )
}

describe('ChangeDockQueuePriorityDialog', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('no muestra nada si entry es null', () => {
    const authState = createLogisticsAuthState({
      permissions: ['logistics.inbound_docks.change_priority'],
    })
    const { container } = render(
      <LogisticsAuthorizationContext.Provider value={authState}>
        <ChangeDockQueuePriorityDialog open={true} entry={null} onOpenChange={vi.fn()} />
      </LogisticsAuthorizationContext.Provider>,
    )
    expect(container).toBeEmptyDOMElement()
  })

  it('valida que el motivo tenga al menos 8 caracteres', async () => {
    const user = userEvent.setup()
    renderDialog()

    const confirmBtn = screen.getByRole('button', { name: 'Confirmar cambio' })
    expect(confirmBtn).toBeDisabled()

    const reasonInput = screen.getByLabelText(/Motivo/i)
    await user.type(reasonInput, 'Corto')
    await user.tab()

    expect(
      screen.getByText('Indica un motivo de al menos 8 caracteres.'),
    ).toBeInTheDocument()
    expect(confirmBtn).toBeDisabled()

    await user.clear(reasonInput)
    await user.type(reasonInput, 'Motivo con longitud suficiente')
    expect(confirmBtn).toBeEnabled()
  })

  it('permite seleccionar opciones de prioridad (LOW, NORMAL, HIGH, URGENT)', async () => {
    const user = userEvent.setup()
    renderDialog()

    expect(screen.getByText('Baja')).toBeInTheDocument()
    expect(screen.getByText('Normal')).toBeInTheDocument()
    expect(screen.getByText('Alta')).toBeInTheDocument()
    expect(screen.getByText('Urgente')).toBeInTheDocument()

    const urgentLabel = screen.getByText('Urgente')
    await user.click(urgentLabel)

    expect(
      screen.getByText(/Prioridad URGENTE. Se exigirá motivo/i),
    ).toBeInTheDocument()
  })

  it('muestra aviso de falta de permisos cuando el usuario no tiene la capability', () => {
    renderDialog(true, [])

    expect(
      screen.getByText('No tienes permiso para cambiar prioridades.'),
    ).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Confirmar cambio' })).toBeDisabled()
  })

  it('llama a la API inboundDockQueueApi.changePriority con el motivo y la prioridad seleccionada', async () => {
    const user = userEvent.setup()
    const onChanged = vi.fn()
    const onOpenChange = vi.fn()
    const updatedEntry = { ...mockEntry, priority: 'HIGH' as const }
    vi.mocked(inboundDockQueueApi.changePriority).mockResolvedValueOnce(updatedEntry)

    renderDialog(true, ['logistics.inbound_docks.change_priority'], onChanged, onOpenChange)

    await user.click(screen.getByText('Alta'))

    const reasonInput = screen.getByLabelText(/Motivo/i)
    await user.type(reasonInput, 'Reordenamiento por prioridad de descarga')

    const confirmBtn = screen.getByRole('button', { name: 'Confirmar cambio' })
    await user.click(confirmBtn)

    expect(inboundDockQueueApi.changePriority).toHaveBeenCalledWith('q-101', {
      priority: 'HIGH',
      reason: 'Reordenamiento por prioridad de descarga',
      evidence_file_id: null,
    })
    expect(onOpenChange).toHaveBeenCalledWith(false)
    expect(onChanged).toHaveBeenCalledWith(updatedEntry)
  })
})
