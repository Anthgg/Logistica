import { describe, it, expect, vi, beforeEach } from 'vitest'
import { dockAssignmentsApi } from '../api/dockAssignmentsApi'
import { apiRequest } from '../../../api/api-client'
import { getCsrfToken } from '../../../api/csrf'

vi.mock('../../../api/api-client', () => ({
  apiRequest: vi.fn(),
}))

vi.mock('../../../api/csrf', () => ({
  getCsrfToken: vi.fn().mockResolvedValue('test-csrf-token-xyz'),
}))

const mockedApiRequest = vi.mocked(apiRequest)

describe('dockAssignmentsApi', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockedApiRequest.mockResolvedValue({} as never)
  })

  it('list consulta las asignaciones con los parámetros serializados', async () => {
    await dockAssignmentsApi.list({ warehouse_id: 'wh-1', status: 'ASSIGNED', page: 1, page_size: 20 })

    expect(mockedApiRequest).toHaveBeenCalledWith({
      path: '/logistics/inbound-dock-assignments?warehouse_id=wh-1&status=ASSIGNED&page=1&page_size=20',
      method: 'GET',
    })
  })

  it('createPlan inyecta el encabezado X-CSRF-Token y la clave de idempotencia', async () => {
    const requestData = {
      queue_entry_id: 'q-10',
      warehouse_id: 'wh-1',
      dock_type: 'GENERAL_INBOUND' as const,
    }

    await dockAssignmentsApi.createPlan(requestData)

    expect(getCsrfToken).toHaveBeenCalled()
    expect(mockedApiRequest).toHaveBeenCalledWith(
      expect.objectContaining({
        path: '/logistics/dock-assignment-plans',
        method: 'POST',
        headers: expect.objectContaining({
          'X-CSRF-Token': 'test-csrf-token-xyz',
          'X-Idempotency-Key': expect.any(String),
        }),
        body: requestData,
      }),
    )
  })

  it('startMovement inyecta X-CSRF-Token y efectúa la petición a backend authority', async () => {
    await dockAssignmentsApi.startMovement('assign-99')

    expect(getCsrfToken).toHaveBeenCalled()
    expect(mockedApiRequest).toHaveBeenCalledWith(
      expect.objectContaining({
        path: '/logistics/inbound-dock-assignments/assign-99/start-movement',
        method: 'POST',
        headers: expect.objectContaining({
          'X-CSRF-Token': 'test-csrf-token-xyz',
        }),
      }),
    )
  })

  it('confirmDockArrival inyecta X-CSRF-Token y efectúa la petición al endpoint correspondiente', async () => {
    await dockAssignmentsApi.confirmDockArrival('assign-99')

    expect(getCsrfToken).toHaveBeenCalled()
    expect(mockedApiRequest).toHaveBeenCalledWith(
      expect.objectContaining({
        path: '/logistics/inbound-dock-assignments/assign-99/confirm-dock-arrival',
        method: 'POST',
        headers: expect.objectContaining({
          'X-CSRF-Token': 'test-csrf-token-xyz',
        }),
      }),
    )
  })

  it('releaseDock inyecta X-CSRF-Token y libera el muelle', async () => {
    await dockAssignmentsApi.releaseDock('assign-99')

    expect(getCsrfToken).toHaveBeenCalled()
    expect(mockedApiRequest).toHaveBeenCalledWith(
      expect.objectContaining({
        path: '/logistics/inbound-dock-assignments/assign-99/release-dock',
        method: 'POST',
        headers: expect.objectContaining({
          'X-CSRF-Token': 'test-csrf-token-xyz',
        }),
      }),
    )
  })

  it('reassign reasigna el muelle con motivo y token CSRF', async () => {
    await dockAssignmentsApi.reassign('assign-99', {
      new_dock_id: 'dock-2',
      reason: 'Muelle 1 bloqueado por mantenimiento',
    })

    expect(getCsrfToken).toHaveBeenCalled()
    expect(mockedApiRequest).toHaveBeenCalledWith(
      expect.objectContaining({
        path: '/logistics/inbound-dock-assignments/assign-99/reassign',
        method: 'POST',
        headers: expect.objectContaining({
          'X-CSRF-Token': 'test-csrf-token-xyz',
        }),
        body: {
          new_dock_id: 'dock-2',
          reason: 'Muelle 1 bloqueado por mantenimiento',
          plan_id: null,
        },
      }),
    )
  })

  it('requestTimeCorrection solicita corrección de tiempo operativo con token CSRF', async () => {
    await dockAssignmentsApi.requestTimeCorrection('assign-99', {
      event_type: 'MOVEMENT_STARTED',
      proposed_time: '2026-08-01T10:15:00Z',
      timezone: 'UTC',
      reason: 'Retraso en marcación manual de inicio',
    })

    expect(getCsrfToken).toHaveBeenCalled()
    expect(mockedApiRequest).toHaveBeenCalledWith(
      expect.objectContaining({
        path: '/logistics/unloading-operations/assign-99/time-corrections',
        method: 'POST',
        headers: expect.objectContaining({
          'X-CSRF-Token': 'test-csrf-token-xyz',
        }),
        body: expect.objectContaining({
          event_type: 'MOVEMENT_STARTED',
          proposed_time: '2026-08-01T10:15:00Z',
          reason: 'Retraso en marcación manual de inicio',
        }),
      }),
    )
  })
})
