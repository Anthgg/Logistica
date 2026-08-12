import type { InventoryMovement } from '../types/inventory-ledger'

interface Props {
  movement: InventoryMovement
}

const STATE_LABEL: Record<string, string> = {
  AVAILABLE: 'Disponible',
  BLOCKED: 'Bloqueado',
  RESERVED: 'Reservado',
  IN_TRANSIT: 'En tránsito',
  QUARANTINED: 'Cuarentena',
  DAMAGED: 'Dañado',
  EXPIRED: 'Vencido',
  PENDING: 'Pendiente',
  APPROVED: 'Aprobado',
  REJECTED: 'Rechazado',
  RELEASED: 'Liberado',
  STABLE: 'Estable',
  ARRIVED: 'Arribado',
  INTACT: 'Íntegro',
  PARTIAL: 'Parcial',
  VALID: 'Vigente',
  EXPIRING_SOON: 'Por vencer',
  UNKNOWN: '—',
}

const TYPE_LABEL: Record<string, string> = {
  ENTRY: 'Entrada',
  EXIT: 'Salida',
  TRANSFER: 'Traslado interno',
  RESERVATION: 'Reserva',
  RELEASE_RESERVATION: 'Liberación de reserva',
  QUARANTINE_APPLY: 'Aplicación de cuarentena',
  QUARANTINE_RELEASE: 'Liberación de cuarentena',
  QUALITY_APPROVAL: 'Aprobación de calidad',
  QUALITY_REJECTION: 'Rechazo',
  PUTAWAY_COMPLETE: 'Putaway completado',
  STATE_BLOCKED: 'Cambio a bloqueado',
  STATE_DAMAGED: 'Cambio a dañado',
  STATE_EXPIRED: 'Cambio a vencido',
  COMPENSATION: 'Compensación',
  OTHER: 'Otro',
}

export function InventoryMovementTransitionPanel({ movement }: Props) {
  const firstLine = movement.lines[0]

  if (!firstLine) {
    return (
      <div className="bg-white p-8 rounded-lg border text-center text-gray-500">
        Sin líneas para visualizar la transición.
      </div>
    )
  }

  return (
    <div className="bg-white p-4 rounded-lg border space-y-4">
      <Alert>
        Etiqueta legible para el tipo técnico. El tipo MOV del backend se preserva como referencia.
      </Alert>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-start">
        <PositionCard
          title="ORIGEN"
          position={firstLine.origin_position}
          availability={firstLine.origin_availability}
          quality={firstLine.origin_quality}
          transit={firstLine.origin_transit}
          damage={firstLine.origin_damage}
          expiration={firstLine.origin_expiration}
        />

        <div className="p-4 bg-blue-50 rounded-lg border border-blue-200 text-center">
          <div className="text-xs text-blue-600 uppercase tracking-wide">MOV</div>
          <div className="font-medium mt-1">{TYPE_LABEL[movement.movement_type] ?? movement.movement_type}</div>
          <div className="text-sm text-gray-500 mt-1">{movement.movement_code}</div>
          <div className="mt-2 text-lg font-mono">
            {firstLine.quantity.value} {firstLine.unit.symbol}
          </div>
          <div className="text-xs text-gray-500 mt-1">{movement.reason}</div>
          <div className="text-xs text-gray-400 mt-1">
            {new Date(movement.occurred_at).toLocaleString()}
          </div>
        </div>

        <PositionCard
          title="DESTINO"
          position={firstLine.destination_position}
          availability={firstLine.destination_availability}
          quality={firstLine.destination_quality}
          transit={firstLine.destination_transit}
          damage={firstLine.destination_damage}
          expiration={firstLine.destination_expiration}
        />
      </div>
    </div>
  )
}

function Alert({ children }: { children: React.ReactNode }) {
  return (
    <div className="p-3 rounded-lg bg-blue-50 border border-blue-200 text-sm text-blue-700">
      {children}
    </div>
  )
}

function PositionCard({
  title,
  position,
  availability,
  quality,
  transit,
  damage,
  expiration,
}: {
  title: string
  position: { external_boundary?: string | null; location?: { code: string; name?: string } | null; warehouse?: { name: string } | null }
  availability: string
  quality: string
  transit: string
  damage: string
  expiration: string
}) {
  return (
    <div className="p-4 bg-white rounded-lg border space-y-1">
      <div className="text-xs text-gray-500 uppercase tracking-wide">{title}</div>
      {position.external_boundary && (
        <div className="text-sm">
          <span className="text-gray-500">Frontera:</span> {position.external_boundary}
        </div>
      )}
      {position.warehouse && (
        <div className="text-sm">
          <span className="text-gray-500">Almacén:</span> {position.warehouse.name}
        </div>
      )}
      {position.location && (
        <div className="text-sm">
          <span className="text-gray-500">Ubicación:</span> {position.location.code}
          {position.location.name && (
            <span className="text-gray-400"> · {position.location.name}</span>
          )}
        </div>
      )}
      <div className="border-t pt-2 mt-2 space-y-0.5 text-xs text-gray-600">
        <div>Disponibilidad: {STATE_LABEL[availability]}</div>
        <div>Calidad: {STATE_LABEL[quality]}</div>
        <div>Tránsito: {STATE_LABEL[transit]}</div>
        <div>Daño: {STATE_LABEL[damage]}</div>
        <div>Vencimiento: {STATE_LABEL[expiration]}</div>
      </div>
    </div>
  )
}
