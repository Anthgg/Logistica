import type { ShipmentStatus } from '../../types/operations'
import type { SupportedLanguage } from '../../types/i18n'

export const SHIPMENT_STATUS_LABELS: Record<
  SupportedLanguage | 'es' | 'en' | 'pt',
  Record<ShipmentStatus, string>
> = {
  'es-PE': {
    registered: 'Registrado',
    pending_pickup: 'Pendiente de recojo',
    picked_up: 'Recogido',
    warehouse_received: 'Recibido en almacén',
    in_transit: 'En tránsito',
    out_for_delivery: 'En reparto',
    delivered: 'Entregado',
    delayed: 'Retrasado',
    cancelled: 'Cancelado',
    returned: 'Devuelto',
  },
  es: {
    registered: 'Registrado',
    pending_pickup: 'Pendiente de recojo',
    picked_up: 'Recogido',
    warehouse_received: 'Recibido en almacén',
    in_transit: 'En tránsito',
    out_for_delivery: 'En reparto',
    delivered: 'Entregado',
    delayed: 'Retrasado',
    cancelled: 'Cancelado',
    returned: 'Devuelto',
  },
  'en-US': {
    registered: 'Registered',
    pending_pickup: 'Pending pickup',
    picked_up: 'Picked up',
    warehouse_received: 'Warehouse received',
    in_transit: 'In transit',
    out_for_delivery: 'Out for delivery',
    delivered: 'Delivered',
    delayed: 'Delayed',
    cancelled: 'Cancelled',
    returned: 'Returned',
  },
  en: {
    registered: 'Registered',
    pending_pickup: 'Pending pickup',
    picked_up: 'Picked up',
    warehouse_received: 'Warehouse received',
    in_transit: 'In transit',
    out_for_delivery: 'Out for delivery',
    delivered: 'Delivered',
    delayed: 'Delayed',
    cancelled: 'Cancelled',
    returned: 'Returned',
  },
  'pt-BR': {
    registered: 'Registrado',
    pending_pickup: 'Pendente de coleta',
    picked_up: 'Coletado',
    warehouse_received: 'Recebido no armazém',
    in_transit: 'Em trânsito',
    out_for_delivery: 'Saiu para entrega',
    delivered: 'Entregue',
    delayed: 'Atrasado',
    cancelled: 'Cancelado',
    returned: 'Devolvido',
  },
  pt: {
    registered: 'Registrado',
    pending_pickup: 'Pendente de coleta',
    picked_up: 'Coletado',
    warehouse_received: 'Recebido no armazém',
    in_transit: 'Em trânsito',
    out_for_delivery: 'Saiu para entrega',
    delivered: 'Entregue',
    delayed: 'Atrasado',
    cancelled: 'Cancelado',
    returned: 'Devolvido',
  },
}

export function getShipmentStatusLabel(
  status: ShipmentStatus,
  language: string,
  backendLabel?: string | null,
): string {
  if (backendLabel && backendLabel.trim()) return backendLabel
  const langKey = (language as SupportedLanguage) || 'es-PE'
  const catalog = SHIPMENT_STATUS_LABELS[langKey] || SHIPMENT_STATUS_LABELS['es-PE']
  return catalog[status] || status
}
