import type { UserRole } from '../types/user'

export interface Permissions {
  manageClients: boolean
  manageShipments: boolean
  changeShipmentStatus: boolean
  manageWarehouses: boolean
  manageInventory: boolean
  registerMovements: boolean
  manageRoutes: boolean
  manageIncidents: boolean
  resolveIncidents: boolean
  viewReports: boolean
  manageResearch: boolean
  viewResearchSessions: boolean
  viewContinuousAuthAdmin: boolean
}

const none: Permissions = {
  manageClients: false,
  manageShipments: false,
  changeShipmentStatus: false,
  manageWarehouses: false,
  manageInventory: false,
  registerMovements: false,
  manageRoutes: false,
  manageIncidents: false,
  resolveIncidents: false,
  viewReports: false,
  manageResearch: false,
  viewResearchSessions: false,
  viewContinuousAuthAdmin: false,
}

export function permissionsFor(role: UserRole | string): Permissions {
  if (role === 'admin') {
    return Object.fromEntries(
      Object.keys(none).map((key) => [key, true]),
    ) as unknown as Permissions
  }
  if (role === 'supervisor') {
    return {
      ...none,
      changeShipmentStatus: true,
      manageRoutes: true,
      manageIncidents: true,
      resolveIncidents: true,
      viewReports: true,
      manageResearch: true,
      viewResearchSessions: true,
      viewContinuousAuthAdmin: true,
    }
  }
  if (role === 'dispatcher') {
    return {
      ...none,
      manageShipments: true,
      changeShipmentStatus: true,
      manageRoutes: true,
      manageIncidents: true,
      resolveIncidents: true,
    }
  }
  if (role === 'warehouse_operator') {
    return {
      ...none,
      changeShipmentStatus: false,
      manageInventory: true,
      registerMovements: true,
      manageIncidents: true,
      resolveIncidents: true,
    }
  }
  return none
}
