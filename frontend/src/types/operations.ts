export type Identifier = string
export type SortOrder = 'asc' | 'desc'

export interface PaginatedResponse<T> {
  items: T[]
  page: number
  page_size: number
  total: number
  total_pages: number
}

export interface ListQuery {
  page?: number
  page_size?: number
  search?: string
  sort_by?: string
  sort_order?: SortOrder
  [key: string]: string | number | boolean | null | undefined
}

export interface ActivityItem {
  event_type: string
  event_type_label: string | null
  created_at: string
  resource_type: string | null
  resource_type_label: string | null
  resource_id: string | null
}

export interface DashboardSummary {
  total_shipments: number
  pending_shipments: number
  in_transit_shipments: number
  delivered_shipments: number
  delayed_shipments: number
  open_incidents: number
  critical_incidents: number
  low_stock_items: number
  routes_today: number
  deliveries_today: number
  recent_shipments: Shipment[]
  recent_activity: ActivityItem[]
  shipments_by_status: Record<string, number>
}

export interface Client {
  id: Identifier
  document_type: string
  document_number: string
  business_name: string
  address: string
  district: string
  province: string
  department: string
  contact_name: string | null
  contact_email: string | null
  contact_phone: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export type ClientCreate = Omit<Client, 'id' | 'is_active' | 'created_at' | 'updated_at'>
export type ClientUpdate = Partial<ClientCreate> & { is_active?: boolean }

export type ShipmentStatus =
  | 'registered'
  | 'pending_pickup'
  | 'picked_up'
  | 'warehouse_received'
  | 'in_transit'
  | 'out_for_delivery'
  | 'delivered'
  | 'delayed'
  | 'cancelled'
  | 'returned'
export type ShipmentPriority = 'low' | 'normal' | 'high' | 'urgent'

export interface Shipment {
  id: Identifier
  tracking_code: string
  client_id: Identifier
  origin_address: string
  destination_address: string
  origin_district: string
  destination_district: string
  package_description: string
  package_count: number
  total_weight: string
  declared_value: string | null
  priority: ShipmentPriority
  priority_label: string
  status: ShipmentStatus
  status_label: string
  expected_delivery_at: string | null
  assigned_route_id: Identifier | null
  delivered_at: string | null
  created_by: Identifier
  created_at: string
  updated_at: string
}

export interface ShipmentCreate {
  client_id: Identifier
  origin_address: string
  destination_address: string
  origin_district: string
  destination_district: string
  package_description: string
  package_count: number
  total_weight: number
  declared_value?: number | null
  priority: ShipmentPriority
  expected_delivery_at?: string | null
}

export type ShipmentUpdate = Partial<Omit<ShipmentCreate, 'client_id'>>

export interface ShipmentEvent {
  id: Identifier
  previous_status: ShipmentStatus | null
  previous_status_label: string | null
  new_status: ShipmentStatus
  new_status_label: string
  description: string | null
  location: string | null
  created_by: Identifier
  created_at: string
}

export interface Warehouse {
  id: Identifier
  code: string
  name: string
  address: string
  district: string
  province: string
  department: string
  capacity: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface WarehouseCreate {
  code: string
  name: string
  address: string
  district: string
  province: string
  department: string
  capacity?: number | null
}
export type WarehouseUpdate = Partial<WarehouseCreate> & { is_active?: boolean }

export type MovementType = 'entry' | 'exit' | 'adjustment'
export interface InventoryItem {
  id: Identifier
  warehouse_id: Identifier
  sku: string
  name: string
  description: string | null
  current_stock: string
  minimum_stock: string
  unit: string
  is_active: boolean
  created_at: string
  updated_at: string
}
export interface InventoryItemCreate {
  warehouse_id: Identifier
  sku: string
  name: string
  description?: string | null
  current_stock: number
  minimum_stock: number
  unit: string
}
export type InventoryItemUpdate = Partial<
  Pick<InventoryItemCreate, 'name' | 'description' | 'minimum_stock' | 'unit'>
> & { is_active?: boolean }
export interface InventoryMovement {
  id: Identifier
  inventory_item_id: Identifier
  movement_type: MovementType
  quantity: string
  previous_stock: string
  resulting_stock: string
  reason: string
  shipment_id: Identifier | null
  created_by: Identifier
  created_at: string
}
export interface InventoryMovementCreate {
  inventory_item_id: Identifier
  movement_type: MovementType
  quantity: number
  reason: string
  shipment_id?: Identifier | null
  adjustment_resulting_stock?: number | null
}

export type RouteStatus = 'planned' | 'active' | 'completed' | 'cancelled'
export interface DeliveryRoute {
  id: Identifier
  route_code: string
  name: string
  origin: string
  destination: string
  scheduled_date: string
  driver_name: string | null
  vehicle_plate: string | null
  status: RouteStatus
  created_at: string
  updated_at: string
}
export interface RouteCreate {
  route_code: string
  name: string
  origin: string
  destination: string
  scheduled_date: string
  driver_name?: string | null
  vehicle_plate?: string | null
  status: RouteStatus
}
export type RouteUpdate = Partial<Omit<RouteCreate, 'route_code'>>

export type IncidentSeverity = 'low' | 'medium' | 'high' | 'critical'
export type IncidentStatus = 'open' | 'investigating' | 'resolved' | 'closed'
export type IncidentType =
  | 'delay'
  | 'damaged_package'
  | 'missing_package'
  | 'incorrect_address'
  | 'failed_delivery'
  | 'vehicle_problem'
  | 'inventory_difference'
  | 'other'
export interface Incident {
  id: Identifier
  shipment_id: Identifier | null
  incident_type: IncidentType
  title: string
  description: string
  severity: IncidentSeverity
  status: IncidentStatus
  assigned_to: Identifier | null
  reported_by: Identifier
  resolution: string | null
  resolved_at: string | null
  created_at: string
  updated_at: string
}
export interface IncidentCreate {
  shipment_id?: Identifier | null
  incident_type: IncidentType
  title: string
  description: string
  severity: IncidentSeverity
  assigned_to?: Identifier | null
}
export type IncidentUpdate = Partial<IncidentCreate> & { status?: IncidentStatus }

export interface CountGroup {
  key: string
  count: number
}
export interface DateCount {
  date: string
  count: number
}
export interface LowStockRow {
  id: Identifier
  warehouse_id: Identifier
  sku: string
  name: string
  current_stock: string
  minimum_stock: string
}
export interface RouteSummaryRow {
  route_id: Identifier
  route_code: string
  status: RouteStatus
  shipment_count: number
}
