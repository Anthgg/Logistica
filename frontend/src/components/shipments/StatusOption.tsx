import type { ShipmentStatus } from '../../types/operations'
import { StatusBadge } from '../common/StatusBadge'

interface StatusMeta {
  label: string
  description: string
  dotColor: string
  badgeTone: 'blue' | 'slate' | 'emerald' | 'amber' | 'rose'
}

const statusDescriptions: Record<ShipmentStatus, StatusMeta> = {
  registered: {
    label: 'Registrado',
    description: 'El envío fue registrado en el sistema.',
    dotColor: 'bg-slate-400',
    badgeTone: 'slate',
  },
  pending_pickup: {
    label: 'Pendiente de recojo',
    description: 'El paquete se encuentra listo para su recojo.',
    dotColor: 'bg-amber-500',
    badgeTone: 'amber',
  },
  picked_up: {
    label: 'Recogido',
    description: 'El paquete fue recogido en el punto de origen.',
    dotColor: 'bg-blue-600',
    badgeTone: 'blue',
  },
  warehouse_received: {
    label: 'Recibido en almacén',
    description: 'Ingresó al centro de distribución principal.',
    dotColor: 'bg-indigo-600',
    badgeTone: 'blue',
  },
  in_transit: {
    label: 'En tránsito',
    description: 'En traslado hacia el almacén o ciudad de destino.',
    dotColor: 'bg-purple-600',
    badgeTone: 'blue',
  },
  out_for_delivery: {
    label: 'En reparto',
    description: 'Asignado a unidad móvil para entrega final.',
    dotColor: 'bg-sky-600',
    badgeTone: 'blue',
  },
  delivered: {
    label: 'Entregado',
    description: 'El paquete fue entregado al destinatario.',
    dotColor: 'bg-emerald-600',
    badgeTone: 'emerald',
  },
  delayed: {
    label: 'Retrasado',
    description: 'El envío presenta una demora o incidencia operativa.',
    dotColor: 'bg-rose-500',
    badgeTone: 'rose',
  },
  cancelled: {
    label: 'Cancelado',
    description: 'El proceso de envío fue cancelado.',
    dotColor: 'bg-slate-600',
    badgeTone: 'slate',
  },
  returned: {
    label: 'Devuelto',
    description: 'El paquete fue retornado a origen o almacén.',
    dotColor: 'bg-rose-600',
    badgeTone: 'rose',
  },
}

interface Props {
  status: ShipmentStatus
}

export function StatusOption({ status }: Props) {
  const meta = statusDescriptions[status] ?? {
    label: status,
    description: 'Cambio de estado operativo.',
    dotColor: 'bg-slate-400',
    badgeTone: 'slate',
  }

  return (
    <div className="flex items-start gap-2 py-0.5">
      <span
        className={`mt-1 h-2.5 w-2.5 rounded-full shrink-0 ${meta.dotColor}`}
        aria-hidden="true"
      />
      <div className="flex flex-col">
        <span className="font-semibold text-slate-900 leading-tight">
          {meta.label}
        </span>
        <span className="text-[11px] text-slate-500 leading-snug">
          {meta.description}
        </span>
      </div>
    </div>
  )
}

export function StatusOptionPreview({ status }: Props) {
  const meta = statusDescriptions[status]
  return (
    <div className="rounded-xl border border-blue-200 bg-blue-50/60 p-3 mt-3">
      <span className="block text-[10px] font-bold uppercase tracking-wider text-blue-700 leading-none mb-1">
        ESTADO SELECCIONADO
      </span>
      <div className="flex items-center gap-2">
        <StatusBadge value={status}>{meta?.label ?? status}</StatusBadge>
        <span className="text-xs text-slate-600">
          Este evento se añadirá a la línea de tiempo.
        </span>
      </div>
    </div>
  )
}
