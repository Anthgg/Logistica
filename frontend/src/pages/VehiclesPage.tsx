import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { vehiclesApi } from '../api/vehicles-api'
import { Button } from '../components/common/Button'
import { LoadingSkeleton } from '../components/common/LoadingSkeleton'
import { PageHeader } from '../components/common/PageHeader'
import { Pagination } from '../components/common/Pagination'
import { VehicleGeneralForm } from '../components/vehicles/VehicleGeneralForm'
import {
  VehicleComplianceBadge,
  VehicleLifecycleBadge,
  VehicleOperationalBadge,
} from '../components/vehicles/VehicleStatusBadge'
import { useLogisticsPermissions } from '../features/logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../features/logistics-permissions/logistics-permissions-map'
import type { PaginatedResponse } from '../types/logistics-resources'
import type {
  VehicleCreate,
  VehicleLifecycleStatus,
  VehicleListQuery,
  VehicleOperationalStatus,
  VehicleStats,
  VehicleSummary,
  VehicleType,
} from '../types/vehicles'

const PAGE_SIZE = 20

export function VehiclesPage() {
  const navigate = useNavigate()
  const { hasPermission } = useLogisticsPermissions()
  const canManage = hasPermission(LOGISTICS_PERMISSIONS.vehicles.manage)

  const [data, setData] = useState<PaginatedResponse<VehicleSummary> | null>(null)
  const [stats, setStats] = useState<VehicleStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [page, setPage] = useState(1)

  // Filters
  const [vehicleType, setVehicleType] = useState<VehicleType | ''>('')
  const [lifecycleStatus, setLifecycleStatus] = useState<VehicleLifecycleStatus | ''>('')
  const [operationalStatus, setOperationalStatus] = useState<VehicleOperationalStatus | ''>('')

  // Modal
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [submittingModal, setSubmittingModal] = useState(false)

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search)
      setPage(1)
    }, 400)
    return () => clearTimeout(timer)
  }, [search])

  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      const query: VehicleListQuery = {
        page,
        page_size: PAGE_SIZE,
        search: debouncedSearch || undefined,
        vehicle_type: vehicleType || undefined,
        lifecycle_status: lifecycleStatus || undefined,
        operational_status: operationalStatus || undefined,
      }
      const [res, statsRes] = await Promise.all([
        vehiclesApi.list(query),
        vehiclesApi.getStats().catch(() => null),
      ])
      setData(res)
      if (statsRes) setStats(statsRes)
    } finally {
      setLoading(false)
    }
  }, [page, debouncedSearch, vehicleType, lifecycleStatus, operationalStatus])

  useEffect(() => {
    void loadData()
  }, [loadData])

  const handleCreate = async (formData: VehicleCreate) => {
    setSubmittingModal(true)
    try {
      const newVehicle = await vehiclesApi.create(formData)
      setShowCreateModal(false)
      navigate(`/logistics/vehicles/${newVehicle.id}`)
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Error al crear vehículo')
    } finally {
      setSubmittingModal(false)
    }
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <PageHeader
        title="Maestro de Vehículos y Flota"
        description="Administración física, placas de rodaje, marcas, modelos, capacidades y control normativo."
        actions={
          canManage ? (
            <Button onClick={() => setShowCreateModal(true)}>
              + Registrar Vehículo
            </Button>
          ) : undefined
        }
      />

      {/* Summary Cards */}
      {stats && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-6 text-xs">
          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-xs">
            <span className="font-bold uppercase tracking-wider text-slate-400 text-[10px] block">Total Vehículos</span>
            <span className="font-mono text-xl font-bold text-slate-800">{stats.total_vehicles}</span>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-xs">
            <span className="font-bold uppercase tracking-wider text-slate-400 text-[10px] block">Activos</span>
            <span className="font-mono text-xl font-bold text-emerald-700">{stats.active_count}</span>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-xs">
            <span className="font-bold uppercase tracking-wider text-slate-400 text-[10px] block">Disponibles</span>
            <span className="font-mono text-xl font-bold text-blue-700">{stats.available_count}</span>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-xs">
            <span className="font-bold uppercase tracking-wider text-slate-400 text-[10px] block">Bloqueados</span>
            <span className="font-mono text-xl font-bold text-red-600">{stats.blocked_count}</span>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-xs">
            <span className="font-bold uppercase tracking-wider text-slate-400 text-[10px] block">Docs. Vencidos</span>
            <span className="font-mono text-xl font-bold text-rose-600">{stats.documents_expired_count}</span>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-xs">
            <span className="font-bold uppercase tracking-wider text-slate-400 text-[10px] block">Mantenimiento</span>
            <span className="font-mono text-xl font-bold text-amber-700">{stats.maintenance_count}</span>
          </div>
        </div>
      )}

      {/* Filter Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-xs text-xs">
        <div className="flex flex-1 flex-wrap items-center gap-3">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar por placa, código, marca, modelo, propietario o transportista..."
            className="w-full sm:w-80 rounded-xl border border-slate-300 px-3.5 py-2 font-medium placeholder:text-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
          />

          <select
            value={vehicleType}
            onChange={(e) => {
              setVehicleType(e.target.value as VehicleType | '')
              setPage(1)
            }}
            className="rounded-xl border border-slate-300 px-3 py-2 bg-white font-medium text-slate-700"
          >
            <option value="">Todos los tipos vehiculares</option>
            <option value="TRUCK">Camión Rígido</option>
            <option value="TRACTOR">Tractocamión / CISTERNA</option>
            <option value="TRAILER">Remolque / Semirremolque</option>
            <option value="VAN">Furgoneta / Van</option>
            <option value="PICKUP">Pickup</option>
            <option value="REFRIGERATED">Frigorífico</option>
          </select>

          <select
            value={lifecycleStatus}
            onChange={(e) => {
              setLifecycleStatus(e.target.value as VehicleLifecycleStatus | '')
              setPage(1)
            }}
            className="rounded-xl border border-slate-300 px-3 py-2 bg-white font-medium text-slate-700"
          >
            <option value="">Todos los ciclos de vida</option>
            <option value="ACTIVE">Activo</option>
            <option value="DRAFT">Borrador</option>
            <option value="INACTIVE">Inactivo</option>
            <option value="SUSPENDED">Suspendido</option>
            <option value="RETIRED">Retirado</option>
          </select>

          <select
            value={operationalStatus}
            onChange={(e) => {
              setOperationalStatus(e.target.value as VehicleOperationalStatus | '')
              setPage(1)
            }}
            className="rounded-xl border border-slate-300 px-3 py-2 bg-white font-medium text-slate-700"
          >
            <option value="">Todos los estados operativos</option>
            <option value="AVAILABLE">Disponible</option>
            <option value="UNAVAILABLE">No disponible</option>
            <option value="BLOCKED">Bloqueado</option>
            <option value="DOCUMENTS_EXPIRED">Docs. Vencidos</option>
            <option value="MAINTENANCE">Mantenimiento</option>
          </select>
        </div>

        {(search || vehicleType || lifecycleStatus || operationalStatus) && (
          <button
            type="button"
            onClick={() => {
              setSearch('')
              setVehicleType('')
              setLifecycleStatus('')
              setOperationalStatus('')
              setPage(1)
            }}
            className="text-xs font-semibold text-indigo-600 hover:underline"
          >
            Limpiar filtros
          </button>
        )}
      </div>

      {/* Table */}
      {loading ? (
        <LoadingSkeleton rows={8} />
      ) : !data || data.items.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-12 text-center text-slate-500">
          No se encontraron vehículos registrados con los criterios seleccionados.
        </div>
      ) : (
        <div className="space-y-4 text-xs">
          <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-xs">
            <table className="min-w-full divide-y divide-slate-200">
              <thead className="bg-slate-50 text-slate-600">
                <tr>
                  <th className="px-4 py-3 text-left font-semibold">Código</th>
                  <th className="px-4 py-3 text-left font-semibold">Placa</th>
                  <th className="px-4 py-3 text-left font-semibold">Marca & Modelo</th>
                  <th className="px-4 py-3 text-left font-semibold">Tipo</th>
                  <th className="px-4 py-3 text-left font-semibold">Propietario / Transportista</th>
                  <th className="px-4 py-3 text-center font-semibold">Ciclo de Vida</th>
                  <th className="px-4 py-3 text-center font-semibold">Estado Operativo</th>
                  <th className="px-4 py-3 text-center font-semibold">Cumplimiento</th>
                  <th className="px-4 py-3 text-right font-semibold">Acción</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {data.items.map((row) => (
                  <tr
                    key={row.id}
                    onClick={() => navigate(`/logistics/vehicles/${row.id}`)}
                    className="cursor-pointer hover:bg-slate-50/80 transition-colors"
                  >
                    <td className="px-4 py-3 font-mono font-bold text-slate-700">{row.internal_code}</td>
                    <td className="px-4 py-3 font-mono font-bold text-slate-900 text-sm">{row.plate_number}</td>
                    <td className="px-4 py-3">
                      <span className="font-semibold text-slate-800">{row.make_name}</span> {row.model_name}
                      <span className="text-slate-400 block text-[10px]">Año: {row.year_of_manufacture}</span>
                    </td>
                    <td className="px-4 py-3 text-slate-700 font-medium">{row.vehicle_type_label || row.vehicle_type}</td>
                    <td className="px-4 py-3 text-slate-600">
                      <span className="block font-medium">{row.current_carrier_name || 'Sin transportista'}</span>
                      <span className="text-[10px] text-slate-400">{row.current_owner_name || 'Propio'}</span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <VehicleLifecycleBadge status={row.lifecycle_status} size="sm" />
                    </td>
                    <td className="px-4 py-3 text-center">
                      <VehicleOperationalBadge status={row.operational_status} size="sm" />
                    </td>
                    <td className="px-4 py-3 text-center">
                      <VehicleComplianceBadge status={row.compliance_status} size="sm" />
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation()
                          navigate(`/logistics/vehicles/${row.id}`)
                        }}
                        className="font-semibold text-indigo-600 hover:underline"
                      >
                        Ver Detalle →
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <Pagination
            page={data.page}
            totalPages={data.total_pages}
            total={data.total}
            onPageChange={setPage}
          />
        </div>
      )}

      {/* Creation Modal */}
      {showCreateModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 text-xs"
          role="presentation"
          onMouseDown={(e) => {
            if (e.target === e.currentTarget && !submittingModal) setShowCreateModal(false)
          }}
        >
          <div
            className="w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl space-y-4"
            role="dialog"
            aria-modal="true"
            aria-labelledby="create-vehicle-title"
            onMouseDown={(e) => e.stopPropagation()}
          >
            <h3 id="create-vehicle-title" className="text-base font-bold text-slate-800">
              Registrar Nuevo Vehículo en Flota
            </h3>

            <VehicleGeneralForm
              onSubmit={handleCreate}
              isSubmitting={submittingModal}
              onCancel={() => setShowCreateModal(false)}
            />
          </div>
        </div>
      )}
    </div>
  )
}
