import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useSensitiveOperationGuard } from '../../continuous-auth/hooks/useSensitiveOperationGuard'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { purchaseOrdersV2Api } from '../api/purchaseOrdersV2Api'
import {
  PurchaseOrderActionDialog,
  PurchaseOrderAmountsPanel,
  PurchaseOrderLinesTable,
  PurchaseOrderRevisionsPanel,
  UnsupportedPurchaseOrderSection,
} from '../components/PurchaseOrderContractPanels'
import type { Phase034DetailSection } from '../components/PurchaseOrderContractPanels'
import { EmptyState, ErrorState, StatusPill, TableSkeleton } from '../components/ui'
import {
  acknowledgementStatusLabel,
  approvalStatusLabel,
  dispatchStatusLabel,
  issuanceStatusLabel,
  purchaseOrderStatusLabel,
} from '../format'
import type {
  PurchaseOrderAction,
  PurchaseOrderDetail,
} from '../types/phase034-contract'
import { PHASE_034_BACKEND_SUPPORT } from '../types/phase034-contract'

interface PurchaseOrderDetailV2PageProps {
  section?: Phase034DetailSection
}

interface ActionDefinition {
  title: string
  description: string
  confirmLabel: string
  minimumReasonLength: number
  destructive?: boolean
  permission: string
}

const ACTIONS: Record<PurchaseOrderAction, ActionDefinition> = {
  submit: {
    title: 'Enviar a aprobación',
    description:
      'La orden será enviada al flujo de aprobación configurado en el backend.',
    confirmLabel: 'Enviar a aprobación',
    minimumReasonLength: 0,
    permission: LOGISTICS_PERMISSIONS.purchaseOrdersV2.submitForApproval,
  },
  approve: {
    title: 'Aprobar orden de compra',
    description:
      'Esta acción es sensible y requiere validación continua antes de ejecutarse.',
    confirmLabel: 'Aprobar orden',
    minimumReasonLength: 0,
    permission: LOGISTICS_PERMISSIONS.purchaseOrdersV2.approveTransitional,
  },
  reject: {
    title: 'Rechazar orden de compra',
    description: 'El motivo será registrado por el backend.',
    confirmLabel: 'Rechazar orden',
    minimumReasonLength: 20,
    destructive: true,
    permission: LOGISTICS_PERMISSIONS.purchaseOrdersV2.reject,
  },
  return: {
    title: 'Devolver para cambios',
    description:
      'La revisión volverá al responsable para que atienda las observaciones.',
    confirmLabel: 'Devolver orden',
    minimumReasonLength: 20,
    permission: LOGISTICS_PERMISSIONS.purchaseOrdersV2.return,
  },
  cancel: {
    title: 'Cancelar orden de compra',
    description:
      'La cancelación es irreversible y el motivo quedará registrado.',
    confirmLabel: 'Cancelar orden',
    minimumReasonLength: 10,
    destructive: true,
    permission: LOGISTICS_PERMISSIONS.purchaseOrdersV2.cancel,
  },
}

const SECTION_LINKS: Array<{
  section: Phase034DetailSection
  label: string
  suffix: string
}> = [
  { section: 'overview', label: 'Resumen', suffix: '' },
  { section: 'revisions', label: 'Revisiones', suffix: '/revisions' },
  { section: 'schedules', label: 'Entregas', suffix: '/schedules' },
  { section: 'document', label: 'Documento', suffix: '/document' },
  { section: 'dispatch', label: 'Despacho', suffix: '/dispatch' },
  { section: 'history', label: 'Historial', suffix: '/history' },
  { section: 'amendments', label: 'Enmiendas', suffix: '/amendments' },
  { section: 'approval', label: 'Aprobación', suffix: '/approval' },
  {
    section: 'approval-chain',
    label: 'Cadena',
    suffix: '/approval-chain',
  },
  {
    section: 'approval-seal',
    label: 'Sello',
    suffix: '/approval-seal',
  },
]

function createIdempotencyKey(): string {
  return typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`
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

export function PurchaseOrderDetailV2Page({
  section = 'overview',
}: PurchaseOrderDetailV2PageProps) {
  const { purchaseOrderId } = useParams<{ purchaseOrderId: string }>()
  const navigate = useNavigate()
  const permissions = useLogisticsPermissions()
  const { guardSensitiveAction, requireReverification } =
    useSensitiveOperationGuard()
  const [order, setOrder] = useState<PurchaseOrderDetail | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [activeAction, setActiveAction] =
    useState<PurchaseOrderAction | null>(null)
  const [reason, setReason] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [actionMessage, setActionMessage] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)

  const load = useCallback(async () => {
    if (!purchaseOrderId) return
    setIsLoading(true)
    setLoadError(null)
    try {
      setOrder(await purchaseOrdersV2Api.get(purchaseOrderId))
    } catch (error: unknown) {
      setOrder(null)
      setLoadError(
        error instanceof Error
          ? error.message
          : 'No se pudo cargar la orden de compra.',
      )
    } finally {
      setIsLoading(false)
    }
  }, [purchaseOrderId])

  useEffect(() => {
    void load()
  }, [load])

  const currentRevision = useMemo(() => {
    if (!order || order.revisions.length === 0) return null
    return (
      order.revisions.find(
        (revision) =>
          revision.revision_number === order.current_revision_number,
      ) ??
      [...order.revisions].sort(
        (left, right) => right.revision_number - left.revision_number,
      )[0] ??
      null
    )
  }, [order])

  const openAction = (action: PurchaseOrderAction) => {
    setReason('')
    setActionError(null)
    setActionMessage(null)
    setActiveAction(action)
  }

  const executeAction = async () => {
    if (!purchaseOrderId || !activeAction) return
    const definition = ACTIONS[activeAction]
    if (!permissions.hasPermission(definition.permission)) {
      setActionError('No tienes permisos para esta acción.')
      return
    }

    setIsSubmitting(true)
    setActionError(null)
    const idempotencyKey = createIdempotencyKey()
    try {
      let updated: PurchaseOrderDetail | null = null
      const executed = await guardSensitiveAction(async () => {
        switch (activeAction) {
          case 'submit':
            updated = await purchaseOrdersV2Api.submitForApproval(
              purchaseOrderId,
              idempotencyKey,
            )
            break
          case 'approve':
            updated = await purchaseOrdersV2Api.approve(
              purchaseOrderId,
              idempotencyKey,
            )
            break
          case 'reject':
            updated = await purchaseOrdersV2Api.reject(
              purchaseOrderId,
              { reason: reason.trim() },
              idempotencyKey,
            )
            break
          case 'return':
            updated = await purchaseOrdersV2Api.returnForChanges(
              purchaseOrderId,
              { reason: reason.trim() },
              idempotencyKey,
            )
            break
          case 'cancel':
            updated = await purchaseOrdersV2Api.cancel(
              purchaseOrderId,
              { cancellation_reason: reason.trim() },
              idempotencyKey,
            )
            break
        }
      })

      if (!executed) {
        setActiveAction(null)
        setActionError(
          'La operación requiere reverificación continua antes de continuar.',
        )
        return
      }

      if (updated) setOrder(updated)
      setActiveAction(null)
      setReason('')
      setActionMessage('La operación se completó correctamente.')
    } catch (error: unknown) {
      setActionError(
        error instanceof Error
          ? error.message
          : 'No se pudo completar la operación.',
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  if (isLoading) return <TableSkeleton rows={8} />
  if (loadError) {
    return <ErrorState message={loadError} onRetry={() => void load()} />
  }
  if (!order || !purchaseOrderId) {
    return <EmptyState title="Orden de compra no encontrada" />
  }

  const basePath = `/logistics/purchasing/purchase-orders/${purchaseOrderId}`
  const activeDefinition = activeAction ? ACTIONS[activeAction] : null

  return (
    <section className="space-y-4" aria-labelledby="purchase-order-title">
      <header className="space-y-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <button
              type="button"
              onClick={() =>
                navigate('/logistics/purchasing/purchase-orders')
              }
              className="mb-2 min-h-10 text-xs font-semibold text-[#1F4E6D] hover:underline"
            >
              ← Volver a órdenes
            </button>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#1F4E6D]">
              Orden de compra
            </p>
            <h1
              id="purchase-order-title"
              className="mt-1 text-xl font-bold text-slate-950"
            >
              {order.purchase_order_code ?? 'Borrador sin numerar'}
            </h1>
            <p className="mt-1 text-sm text-slate-500">
              {order.supplier_name ?? 'Proveedor sin nombre'} ·{' '}
              {order.currency_code} · Revisión{' '}
              {order.current_revision_number}
            </p>
          </div>
          <div className="flex max-w-2xl flex-wrap items-center justify-end gap-2">
            <StatusPill tone="info">
              {purchaseOrderStatusLabel(order.status)}
            </StatusPill>
            <StatusPill>
              Aprobación: {approvalStatusLabel(order.approval_status)}
            </StatusPill>
            <StatusPill>
              Emisión: {issuanceStatusLabel(order.issuance_status)}
            </StatusPill>
            <StatusPill>
              Envío: {dispatchStatusLabel(order.dispatch_status)}
            </StatusPill>
            <StatusPill>
              Acuse:{' '}
              {acknowledgementStatusLabel(order.acknowledgement_status)}
            </StatusPill>
          </div>
        </div>

        <div className="flex flex-wrap gap-2 border-t border-slate-100 pt-4">
          {(Object.keys(ACTIONS) as PurchaseOrderAction[]).map((action) => {
            const definition = ACTIONS[action]
            if (!permissions.hasPermission(definition.permission)) return null
            return (
              <button
                key={action}
                type="button"
                disabled={isSubmitting || requireReverification}
                onClick={() => openAction(action)}
                className={
                  definition.destructive
                    ? 'min-h-10 rounded-lg border border-rose-200 px-3 text-xs font-semibold text-rose-700 hover:bg-rose-50 disabled:opacity-40'
                    : 'min-h-10 rounded-lg border border-slate-200 px-3 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-40'
                }
              >
                {definition.confirmLabel}
              </button>
            )
          })}
        </div>
      </header>

      {!PHASE_034_BACKEND_SUPPORT.capabilities && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900">
          <strong>Contrato parcial:</strong> el backend no publica
          `getPurchaseOrderCapabilities`. La visibilidad usa permisos entregados
          por el servicio de autorización y cada transición vuelve a validarse
          en el servidor; no se infieren permisos por rol.
        </div>
      )}

      {actionMessage && (
        <div
          role="status"
          className="rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm font-medium text-emerald-800"
        >
          {actionMessage}
        </div>
      )}
      {actionError && (
        <div
          role="alert"
          className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm font-medium text-rose-800"
        >
          {actionError}
        </div>
      )}

      <nav
        aria-label="Secciones de la orden"
        className="flex flex-wrap gap-1 rounded-xl border border-slate-200 bg-slate-50 p-1"
      >
        {SECTION_LINKS.map((item) => (
          <button
            key={item.section}
            type="button"
            aria-current={section === item.section ? 'page' : undefined}
            onClick={() => navigate(`${basePath}${item.suffix}`)}
            className={
              section === item.section
                ? 'min-h-10 rounded-lg bg-white px-3 text-xs font-semibold text-[#1F4E6D] shadow-sm'
                : 'min-h-10 rounded-lg px-3 text-xs font-medium text-slate-600 hover:bg-white'
            }
          >
            {item.label}
          </button>
        ))}
      </nav>

      {section === 'overview' && (
        <div className="space-y-4">
          <dl className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
            {[
              ['ID de decisión', order.source_decision_id],
              ['ID de comprador', order.buyer_user_id],
              ['Sede', order.branch_id],
              ['Creada', formatDate(order.created_at)],
              ['Actualizada', formatDate(order.updated_at)],
              ['Aprobada', formatDate(order.approved_at)],
              ['Emitida', formatDate(order.issued_at)],
              ['Cancelada', formatDate(order.cancelled_at)],
            ].map(([label, value]) => (
              <div
                key={label}
                className="min-w-0 rounded-xl border border-slate-200 bg-white p-3"
              >
                <dt className="text-xs text-slate-500">{label}</dt>
                <dd className="mt-1 truncate text-sm font-semibold text-slate-800">
                  {value || '—'}
                </dd>
              </div>
            ))}
          </dl>
          {order.notes && (
            <div className="rounded-xl border border-slate-200 bg-white p-4">
              <h2 className="text-sm font-bold text-slate-900">Notas</h2>
              <p className="mt-2 whitespace-pre-wrap text-sm text-slate-600">
                {order.notes}
              </p>
            </div>
          )}
          {order.cancellation_reason && (
            <div className="rounded-xl border border-rose-200 bg-rose-50 p-4">
              <h2 className="text-sm font-bold text-rose-900">
                Motivo de cancelación
              </h2>
              <p className="mt-2 text-sm text-rose-800">
                {order.cancellation_reason}
              </p>
            </div>
          )}
          <PurchaseOrderAmountsPanel order={order} />
          <PurchaseOrderLinesTable revision={currentRevision} />
        </div>
      )}

      {section === 'lines' && (
        <PurchaseOrderLinesTable revision={currentRevision} />
      )}

      {section === 'revisions' && (
        <PurchaseOrderRevisionsPanel revisions={order.revisions} />
      )}

      {section === 'approval' && (
        <div className="space-y-3 rounded-xl border border-slate-200 bg-white p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <h2 className="text-base font-bold text-slate-900">
                Aprobación de la orden
              </h2>
              <p className="mt-1 text-sm text-slate-500">
                Estado informado directamente por la orden.
              </p>
            </div>
            <StatusPill tone="info">
              {approvalStatusLabel(order.approval_status)}
            </StatusPill>
          </div>
          <p className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
            El backend no permite localizar la solicitud de aprobación por
            `subject_id`; por ello no se reconstruye la cadena desde la orden.
          </p>
          <button
            type="button"
            onClick={() =>
              navigate('/logistics/purchasing/approvals/inbox')
            }
            className="min-h-11 rounded-lg border border-[#1F4E6D]/30 px-4 text-sm font-semibold text-[#1F4E6D]"
          >
            Abrir mi bandeja de aprobaciones
          </button>
        </div>
      )}

      {!['overview', 'lines', 'revisions', 'approval'].includes(section) && (
        <UnsupportedPurchaseOrderSection
          section={
            section as Exclude<
              Phase034DetailSection,
              'overview' | 'lines' | 'revisions'
            >
          }
        />
      )}

      {activeDefinition && (
        <PurchaseOrderActionDialog
          open
          title={activeDefinition.title}
          description={activeDefinition.description}
          confirmLabel={activeDefinition.confirmLabel}
          destructive={activeDefinition.destructive}
          reason={reason}
          minimumReasonLength={activeDefinition.minimumReasonLength}
          isSubmitting={isSubmitting}
          onReasonChange={setReason}
          onCancel={() => {
            if (!isSubmitting) {
              setActiveAction(null)
              setReason('')
            }
          }}
          onConfirm={() => void executeAction()}
        />
      )}
    </section>
  )
}
