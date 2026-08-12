import { describe, expect, it } from 'vitest'
import { permissionsFor } from './permissions'

describe('matriz de permisos operativos', () => {
  it('permite administración de investigación a admin y supervisor', () => {
    expect(permissionsFor('admin').manageResearch).toBe(true)
    expect(permissionsFor('supervisor').manageResearch).toBe(true)
    expect(permissionsFor('supervisor').viewResearchSessions).toBe(true)
  })

  it('permite movimientos al operador de almacén sin administrar rutas', () => {
    const permissions = permissionsFor('warehouse_operator')
    expect(permissions.registerMovements).toBe(true)
    expect(permissions.manageRoutes).toBe(false)
  })

  it('permite rutas al despachador y reportes al supervisor', () => {
    expect(permissionsFor('dispatcher').manageRoutes).toBe(true)
    expect(permissionsFor('supervisor').viewReports).toBe(true)
  })

  it('aplica los límites de escritura logística por rol', () => {
    const supervisor = permissionsFor('supervisor')
    const dispatcher = permissionsFor('dispatcher')
    const warehouse = permissionsFor('warehouse_operator')

    expect(supervisor.manageClients).toBe(false)
    expect(supervisor.manageShipments).toBe(false)
    expect(supervisor.manageWarehouses).toBe(false)
    expect(supervisor.manageInventory).toBe(false)
    expect(supervisor.changeShipmentStatus).toBe(true)

    expect(dispatcher.manageShipments).toBe(true)
    expect(dispatcher.manageClients).toBe(false)
    expect(dispatcher.changeShipmentStatus).toBe(true)

    expect(warehouse.manageInventory).toBe(true)
    expect(warehouse.changeShipmentStatus).toBe(false)
  })

  it('permite registrar y resolver incidencias a todos los roles', () => {
    for (const role of [
      'admin',
      'supervisor',
      'dispatcher',
      'warehouse_operator',
    ] as const) {
      expect(permissionsFor(role).manageIncidents).toBe(true)
      expect(permissionsFor(role).resolveIncidents).toBe(true)
    }
  })
})
