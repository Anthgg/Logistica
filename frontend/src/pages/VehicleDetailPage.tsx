import { useCallback, useEffect, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { vehiclesApi } from '../api/vehicles-api'
import { Button } from '../components/common/Button'
import { LoadingSkeleton } from '../components/common/LoadingSkeleton'
import { PageHeader } from '../components/common/PageHeader'
import { BlockVehicleDialog, UnblockVehicleDialog } from '../components/vehicles/BlockVehicleDialog'
import { ChangeVehiclePlateDialog } from '../components/vehicles/ChangeVehiclePlateDialog'
import { VehicleCapacityPanel } from '../components/vehicles/VehicleCapacityPanel'
import { VehicleCarrierAssignmentPanel } from '../components/vehicles/VehicleCarrierAssignmentPanel'
import { VehicleCompliancePanel } from '../components/vehicles/VehicleCompliancePanel'
import { VehicleDimensionsPanel } from '../components/vehicles/VehicleDimensionsPanel'
import { VehicleDocumentsPanel } from '../components/vehicles/VehicleDocumentsPanel'
import { VehicleHistoryTimeline } from '../components/vehicles/VehicleHistoryTimeline'
import {
  VehicleComplianceBadge,
  VehicleLifecycleBadge,
  VehicleOperationalBadge,
} from '../components/vehicles/VehicleStatusBadge'
import { VehicleVersionsPanel } from '../components/vehicles/VehicleVersionsPanel'
import { VehicleVerificationsPanel } from '../components/vehicle-verifications/VehicleVerificationsPanel'
import { useSensitiveOperationGuard } from '../features/continuous-auth/hooks/useSensitiveOperationGuard'
import type {
  Vehicle,
  VehicleCapacityProfile,
  VehicleCarrierAssignment,
  VehicleCompliance,
  VehicleDocument,
  VehicleOwnershipAssignment,
  VehicleVersion,
} from '../types/vehicles'

type VehicleTab =
  | 'summary'
  | 'identification'
  | 'capacity'
  | 'ownership_carrier'
  | 'documents'
  | 'verifications'
  | 'compliance'
  | 'versions'
  | 'history'

export function VehicleDetailPage() {
  const { vehicleId } = useParams<{ vehicleId: string }>()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const activeTab: VehicleTab = (searchParams.get('tab') as VehicleTab) || 'summary'

  const { guardSensitiveAction } = useSensitiveOperationGuard()

  const [vehicle, setVehicle] = useState<Vehicle | null>(null)
  const [capacityProfiles, setCapacityProfiles] = useState<VehicleCapacityProfile[]>([])
  const [ownerships, setOwnerships] = useState<VehicleOwnershipAssignment[]>([])
  const [carrierAssignments, setCarrierAssignments] = useState<VehicleCarrierAssignment[]>([])
  const [documents, setDocuments] = useState<VehicleDocument[]>([])
  const [compliance, setCompliance] = useState<VehicleCompliance | null>(null)
  const [versions, setVersions] = useState<VehicleVersion[]>([])
  const [history, setHistory] = useState<Array<{ id: string; event_type: string; action_description: string; user_name: string; created_at: string }>>([])

  const [loading, setLoading] = useState(true)
  const [isActionLoading, setIsActionLoading] = useState(false)

  // Dialog states
  const [showPlateModal, setShowPlateModal] = useState(false)
  const [showBlockModal, setShowBlockModal] = useState(false)
  const [showUnblockModal, setShowUnblockModal] = useState(false)

  const loadVehicleData = useCallback(async () => {
    if (!vehicleId) return
    setLoading(true)
    try {
      const v = await vehiclesApi.get(vehicleId)
      setVehicle(v)

      const [cProfiles, ownList, carrList, docList, compRes, verList, histList] = await Promise.all([
        vehiclesApi.listCapacityProfiles(vehicleId).catch(() => []),
        vehiclesApi.listOwnershipAssignments(vehicleId).catch(() => []),
        vehiclesApi.listCarrierAssignments(vehicleId).catch(() => []),
        vehiclesApi.listDocuments(vehicleId).catch(() => []),
        vehiclesApi.getCompliance(vehicleId).catch(() => null),
        vehiclesApi.listVersions(vehicleId).catch(() => []),
        vehiclesApi.getHistory(vehicleId).catch(() => []),
      ])

      setCapacityProfiles(cProfiles)
      setOwnerships(ownList)
      setCarrierAssignments(carrList)
      setDocuments(docList)
      setCompliance(compRes)
      setVersions(verList)
      setHistory(histList)
    } catch {
      // Handled by UI null state
    } finally {
      setLoading(false)
    }
  }, [vehicleId])

  useEffect(() => {
    void loadVehicleData()
  }, [loadVehicleData])

  const setTab = (tab: VehicleTab) => {
    setSearchParams({ tab })
  }

  // State Transition Handlers
  const handleActivate = async () => {
    if (!vehicleId) return
    setIsActionLoading(true)
    try {
      const executed = await guardSensitiveAction(async () => {
        await vehiclesApi.activate(vehicleId)
      })
      if (executed) void loadVehicleData()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Error al activar vehículo')
    } finally {
      setIsActionLoading(false)
    }
  }

  const handleBlock = async (reason: string) => {
    if (!vehicleId) return
    setIsActionLoading(true)
    try {
      const executed = await guardSensitiveAction(async () => {
        await vehiclesApi.block(vehicleId, reason)
      })
      if (executed) {
        setShowBlockModal(false)
        void loadVehicleData()
      }
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Error al bloquear vehículo')
    } finally {
      setIsActionLoading(false)
    }
  }

  const handleUnblock = async (reason: string) => {
    if (!vehicleId) return
    setIsActionLoading(true)
    try {
      const executed = await guardSensitiveAction(async () => {
        await vehiclesApi.unblock(vehicleId, reason)
      })
      if (executed) {
        setShowUnblockModal(false)
        void loadVehicleData()
      }
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Error al desbloquear vehículo')
    } finally {
      setIsActionLoading(false)
    }
  }

  const handleChangePlate = async (newPlate: string, reason: string) => {
    if (!vehicleId) return
    setIsActionLoading(true)
    try {
      const executed = await guardSensitiveAction(async () => {
        await vehiclesApi.changePlate(vehicleId, newPlate, reason)
      })
      if (executed) {
        setShowPlateModal(false)
        void loadVehicleData()
      }
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Error al cambiar placa')
    } finally {
      setIsActionLoading(false)
    }
  }

  if (loading) return <LoadingSkeleton rows={10} />
  if (!vehicle) {
    return (
      <div className="mx-auto max-w-5xl p-6 text-center space-y-4">
        <p className="text-slate-500">No se encontró el vehículo especificado.</p>
        <Button onClick={() => navigate('/logistics/vehicles')}>Volver al catálogo</Button>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      {/* Header */}
      <PageHeader
        eyebrow={`Código: ${vehicle.internal_code} · VIN: ${vehicle.vin || 'N/A'}`}
        title={`Placa ${vehicle.plate_number} — ${vehicle.make_name} ${vehicle.model_name}`}
        description={`${vehicle.vehicle_type_label || vehicle.vehicle_type} (${vehicle.body_type_label || vehicle.body_type}) · Año ${vehicle.year_of_manufacture}`}
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <VehicleLifecycleBadge status={vehicle.lifecycle_status} />
            <VehicleOperationalBadge status={vehicle.operational_status} />
            {compliance && <VehicleComplianceBadge status={compliance.general_status} />}

            {/* Action Bar */}
            {vehicle.lifecycle_status === 'DRAFT' && vehicle.capabilities?.can_activate && (
              <Button size="small" onClick={() => void handleActivate()} isLoading={isActionLoading}>
                Activar Vehículo
              </Button>
            )}

            {vehicle.operational_status !== 'BLOCKED' && vehicle.capabilities?.can_block && (
              <Button size="small" variant="secondary" onClick={() => setShowBlockModal(true)}>
                Bloquear (Step-Up)
              </Button>
            )}

            {vehicle.operational_status === 'BLOCKED' && vehicle.capabilities?.can_unblock && (
              <Button size="small" variant="secondary" onClick={() => setShowUnblockModal(true)}>
                Desbloquear (Step-Up)
              </Button>
            )}

            {vehicle.capabilities?.can_change_plate && (
              <Button size="small" variant="secondary" onClick={() => setShowPlateModal(true)}>
                Cambiar Placa (Step-Up)
              </Button>
            )}
          </div>
        }
      />

      {/* Tabs */}
      <div className="border-b border-slate-200">
        <nav className="flex gap-1" aria-label="Pestañas de Vehículo">
          {[
            { id: 'summary', label: 'Resumen' },
            { id: 'identification', label: 'Identificación Físico-Registral' },
            { id: 'capacity', label: 'Capacidad & Dimensiones' },
            { id: 'ownership_carrier', label: 'Propiedad & Transportista' },
            { id: 'documents', label: `Documentos (${documents.length})` },
            { id: 'verifications', label: 'Verificaciones Registrales' },
            { id: 'compliance', label: 'Cumplimiento Normativo' },
            { id: 'versions', label: `Versiones (v${vehicle.active_version_number})` },
            { id: 'history', label: 'Historial' },
          ].map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => setTab(t.id as VehicleTab)}
              className={`px-4 py-2.5 text-xs font-semibold border-b-2 transition-colors ${
                activeTab === t.id
                  ? 'border-indigo-600 text-indigo-600 font-bold'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              {t.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Contents */}
      <div className="pt-2 text-xs">
        {activeTab === 'summary' && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:grid-cols-4">
              <div>
                <span className="font-bold uppercase tracking-wider text-slate-400 text-[10px] block mb-1">Transportista Asignado</span>
                <span className="font-bold text-slate-800 text-sm">{vehicle.current_carrier_name || 'Sin asignar'}</span>
              </div>
              <div>
                <span className="font-bold uppercase tracking-wider text-slate-400 text-[10px] block mb-1">Propietario Legal</span>
                <span className="font-bold text-slate-800 text-sm">{vehicle.current_owner_name || 'Propio'}</span>
              </div>
              <div>
                <span className="font-bold uppercase tracking-wider text-slate-400 text-[10px] block mb-1">Capacidad Resumida</span>
                <span className="font-mono font-bold text-indigo-700 text-sm">{vehicle.current_capacity_summary || 'Sin perfil'}</span>
              </div>
              <div>
                <span className="font-bold uppercase tracking-wider text-slate-400 text-[10px] block mb-1">Combustible</span>
                <span className="font-bold text-slate-800 text-sm">{vehicle.fuel_type}</span>
              </div>
            </div>

            {compliance && <VehicleCompliancePanel compliance={compliance} />}
          </div>
        )}

        {activeTab === 'identification' && (
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
            <h3 className="text-sm font-bold text-slate-800 border-b border-slate-100 pb-2">
              Identificación y Características Físicas
            </h3>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 text-slate-700">
              <div><span className="font-bold uppercase text-[10px] text-slate-400 block">Placa Actual:</span><span className="font-mono font-bold text-slate-900 text-base">{vehicle.plate_number}</span></div>
              <div><span className="font-bold uppercase text-[10px] text-slate-400 block">VIN:</span><span className="font-mono font-bold text-slate-900">{vehicle.vin || '—'}</span></div>
              <div><span className="font-bold uppercase text-[10px] text-slate-400 block">País de Registro:</span><span className="font-bold text-slate-900">{vehicle.country_of_registration}</span></div>
              <div><span className="font-bold uppercase text-[10px] text-slate-400 block">Marca:</span><span className="font-bold text-slate-900">{vehicle.make_name}</span></div>
              <div><span className="font-bold uppercase text-[10px] text-slate-400 block">Modelo:</span><span className="font-bold text-slate-900">{vehicle.model_name}</span></div>
              <div><span className="font-bold uppercase text-[10px] text-slate-400 block">Año Fabricación:</span><span className="font-mono font-bold text-slate-900">{vehicle.year_of_manufacture}</span></div>
              <div><span className="font-bold uppercase text-[10px] text-slate-400 block">Ejes / Ruedas:</span><span className="font-bold text-slate-900">{vehicle.axles_count} ejes / {vehicle.wheels_count || 'N/A'} ruedas</span></div>
              <div><span className="font-bold uppercase text-[10px] text-slate-400 block">Color:</span><span className="font-bold text-slate-900">{vehicle.color || 'Sin especificar'}</span></div>
              <div><span className="font-bold uppercase text-[10px] text-slate-400 block">Creado por:</span><span className="text-slate-600">{vehicle.created_by_user_name}</span></div>
            </div>
          </div>
        )}

        {activeTab === 'capacity' && (
          <div className="space-y-6">
            <VehicleCapacityPanel
              vehicleId={vehicle.id}
              profiles={capacityProfiles}
              onProfileCreated={loadVehicleData}
              canManageCapacity={vehicle.capabilities?.can_manage_capacity}
            />
            <VehicleDimensionsPanel dimensions={null} />
          </div>
        )}

        {activeTab === 'ownership_carrier' && (
          <div className="space-y-6">
            <VehicleCarrierAssignmentPanel
              vehicleId={vehicle.id}
              assignments={carrierAssignments}
              onCarrierAssigned={loadVehicleData}
              canManageCarrier={vehicle.capabilities?.can_manage_carrier}
            />

            {/* Ownership Summary */}
            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-3">
              <h4 className="font-bold text-slate-800 text-sm border-b border-slate-100 pb-2">
                Historial de Propiedad ({ownerships.length})
              </h4>
              {ownerships.length === 0 ? (
                <p className="text-slate-400">Propiedad interna por defecto.</p>
              ) : (
                <div className="space-y-2">
                  {ownerships.map((o) => (
                    <div key={o.id} className="flex justify-between items-center p-3 bg-slate-50 rounded-xl border border-slate-200">
                      <div>
                        <span className="font-bold text-slate-800">{o.ownership_type}</span>
                        <span className="ml-2 text-slate-600 font-medium">{o.owner_partner_name || 'Propio / Interno'}</span>
                      </div>
                      <span className="text-slate-400">{new Date(o.start_date).toLocaleDateString('es-PE')}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'documents' && (
          <VehicleDocumentsPanel
            vehicleId={vehicle.id}
            documents={documents}
            onDocumentAdded={loadVehicleData}
            canManageDocuments={vehicle.capabilities?.can_manage_documents}
          />
        )}

        {activeTab === 'verifications' && (
          <VehicleVerificationsPanel
            vehicleId={vehicle.id}
            plateNumber={vehicle.plate_number}
            currentVehicleVersion={vehicle.active_version_number}
          />
        )}

        {activeTab === 'compliance' && compliance && (
          <VehicleCompliancePanel compliance={compliance} />
        )}

        {activeTab === 'versions' && (
          <VehicleVersionsPanel versions={versions} />
        )}

        {activeTab === 'history' && (
          <VehicleHistoryTimeline history={history} />
        )}
      </div>

      {/* Dialog Modals */}
      {showPlateModal && (
        <ChangeVehiclePlateDialog
          isOpen={showPlateModal}
          isSubmitting={isActionLoading}
          vehicleId={vehicle.id}
          currentPlate={vehicle.plate_number}
          onChangePlate={handleChangePlate}
          onClose={() => setShowPlateModal(false)}
        />
      )}

      {showBlockModal && (
        <BlockVehicleDialog
          isOpen={showBlockModal}
          isSubmitting={isActionLoading}
          vehiclePlate={vehicle.plate_number}
          onBlock={handleBlock}
          onClose={() => setShowBlockModal(false)}
        />
      )}

      {showUnblockModal && (
        <UnblockVehicleDialog
          isOpen={showUnblockModal}
          isSubmitting={isActionLoading}
          vehiclePlate={vehicle.plate_number}
          onUnblock={handleUnblock}
          onClose={() => setShowUnblockModal(false)}
        />
      )}
    </div>
  )
}
