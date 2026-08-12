import type { InboundScanEvent, InboundScanEventStatus } from '../../types/inbound-receiving'

const STATUS_CONFIG: Record<InboundScanEventStatus, { label: string; tone: string; bg: string }> = {
  APPLIED: { label: 'Aplicado', tone: 'text-emerald-700', bg: 'bg-emerald-50 border-emerald-200' },
  REQUIRES_QUANTITY: { label: 'Requiere cantidad', tone: 'text-amber-700', bg: 'bg-amber-50 border-amber-200' },
  REQUIRES_LOT: { label: 'Requiere lote', tone: 'text-amber-700', bg: 'bg-amber-50 border-amber-200' },
  REQUIRES_SERIAL: { label: 'Requiere serie', tone: 'text-amber-700', bg: 'bg-amber-50 border-amber-200' },
  REQUIRES_EXPIRATION: { label: 'Requiere vencimiento', tone: 'text-amber-700', bg: 'bg-amber-50 border-amber-200' },
  UNKNOWN_CODE: { label: 'Código desconocido', tone: 'text-rose-700', bg: 'bg-rose-50 border-rose-200' },
  AMBIGUOUS: { label: 'Ambiguo', tone: 'text-orange-700', bg: 'bg-orange-50 border-orange-200' },
  DUPLICATE: { label: 'Duplicado', tone: 'text-rose-700', bg: 'bg-rose-50 border-rose-200' },
  REJECTED: { label: 'Rechazado', tone: 'text-slate-600', bg: 'bg-slate-50 border-slate-200' },
  EXCESS: { label: 'Exceso', tone: 'text-rose-700', bg: 'bg-rose-50 border-rose-200' },
  REVIEW: { label: 'Revisión', tone: 'text-purple-700', bg: 'bg-purple-50 border-purple-200' },
  COMPENSATED: { label: 'Compensado', tone: 'text-slate-500', bg: 'bg-slate-50 border-slate-200' },
}

interface ScanResultPanelProps {
  event: InboundScanEvent | null
}

export function ScanResultPanel({ event }: ScanResultPanelProps) {
  if (!event) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-3 text-xs text-slate-400">
        Esperando primer escaneo…
      </div>
    )
  }

  const cfg = STATUS_CONFIG[event.status]

  return (
    <div className={`rounded-xl border p-3 text-xs ${cfg.bg}`} role="status" aria-live="polite">
      <div className="flex items-center justify-between">
        <span className="font-mono font-semibold text-slate-800">{event.raw_code}</span>
        <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${cfg.tone}`}>
          {cfg.label}
        </span>
      </div>

      {event.symbology !== 'UNKNOWN' && (
        <p className="mt-1 text-slate-500">Simbología: {event.symbology}</p>
      )}

      {event.product && (
        <div className="mt-2 rounded-lg bg-white/70 p-2">
          <p className="font-semibold text-slate-800">{event.product.name}</p>
          <p className="text-slate-500">SKU: {event.product.sku}</p>
        </div>
      )}

      {event.matched_line_id && event.unit && (
        <p className="mt-1 text-slate-600">
          Línea: {event.matched_line_id} · {event.applied_quantity ?? '—'} {event.unit.symbol}
        </p>
      )}

      {event.tracking_required && (
        <div className="mt-2 flex flex-wrap gap-1">
          {event.tracking_required.requires_lot && (
            <span className="rounded bg-amber-100 px-1.5 py-0.5 text-[10px] font-bold text-amber-700">Lote requerido</span>
          )}
          {event.tracking_required.requires_serial && (
            <span className="rounded bg-amber-100 px-1.5 py-0.5 text-[10px] font-bold text-amber-700">Serie requerida</span>
          )}
          {event.tracking_required.requires_expiration && (
            <span className="rounded bg-amber-100 px-1.5 py-0.5 text-[10px] font-bold text-amber-700">Vencimiento requerido</span>
          )}
        </div>
      )}

      {event.warning && (
        <p className="mt-2 rounded bg-amber-100 px-2 py-1 text-amber-800" role="alert">{event.warning}</p>
      )}
      {event.error && (
        <p className="mt-2 rounded bg-rose-100 px-2 py-1 text-rose-800" role="alert">{event.error}</p>
      )}

      {event.next_step && (
        <p className="mt-2 text-[11px] font-semibold text-slate-600">Siguiente: {event.next_step}</p>
      )}

      <p className="mt-2 text-[10px] text-slate-400">
        {event.server_timestamp} · {event.operator.display_name}
      </p>
    </div>
  )
}
