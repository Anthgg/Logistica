import type { InventoryMovement } from '../types/inventory-ledger'

interface Props {
  movement: InventoryMovement
}

export function InventoryMovementSummaryPanel({ movement }: Props) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div className="bg-white p-4 rounded-lg border space-y-2">
        <h3 className="text-sm font-medium text-gray-700">Identificación</h3>
        <Row label="Organización" value={movement.organization_id} />
        <Row label="Sede" value={movement.branch_id} />
        <Row label="Almacén" value={movement.warehouse.name} />
        <Row label="Código MOV" value={movement.movement_code} />
        <Row label="Secuencia" value={`#${movement.ledger_sequence}`} />
        <Row label="Familia" value={movement.family} />
        <Row label="Tipo" value={movement.movement_type} />
        <Row label="Razón" value={movement.reason} />
        <Row label="Versión de esquema" value={movement.schema_version} />
      </div>
      <div className="bg-white p-4 rounded-lg border space-y-2">
        <h3 className="text-sm font-medium text-gray-700">Estado y trazabilidad</h3>
        <Row label="Estado" value={movement.status} />
        <Row label="Líneas" value={String(movement.total_lines)} />
        <Row label="Documento fuente" value={movement.source_document?.document_code ?? '—'} />
        <Row label="Evento fuente" value={movement.source?.event_id ?? '—'} />
        <Row label="Actor" value={movement.created_by.display_name} />
        <Row label="Fecha del hecho" value={new Date(movement.occurred_at).toLocaleString()} />
        <Row label="Fecha de publicación" value={movement.posted_at ? new Date(movement.posted_at).toLocaleString() : '—'} />
        <Row label="Compensado por" value={movement.compensated_by_movement_id ?? '—'} />
        <Row label="Compensa a" value={movement.compensation_origin_movement_id ?? '—'} />
      </div>
      <div className="bg-white p-4 rounded-lg border space-y-2 md:col-span-2">
        <h3 className="text-sm font-medium text-gray-700">Integridad</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
          <Row label="Estado" value={movement.integrity_status} />
          <Row label="Hash anterior (parcial)" value={movement.integrity_hash_partial ?? '—'} mono />
          <Row label="Algoritmo" value={movement.integrity_algorithm} />
          <Row label="Versión de canonicalización" value={movement.canonicalization_version} />
        </div>
      </div>
    </div>
  )
}

function Row({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex items-start justify-between gap-3 text-sm">
      <span className="text-gray-500">{label}</span>
      <span className={`text-right ${mono ? 'font-mono text-xs' : ''}`}>{value}</span>
    </div>
  )
}
