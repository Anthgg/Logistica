import type { ReactNode } from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { QualityAvailabilityPage } from './QualityAvailabilityPage'
import { QualityInspectionsPage } from './QualityInspectionsPage'
import { QualityQuarantineCasesPage } from './QualityQuarantineCasesPage'
import { QualityQuarantineDashboardPage } from './QualityQuarantineDashboardPage'
import { QuarantineZonesPage } from './QuarantineZonesPage'
import { QualityInspectionWorkspacePage } from './QualityInspectionWorkspacePage'
import { QualityNonConformityPage } from './QualityNonConformityPage'
import { QualityQuarantineHistoryPage } from './QualityQuarantineHistoryPage'
import { QuarantineReleasePage } from './QuarantineReleasePage'

const mocks = vi.hoisted(() => ({ useQuery: vi.fn(), useMutation: vi.fn(), useLogisticsAccess: vi.fn() }))

vi.mock('../../inbound-docks/hooks/useQuery', () => ({ useQuery: mocks.useQuery, useMutation: mocks.useMutation }))
vi.mock('../../logistics-me/hooks/useLogisticsAccess', () => ({ useLogisticsAccess: mocks.useLogisticsAccess }))
vi.mock('../../logistics-permissions/hooks/useLogisticsPermissions', () => ({ useLogisticsPermissions: () => ({ hasPermission: () => true }) }))
vi.mock('../../../components/logistics/LogisticsContextSwitcher', () => ({ LogisticsContextSwitcher: () => <button type="button">Seleccionar contexto</button> }))

const emptyQuery = { data: [], isLoading: false, isFetching: false, isError: false, error: null, errorCode: null, status: null, refetch: vi.fn(), setData: vi.fn() }
const caseDetail = {
  id: 'case-id', quarantine_code: 'QC-001', status: 'ACTIVE', severity: 'MEDIUM',
  quality_result: null, release_status: 'PENDING', source_type: 'RECEIPT',
  inbound_receipt_id: 'receipt-id', product_id: 'product-id', quarantine_reason: 'CONTROL',
  quality_decision_status: 'PENDING', physical_segregation_status: 'CONFIRMED',
  opened_at: '2026-08-11T12:00:00Z', created_at: '2026-08-11T11:00:00Z',
}
const emptyMutation = { mutate: vi.fn(), mutateAsync: vi.fn(), isPending: false, error: null, reset: vi.fn() }

function renderPage(ui: ReactNode) {
  return render(<MemoryRouter>{ui}</MemoryRouter>)
}

function renderRoute(path: string, pattern: string, ui: ReactNode) {
  return render(<MemoryRouter initialEntries={[path]}><Routes><Route path={pattern} element={ui} /></Routes></MemoryRouter>)
}

describe('contratos efectivos de la Fase 042', () => {
  beforeEach(() => {
    mocks.useQuery.mockReset()
    mocks.useMutation.mockReset()
    mocks.useQuery.mockReturnValue(emptyQuery)
    mocks.useMutation.mockReturnValue(emptyMutation)
    mocks.useLogisticsAccess.mockReturnValue({ currentContext: { organization_id: 'org-id', branch_id: 'branch-id', warehouse_id: 'warehouse-id' } })
  })

  it('deriva el tablero desde tres listados reales', () => {
    renderPage(<QualityQuarantineDashboardPage />)
    const paths = mocks.useQuery.mock.calls.map((call) => call[1])
    expect(paths).toEqual(expect.arrayContaining(['/logistics/quality-quarantine-cases', '/logistics/quarantine-zones', '/logistics/quality-availability']))
    expect(paths.some((path) => String(path).includes('/dashboard'))).toBe(false)
  })

  it('consulta casos como lista directa por almacén', () => {
    renderPage(<QualityQuarantineCasesPage />)
    expect(mocks.useQuery).toHaveBeenCalledWith(expect.any(Array), '/logistics/quality-quarantine-cases', { warehouse_id: 'warehouse-id' }, { enabled: true })
    expect(screen.getByRole('heading', { name: 'No hay casos para este filtro' })).toBeInTheDocument()
  })

  it('consulta zonas y disponibilidad sin endpoints resumen inexistentes', () => {
    renderPage(<QuarantineZonesPage />)
    renderPage(<QualityAvailabilityPage />)
    const paths = mocks.useQuery.mock.calls.map((call) => call[1])
    expect(paths).toEqual(expect.arrayContaining(['/logistics/quarantine-zones', '/logistics/quality-availability']))
    expect(paths.some((path) => String(path).endsWith('/summary'))).toBe(false)
  })

  it('exige el ID de caso para listar inspecciones', async () => {
    const user = userEvent.setup()
    renderPage(<QualityInspectionsPage />)
    await user.type(screen.getByLabelText('ID del caso de cuarentena'), 'case-id')
    await user.click(screen.getByRole('button', { name: 'Consultar inspección' }))
    expect(mocks.useQuery).toHaveBeenLastCalledWith(expect.any(Array), '/logistics/quality-inspections', { quarantine_case_id: 'case-id' }, { enabled: true })
  })

  it('deriva el historial desde recursos publicados y no llama /history', () => {
    mocks.useQuery.mockImplementation((_key, path) => ({ ...emptyQuery, data: path.endsWith('/case-id') ? caseDetail : [] }))
    renderRoute('/logistics/quality/quarantine/case-id/history', '/logistics/quality/quarantine/:caseId/history', <QualityQuarantineHistoryPage />)
    const paths = mocks.useQuery.mock.calls.map((call) => call[1])
    expect(paths).toEqual(expect.arrayContaining([
      '/logistics/quality-quarantine-cases/case-id',
      '/logistics/quality-quarantine-cases/case-id/decisions',
      '/logistics/quality-quarantine-cases/case-id/release-authorizations',
      '/logistics/quality-quarantine-cases/case-id/rejection-authorizations',
    ]))
    expect(paths.some((path) => String(path).endsWith('/history'))).toBe(false)
  })

  it('muestra la no conformidad como operación no publicada sin llamar rutas inexistentes', () => {
    mocks.useQuery.mockReturnValue({ ...emptyQuery, data: caseDetail })
    renderRoute('/logistics/quality/quarantine/case-id/document', '/logistics/quality/quarantine/:caseId/document', <QualityNonConformityPage />)
    expect(screen.getByText(/no expone emisión/i)).toBeInTheDocument()
    expect(mocks.useQuery.mock.calls.map((call) => call[1])).toEqual(['/logistics/quality-quarantine-cases/case-id'])
  })

  it('consulta liberaciones anidadas y no ofrece aprobación inexistente', () => {
    mocks.useQuery.mockImplementation((_key, path) => ({ ...emptyQuery, data: path.endsWith('/case-id') ? caseDetail : [] }))
    renderRoute('/logistics/quality/quarantine/case-id/release', '/logistics/quality/quarantine/:caseId/release', <QuarantineReleasePage />)
    expect(mocks.useQuery.mock.calls.map((call) => call[1])).toEqual(expect.arrayContaining([
      '/logistics/quality-quarantine-cases/case-id',
      '/logistics/quality-quarantine-cases/case-id/release-authorizations',
    ]))
    expect(screen.queryByRole('button', { name: /aprobar liberación/i })).not.toBeInTheDocument()
  })

  it('abre la inspección por caso sin tratar el caseId como inspectionId', () => {
    mocks.useQuery.mockImplementation((_key, path) => ({ ...emptyQuery, data: path.endsWith('/case-id') ? caseDetail : [] }))
    renderRoute('/logistics/quality/quarantine/case-id/inspection', '/logistics/quality/quarantine/:caseId/inspection', <QualityInspectionWorkspacePage />)
    expect(mocks.useQuery).toHaveBeenCalledWith(expect.any(Array), '/logistics/quality-inspections', { quarantine_case_id: 'case-id' }, { enabled: true })
    expect(mocks.useQuery.mock.calls.some((call) => call[1] === '/logistics/quality-inspections/case-id')).toBe(false)
  })
})
