import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { FloatingNavigationBar } from './FloatingNavigationBar'
import { NAVIGATION_GROUPS } from './nav-modules.config'

const permissionState = { permissions: new Set<string>(), isLoading: false }

vi.mock('../../features/logistics-permissions/hooks/useLogisticsPermissions', () => ({
  useLogisticsPermissions: () => ({
    isLoading: permissionState.isLoading,
    hasPermission: (code: string) => permissionState.permissions.has(code),
    hasAnyPermission: (codes: readonly string[]) =>
      codes.some((code) => permissionState.permissions.has(code)),
  }),
}))

function renderBar(pathname: string) {
  return render(
    <MemoryRouter initialEntries={[pathname]}>
      <FloatingNavigationBar />
    </MemoryRouter>,
  )
}

function grantPermissions(...codes: string[]) {
  permissionState.permissions = new Set(codes)
}

beforeEach(() => {
  localStorage.clear()
  permissionState.isLoading = false
  grantPermissions()
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('FloatingNavigationBar · visibilidad por permisos', () => {
  it('no muestra un grupo cuando el usuario no tiene ninguno de sus permisos', () => {
    renderBar('/dashboard')

    expect(
      screen.queryByRole('button', { name: new RegExp(NAVIGATION_GROUPS.fleet.label, 'i') }),
    ).not.toBeInTheDocument()
  })

  it('convierte el grupo en acceso directo cuando solo un hijo es visible', async () => {
    grantPermissions('logistics.vehicles.verify')
    renderBar('/dashboard')

    expect(
      screen.getByRole('link', { name: 'Verificaciones Vehiculares' }),
    ).toBeInTheDocument()
    expect(
      screen.queryByRole('button', { name: /Abrir Flota/i }),
    ).not.toBeInTheDocument()
  })

  it('muestra el grupo cuando hay dos o más hijos permitidos', async () => {
    grantPermissions('logistics.vehicles.read', 'logistics.vehicles.verify')
    renderBar('/dashboard')

    const trigger = screen.getByRole('button', { name: /Abrir Flota/i })
    expect(trigger).toHaveAttribute('aria-expanded', 'false')
    expect(trigger).toHaveAttribute('aria-haspopup', 'menu')
  })

  it('el desplegable solo lista los hijos permitidos', async () => {
    const user = userEvent.setup()
    grantPermissions('logistics.vehicles.read', 'logistics.vehicles.verify')
    renderBar('/dashboard')

    await user.click(screen.getByRole('button', { name: /Abrir Flota/i }))
    const menu = screen.getByRole('menu', { name: 'Flota' })

    expect(within(menu).getByRole('menuitem', { name: /Vehículos & Flota/ })).toBeInTheDocument()
    expect(within(menu).getByRole('menuitem', { name: /Verificaciones Vehiculares/ })).toBeInTheDocument()
    // Marcas y Modelos comparten permiso con Vehículos, así que también entran.
    expect(within(menu).getAllByRole('menuitem')).toHaveLength(4)
  })

  it('no muestra nada mientras los permisos están cargando salvo los módulos legacy', () => {
    permissionState.isLoading = true
    renderBar('/dashboard')

    expect(screen.getByRole('link', { name: 'Panel principal' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Abrir Flota/i })).not.toBeInTheDocument()
  })
})

describe('FloatingNavigationBar · estado activo', () => {
  it('marca un único módulo activo aunque las rutas se solapen', () => {
    grantPermissions('logistics.putaway.read', 'logistics.putaway.execute')
    renderBar('/logistics/putaway/mobile')

    const activos = screen.getAllByRole('button', { name: /Abrir Inventario/i })
    expect(activos).toHaveLength(1)
    expect(document.querySelectorAll('[aria-current="page"]')).toHaveLength(0)
  })

  it('el hijo activo dentro del desplegable es exactamente uno', async () => {
    const user = userEvent.setup()
    grantPermissions('logistics.putaway.read', 'logistics.putaway.execute')
    renderBar('/logistics/putaway/mobile')

    await user.click(screen.getByRole('button', { name: /Abrir Inventario/i }))
    const menu = screen.getByRole('menu', { name: 'Inventario' })
    const current = within(menu)
      .getAllByRole('menuitem')
      .filter((item) => item.getAttribute('aria-current') === 'page')

    expect(current).toHaveLength(1)
    expect(current[0]).toHaveAccessibleName(/Ubicación Móvil/)
  })
})

describe('FloatingNavigationBar · accesibilidad del desplegable', () => {
  it('se abre con flecha abajo y enfoca la primera opción', async () => {
    const user = userEvent.setup()
    grantPermissions('logistics.vehicles.read', 'logistics.vehicles.verify')
    renderBar('/dashboard')

    const trigger = screen.getByRole('button', { name: /Abrir Flota/i })
    trigger.focus()
    await user.keyboard('{ArrowDown}')

    const menu = await screen.findByRole('menu', { name: 'Flota' })
    expect(trigger).toHaveAttribute('aria-expanded', 'true')
    expect(within(menu).getAllByRole('menuitem')[0]).toHaveFocus()
  })

  it('las flechas recorren las opciones y Escape devuelve el foco al botón', async () => {
    const user = userEvent.setup()
    grantPermissions('logistics.vehicles.read', 'logistics.vehicles.verify')
    renderBar('/dashboard')

    const trigger = screen.getByRole('button', { name: /Abrir Flota/i })
    trigger.focus()
    await user.keyboard('{ArrowDown}')

    const items = within(await screen.findByRole('menu', { name: 'Flota' })).getAllByRole('menuitem')
    await user.keyboard('{ArrowDown}')
    expect(items[1]).toHaveFocus()
    await user.keyboard('{End}')
    expect(items.at(-1)).toHaveFocus()
    await user.keyboard('{Home}')
    expect(items[0]).toHaveFocus()

    await user.keyboard('{Escape}')
    expect(screen.queryByRole('menu', { name: 'Flota' })).not.toBeInTheDocument()
    expect(trigger).toHaveFocus()
  })

  it('el botón del grupo expone cuántas opciones contiene', () => {
    grantPermissions('logistics.vehicles.read', 'logistics.vehicles.verify')
    renderBar('/dashboard')

    expect(
      screen.getByRole('button', { name: /Abrir Flota.*\(4 opciones\)/i }),
    ).toBeInTheDocument()
  })
})
