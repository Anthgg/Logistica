import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { UnloadingCompletionChecklist } from '../components/UnloadingCompletionChecklist'
import { LogisticsAuthorizationContext } from '../../logistics-permissions/contexts/logistics-authorization-context'
import { createLogisticsAuthState } from '../../logistics-permissions/test/test-utils'
import type { UnloadingCompletionCheck, UnloadingOperation } from '../types/inbound-docks'

const mockOperation: UnloadingOperation = {
  id: 'op-1',
  assignment_id: 'assign-1',
  check_in_id: 'chk-1',
  cpv_code: 'CPV-001',
  cit_code: null,
  dock_id: 'dock-1',
  dock_code: 'M-01',
  dock_name: 'Muelle 1',
  warehouse_id: 'wh-1',
  supplier: null,
  carrier: null,
  vehicle: null,
  status: 'ACTIVE',
  started_at: '2026-08-01T10:00:00Z',
  completed_at: null,
  aborted_at: null,
  started_at_server: '2026-08-01T10:00:00Z',
  active_pause_started_at: null,
  accumulated_pause_seconds: 0,
  readiness_status: 'COMPLETE',
  responsibles: [],
  seal_opening: null,
  active_pause: null,
  alerts: [],
  capabilities: {
    can_view: true,
    can_manage_readiness: true,
    can_manage_responsibles: true,
    can_record_seal_opening: true,
    can_start_unloading: true,
    can_pause: true,
    can_resume: false,
    can_abort: false,
    can_complete: true,
    can_view_metrics: true,
    can_view_history: true,
    can_view_receiving_preparation: true,
    can_request_time_correction: true,
  },
  server_time: '2026-08-01T10:10:00Z',
  created_at: '2026-08-01T10:00:00Z',
  updated_at: '2026-08-01T10:00:00Z',
}

const mockChecks: UnloadingCompletionCheck[] = [
  {
    id: 'chk-comp-1',
    operation_id: 'op-1',
    code: 'CLEANLINESS',
    name: 'Inspección de limpieza del muelle',
    result: 'PASS',
    observation: null,
    evidence_file_id: null,
    performed_by: { id: 'u-1', display_name: 'Juan Pérez' },
    performed_at: '2026-08-01T10:05:00Z',
  },
  {
    id: 'chk-comp-2',
    operation_id: 'op-1',
    code: 'PALLET_COUNT',
    name: 'Conteo de parihuelas y empaques',
    result: 'FAIL',
    observation: 'Discrepancia en 2 pallets',
    evidence_file_id: null,
    performed_by: null,
    performed_at: null,
  },
  {
    id: 'chk-comp-3',
    operation_id: 'op-1',
    code: 'TEMPERATURE',
    name: 'Verificación de temperatura',
    result: 'NOT_APPLICABLE',
    observation: null,
    evidence_file_id: null,
    performed_by: null,
    performed_at: null,
  },
  {
    id: 'chk-comp-4',
    operation_id: 'op-1',
    code: 'SEAL_INTEGRITY',
    name: 'Integridad de precintos',
    result: 'PASS_WITH_OBSERVATION',
    observation: 'Precinto secundario con roce',
    evidence_file_id: null,
    performed_by: null,
    performed_at: null,
  },
]

function renderChecklist(permissions: string[] = ['logistics.inbound_docks.complete']) {
  const authState = createLogisticsAuthState({ permissions })
  return render(
    <LogisticsAuthorizationContext.Provider value={authState}>
      <UnloadingCompletionChecklist
        operation={mockOperation}
        checks={mockChecks}
        loading={false}
        error={null}
      />
    </LogisticsAuthorizationContext.Provider>,
  )
}

describe('UnloadingCompletionChecklist', () => {
  it('renderiza correctamente los resultados de la lista (PASS, FAIL, NOT_APPLICABLE, PASS_WITH_OBSERVATION)', () => {
    renderChecklist()

    expect(screen.getByText('Inspección de limpieza del muelle')).toBeInTheDocument()
    expect(screen.getByText('Cumple')).toBeInTheDocument()

    expect(screen.getByText('Conteo de parihuelas y empaques')).toBeInTheDocument()
    expect(screen.getByText('No cumple')).toBeInTheDocument()

    expect(screen.getByText('Verificación de temperatura')).toBeInTheDocument()
    expect(screen.getByText('No aplica')).toBeInTheDocument()

    expect(screen.getByText('Integridad de precintos')).toBeInTheDocument()
    expect(screen.getByText('Cumple con observación')).toBeInTheDocument()
  })

  it('muestra el botón de Actualizar solo cuando el usuario tiene permiso logistics.inbound_docks.complete', () => {
    const { rerender } = renderChecklist(['logistics.inbound_docks.complete'])
    const updateButtons = screen.getAllByRole('button', { name: 'Actualizar' })
    expect(updateButtons.length).toBe(4)

    const noPermState = createLogisticsAuthState({ permissions: [] })
    rerender(
      <LogisticsAuthorizationContext.Provider value={noPermState}>
        <UnloadingCompletionChecklist
          operation={mockOperation}
          checks={mockChecks}
          loading={false}
          error={null}
        />
      </LogisticsAuthorizationContext.Provider>,
    )

    expect(screen.queryByRole('button', { name: 'Actualizar' })).not.toBeInTheDocument()
  })

  it('abre el dialogo de actualización al hacer click en el botón Actualizar', async () => {
    const user = userEvent.setup()
    renderChecklist(['logistics.inbound_docks.complete'])

    const updateBtns = screen.getAllByRole('button', { name: 'Actualizar' })
    await user.click(updateBtns[0])

    expect(screen.getByRole('dialog')).toBeInTheDocument()
  })
})
