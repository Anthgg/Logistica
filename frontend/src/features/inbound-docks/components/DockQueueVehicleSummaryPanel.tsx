import { KeyValueGrid, SectionPanel } from './ui/Primitives'
import { formatServerDateTime } from '../utils/format'
import type { GateCheckInSummary } from '../types/inbound-docks'

export function DockQueueVehicleSummaryPanel({
  checkIn,
  queueEntry,
  className,
}: {
  checkIn: GateCheckInSummary | null | undefined
  queueEntry?: {
    vehicle_plate?: string | null
    vehicle_type?: string | null
    driver_name_redacted?: string | null
    carrier_name?: string | null
    pallets?: number | null
    packages?: number | null
    weight?: string | null
    special_requirements?: string[]
    cit_window_start?: string | null
    cit_window_end?: string | null
    assigned_dock_code?: string | null
    assigned_dock_name?: string | null
  } | null
  className?: string
}) {
  if (!checkIn) {
    return (
      <SectionPanel
        title="Resumen del vehículo"
        description="Sin datos disponibles"
        className={className}
      >
        <p className="text-xs text-slate-500">No hay información del vehículo en la cola.</p>
      </SectionPanel>
    )
  }
  return (
    <SectionPanel
      title="Resumen del vehículo"
      description="Datos del check-in autorizado. Solo lectura."
      className={className}
    >
      <KeyValueGrid
        items={[
          { label: 'CPV', value: checkIn.cpv_code ?? '—', mono: true },
          { label: 'CIT', value: checkIn.cit_code ?? '—', mono: true },
          { label: 'Proveedor', value: checkIn.supplier_name ?? '—' },
          { label: 'Transportista', value: checkIn.carrier_name ?? queueEntry?.carrier_name ?? '—' },
          { label: 'Placa', value: checkIn.vehicle_plate ?? queueEntry?.vehicle_plate ?? '—', mono: true },
          { label: 'Tipo de vehículo', value: checkIn.vehicle_id ? '—' : queueEntry?.vehicle_type ?? '—' },
          { label: 'Conductor', value: checkIn.driver_name_redacted ?? queueEntry?.driver_name_redacted ?? '—' },
          { label: 'Llegada a garita', value: checkIn.arrived_at ? formatServerDateTime(checkIn.arrived_at) : '—' },
          { label: 'Autorización', value: checkIn.authorized_at ? formatServerDateTime(checkIn.authorized_at) : '—' },
          { label: 'Precinto', value: checkIn.seal_number ?? '—', mono: true },
          { label: 'Pallets esperados', value: checkIn.pallets ?? queueEntry?.pallets ?? '—' },
          { label: 'Bultos esperados', value: checkIn.packages ?? queueEntry?.packages ?? '—' },
          { label: 'Peso esperado', value: checkIn.weight ?? queueEntry?.weight ?? '—' },
          {
            label: 'Requisitos especiales',
            value:
              checkIn.special_requirements ??
              (queueEntry?.special_requirements?.length ? queueEntry.special_requirements.join(', ') : '—'),
          },
          {
            label: 'Condiciones de ingreso',
            value: checkIn.conditions ?? '—',
          },
        ]}
      />
    </SectionPanel>
  )
}
