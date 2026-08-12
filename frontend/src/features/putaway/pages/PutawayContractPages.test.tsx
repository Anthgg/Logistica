import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { ReactNode } from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { PutawayDashboardPage } from './PutawayDashboardPage'
import { PutawayOrdersPage } from './PutawayOrdersPage'
import { PutawayTasksPage } from './PutawayTasksPage'
import { PutawayExceptionsPage } from './PutawayExceptionsPage'
import { PutawayCapacityPage } from './PutawayCapacityPage'

const mocks = vi.hoisted(() => ({ useQuery: vi.fn(), useLogisticsAccess: vi.fn() }))

vi.mock('../../inbound-docks/hooks/useQuery', () => ({ useQuery: mocks.useQuery }))
vi.mock('../../logistics-me/hooks/useLogisticsAccess', () => ({ useLogisticsAccess: mocks.useLogisticsAccess }))
vi.mock('../../logistics-permissions/hooks/useLogisticsPermissions', () => ({ useLogisticsPermissions: () => ({ hasPermission: () => true }) }))
vi.mock('../../../components/logistics/LogisticsContextSwitcher', () => ({ LogisticsContextSwitcher: () => <button type="button">Seleccionar organización</button> }))

const idleQuery = { data: undefined, isLoading: false, isFetching: false, isError: false, error: null, errorCode: null, status: null, refetch: vi.fn(), setData: vi.fn() }
const emptyEnvelope = { items: [], total: 0, page: 1, page_size: 50 }

function renderPage(ui: ReactNode) { return render(<MemoryRouter>{ui}</MemoryRouter>) }

describe('contratos efectivos de la Fase 043', () => {
  beforeEach(() => {
    mocks.useQuery.mockReset()
    mocks.useQuery.mockImplementation((_key, path) => path.includes('/capacity/') ? { ...idleQuery, data: undefined } : { ...idleQuery, data: emptyEnvelope })
    mocks.useLogisticsAccess.mockReturnValue({ currentContext: { organization_id: '11111111-1111-4111-8111-111111111111', branch_id: null, warehouse_id: null } })
  })

  it('construye el tablero desde órdenes y tareas reales', () => {
    renderPage(<PutawayDashboardPage />)
    expect(mocks.useQuery.mock.calls.map((call) => call[1])).toEqual(expect.arrayContaining(['/logistics/putaway/orders', '/logistics/putaway/tasks']))
    expect(mocks.useQuery.mock.calls.some((call) => call[1] === '/logistics/putaway-dashboard')).toBe(false)
  })

  it('usa el envelope paginado de órdenes', () => {
    renderPage(<PutawayOrdersPage />)
    expect(screen.getByRole('heading', { name: '0 orden(es)' })).toBeInTheDocument()
    expect(mocks.useQuery).toHaveBeenCalledWith(expect.any(Array), '/logistics/putaway/orders', expect.objectContaining({ page: 1, page_size: 50 }), { enabled: true })
  })

  it('usa el envelope paginado de tareas', () => {
    renderPage(<PutawayTasksPage />)
    expect(screen.getByRole('heading', { name: '0 tarea(s)' })).toBeInTheDocument()
    expect(mocks.useQuery).toHaveBeenCalledWith(expect.any(Array), '/logistics/putaway/tasks', expect.objectContaining({ page: 1, page_size: 50 }), { enabled: true })
  })

  it('deriva las excepciones desde tareas y no consulta un listado inexistente', () => {
    renderPage(<PutawayExceptionsPage />)
    expect(screen.getByRole('heading', { name: 'Operación sin excepciones abiertas' })).toBeInTheDocument()
    expect(mocks.useQuery.mock.calls.some((call) => call[1] === '/logistics/putaway-exceptions')).toBe(false)
    expect(mocks.useQuery).toHaveBeenCalledWith(expect.any(Array), '/logistics/putaway/tasks', expect.any(Object), { enabled: true })
  })

  it('consulta capacidad con almacén y ubicación obligatorios', async () => {
    const user = userEvent.setup()
    renderPage(<PutawayCapacityPage />)
    await user.type(screen.getByLabelText('Almacén ID'), 'warehouse-id')
    await user.type(screen.getByLabelText('Ubicación ID'), 'location-id')
    await user.click(screen.getByRole('button', { name: 'Consultar proyección' }))
    expect(mocks.useQuery).toHaveBeenLastCalledWith(expect.any(Array), '/logistics/putaway/capacity/projections', { warehouse_id: 'warehouse-id', location_id: 'location-id' }, { enabled: true })
  })
})
