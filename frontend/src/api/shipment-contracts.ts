import { ApiRequestError } from '../types/api'
import type {
  PaginatedResponse,
  Shipment,
  ShipmentEvent,
  ShipmentPriority,
  ShipmentStatus,
} from '../types/operations'

const shipmentStatuses = new Set<ShipmentStatus>([
  'registered',
  'pending_pickup',
  'picked_up',
  'warehouse_received',
  'in_transit',
  'out_for_delivery',
  'delivered',
  'delayed',
  'cancelled',
  'returned',
])
const shipmentPriorities = new Set<ShipmentPriority>([
  'low',
  'normal',
  'high',
  'urgent',
])

function invalidResponse(): never {
  throw new ApiRequestError(
    'El servidor devolvió un contrato de envíos inválido.',
    { code: 'INVALID_RESPONSE' },
  )
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function stringValue(value: unknown): string {
  return typeof value === 'string' ? value : invalidResponse()
}

function nullableString(value: unknown): string | null {
  return value === null ? null : stringValue(value)
}

function numberValue(value: unknown): number {
  return typeof value === 'number' && Number.isFinite(value)
    ? value
    : invalidResponse()
}

function shipmentStatus(value: unknown): ShipmentStatus {
  return (
    typeof value === 'string' &&
    shipmentStatuses.has(value as ShipmentStatus)
  )
    ? (value as ShipmentStatus)
    : invalidResponse()
}

function nullableShipmentStatus(
  value: unknown,
): ShipmentStatus | null {
  return value === null ? null : shipmentStatus(value)
}

function shipmentPriority(value: unknown): ShipmentPriority {
  return (
    typeof value === 'string' &&
    shipmentPriorities.has(value as ShipmentPriority)
  )
    ? (value as ShipmentPriority)
    : invalidResponse()
}

export function parseShipment(value: unknown): Shipment {
  if (!isRecord(value)) {
    return invalidResponse()
  }

  return {
    id: stringValue(value.id),
    tracking_code: stringValue(value.tracking_code),
    client_id: stringValue(value.client_id),
    origin_address: stringValue(value.origin_address),
    destination_address: stringValue(value.destination_address),
    origin_district: stringValue(value.origin_district),
    destination_district: stringValue(value.destination_district),
    package_description: stringValue(value.package_description),
    package_count: numberValue(value.package_count),
    total_weight: stringValue(value.total_weight),
    declared_value: nullableString(value.declared_value),
    priority: shipmentPriority(value.priority),
    priority_label: stringValue(value.priority_label),
    status: shipmentStatus(value.status),
    status_label: stringValue(value.status_label),
    expected_delivery_at: nullableString(value.expected_delivery_at),
    assigned_route_id: nullableString(value.assigned_route_id),
    delivered_at: nullableString(value.delivered_at),
    created_by: stringValue(value.created_by),
    created_at: stringValue(value.created_at),
    updated_at: stringValue(value.updated_at),
  }
}

export function parseShipmentPage(
  value: unknown,
): PaginatedResponse<Shipment> {
  if (!isRecord(value) || !Array.isArray(value.items)) {
    return invalidResponse()
  }

  return {
    items: value.items.map(parseShipment),
    page: numberValue(value.page),
    page_size: numberValue(value.page_size),
    total: numberValue(value.total),
    total_pages: numberValue(value.total_pages),
  }
}

export function parseShipmentEvent(value: unknown): ShipmentEvent {
  if (!isRecord(value)) {
    return invalidResponse()
  }

  return {
    id: stringValue(value.id),
    previous_status: nullableShipmentStatus(value.previous_status),
    previous_status_label: nullableString(
      value.previous_status_label,
    ),
    new_status: shipmentStatus(value.new_status),
    new_status_label: stringValue(value.new_status_label),
    description: nullableString(value.description),
    location: nullableString(value.location),
    created_by: stringValue(value.created_by),
    created_at: stringValue(value.created_at),
  }
}

export function parseShipmentTimeline(
  value: unknown,
): ShipmentEvent[] {
  return Array.isArray(value)
    ? value.map(parseShipmentEvent)
    : invalidResponse()
}
