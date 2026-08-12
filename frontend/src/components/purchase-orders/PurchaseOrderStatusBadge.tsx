import type { PurchaseOrderStatus } from '../../types/purchase-orders'

interface Props {
  status: PurchaseOrderStatus
  size?: 'sm' | 'md'
}

const STATUS_CONFIG: Record<
  PurchaseOrderStatus,
  { label: string; className: string }
> = {
  DRAFT: {
    label: 'Borrador',
    className: 'bg-slate-100 text-slate-600 border border-slate-300',
  },
  APPROVED: {
    label: 'Aprobada',
    className: 'bg-blue-100 text-blue-700 border border-blue-300',
  },
  ISSUED: {
    label: 'Emitida',
    className: 'bg-cyan-100 text-cyan-700 border border-cyan-300',
  },
  CONFIRMED: {
    label: 'Confirmada',
    className: 'bg-emerald-100 text-emerald-700 border border-emerald-300',
  },
  PARTIALLY_RECEIVED: {
    label: 'Recibida parcialmente',
    className: 'bg-violet-100 text-violet-700 border border-violet-300',
  },
  ANNULLED: {
    label: 'Anulada',
    className: 'bg-red-100 text-red-700 border border-red-300',
  },
  CLOSED: {
    label: 'Cerrada',
    className: 'bg-gray-200 text-gray-600 border border-gray-300',
  },
}

export function PurchaseOrderStatusBadge({ status, size = 'md' }: Props) {
  const cfg = STATUS_CONFIG[status] ?? {
    label: status,
    className: 'bg-gray-100 text-gray-600 border border-gray-300',
  }

  const sizeClass = size === 'sm' ? 'text-xs px-2 py-0.5' : 'text-sm px-3 py-1'

  return (
    <span
      className={`inline-flex items-center rounded-full font-medium ${sizeClass} ${cfg.className}`}
    >
      {cfg.label}
    </span>
  )
}
