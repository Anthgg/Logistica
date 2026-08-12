import type { InventoryMovementCompensationRequest } from '../types/inventory-ledger'
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton'

interface Props {
  compensations: InventoryMovementCompensationRequest[]
  loading: boolean
}

const STATUS_COLORS: Record<string, string> = {
  DRAFT: 'bg-gray-100 text-gray-700',
  SUBMITTED: 'bg-blue-100 text-blue-700',
  IN_REVIEW: 'bg-yellow-100 text-yellow-700',
  APPROVED: 'bg-green-100 text-green-700',
  REJECTED: 'bg-red-100 text-red-700',
  EXECUTED: 'bg-purple-100 text-purple-700',
  CANCELLED: 'bg-gray-100 text-gray-500',
}

const STATUS_LABELS: Record<string, string> = {
  DRAFT: 'Borrador',
  SUBMITTED: 'Solicitada',
  IN_REVIEW: 'En revisión',
  APPROVED: 'Aprobada',
  REJECTED: 'Rechazada',
  EXECUTED: 'Ejecutada',
  CANCELLED: 'Cancelada',
}

export function InventoryMovementCompensationsPanel({ compensations, loading }: Props) {
  if (loading) return <LoadingSkeleton rows={3} />

  if (compensations.length === 0) {
    return (
      <div className="bg-white p-8 rounded-lg border text-center text-gray-500">
        Sin solicitudes de compensación para este movimiento.
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <Alert>
        Una compensación no elimina ni modifica el movimiento original.
      </Alert>

      {compensations.map((c) => (
        <div key={c.compensation_id} className="bg-white p-4 rounded-lg border space-y-2">
          <div className="flex items-center justify-between">
            <div>
              <span className="font-medium">{c.compensation_id}</span>
              <span className="ml-2 text-sm text-gray-500">
                {c.compensation_type === 'FULL' ? 'Total' : 'Parcial'}
              </span>
            </div>
            <span className={`px-2 py-1 text-xs rounded-full ${STATUS_COLORS[c.status]}`}>
              {STATUS_LABELS[c.status]}
            </span>
          </div>

          <div className="text-sm">
            <span className="text-gray-500">MOV original:</span>{' '}
            <span className="font-mono">{c.original_movement.movement_code}</span>
          </div>
          <div className="text-sm">
            <span className="text-gray-500">Razón:</span> {c.reason_code} — {c.description}
          </div>

          {c.inverse_movement && (
            <div className="text-sm">
              <span className="text-gray-500">MOV compensatorio:</span>{' '}
              <span className="font-mono">{c.inverse_movement.movement_code}</span>
            </div>
          )}

          <dl className="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-1 text-sm">
            <Row label="Solicitante" value={c.requester.display_name} />
            <Row label="Revisor" value={c.reviewer?.display_name ?? '—'} />
            <Row label="Aprobador" value={c.approver?.display_name ?? '—'} />
            <Row label="Ejecutor" value={c.executor?.display_name ?? '—'} />
            <Row label="Hash original" value={c.integrity_hashes.original ?? '—'} mono />
            <Row label="Hash inverso" value={c.integrity_hashes.inverse ?? '—'} mono />
          </dl>
        </div>
      ))}
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

function Row({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex items-start justify-between gap-3">
      <span className="text-gray-500">{label}</span>
      <span className={`text-right ${mono ? 'font-mono text-xs' : ''}`}>{value}</span>
    </div>
  )
}
