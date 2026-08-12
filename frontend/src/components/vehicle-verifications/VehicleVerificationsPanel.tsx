import { useCallback, useEffect, useState } from 'react'
import { vehicleVerificationsApi } from '../../api/vehicle-verifications-api'
import { Button } from '../common/Button'
import { LoadingSkeleton } from '../common/LoadingSkeleton'
import { ApplyVehicleVerificationDialog } from './ApplyVehicleVerificationDialog'
import { ApproveAssistedVehicleVerificationDialog } from './ApproveAssistedVehicleVerificationDialog'
import { AssistedVehicleVerificationForm } from './AssistedVehicleVerificationForm'
import { RequestVehicleVerificationDialog } from './RequestVehicleVerificationDialog'
import { VehicleVerificationCompliancePanel } from './VehicleVerificationCompliancePanel'
import { VehicleVerificationConflictsPanel } from './VehicleVerificationConflictsPanel'
import { VehicleVerificationDomainsGrid } from './VehicleVerificationDomainsGrid'
import { VehicleVerificationHistoryTimeline } from './VehicleVerificationHistoryTimeline'
import { VehicleVerificationProgress } from './VehicleVerificationProgress'
import { VehicleVerificationResultPanel } from './VehicleVerificationResultPanel'
import { useSensitiveOperationGuard } from '../../features/continuous-auth/hooks/useSensitiveOperationGuard'
import { useLogisticsPermissions } from '../../features/logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../../features/logistics-permissions/logistics-permissions-map'
import type {
  AssistedVehicleVerification,
  AssistedVehicleVerificationCreate,
  VehicleVerification,
  VehicleVerificationCompliance,
  VehicleVerificationConflict,
  VehicleVerificationConflictResolve,
  VehicleVerificationDomain,
  VehicleVerificationRequest,
} from '../../types/vehicle-verifications'

interface Props {
  vehicleId: string
  plateNumber: string
  currentVehicleVersion: number
}

export function VehicleVerificationsPanel({
  vehicleId,
  plateNumber,
  currentVehicleVersion,
}: Props) {
  const { guardSensitiveAction } = useSensitiveOperationGuard()
  const { hasPermission } = useLogisticsPermissions()
  const canRequest = hasPermission(LOGISTICS_PERMISSIONS.vehicleVerifications.request)
  const canApply = hasPermission(LOGISTICS_PERMISSIONS.vehicleVerifications.applyResult)
  const canResolveConflict = hasPermission(LOGISTICS_PERMISSIONS.vehicleVerifications.resolveConflict)
  const canApproveAssisted = hasPermission(LOGISTICS_PERMISSIONS.vehicleVerifications.approveAssisted)

  const [verifications, setVerifications] = useState<VehicleVerification[]>([])
  const [compliance, setCompliance] = useState<VehicleVerificationCompliance | null>(null)
  const [conflicts, setConflicts] = useState<VehicleVerificationConflict[]>([])
  const [pendingAssisted, setPendingAssisted] = useState<AssistedVehicleVerification[]>([])
  const [selectedVerification, setSelectedVerification] = useState<VehicleVerification | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshTick, setRefreshTick] = useState(0)

  // Dialogs
  const [showRequestModal, setShowRequestModal] = useState(false)
  const [showAssistedModal, setShowAssistedModal] = useState(false)
  const [showApplyModal, setShowApplyModal] = useState(false)
  const [approveTarget, setApproveTarget] = useState<AssistedVehicleVerification | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      const [vList, compRes, conflictList, assistedList] = await Promise.all([
        vehicleVerificationsApi.listByVehicle(vehicleId).catch(() => []),
        vehicleVerificationsApi.getVehicleCompliance(vehicleId).catch(() => null),
        vehicleVerificationsApi.listConflicts(undefined).catch(() => []),
        vehicleVerificationsApi.listAssistedVerifications().catch(() => []),
      ])
      setVerifications(vList)
      setCompliance(compRes)
      setConflicts(conflictList.filter((c) => c.vehicle_id === vehicleId))
      setPendingAssisted(assistedList.filter((a) => a.vehicle_id === vehicleId && a.review_status === 'PENDING_APPROVAL'))
      setSelectedVerification((prev) => {
        if (prev) {
          const updated = vList.find((v) => v.id === prev.id) ?? null
          return updated
        }
        return vList.length > 0 ? vList[0] : null
      })
    } finally {
      setLoading(false)
    }
  }, [vehicleId])

  useEffect(() => {
    void loadData()
  }, [loadData])

  // Poll for active verifications only
  const hasActive = verifications.some(
    (v) => v.status === 'REQUESTED' || v.status === 'QUEUED' || v.status === 'IN_PROGRESS',
  )
  useEffect(() => {
    if (!hasActive) return
    const timer = setInterval(() => {
      setRefreshTick((t) => t + 1)
    }, 5000)
    return () => clearInterval(timer)
  }, [hasActive])

  useEffect(() => {
    if (refreshTick === 0) return
    void loadData()
  }, [refreshTick, loadData])

  const handleRequestVerification = async (data: VehicleVerificationRequest) => {
    setSubmitting(true)
    try {
      await vehicleVerificationsApi.requestVerification(data)
      setShowRequestModal(false)
      void loadData()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Error al solicitar verificación')
    } finally {
      setSubmitting(false)
    }
  }

  const handleCreateAssisted = async (data: AssistedVehicleVerificationCreate) => {
    setSubmitting(true)
    try {
      await vehicleVerificationsApi.createAssistedVerification(data)
      setShowAssistedModal(false)
      void loadData()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Error al registrar validación asistida')
    } finally {
      setSubmitting(false)
    }
  }

  const handleApplyVerification = async (selectedFields: string[], reason: string, expectedVersion: number) => {
    if (!selectedVerification) return
    setSubmitting(true)
    try {
      const executed = await guardSensitiveAction(async () => {
        await vehicleVerificationsApi.applyVerification(selectedVerification.id, {
          selected_fields: selectedFields,
          reason,
          expected_vehicle_version: expectedVersion,
        })
      })
      if (executed) {
        setShowApplyModal(false)
        void loadData()
      }
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Error al aplicar verificación al vehículo')
    } finally {
      setSubmitting(false)
    }
  }

  const handleResolveConflict = async (conflictId: string, data: VehicleVerificationConflictResolve) => {
    setSubmitting(true)
    try {
      const executed = await guardSensitiveAction(async () => {
        await vehicleVerificationsApi.resolveConflict(conflictId, data)
      })
      if (executed) void loadData()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Error al resolver conflicto')
    } finally {
      setSubmitting(false)
    }
  }

  const handleRetry = async () => {
    if (!selectedVerification) return
    setSubmitting(true)
    try {
      await vehicleVerificationsApi.retryVerification(selectedVerification.id)
      void loadData()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Error al reintentar verificación')
    } finally {
      setSubmitting(false)
    }
  }

  const handleRevoke = async () => {
    if (!selectedVerification) return
    const reason = window.prompt('Motivo de revocación:')
    if (!reason) return
    setSubmitting(true)
    try {
      const executed = await guardSensitiveAction(async () => {
        await vehicleVerificationsApi.revokeVerification(selectedVerification.id, reason)
      })
      if (executed) void loadData()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Error al revocar verificación')
    } finally {
      setSubmitting(false)
    }
  }

  const handleApproveAssisted = async (notes: string) => {
    if (!approveTarget) return
    setSubmitting(true)
    try {
      const executed = await guardSensitiveAction(async () => {
        await vehicleVerificationsApi.approveAssistedVerification(approveTarget.id, notes)
      })
      if (executed) {
        setApproveTarget(null)
        void loadData()
      }
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Error al aprobar validación asistida')
    } finally {
      setSubmitting(false)
    }
  }

  const handleRejectAssisted = async (reason: string) => {
    if (!approveTarget) return
    setSubmitting(true)
    try {
      await vehicleVerificationsApi.rejectAssistedVerification(approveTarget.id, reason)
      setApproveTarget(null)
      void loadData()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Error al rechazar validación asistida')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) return <LoadingSkeleton rows={8} />

  const activeVerification = verifications.find(
    (v) => v.status === 'REQUESTED' || v.status === 'QUEUED' || v.status === 'IN_PROGRESS',
  )

  return (
    <div className="space-y-6 text-xs">
      {/* Notice */}
      <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-slate-700 space-y-1">
        <p className="font-bold text-slate-800">
          ℹ️ Verificaciones Registrales y Normativas Oficiales
        </p>
        <p>
          Las verificaciones son procesadas por el backend utilizando fuentes autorizadas o validación asistida normada.
          React no consulta portales externos directamente, no realiza scraping, no automatiza CAPTCHA ni expone credenciales.
        </p>
      </div>

      {/* Top Action Bar */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-bold text-slate-800">
          Historial de Verificaciones de la Placa{' '}
          <span className="font-mono text-indigo-700">{plateNumber}</span>
        </h3>
        <div className="flex flex-wrap gap-2">
          {canRequest && (
            <Button size="small" onClick={() => setShowRequestModal(true)}>
              + Solicitar Verificación
            </Button>
          )}
          {canRequest && (
            <Button size="small" variant="secondary" onClick={() => setShowAssistedModal(true)}>
              + Validación Asistida
            </Button>
          )}
        </div>
      </div>

      {/* Compliance Panel */}
      {compliance && <VehicleVerificationCompliancePanel compliance={compliance} />}

      {/* Active Progress (polling) */}
      {activeVerification && (
        <VehicleVerificationProgress
          verification={activeVerification}
          onRefreshNeeded={() => setRefreshTick((t) => t + 1)}
        />
      )}

      {/* Pending Assisted Approvals */}
      {pendingAssisted.length > 0 && (
        <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 space-y-2">
          <h4 className="font-bold text-amber-800 text-xs uppercase tracking-wider">
            Validaciones asistidas pendientes de aprobación ({pendingAssisted.length})
          </h4>
          <ul className="space-y-1">
            {pendingAssisted.map((a) => (
              <li
                key={a.id}
                className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-amber-200 bg-white p-2"
              >
                <span className="text-slate-700">
                  <strong className="font-mono">{a.domain}</strong> · por {a.created_by_user_name} ·{' '}
                  {a.result_status}
                </span>
                {canApproveAssisted && (
                  <Button size="small" onClick={() => setApproveTarget(a)}>
                    Revisar / Aprobar
                  </Button>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Domains Grid */}
      <VehicleVerificationDomainsGrid
        verifications={verifications}
        onSelectDomain={(v) => setSelectedVerification(v)}
        onRequestDomain={(domain: VehicleVerificationDomain) => {
          void handleRequestVerification({
            vehicle_id: vehicleId,
            plate_number: plateNumber,
            domain,
            reason: 'Solicitud desde matriz de dominios',
          })
        }}
        canRequest={canRequest}
      />

      {/* Selected Verification Result */}
      {selectedVerification && (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center justify-end gap-2">
            {selectedVerification.status === 'FAILED' && (
              <Button size="small" variant="secondary" onClick={() => void handleRetry()} disabled={submitting}>
                Reintentar
              </Button>
            )}
            {selectedVerification.status === 'COMPLETED' && (
              <Button size="small" variant="secondary" onClick={() => void handleRevoke()} disabled={submitting}>
                Revocar (Step-Up)
              </Button>
            )}
          </div>

          <VehicleVerificationResultPanel
            verification={selectedVerification}
            onApplyRequested={() => setShowApplyModal(true)}
            canApply={canApply}
          />

          {/* History */}
          {selectedVerification.history && selectedVerification.history.length > 0 && (
            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <VehicleVerificationHistoryTimeline history={selectedVerification.history} />
            </div>
          )}
        </div>
      )}

      {/* Conflicts */}
      {conflicts.length > 0 && (
        <div className="rounded-2xl border border-rose-200 bg-rose-50/30 p-4">
          <VehicleVerificationConflictsPanel
            conflicts={conflicts}
            onResolveConflict={handleResolveConflict}
            canResolve={canResolveConflict}
          />
        </div>
      )}

      {/* Request Modal */}
      {showRequestModal && (
        <RequestVehicleVerificationDialog
          isOpen={showRequestModal}
          isSubmitting={submitting}
          vehicleId={vehicleId}
          plateNumber={plateNumber}
          availableSources={[
            { source_type: 'SUNARP', source_name: 'SUNARP', method: 'AUTHORIZED_API', authorization_status: 'AUTHORIZED', available: true },
            { source_type: 'MTC', source_name: 'MTC', method: 'AUTHORIZED_API', authorization_status: 'AUTHORIZED', available: true },
            { source_type: 'SBS', source_name: 'SBS', method: 'AUTHORIZED_API', authorization_status: 'AUTHORIZED', available: true },
            { source_type: 'ASSISTED_MANUAL', source_name: 'Validación Asistida', method: 'ASSISTED_MANUAL', authorization_status: 'AUTHORIZED', available: true },
          ]}
          onSubmit={handleRequestVerification}
          onClose={() => setShowRequestModal(false)}
        />
      )}

      {/* Assisted Modal */}
      {showAssistedModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 text-xs"
          role="presentation"
          onMouseDown={(e) => {
            if (e.target === e.currentTarget && !submitting) setShowAssistedModal(false)
          }}
        >
          <div
            className="w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl space-y-4"
            role="dialog"
            aria-modal="true"
            aria-labelledby="assisted-modal-title"
            onMouseDown={(e) => e.stopPropagation()}
          >
            <AssistedVehicleVerificationForm
              vehicleId={vehicleId}
              plateNumber={plateNumber}
              onSubmit={handleCreateAssisted}
              isSubmitting={submitting}
              onCancel={() => setShowAssistedModal(false)}
            />
          </div>
        </div>
      )}

      {/* Apply Modal */}
      {selectedVerification && showApplyModal && (
        <ApplyVehicleVerificationDialog
          isOpen={showApplyModal}
          isSubmitting={submitting}
          verification={selectedVerification}
          currentVehicleVersion={currentVehicleVersion}
          onApply={handleApplyVerification}
          onClose={() => setShowApplyModal(false)}
        />
      )}

      {/* Approve Assisted Modal */}
      {approveTarget && (
        <ApproveAssistedVehicleVerificationDialog
          isOpen={Boolean(approveTarget)}
          isSubmitting={submitting}
          verification={approveTarget}
          proposedConfidence={null}
          warnings={[]}
          differences={[]}
          canSelfApprove={canApproveAssisted}
          onApprove={handleApproveAssisted}
          onReject={handleRejectAssisted}
          onClose={() => setApproveTarget(null)}
        />
      )}
    </div>
  )
}