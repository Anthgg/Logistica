import { useState } from 'react'
import type { InventoryMovementSnapshot } from '../types/inventory-ledger'
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton'

interface Props {
  snapshot: InventoryMovementSnapshot | null
  loading: boolean
}

export function InventoryMovementSnapshotPanel({ snapshot, loading }: Props) {
  const [showRawJson, setShowRawJson] = useState(false)

  if (loading) return <LoadingSkeleton rows={6} />

  if (!snapshot) {
    return (
      <div className="bg-white p-8 rounded-lg border text-center text-gray-500">
        Sin snapshot disponible para este movimiento.
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg border space-y-4">
      <header className="p-4 border-b flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-700">Snapshot estructurado (solo lectura)</h3>
        <label className="flex items-center gap-2 text-xs text-gray-500">
          <input
            type="checkbox"
            checked={showRawJson}
            onChange={(e) => setShowRawJson(e.target.checked)}
            className="rounded"
          />
          Vista JSON (auditor)
        </label>
      </header>

      <div className="p-4 grid grid-cols-1 md:grid-cols-2 gap-4">
        <Section title="Identificación">
          <Row label="Snapshot ID" value={snapshot.snapshot_id} mono />
          <Row label="Organización" value={snapshot.organization_id} mono />
          <Row label="Almacén" value={snapshot.warehouse_id} mono />
          <Row label="Producto" value={snapshot.product_id} mono />
          <Row label="Unidad" value={snapshot.unit_id} mono />
        </Section>

        <Section title="Posiciones">
          <Row label="Origen" value={snapshot.origin_position.location?.code ?? snapshot.origin_position.external_boundary ?? '—'} />
          <Row label="Destino" value={snapshot.destination_position.location?.code ?? snapshot.destination_position.external_boundary ?? '—'} />
          <Row label="Disponibilidad origen" value={snapshot.origin_availability} />
          <Row label="Disponibilidad destino" value={snapshot.destination_availability} />
          <Row label="Calidad origen" value={snapshot.origin_quality} />
          <Row label="Calidad destino" value={snapshot.destination_quality} />
        </Section>

        <Section title="Fuente">
          <Row label="Sistema fuente" value={snapshot.source_system} />
          <Row label="Evento" value={snapshot.source_event_id ?? '—'} mono />
          <Row label="Actor" value={snapshot.actor.display_name} />
          <Row label="Motivo" value={snapshot.reason} />
        </Section>

        <Section title="Conversiones y referencias">
          {Object.entries(snapshot.conversions).map(([k, v]) => (
            <Row key={k} label={k} value={String(v)} mono />
          ))}
          {Object.entries(snapshot.references).map(([k, v]) => (
            <Row key={k} label={k} value={v} mono />
          ))}
        </Section>

        <Section title="Fechas">
          <Row label="Hecho" value={new Date(snapshot.occurred_at).toLocaleString()} />
          <Row label="Publicación" value={snapshot.posted_at ? new Date(snapshot.posted_at).toLocaleString() : '—'} />
        </Section>

        <Section title="Hash">
          <Row label="Hash" value={snapshot.hash} mono />
          <Row label="Esquema" value={snapshot.schema_version} />
          <Row label="Canonicalización" value={snapshot.canonicalization_version} />
        </Section>
      </div>

      {showRawJson && (
        <div className="p-4 border-t">
          <pre className="text-xs bg-gray-50 p-3 rounded overflow-auto max-h-96">
            {JSON.stringify(snapshot, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1">
      <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">{title}</h4>
      <div className="space-y-1">{children}</div>
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
