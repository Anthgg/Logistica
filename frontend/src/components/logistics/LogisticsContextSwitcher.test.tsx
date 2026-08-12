import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { LogisticsContextSwitcher } from './LogisticsContextSwitcher'
import { LogisticsAccessContext } from '../../features/logistics-me/contexts/logistics-access-context'
import { createLogisticsAccessState } from '../../features/logistics-me/test/test-utils'
import type { LogisticsAccessState } from '../../features/logistics-me/contexts/logistics-access-context'

const useQueryMock = vi.hoisted(() => vi.fn())

vi.mock('../../features/inbound-docks/hooks/useQuery', () => ({
  useQuery: useQueryMock,
}))

function renderSwitcher(
  overrides: Parameters<typeof createLogisticsAccessState>[0] = {},
  stateOverrides: Partial<LogisticsAccessState> = {},
) {
  const state = { ...createLogisticsAccessState(overrides), ...stateOverrides }
  return render(
    <MemoryRouter>
      <LogisticsAccessContext.Provider value={state}>
        <LogisticsContextSwitcher />
      </LogisticsAccessContext.Provider>
    </MemoryRouter>,
  )
}

describe('LogisticsContextSwitcher', () => {
  beforeEach(() => {
    useQueryMock.mockReturnValue({
      data: undefined,
      isLoading: false,
      isFetching: false,
      isError: false,
      error: null,
      errorCode: null,
      status: null,
      refetch: vi.fn(),
      setData: vi.fn(),
    })
  })

  it('muestra botón de cambiar cuando hay múltiples opciones', () => {
    renderSwitcher({
      me: { organizations: ['org-1', 'org-2'], branches: ['b1', 'b2'], warehouses: ['w1', 'w2'] },
    })
    expect(screen.getByText('Cambiar')).toBeInTheDocument()
  })

  it('no renderiza cuando solo hay una opción en todo', () => {
    renderSwitcher({
      me: { organizations: ['org-1'], branches: ['b1'], warehouses: ['w1'] },
    })
    expect(screen.queryByText('Cambiar')).not.toBeInTheDocument()
  })

  it('abre el selector al hacer clic en Cambiar', async () => {
    const user = userEvent.setup()
    renderSwitcher({
      me: { organizations: ['org-1', 'org-2'], branches: [], warehouses: [] },
    })
    await user.click(screen.getByText('Cambiar'))
    expect(screen.getByText('Cambiar contexto organizacional')).toBeInTheDocument()
    expect(screen.getByText('Organización')).toBeInTheDocument()
  })

  it('muestra las organizaciones autorizadas como opciones', async () => {
    const user = userEvent.setup()
    renderSwitcher({
      me: { organizations: ['org-1', 'org-2'], branches: [], warehouses: [] },
    })
    await user.click(screen.getByText('Cambiar'))
    const select = screen.getByRole('combobox', { name: /organización/i }) as HTMLSelectElement
    const options = Array.from(select.options).map((o) => o.value)
    expect(options).toContain('org-1')
    expect(options).toContain('org-2')
  })

  it('permite elegir organización cuando el acceso global no trae scopes en /me', async () => {
    useQueryMock.mockReturnValue({
      data: {
        items: [
          {
            id: 'org-global-1',
            code: 'ORG-001',
            name: 'Organización global',
            status: 'active',
            country_code: 'PE',
            timezone: 'America/Lima',
            created_at: '2026-01-01T00:00:00Z',
            updated_at: '2026-01-01T00:00:00Z',
          },
        ],
        page: 1,
        page_size: 100,
        total: 1,
        total_pages: 1,
      },
      isLoading: false,
      isFetching: false,
      isError: false,
      error: null,
      errorCode: null,
      status: null,
      refetch: vi.fn(),
      setData: vi.fn(),
    })

    const user = userEvent.setup()
    renderSwitcher({
      me: { organizations: [], branches: [], warehouses: [] },
      currentContext: { organization_id: null, branch_id: null, warehouse_id: null },
    })

    expect(useQueryMock).toHaveBeenCalled()
    expect(useQueryMock.mock.results.at(-1)?.value.data.items).toHaveLength(1)
    await user.click(screen.getByText('Cambiar'))
    expect(screen.getByRole('option', { name: 'Organización global (ORG-001)' })).toBeInTheDocument()
  })

  it('conserva el contexto seleccionado sin recargar /me', async () => {
    const changeContext = vi.fn().mockResolvedValue(true)
    const refreshLogisticsSession = vi.fn().mockResolvedValue(undefined)
    const user = userEvent.setup()
    renderSwitcher(
      { me: { organizations: ['org-1', 'org-2'], branches: [], warehouses: [] } },
      { changeContext, refreshLogisticsSession },
    )

    await user.click(screen.getByText('Cambiar'))
    await user.selectOptions(screen.getByRole('combobox', { name: /organización/i }), 'org-2')
    await user.click(screen.getByRole('button', { name: 'Confirmar contexto' }))

    expect(changeContext).toHaveBeenCalledWith({
      organization_id: 'org-2',
      branch_id: null,
      warehouse_id: null,
    })
    expect(refreshLogisticsSession).not.toHaveBeenCalled()
  })

  it('muestra error de contexto cuando existe', async () => {
    const user = userEvent.setup()
    renderSwitcher({
      me: { organizations: ['org-1', 'org-2'] },
      contextError: 'El contexto seleccionado no es válido.',
    })
    await user.click(screen.getByText('Cambiar'))
    expect(screen.getByText('El contexto seleccionado no es válido.')).toBeInTheDocument()
  })
})
