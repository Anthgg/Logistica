import { formatDecimal, formatMoney } from '../format'
import type {
  PurchaseOrderDetail,
  PurchaseOrderLine,
  PurchaseOrderRevision,
} from '../types/phase034-contract'
import { EmptyState, Modal, StatusPill } from './ui'

export type Phase034DetailSection =
  | 'overview'
  | 'lines'
  | 'revisions'
  | 'edit'
  | 'schedules'
  | 'dispatch'
  | 'document'
  | 'history'
  | 'amendments'
  | 'approval'
  | 'approval-chain'
  | 'approval-seal'

const UNSUPPORTED_SECTION_COPY: Record<
  Exclude<Phase034DetailSection, 'overview' | 'lines' | 'revisions'>,
  { title: string; description: string }
> = {
  edit: {
    title: 'Edición no publicada',
    description:
      'El backend 0.9.1 no publica PATCH para órdenes de procurement. La orden se mantiene en modo lectura.',
  },
  schedules: {
    title: 'Entregas parciales no publicadas',
    description:
      'No existe un endpoint de schedules en el contrato actual. No se muestran entregas simuladas.',
  },
  dispatch: {
    title: 'Despacho no publicado',
    description:
      'El contrato actual no expone creación, envío ni reintentos de despacho.',
  },
  document: {
    title: 'Documento no publicado',
    description:
      'No hay endpoints de preview, emisión, descarga o reimpresión para esta versión.',
  },
  history: {
    title: 'Historial dedicado no publicado',
    description:
      'La respuesta incluye revisiones, pero no un timeline de auditoría de la orden.',
  },
  amendments: {
    title: 'Enmiendas no publicadas',
    description:
      'El backend actual no expone operaciones de enmienda para órdenes de compra.',
  },
  approval: {
    title: 'Solicitud de aprobación no enlazada',
    description:
      'La orden informa approval_status, pero el backend no publica búsqueda de la solicitud de aprobación por subject_id.',
  },
  'approval-chain': {
    title: 'Cadena de aprobación no publicada',
    description:
      'No existe un endpoint para consultar pasos, asignaciones o progreso de la cadena desde la orden.',
  },
  'approval-seal': {
    title: 'Sello de aprobación no enlazado',
    description:
      'El sello se consulta por request_id y la orden no devuelve ese identificador.',
  },
}

export function UnsupportedPurchaseOrderSection({
  section,
}: {
  section: Exclude<
    Phase034DetailSection,
    'overview' | 'lines' | 'revisions'
  >
}) {
  const copy = UNSUPPORTED_SECTION_COPY[section]
  return (
    <div className="rounded-xl border border-amber-200 bg-amber-50 p-5">
      <h2 className="text-base font-bold text-amber-900">{copy.title}</h2>
      <p className="mt-2 max-w-3xl text-sm text-amber-800">
        {copy.description}
      </p>
    </div>
  )
}

export function PurchaseOrderAmountsPanel({
  order,
}: {
  order: PurchaseOrderDetail
}) {
  const amounts = [
    ['Subtotal', order.subtotal],
    ['Descuentos', order.discount_total],
    ['Impuestos', order.tax_total],
    ['Flete', order.freight_total],
    ['Total general', order.grand_total],
  ]

  return (
    <section
      aria-labelledby="purchase-order-amounts"
      className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
    >
      <h2
        id="purchase-order-amounts"
        className="text-sm font-bold text-slate-900"
      >
        Resumen monetario del backend
      </h2>
      <dl className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-5">
        {amounts.map(([label, value]) => (
          <div
            key={label}
            className="rounded-lg border border-slate-100 bg-slate-50 p-3"
          >
            <dt className="text-xs text-slate-500">{label}</dt>
            <dd className="mt-1 font-mono text-sm font-bold text-slate-900">
              {formatMoney(value, order.currency_code)}
            </dd>
          </div>
        ))}
      </dl>
      <p className="mt-3 text-xs text-slate-500">
        No se realiza ningún cálculo autoritativo en React.
      </p>
    </section>
  )
}

function LineRows({ lines }: { lines: PurchaseOrderLine[] }) {
  return (
    <tbody className="divide-y divide-slate-100">
      {lines.map((line) => (
        <tr key={line.id}>
          <td className="px-3 py-3 font-mono text-xs">{line.line_number}</td>
          <td className="px-3 py-3 text-xs">
            <div className="font-semibold text-slate-800">
              {line.product_name_snapshot}
            </div>
            {line.supplier_product_reference && (
              <div className="mt-0.5 text-slate-500">
                Ref. proveedor: {line.supplier_product_reference}
              </div>
            )}
          </td>
          <td className="px-3 py-3 text-right font-mono text-xs">
            {formatDecimal(line.ordered_quantity, 6)}{' '}
            {line.ordered_unit_code}
          </td>
          <td className="px-3 py-3 text-right font-mono text-xs">
            {formatMoney(line.unit_price, line.currency_code)}
          </td>
          <td className="px-3 py-3 text-right font-mono text-xs">
            {formatMoney(line.discount_amount, line.currency_code)}
          </td>
          <td className="px-3 py-3 text-right font-mono text-xs">
            {formatMoney(line.tax_amount, line.currency_code)}
          </td>
          <td className="px-3 py-3 text-right font-mono text-xs">
            {formatMoney(line.freight_amount, line.currency_code)}
          </td>
          <td className="px-3 py-3 text-right font-mono text-xs">
            {formatMoney(line.other_charges_amount, line.currency_code)}
          </td>
          <td className="px-3 py-3 text-right font-mono text-xs font-bold">
            {formatMoney(line.line_total, line.currency_code)}
          </td>
          <td className="px-3 py-3">
            <StatusPill>{line.status}</StatusPill>
          </td>
        </tr>
      ))}
    </tbody>
  )
}

export function PurchaseOrderLinesTable({
  revision,
}: {
  revision: PurchaseOrderRevision | null
}) {
  if (!revision || revision.lines.length === 0) {
    return (
      <EmptyState
        title="La revisión activa no contiene líneas"
        description="No se inventan productos ni cantidades cuando el backend no los devuelve."
      />
    )
  }

  return (
    <section
      aria-labelledby="purchase-order-lines"
      className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm"
    >
      <header className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 p-4">
        <div>
          <h2 id="purchase-order-lines" className="text-sm font-bold text-slate-900">
            Líneas de la revisión {revision.revision_number}
          </h2>
          <p className="mt-1 text-xs text-slate-500">
            Cantidades, precios, descuentos, impuestos y cargos conservados como
            strings.
          </p>
        </div>
        <StatusPill tone="info">{revision.status}</StatusPill>
      </header>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-3 py-3 text-left">Línea</th>
              <th className="px-3 py-3 text-left">Producto</th>
              <th className="px-3 py-3 text-right">Cantidad</th>
              <th className="px-3 py-3 text-right">Precio</th>
              <th className="px-3 py-3 text-right">Descuento</th>
              <th className="px-3 py-3 text-right">Impuesto</th>
              <th className="px-3 py-3 text-right">Flete</th>
              <th className="px-3 py-3 text-right">Otros</th>
              <th className="px-3 py-3 text-right">Total</th>
              <th className="px-3 py-3 text-left">Estado</th>
            </tr>
          </thead>
          <LineRows lines={revision.lines} />
        </table>
      </div>
    </section>
  )
}

function formatDate(value: string | null): string {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('es-PE', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)
}

export function PurchaseOrderRevisionsPanel({
  revisions,
}: {
  revisions: PurchaseOrderRevision[]
}) {
  if (revisions.length === 0) {
    return <EmptyState title="No hay revisiones disponibles" />
  }

  const sorted = revisions.toSorted(
    (left, right) => right.revision_number - left.revision_number,
  )

  return (
    <section className="space-y-3" aria-labelledby="purchase-order-revisions">
      <h2 id="purchase-order-revisions" className="text-base font-bold text-slate-900">
        Revisiones
      </h2>
      {sorted.map((revision) => (
        <article
          key={revision.id}
          className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
        >
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <h3 className="text-sm font-bold text-slate-900">
                Revisión {revision.revision_number}
              </h3>
              <p className="mt-1 text-xs text-slate-500">
                Creada {formatDate(revision.created_at)} ·{' '}
                {revision.lines.length} línea(s)
              </p>
            </div>
            <StatusPill tone={revision.approved_at ? 'success' : 'neutral'}>
              {revision.status}
            </StatusPill>
          </div>
          {revision.approved_at && (
            <p className="mt-2 text-xs text-emerald-700">
              Aprobada {formatDate(revision.approved_at)}
            </p>
          )}
        </article>
      ))}
    </section>
  )
}

export interface PurchaseOrderActionDialogProps {
  open: boolean
  title: string
  description: string
  confirmLabel: string
  destructive?: boolean
  reason: string
  minimumReasonLength: number
  isSubmitting: boolean
  onReasonChange: (value: string) => void
  onCancel: () => void
  onConfirm: () => void
}

export function PurchaseOrderActionDialog({
  open,
  title,
  description,
  confirmLabel,
  destructive = false,
  reason,
  minimumReasonLength,
  isSubmitting,
  onReasonChange,
  onCancel,
  onConfirm,
}: PurchaseOrderActionDialogProps) {
  const requiresReason = minimumReasonLength > 0
  const valid =
    !requiresReason || reason.trim().length >= minimumReasonLength

  return (
    <Modal
      open={open}
      onOpenChange={(nextOpen) => {
        if (!nextOpen && !isSubmitting) onCancel()
      }}
      title={title}
      description={description}
      footer={
        <>
          <button
            type="button"
            disabled={isSubmitting}
            onClick={onCancel}
            className="min-h-10 rounded-lg border border-slate-200 px-3 text-xs font-semibold text-slate-700 disabled:opacity-50"
          >
            Volver
          </button>
          <button
            type="button"
            disabled={!valid || isSubmitting}
            onClick={onConfirm}
            className={
              destructive
                ? 'min-h-10 rounded-lg bg-rose-600 px-3 text-xs font-semibold text-white disabled:opacity-50'
                : 'min-h-10 rounded-lg bg-[#1F4E6D] px-3 text-xs font-semibold text-white disabled:opacity-50'
            }
          >
            {isSubmitting ? 'Procesando…' : confirmLabel}
          </button>
        </>
      }
    >
      {requiresReason ? (
        <label className="block">
          <span className="mb-1 block text-xs font-semibold text-slate-700">
            Motivo (mínimo {minimumReasonLength} caracteres)
          </span>
          <textarea
            value={reason}
            disabled={isSubmitting}
            onChange={(event) => onReasonChange(event.target.value)}
            rows={4}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1F4E6D] focus:ring-2 focus:ring-[#1F4E6D]/20"
          />
        </label>
      ) : (
        <p className="text-sm text-slate-600">
          La operación será validada nuevamente por el backend.
        </p>
      )}
    </Modal>
  )
}
