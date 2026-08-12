import { useCallback, useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { purchaseOrdersApi } from '../api/purchase-orders-api'
import { Alert } from '../components/common/Alert'
import { Button } from '../components/common/Button'
import { ConfirmDialog } from '../components/common/ConfirmDialog'
import { LoadingSkeleton } from '../components/common/LoadingSkeleton'
import { PageHeader } from '../components/common/PageHeader'
import { PurchaseOrderLineItemsTable } from '../components/purchase-orders/PurchaseOrderLineItemsTable'
import { PurchaseOrderStatusBadge } from '../components/purchase-orders/PurchaseOrderStatusBadge'
import { useLogisticsPermissions } from '../features/logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../features/logistics-permissions/logistics-permissions-map'
import { ApiRequestError } from '../types/api'
import type { PurchaseOrder } from '../types/purchase-orders'

type Confirmation = 'approve' | 'issue' | null

function formatDate(value: string | null) {
  return value
    ? new Date(value).toLocaleString('es-PE', { dateStyle: 'medium', timeStyle: 'short' })
    : '—'
}

function formatAmount(value: string, currency: string) {
  const amount = Number(value)
  return Number.isFinite(amount)
    ? new Intl.NumberFormat('es-PE', { style: 'currency', currency }).format(amount)
    : `${value} ${currency}`
}

export function PurchaseOrderDetailPage() {
  const { purchaseOrderId } = useParams<{ purchaseOrderId: string }>()
  const navigate = useNavigate()
  const { hasPermission } = useLogisticsPermissions()
  const [order, setOrder] = useState<PurchaseOrder | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [actionLoading, setActionLoading] = useState(false)
  const [confirmation, setConfirmation] = useState<Confirmation>(null)
  const [showCancel, setShowCancel] = useState(false)
  const [cancelReason, setCancelReason] = useState('')
  const [deliveryDate, setDeliveryDate] = useState('')
  const [notes, setNotes] = useState('')
  const [stepUpProofId, setStepUpProofId] = useState('')
  const [proofRequired, setProofRequired] = useState(false)

  const load = useCallback(async () => {
    if (!purchaseOrderId) return
    setLoading(true)
    setError(null)
    try {
      const response = await purchaseOrdersApi.get(purchaseOrderId)
      setOrder(response)
      setDeliveryDate(response.expected_delivery_date ?? '')
      setNotes(response.notes ?? '')
    } catch (loadError) {
      setError(
        loadError instanceof Error
          ? loadError.message
          : 'No se pudo cargar la orden de compra.',
      )
    } finally {
      setLoading(false)
    }
  }, [purchaseOrderId])

  useEffect(() => {
    void load()
  }, [load])

  const runAction = async (action: () => Promise<PurchaseOrder>) => {
    setActionLoading(true)
    setActionError(null)
    try {
      const updated = await action()
      setOrder(updated)
      setDeliveryDate(updated.expected_delivery_date ?? '')
      setNotes(updated.notes ?? '')
      setProofRequired(false)
      setStepUpProofId('')
    } catch (actionFailure) {
      if (
        actionFailure instanceof ApiRequestError &&
        actionFailure.code === 'STEP_UP_REQUIRED'
      ) {
        setProofRequired(true)
        setActionError(
          'La aprobación requiere verificación reforzada. Completa el desafío de seguridad e ingresa el ID del comprobante.',
        )
      } else {
        setActionError(
          actionFailure instanceof Error
            ? actionFailure.message
            : 'No se pudo completar la acción.',
        )
      }
    } finally {
      setActionLoading(false)
    }
  }

  if (loading) return <LoadingSkeleton rows={10} />
  if (error || !order) {
    return (
      <div className="p-6">
        <Alert variant="error" title="No se pudo abrir la orden">
          {error ?? 'La orden de compra no existe.'}
        </Alert>
      </div>
    )
  }

  const canUpdate =
    hasPermission(LOGISTICS_PERMISSIONS.purchaseOrders.update) &&
    ['DRAFT', 'APPROVED'].includes(order.status)
  const canApprove =
    hasPermission(LOGISTICS_PERMISSIONS.purchaseOrders.approve) &&
    order.status === 'DRAFT'
  const canIssue =
    hasPermission(LOGISTICS_PERMISSIONS.purchaseOrders.issue) &&
    ['DRAFT', 'APPROVED'].includes(order.status)
  const canCancel =
    hasPermission(LOGISTICS_PERMISSIONS.purchaseOrders.cancel) &&
    ['DRAFT', 'APPROVED', 'ISSUED'].includes(order.status)

  const saveChanges = () =>
    void runAction(() =>
      purchaseOrdersApi.update(order.id, {
        expected_delivery_date: deliveryDate || null,
        notes: notes.trim() || null,
      }),
    )

  const confirmAction = () => {
    const selected = confirmation
    setConfirmation(null)
    if (selected === 'approve') {
      void runAction(() =>
        purchaseOrdersApi.approve(order.id, stepUpProofId.trim() || undefined),
      )
    } else if (selected === 'issue') {
      void runAction(() => purchaseOrdersApi.issue(order.id))
    }
  }

  const cancelOrder = () => {
    const reason = cancelReason.trim()
    if (reason.length < 15) return
    setShowCancel(false)
    void runAction(() => purchaseOrdersApi.cancel(order.id, { reason }))
  }

  return (
    <div className="mx-auto max-w-6xl space-y-5 p-6">
      <PageHeader
        eyebrow="Orden de compra"
        title={order.order_number}
        description={`Proveedor: ${order.supplier_name}`}
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <PurchaseOrderStatusBadge status={order.status} />
            <Button variant="secondary" onClick={() => navigate('/logistics/purchase-orders')}>
              Volver
            </Button>
          </div>
        }
      />

      {actionError && (
        <Alert variant="error" title="No se pudo completar" onDismiss={() => setActionError(null)}>
          {actionError}
        </Alert>
      )}

      {proofRequired && (
        <label className="field rounded-xl border border-amber-200 bg-amber-50 p-4">
          <span className="field__label">ID de comprobante de verificación reforzada</span>
          <span className="field__control">
            <input
              className="field__input"
              value={stepUpProofId}
              onChange={(event) => setStepUpProofId(event.target.value)}
              placeholder="UUID emitido por el flujo de step-up"
            />
          </span>
        </label>
      )}

      <div className="flex flex-wrap gap-2">
        {canApprove && (
          <Button onClick={() => setConfirmation('approve')} disabled={actionLoading}>
            Aprobar
          </Button>
        )}
        {canIssue && (
          <Button variant="secondary" onClick={() => setConfirmation('issue')} disabled={actionLoading}>
            Emitir
          </Button>
        )}
        {canCancel && (
          <Button variant="danger" onClick={() => setShowCancel(true)} disabled={actionLoading}>
            Anular
          </Button>
        )}
      </div>

      <section className="grid gap-4 md:grid-cols-3">
        <article className="rounded-xl border border-slate-200 bg-white p-5 md:col-span-2">
          <h2 className="mb-4 text-sm font-bold uppercase tracking-wide text-slate-500">
            Datos generales
          </h2>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <p className="text-xs text-slate-500">Proveedor</p>
              <p className="font-semibold text-slate-900">{order.supplier_name}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Moneda</p>
              <p className="font-semibold text-slate-900">{order.currency_code}</p>
            </div>
            <label className="field">
              <span className="field__label">Entrega esperada</span>
              <span className="field__control">
                <input
                  className="field__input"
                  type="date"
                  value={deliveryDate}
                  onChange={(event) => setDeliveryDate(event.target.value)}
                  disabled={!canUpdate}
                />
              </span>
            </label>
            <label className="field sm:col-span-2">
              <span className="field__label">Observaciones</span>
              <span className="field__control">
                <textarea
                  className="field__input field__textarea"
                  value={notes}
                  onChange={(event) => setNotes(event.target.value)}
                  disabled={!canUpdate}
                  maxLength={2000}
                  rows={3}
                />
              </span>
            </label>
          </div>
          {canUpdate && (
            <div className="mt-4">
              <Button variant="secondary" onClick={saveChanges} isLoading={actionLoading}>
                Guardar cambios
              </Button>
            </div>
          )}
        </article>

        <article className="rounded-xl border border-slate-200 bg-white p-5">
          <h2 className="mb-4 text-sm font-bold uppercase tracking-wide text-slate-500">
            Totales
          </h2>
          <dl className="space-y-3 text-sm">
            <div className="flex justify-between"><dt>Subtotal</dt><dd>{formatAmount(order.subtotal_amount, order.currency_code)}</dd></div>
            <div className="flex justify-between"><dt>Impuestos</dt><dd>{formatAmount(order.tax_amount, order.currency_code)}</dd></div>
            <div className="flex justify-between border-t pt-3 text-base font-bold"><dt>Total</dt><dd>{formatAmount(order.total_amount, order.currency_code)}</dd></div>
          </dl>
        </article>
      </section>

      <section>
        <h2 className="mb-3 text-sm font-bold uppercase tracking-wide text-slate-500">
          Líneas de la orden
        </h2>
        <PurchaseOrderLineItemsTable lines={order.lines} currency={order.currency_code} />
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-5">
        <h2 className="mb-3 text-sm font-bold uppercase tracking-wide text-slate-500">Historial</h2>
        <dl className="grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-4">
          <div><dt className="text-slate-500">Creada</dt><dd>{formatDate(order.created_at)}</dd></div>
          <div><dt className="text-slate-500">Aprobada</dt><dd>{formatDate(order.approved_at)}</dd></div>
          <div><dt className="text-slate-500">Emitida</dt><dd>{formatDate(order.issued_at)}</dd></div>
          <div><dt className="text-slate-500">Actualizada</dt><dd>{formatDate(order.updated_at)}</dd></div>
        </dl>
        {order.annulment_reason && (
          <p className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">
            Motivo de anulación: {order.annulment_reason}
          </p>
        )}
      </section>

      <ConfirmDialog
        isOpen={confirmation !== null}
        title={confirmation === 'approve' ? 'Aprobar orden' : 'Emitir orden'}
        description={
          confirmation === 'approve'
            ? 'La orden pasará a estado aprobada.'
            : 'La orden se marcará como emitida al proveedor.'
        }
        confirmLabel={confirmation === 'approve' ? 'Aprobar' : 'Emitir'}
        tone="primary"
        isLoading={actionLoading}
        onConfirm={confirmAction}
        onCancel={() => setConfirmation(null)}
      />

      <ConfirmDialog
        isOpen={showCancel}
        title="Anular orden"
        description={
          <label className="field text-left">
            <span className="field__label">Motivo (mínimo 15 caracteres)</span>
            <span className="field__control">
              <textarea
                className="field__input field__textarea"
                value={cancelReason}
                onChange={(event) => setCancelReason(event.target.value)}
                minLength={15}
                maxLength={1000}
                rows={3}
              />
            </span>
          </label>
        }
        confirmLabel="Anular"
        tone="danger"
        isLoading={actionLoading}
        onConfirm={cancelOrder}
        onCancel={() => setShowCancel(false)}
      />
    </div>
  )
}
