import type { InventoryMovementIntegrity } from '../types/inventory-ledger'
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton'

interface Props {
  integrity: InventoryMovementIntegrity | null
  loading: boolean
}

const STATUS_COLORS: Record<string, string> = {
  OK: 'bg-green-100 text-green-700',
  WARNING: 'bg-yellow-100 text-yellow-700',
  FAILED: 'bg-red-100 text-red-700',
  PENDING: 'bg-gray-100 text-gray-700',
}

export function InventoryMovementIntegrityPanel({ integrity, loading }: Props) {
  if (loading) return <LoadingSkeleton rows={4} />

  if (!integrity) {
    return (
      <div className="bg-white p-8 rounded-lg border text-center text-gray-500">
        Sin datos de integridad para este movimiento.
      </div>
    )
  }

  return (
    <div className="bg-white p-4 rounded-lg border space-y-4">
      <Alert>
        SHA-256 es un hash criptográfico, no una firma digital. No debe interpretarse como blockchain ni como atestación legal.
      </Alert>

      <div className="flex items-center gap-3">
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${STATUS_COLORS[integrity.status]}`}>
          {integrity.status}
        </span>
        <span className="text-sm text-gray-500">Algoritmo: {integrity.algorithm}</span>
        <span className="text-sm text-gray-500">Canonicalización: {integrity.canonicalization_version}</span>
      </div>

      <dl className="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-2 text-sm">
        <Row label="Hash fuente" value={integrity.source_hash ?? '—'} mono />
        <Row label="Hash snapshot" value={integrity.snapshot_hash ?? '—'} mono />
        <Row label="Hash de líneas" value={integrity.lines_hash ?? '—'} mono />
        <Row label="Hash anterior" value={integrity.previous_movement_hash ?? '—'} mono />
        <Row label="Hash del movimiento" value={integrity.movement_hash} mono />
        <Row label="Secuencia" value={`#${integrity.ledger_sequence}`} />
        <Row label="Última verificación" value={integrity.last_verified_at ? new Date(integrity.last_verified_at).toLocaleString() : '—'} />
      </dl>
    </div>
  )
}

function Alert({ children }: { children: React.ReactNode }) {
  return (
    <div className="p-3 rounded-lg bg-amber-50 border border-amber-200 text-sm text-amber-700">
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
