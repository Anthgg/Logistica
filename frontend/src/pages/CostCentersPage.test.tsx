import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { CostCentersPage } from './CostCentersPage'
import type { CostCenter } from '../types/purchase-requisitions'

const mocks = vi.hoisted(() => ({
  list: vi.fn(),
  create: vi.fn(),
  update: vi.fn(),
  activate: vi.fn(),
  deactivate: vi.fn(),
  archive: vi.fn(),
  access: {
    currentContext: {
      organization_id: '11111111-1111-4111-8111-111111111111' as string | null,
      branch_id: null as string | null,
      warehouse_id: null as string | null,
    },
  },
  canManage: true,
}))

vi.mock('../api/cost-centers-api', () => ({
  costCentersApi: {
    list: mocks.list,
    create: mocks.create,
    update: mocks.update,
    activate: mocks.activate,
    deactivate: mocks.deactivate,
    archive: mocks.archive,
  },
}))
vi.mock('../features/logistics-me/hooks/useLogisticsAccess', () => ({ useLogisticsAccess: () => mocks.access }))
vi.mock('../features/logistics-permissions/hooks/useLogisticsPermissions', () => ({
  useLogisticsPermissions: () => ({ hasPermission: () => mocks.canManage }),
}))

const center: CostCenter = {
  id: '22222222-2222-4222-8222-222222222222',
  organization_id: '11111111-1111-4111-8111-111111111111',
  branch_id: null,
  code: 'CC_OPERACIONES',
  normalized_code: 'CC_OPERACIONES',
  name: 'Centro operativo',
  description: 'Imputación para operaciones logísticas.',
  responsible_user_id: null,
  parent_cost_center_id: null,
  status: 'ACTIVE',
  valid_from: '2026-01-01',
  valid_until: null,
  created_by: '33333333-3333-4333-8333-333333333333',
  updated_by: '33333333-3333-4333-8333-333333333333',
  row_version: 1,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
}

describe('catálogo de centros de costo', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mocks.access.currentContext = {
      organization_id: '11111111-1111-4111-8111-111111111111',
      branch_id: null,
      warehouse_id: null,
    }
    mocks.canManage = true
    mocks.list.mockResolvedValue([center])
    mocks.create.mockResolvedValue(center)
  })

  it('espera un contexto organizacional antes de consultar', () => {
    mocks.access.currentContext = { organization_id: null, branch_id: null, warehouse_id: null }
    render(<CostCentersPage />)
    expect(screen.getByRole('heading', { name: 'Selecciona una organización' })).toBeInTheDocument()
    expect(mocks.list).not.toHaveBeenCalled()
  })

  it('consulta el endpoint real y presenta el estado del catálogo', async () => {
    render(<CostCentersPage />)
    expect((await screen.findAllByText('Centro operativo')).length).toBeGreaterThan(0)
    expect(screen.getAllByText('Activo').length).toBeGreaterThan(0)
    expect(mocks.list).toHaveBeenCalledWith({ branch_id: null, limit: 100 })
  })

  it('crea un borrador con el contrato publicado por el backend', async () => {
    const user = userEvent.setup()
    render(<CostCentersPage />)
    await screen.findAllByText('Centro operativo')
    await user.click(screen.getByRole('button', { name: 'Nuevo centro' }))
    await user.type(screen.getByLabelText('Código'), 'cc_nuevo')
    await user.type(screen.getByLabelText('Nombre'), 'Centro nuevo')
    await user.click(screen.getByRole('button', { name: 'Crear borrador' }))
    await waitFor(() => expect(mocks.create).toHaveBeenCalledTimes(1))
    expect(mocks.create).toHaveBeenCalledWith(
      expect.objectContaining({
        code: 'CC_NUEVO',
        name: 'Centro nuevo',
        branch_id: null,
        parent_cost_center_id: null,
        valid_until: null,
      }),
    )
  })
})
