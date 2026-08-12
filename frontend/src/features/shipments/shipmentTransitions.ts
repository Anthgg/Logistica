import type { ShipmentStatus } from '../../types/operations'

export const SHIPMENT_TRANSITIONS: Record<ShipmentStatus, ShipmentStatus[]> = {
  registered: ['pending_pickup', 'cancelled'],
  pending_pickup: ['picked_up', 'delayed', 'cancelled'],
  picked_up: [
    'warehouse_received',
    'in_transit',
    'delayed',
    'cancelled',
  ],
  warehouse_received: [
    'in_transit',
    'delayed',
    'returned',
    'cancelled',
  ],
  in_transit: [
    'out_for_delivery',
    'delayed',
    'returned',
  ],
  out_for_delivery: [
    'delivered',
    'delayed',
    'returned',
  ],
  delayed: [
    'pending_pickup',
    'picked_up',
    'warehouse_received',
    'in_transit',
    'out_for_delivery',
    'returned',
    'cancelled',
  ],
  delivered: ['returned'],
  cancelled: [],
  returned: [],
}

export const ALL_SHIPMENT_STATUSES: ShipmentStatus[] = [
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
]

export function isAllowedTransition(
  currentStatus: ShipmentStatus,
  targetStatus: ShipmentStatus,
): boolean {
  if (currentStatus === targetStatus) return false
  const allowed = SHIPMENT_TRANSITIONS[currentStatus] || []
  return allowed.includes(targetStatus)
}
