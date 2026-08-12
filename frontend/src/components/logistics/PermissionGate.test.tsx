import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PermissionGate } from './PermissionGate'
import {
  createLogisticsAuthState,
  renderWithLogisticsAuth,
} from '../../features/logistics-permissions/test/test-utils'
import { LOGISTICS_PERMISSIONS } from '../../features/logistics-permissions/logistics-permissions-map'

describe('PermissionGate - autorizado', () => {
  it('renderiza children cuando tiene el permiso', () => {
    const state = createLogisticsAuthState({
      permissions: [LOGISTICS_PERMISSIONS.warehouses.create],
    })
    renderWithLogisticsAuth(
      <PermissionGate permission={LOGISTICS_PERMISSIONS.warehouses.create}>
        <button>Crear almacén</button>
      </PermissionGate>,
      state,
    )
    expect(screen.getByText('Crear almacén')).toBeInTheDocument()
  })

  it('anyOf concede si al menos uno existe', () => {
    const state = createLogisticsAuthState({
      permissions: [LOGISTICS_PERMISSIONS.documents.download],
    })
    renderWithLogisticsAuth(
      <PermissionGate
        anyOf={[LOGISTICS_PERMISSIONS.documents.download, LOGISTICS_PERMISSIONS.documents.export]}
      >
        <button>Descargar</button>
      </PermissionGate>,
      state,
    )
    expect(screen.getByText('Descargar')).toBeInTheDocument()
  })

  it('allOf concede si todos existen', () => {
    const state = createLogisticsAuthState({
      permissions: [
        LOGISTICS_PERMISSIONS.warehouses.read,
        LOGISTICS_PERMISSIONS.warehouses.create,
      ],
    })
    renderWithLogisticsAuth(
      <PermissionGate
        allOf={[LOGISTICS_PERMISSIONS.warehouses.read, LOGISTICS_PERMISSIONS.warehouses.create]}
      >
        <button>Gestionar</button>
      </PermissionGate>,
      state,
    )
    expect(screen.getByText('Gestionar')).toBeInTheDocument()
  })
})

describe('PermissionGate - denegado', () => {
  it('oculta children por defecto (hide)', () => {
    const state = createLogisticsAuthState({ permissions: [] })
    renderWithLogisticsAuth(
      <PermissionGate permission={LOGISTICS_PERMISSIONS.warehouses.create}>
        <button>Crear almacén</button>
      </PermissionGate>,
      state,
    )
    expect(screen.queryByText('Crear almacén')).not.toBeInTheDocument()
  })

  it('renderiza fallback cuando se provee', () => {
    const state = createLogisticsAuthState({ permissions: [] })
    renderWithLogisticsAuth(
      <PermissionGate
        permission={LOGISTICS_PERMISSIONS.warehouses.create}
        fallback={<p>Sin acceso</p>}
      >
        <button>Crear almacén</button>
      </PermissionGate>,
      state,
    )
    expect(screen.getByText('Sin acceso')).toBeInTheDocument()
    expect(screen.queryByText('Crear almacén')).not.toBeInTheDocument()
  })

  it('muestra acción deshabilitada con explicación en modo disable', () => {
    const state = createLogisticsAuthState({ permissions: [] })
    renderWithLogisticsAuth(
      <PermissionGate
        permission={LOGISTICS_PERMISSIONS.warehouses.create}
        mode="disable"
        disabledReason="Requiere permiso logistics.warehouses.create"
      >
        <button>Crear almacén</button>
      </PermissionGate>,
      state,
    )
    expect(screen.getByText('Crear almacén')).toBeInTheDocument()
    expect(screen.getByText('Requiere permiso logistics.warehouses.create')).toBeInTheDocument()
  })
})

describe('PermissionGate - loading', () => {
  it('oculta children mientras carga', () => {
    const state = createLogisticsAuthState({
      isLoading: true,
      permissions: [LOGISTICS_PERMISSIONS.warehouses.create],
    })
    renderWithLogisticsAuth(
      <PermissionGate permission={LOGISTICS_PERMISSIONS.warehouses.create}>
        <button>Crear almacén</button>
      </PermissionGate>,
      state,
    )
    expect(screen.queryByText('Crear almacén')).not.toBeInTheDocument()
  })
})

describe('PermissionGate - scope', () => {
  it('deniega cuando el scope no coincide', () => {
    const state = createLogisticsAuthState({
      permissions: [LOGISTICS_PERMISSIONS.warehouses.read],
      organizationId: 'org-otra',
    })
    renderWithLogisticsAuth(
      <PermissionGate
        permission={LOGISTICS_PERMISSIONS.warehouses.read}
        scope={{ organization_id: 'org-1', branch_id: null, warehouse_id: null }}
        fallback={<p>scope denegado</p>}
      >
        <button>Ver</button>
      </PermissionGate>,
      state,
    )
    expect(screen.getByText('scope denegado')).toBeInTheDocument()
    expect(screen.queryByText('Ver')).not.toBeInTheDocument()
  })
})

describe('PermissionGate - sin provider', () => {
  it('deniega por defecto (estado default isLoading)', () => {
    render(
      <PermissionGate permission={LOGISTICS_PERMISSIONS.warehouses.read}>
        <button>Ver</button>
      </PermissionGate>,
    )
    expect(screen.queryByText('Ver')).not.toBeInTheDocument()
  })
})