import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { purchaseOrdersApi } from '../api/purchase-orders-api'
import { Alert } from '../components/common/Alert'
import { Button } from '../components/common/Button'
import { LoadingSkeleton } from '../components/common/LoadingSkeleton'
import { MetricCard } from '../components/common/MetricCard'
import { PageHeader } from '../components/common/PageHeader'
import { Pagination } from '../components/common/Pagination'
import { PurchaseOrderFormModal } from '../components/purchase-orders/PurchaseOrderFormModal'
import { PurchaseOrderStatusBadge } from '../components/purchase-orders/PurchaseOrderStatusBadge'
import { useLogisticsPermissions } from '../features/logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../features/logistics-permissions/logistics-permissions-map'
import type {
  PurchaseOrder,
  PurchaseOrderCreate,
  PurchaseOrderStatus,
} from '../types/purchase-orders'

const PAGE_SIZE = 20
const STATUS_OPTIONS: Array<{ value: '' | PurchaseOrderStatus; label: string }> = [
  { value: '', label: 'Todos los estados' },
  { value: 'DRAFT', label: 'Borrador' },
  { value: 'APPROVED', label: 'Aprobada' },
  { value: 'ISSUED', label: 'Emitida' },
  { value: 'CONFIRMED', label: 'Confirmada' },
  { value: 'PARTIALLY_RECEIVED', label: 'Recepción parcial' },
  { value: 'CLOSED', label: 'Cerrada' },
  { value: 'ANNULLED', label: 'Anulada' },
]

function formatAmount(value: string, currency: string) {
  const amount = Number(value)
  if (!Number.isFinite(amount)) return `${value} ${currency}`
  return new Intl.NumberFormat('es-PE', {
    style: 'currency',
    currency,
  }).format(amount)
}

export function PurchaseOrdersPage() {
  const navigate = useNavigate()
  const { hasPermission } = useLogisticsPermissions()
  const canCreate = hasPermission(LOGISTICS_PERMISSIONS.purchaseOrders.create)
  const [orders, setOrders] = useState<PurchaseOrder[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState<'' | PurchaseOrderStatus>('')
  const [page, setPage] = useState(1)
  const [showForm, setShowForm] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      setOrders(await purchaseOrdersApi.list(status ? { status } : undefined))
    } catch (loadError) {
      setError(
        loadError instanceof Error
          ? loadError.message
          : 'No se pudieron cargar las órdenes de compra.',
      )
    } finally {
      setLoading(false)
    }
  }, [status])

  useEffect(() => {
    void load()
  }, [load])

  const filteredOrders = useMemo(() => {
    const term = search.trim().toLocaleLowerCase('es-PE')
    if (!term) return orders
    return orders.filter((order) =>
      `${order.order_number} ${order.supplier_name}`
        .toLocaleLowerCase('es-PE')
        .includes(term),
    )
  }, [orders, search])

  const totalPages = Math.max(Math.ceil(filteredOrders.length / PAGE_SIZE), 1)
  const pageItems = filteredOrders.slice(
    (page - 1) * PAGE_SIZE,
    page * PAGE_SIZE,
  )
  const stats = useMemo(
    () => ({
      drafts: orders.filter((order) => order.status === 'DRAFT').length,
      approved: orders.filter((order) => order.status === 'APPROVED').length,
      issued: orders.filter((order) => order.status === 'ISSUED').length,
    }),
    [orders],
  )

  const createOrder = async (payload: PurchaseOrderCreate) => {
    setSubmitting(true)
    setSubmitError(null)
    try {
      const created = await purchaseOrdersApi.create(payload)
      setShowForm(false)
      navigate(`/logistics/purchase-orders/${created.id}`)
    } catch (createError) {
      setSubmitError(
        createError instanceof Error
          ? createError.message
          : 'No se pudo crear la orden.',
      )
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="mx-auto max-w-7xl space-y-5 p-6">
      <PageHeader
        eyebrow="Compras"
        title="Órdenes de compra"
        description="Crea, aprueba, emite y anula órdenes usando el flujo del backend."
        actions={
          canCreate ? (
            <Button onClick={() => setShowForm(true)}>Nueva orden</Button>
          ) : undefined
        }
      />

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard label="Total" value={orders.length} detail="Órdenes registradas" icon="document" />
        <MetricCard label="Borradores" value={stats.drafts} detail="Pendientes de aprobación" icon="document" tone="neutral" />
        <MetricCard label="Aprobadas" value={stats.approved} detail="Listas para emitir" icon="check" tone="success" />
        <MetricCard label="Emitidas" value={stats.issued} detail="Enviadas al proveedor" icon="activity" tone="primary" />
      </div>

      <div className="grid gap-3 rounded-xl border border-slate-200 bg-white p-4 sm:grid-cols-[1fr_220px_auto]">
        <input
          className="field__input"
          type="search"
          value={search}
          onChange={(event) => {
            setSearch(event.target.value)
            setPage(1)
          }}
          placeholder="Buscar por número o proveedor"
          aria-label="Buscar órdenes de compra"
        />
        <select
          className="field__input"
          value={status}
          onChange={(event) => {
            setStatus(event.target.value as '' | PurchaseOrderStatus)
            setPage(1)
          }}
          aria-label="Filtrar por estado"
        >
          {STATUS_OPTIONS.map((option) => (
            <option key={option.value || 'all'} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        <Button variant="secondary" onClick={() => void load()}>
          Actualizar
        </Button>
      </div>

      {error && (
        <Alert variant="error" title="No se pudo cargar" onDismiss={() => setError(null)}>
          {error}
        </Alert>
      )}
      {loading ? (
        <LoadingSkeleton rows={8} />
      ) : pageItems.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-300 bg-white p-12 text-center text-sm text-slate-500">
          No hay órdenes que coincidan con los filtros.
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-4 py-3">Número</th>
                <th className="px-4 py-3">Proveedor</th>
                <th className="px-4 py-3">Estado</th>
                <th className="px-4 py-3 text-right">Total</th>
                <th className="px-4 py-3">Entrega</th>
                <th className="px-4 py-3">Actualizada</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {pageItems.map((order) => (
                <tr
                  key={order.id}
                  className="cursor-pointer hover:bg-slate-50"
                  onClick={() => navigate(`/logistics/purchase-orders/${order.id}`)}
                >
                  <td className="px-4 py-3 font-mono font-semibold text-primary">{order.order_number}</td>
                  <td className="px-4 py-3 font-medium text-slate-800">{order.supplier_name}</td>
                  <td className="px-4 py-3"><PurchaseOrderStatusBadge status={order.status} size="sm" /></td>
                  <td className="px-4 py-3 text-right font-semibold">{formatAmount(order.total_amount, order.currency_code)}</td>
                  <td className="px-4 py-3 text-slate-600">{order.expected_delivery_date ?? '—'}</td>
                  <td className="px-4 py-3 text-slate-600">{new Date(order.updated_at).toLocaleDateString('es-PE')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Pagination
        page={Math.min(page, totalPages)}
        totalPages={totalPages}
        total={filteredOrders.length}
        onPageChange={setPage}
      />

      <PurchaseOrderFormModal
        isOpen={showForm}
        isSubmitting={submitting}
        error={submitError}
        onSubmit={(payload) => void createOrder(payload)}
        onClose={() => {
          setShowForm(false)
          setSubmitError(null)
        }}
      />
    </div>
  )
}
