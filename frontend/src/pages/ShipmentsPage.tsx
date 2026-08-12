import { useCallback, useEffect, useMemo, useState } from 'react'
import { operationsApi } from '../api/operations-api'
import { Alert } from '../components/common/Alert'
import { LogisticsIcon } from '../components/common/LogisticsIcon'
import { Pagination } from '../components/common/Pagination'
import { CreateShipmentDialog } from '../components/shipments/CreateShipmentDialog'
import { ShipmentFilters } from '../components/shipments/ShipmentFilters'
import { ShipmentsPageHeader } from '../components/shipments/ShipmentsPageHeader'
import { ShipmentsTable } from '../components/shipments/ShipmentsTable'
import { ShipmentSummaryMetrics } from '../components/shipments/ShipmentSummaryMetrics'
import { useAuth } from '../hooks/useAuth'
import { useTranslations } from '../hooks/useTranslations'
import type {
  Client,
  PaginatedResponse,
  Shipment,
  ShipmentCreate,
} from '../types/operations'
import { getErrorMessage } from '../utils/errors'
import { permissionsFor } from '../utils/permissions'

const emptyForm: ShipmentCreate = {
  client_id: '',
  origin_address: '',
  destination_address: '',
  origin_district: '',
  destination_district: '',
  package_description: '',
  package_count: 1,
  total_weight: 1,
  declared_value: null,
  priority: 'normal',
  expected_delivery_at: null,
}

export function ShipmentsPage() {
  const { user } = useAuth()
  const { catalogVersion } = useTranslations()
  const canManage = user ? permissionsFor(user.role).manageShipments : false

  const [data, setData] = useState<PaginatedResponse<Shipment>>({
    items: [],
    page: 1,
    page_size: 20,
    total: 0,
    total_pages: 0,
  })
  const [clients, setClients] = useState<Client[]>([])
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const [priority, setPriority] = useState('')
  const [page, setPage] = useState(1)
  const [form, setForm] = useState<ShipmentCreate>(emptyForm)
  const [isOpen, setIsOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const load = useCallback(async () => {
    void catalogVersion
    setIsLoading(true)
    setError(null)
    try {
      const [shipments, clientPage] = await Promise.all([
        operationsApi.shipments.list({
          page,
          page_size: 20,
          search,
          status,
          priority,
          sort_by: 'created_at',
          sort_order: 'desc',
        }),
        operationsApi.clients.list({ page_size: 100, is_active: true }),
      ])
      setData(shipments)
      setClients(clientPage.items)
    } catch (caught: unknown) {
      setError(getErrorMessage(caught))
    } finally {
      setIsLoading(false)
    }
  }, [catalogVersion, page, priority, search, status])

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 250)
    return () => window.clearTimeout(timer)
  }, [load])

  const save = async () => {
    setIsSaving(true)
    setError(null)
    try {
      const created = await operationsApi.shipments.create({
        ...form,
        declared_value: form.declared_value || null,
        expected_delivery_at: form.expected_delivery_at
          ? new Date(form.expected_delivery_at).toISOString()
          : null,
      })
      setIsOpen(false)
      setForm(emptyForm)
      setSuccess(`Envío ${created.tracking_code} registrado.`)
      await load()
    } catch (caught: unknown) {
      setError(getErrorMessage(caught))
    } finally {
      setIsSaving(false)
    }
  }

  // Cálculos de métricas de resumen
  const metrics = useMemo(() => {
    let inTransit = 0
    let delivered = 0
    let incidences = 0

    for (const item of data.items) {
      if (item.status === 'in_transit' || item.status === 'out_for_delivery' || item.status === 'picked_up') {
        inTransit++
      } else if (item.status === 'delivered') {
        delivered++
      } else if (item.status === 'delayed' || item.status === 'cancelled' || item.status === 'returned') {
        incidences++
      }
    }

    return {
      total: data.total,
      inTransit,
      delivered,
      incidences,
    }
  }, [data])

  return (
    <div className="w-full min-w-0 space-y-5">
      {/* Encabezado Principal */}
      <ShipmentsPageHeader
        eyebrow="OPERACIONES / ENVÍOS"
        title="Gestión de envíos"
        description="Registra, consulta y supervisa el recorrido de cada despacho."
        actions={
          canManage ? (
            <button
              type="button"
              onClick={() => setIsOpen(true)}
              className="inline-flex h-10 items-center justify-center gap-2 rounded-[#0A0F1D] bg-[#1F4E6D] px-4 text-xs font-semibold text-white shadow-2xs transition-colors hover:bg-[#173F5F] focus-visible:outline-2 focus-visible:outline-[#1F4E6D]"
            >
              <LogisticsIcon name="package" size={16} />
              <span>Nuevo envío</span>
            </button>
          ) : undefined
        }
      />

      {/* Alertas */}
      {error && (
        <Alert variant="error" onDismiss={() => setError(null)}>
          {error}
        </Alert>
      )}
      {success && (
        <Alert variant="success" onDismiss={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      {/* Tarjetas de Resumen */}
      <ShipmentSummaryMetrics
        total={metrics.total}
        inTransit={metrics.inTransit}
        delivered={metrics.delivered}
        incidences={metrics.incidences}
      />

      {/* Barra de Filtros */}
      <ShipmentFilters
        search={search}
        onSearchChange={(val) => {
          setSearch(val)
          setPage(1)
        }}
        status={status}
        onStatusChange={(val) => {
          setStatus(val)
          setPage(1)
        }}
        priority={priority}
        onPriorityChange={(val) => {
          setPriority(val)
          setPage(1)
        }}
        onClearFilters={() => {
          setSearch('')
          setStatus('')
          setPriority('')
          setPage(1)
        }}
        totalResults={data.total}
      />

      {/* Tabla de Envíos */}
      <ShipmentsTable
        shipments={data.items}
        clients={clients}
        isLoading={isLoading}
      />

      {/* Paginación */}
      <div className="flex justify-end pt-1">
        <Pagination
          page={data.page}
          totalPages={data.total_pages}
          total={data.total}
          onPageChange={setPage}
        />
      </div>

      {/* Modal de Registro */}
      <CreateShipmentDialog
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        onSubmit={() => void save()}
        isSubmitting={isSaving}
        form={form}
        setForm={setForm}
        clients={clients}
      />
    </div>
  )
}

