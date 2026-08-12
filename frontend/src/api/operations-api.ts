import { apiRequest } from './api-client'
import {
  parseShipment,
  parseShipmentPage,
  parseShipmentTimeline,
} from './shipment-contracts'
import type {
  Client,
  ClientCreate,
  ClientUpdate,
  CountGroup,
  DashboardSummary,
  DateCount,
  DeliveryRoute,
  Incident,
  IncidentCreate,
  IncidentUpdate,
  InventoryItem,
  InventoryItemCreate,
  InventoryItemUpdate,
  InventoryMovement,
  InventoryMovementCreate,
  ListQuery,
  LowStockRow,
  PaginatedResponse,
  RouteCreate,
  RouteSummaryRow,
  RouteUpdate,
  Shipment,
  ShipmentCreate,
  ShipmentStatus,
  ShipmentUpdate,
  Warehouse,
  WarehouseCreate,
  WarehouseUpdate,
} from '../types/operations'

function withQuery(path: string, query: ListQuery = {}): string {
  const params = new URLSearchParams()
  Object.entries(query).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      params.set(key, String(value))
    }
  })
  const suffix = params.toString()
  return suffix ? `${path}?${suffix}` : path
}

function list<T>(path: string, query?: ListQuery) {
  return apiRequest<PaginatedResponse<T>>({ path: withQuery(path, query) })
}

export const operationsApi = {
  // Sistema & Diagnóstico
  health: () => apiRequest<{ status: string; database: string }>({ path: '/health' }),

  // Dashboard
  dashboard: () => apiRequest<DashboardSummary>({ path: '/dashboard/summary' }),

  // Clientes
  clients: {
    list: (query?: ListQuery) => list<Client>('/clients', query),
    get: (id: string) => apiRequest<Client>({ path: `/clients/${id}` }),
    create: (body: ClientCreate) =>
      apiRequest<Client>({ path: '/clients', method: 'POST', body }),
    update: (id: string, body: ClientUpdate) =>
      apiRequest<Client>({ path: `/clients/${id}`, method: 'PATCH', body }),
    remove: (id: string) =>
      apiRequest<void>({ path: `/clients/${id}`, method: 'DELETE' }),
  },

  // Envíos
  shipments: {
    list: async (query?: ListQuery) => {
      const response = await apiRequest<unknown>({
        path: withQuery('/shipments', {
          page: 1,
          page_size: 20,
          sort_by: 'created_at',
          sort_order: 'desc',
          ...query,
        }),
      })
      return parseShipmentPage(response)
    },
    get: async (id: string) => {
      const response = await apiRequest<unknown>({
        path: `/shipments/${id}`,
      })
      return parseShipment(response)
    },
    create: async (body: ShipmentCreate) => {
      const response = await apiRequest<unknown>({
        path: '/shipments',
        method: 'POST',
        body,
      })
      return parseShipment(response)
    },
    update: async (id: string, body: ShipmentUpdate) => {
      const response = await apiRequest<unknown>({
        path: `/shipments/${id}`,
        method: 'PATCH',
        body,
      })
      return parseShipment(response)
    },
    status: (
      id: string,
      body: {
        status: ShipmentStatus
        description?: string | null
        location?: string | null
      },
    ) => apiRequest<unknown>({
        path: `/shipments/${id}/status`,
        method: 'POST',
        body: {
          status: body.status,
          location: body.location?.trim() || null,
          description: body.description?.trim() || null,
        },
      }).then(parseShipment),
    timeline: (id: string) =>
      apiRequest<unknown>({
        path: `/shipments/${id}/timeline`,
      }).then(parseShipmentTimeline),
  },

  // Almacenes
  warehouses: {
    list: (query?: ListQuery) => list<Warehouse>('/warehouses', query),
    get: (id: string) => apiRequest<Warehouse>({ path: `/warehouses/${id}` }),
    create: (body: WarehouseCreate) =>
      apiRequest<Warehouse>({ path: '/warehouses', method: 'POST', body }),
    update: (id: string, body: WarehouseUpdate) =>
      apiRequest<Warehouse>({ path: `/warehouses/${id}`, method: 'PATCH', body }),
    remove: (id: string) =>
      apiRequest<void>({ path: `/warehouses/${id}`, method: 'DELETE' }),
  },

  // Inventario
  inventory: {
    list: (query?: ListQuery) => list<InventoryItem>('/inventory', query),
    get: (id: string) => apiRequest<InventoryItem>({ path: `/inventory/${id}` }),
    create: (body: InventoryItemCreate) =>
      apiRequest<InventoryItem>({ path: '/inventory', method: 'POST', body }),
    update: (id: string, body: InventoryItemUpdate) =>
      apiRequest<InventoryItem>({ path: `/inventory/${id}`, method: 'PATCH', body }),
    movements: (query?: ListQuery) =>
      list<InventoryMovement>('/inventory/movements', query),
    createMovement: (body: InventoryMovementCreate) =>
      apiRequest<InventoryMovement>({
        path: '/inventory/movements',
        method: 'POST',
        body,
      }),
  },

  // Rutas logísticas
  routes: {
    list: (query?: ListQuery) => list<DeliveryRoute>('/routes', query),
    get: (id: string) => apiRequest<DeliveryRoute>({ path: `/routes/${id}` }),
    create: (body: RouteCreate) =>
      apiRequest<DeliveryRoute>({ path: '/routes', method: 'POST', body }),
    update: (id: string, body: RouteUpdate) =>
      apiRequest<DeliveryRoute>({ path: `/routes/${id}`, method: 'PATCH', body }),
    assign: (id: string, shipmentIds: string[]) =>
      apiRequest<Shipment[]>({
        path: `/routes/${id}/assign-shipments`,
        method: 'POST',
        body: { shipment_ids: shipmentIds },
      }),
    unassign: (routeId: string, shipmentId: string) =>
      apiRequest<void>({
        path: `/routes/${routeId}/shipments/${shipmentId}`,
        method: 'DELETE',
      }),
  },

  // Incidencias
  incidents: {
    list: (query?: ListQuery) => list<Incident>('/incidents', query),
    get: (id: string) => apiRequest<Incident>({ path: `/incidents/${id}` }),
    create: (body: IncidentCreate) =>
      apiRequest<Incident>({ path: '/incidents', method: 'POST', body }),
    update: (id: string, body: IncidentUpdate) =>
      apiRequest<Incident>({ path: `/incidents/${id}`, method: 'PATCH', body }),
    resolve: (id: string, resolution: string) =>
      apiRequest<Incident>({
        path: `/incidents/${id}/resolve`,
        method: 'POST',
        body: { resolution },
      }),
  },

  // Reportes
  reports: {
    count: (name: 'shipments-by-status' | 'shipments-by-priority' | 'incidents-summary', query?: ListQuery) =>
      apiRequest<CountGroup[]>({ path: withQuery(`/reports/${name}`, query) }),
    deliveries: (query?: ListQuery) =>
      apiRequest<DateCount[]>({ path: withQuery('/reports/deliveries-by-date', query) }),
    lowStock: (query?: ListQuery) =>
      apiRequest<LowStockRow[]>({ path: withQuery('/reports/low-stock', query) }),
    routes: (query?: ListQuery) =>
      apiRequest<RouteSummaryRow[]>({ path: withQuery('/reports/routes-summary', query) }),
  },

}
