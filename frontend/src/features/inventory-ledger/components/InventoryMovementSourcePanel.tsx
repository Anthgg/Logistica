import { useNavigate } from 'react-router-dom'
import type { InventoryMovementSource } from '../types/inventory-ledger'
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton'

interface Props {
  sources: InventoryMovementSource[]
  loading: boolean
}

const STATUS_COLORS: Record<string, string> = {
  PENDING: 'bg-gray-100 text-gray-700',
  VALID: 'bg-green-100 text-green-700',
  INVALID: 'bg-red-100 text-red-700',
  DUPLICATE: 'bg-yellow-100 text-yellow-700',
}

export function InventoryMovementSourcePanel({ sources, loading }: Props) {
  const navigate = useNavigate()

  if (loading) return <LoadingSkeleton rows={3} />

  if (sources.length === 0) {
    return (
      <div className="bg-white p-8 rounded-lg border text-center text-gray-500">
        Sin fuente registrada para este movimiento.
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {sources.map((source) => (
        <div key={source.source_id} className="bg-white p-4 rounded-lg border space-y-2">
          <div className="flex items-center justify-between">
            <div className="font-medium">{source.source_system} · {source.module}</div>
            <span className={`px-2 py-1 text-xs rounded-full ${STATUS_COLORS[source.validation_status]}`}>
              {source.validation_status}
            </span>
          </div>

          <dl className="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-1 text-sm">
            <Row label="Tipo de evento" value={source.event_type} />
            <Row label="ID del evento" value={source.event_id} mono />
            <Row label="Versión" value={source.event_version} />
            <Row label="Entidad fuente" value={`${source.entity_type} ${source.entity_id}`} />
            <Row label="Documento" value={source.document_code ?? '—'} />
            <Row label="Fecha del hecho" value={new Date(source.occurred_at).toLocaleString()} />
            <Row label="Adaptador" value={`${source.adapter} v${source.adapter_version}`} />
            <Row label="Hash parcial" value={source.hash_partial ?? '—'} mono />
          </dl>

          {source.validation_errors.length > 0 && (
            <div className="text-xs text-red-700 bg-red-50 p-2 rounded">
              {source.validation_errors.map((err, i) => (
                <div key={i}>⚠ {err}</div>
              ))}
            </div>
          )}

          <div className="flex flex-wrap gap-2 pt-2 border-t">
            <Button
              variant="outline"
              onClick={() => navigate(`/logistics/inventory/ledger/movements/${source.entity_id}`)}
            >
              Abrir movimiento relacionado
            </Button>
            {source.event_type.toLowerCase().includes('quarantine') && (
              <Button
                variant="outline"
                onClick={() => navigate(`/logistics/quality/quarantine/${source.entity_id}`)}
              >
                Abrir cuarentena
              </Button>
            )}
            {source.event_type.toLowerCase().includes('putaway') && (
              <Button
                variant="outline"
                onClick={() => navigate(`/logistics/putaway/orders/${source.entity_id}`)}
              >
                Abrir putaway
              </Button>
            )}
          </div>
        </div>
      ))}
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

function Button({
  children,
  variant,
  onClick,
}: {
  children: React.ReactNode
  variant?: 'outline'
  onClick?: () => void
}) {
  const baseClasses = 'px-3 py-1.5 text-sm rounded-lg transition'
  const variantClasses = variant === 'outline' ? 'border border-gray-300 bg-white hover:bg-gray-50' : 'bg-blue-600 text-white hover:bg-blue-700'
  return (
    <button className={`${baseClasses} ${variantClasses}`} onClick={onClick}>
      {children}
    </button>
  )
}
