import { useEffect, useState } from 'react'
import { businessPartnersApi } from '../../api/business-partners-api'
import { vehiclesApi } from '../../api/vehicles-api'
import { Button } from '../common/Button'
import type { BusinessPartner } from '../../types/business-partners'
import type { VehicleCarrierAssignment } from '../../types/vehicles'

interface PanelProps {
  vehicleId: string
  assignments: VehicleCarrierAssignment[]
  onCarrierAssigned?: () => void
  canManageCarrier?: boolean
}

export function VehicleCarrierAssignmentPanel({
  vehicleId,
  assignments,
  onCarrierAssigned,
  canManageCarrier = true,
}: PanelProps) {
  const [showAssignModal, setShowAssignModal] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const activeAssignment = assignments.find((a) => a.is_active)

  const handleAssignCarrier = async (carrierId: string, assignmentType: 'PRIMARY' | 'SECONDARY' | 'TEMPORARY', reason: string) => {
    setSubmitting(true)
    try {
      await vehiclesApi.assignCarrier(vehicleId, carrierId, assignmentType, reason)
      setShowAssignModal(false)
      if (onCarrierAssigned) onCarrierAssigned()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Error al asignar transportista')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="space-y-6 text-xs">
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <span className="font-bold uppercase tracking-wider text-slate-400 text-[10px]">
              Transportista Asignado
            </span>
            <h3 className="text-sm font-bold text-slate-800">
              {activeAssignment ? activeAssignment.carrier_partner_name : 'Sin Transportista Asignado'}
            </h3>
          </div>
          {canManageCarrier && (
            <Button size="small" onClick={() => setShowAssignModal(true)}>
              {activeAssignment ? 'Cambiar Transportista' : 'Asignar Transportista'}
            </Button>
          )}
        </div>

        {activeAssignment && (
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 text-slate-700">
            <div>
              <span className="font-bold uppercase text-[10px] text-slate-400 block">Código Socio:</span>
              <span className="font-mono font-bold text-slate-900">{activeAssignment.carrier_partner_code}</span>
            </div>
            <div>
              <span className="font-bold uppercase text-[10px] text-slate-400 block">Tipo Asignación:</span>
              <span className="font-bold text-indigo-700">{activeAssignment.assignment_type}</span>
            </div>
            <div>
              <span className="font-bold uppercase text-[10px] text-slate-400 block">Fecha Asignación:</span>
              <span className="text-slate-800">{new Date(activeAssignment.start_date).toLocaleDateString('es-PE')}</span>
            </div>
          </div>
        )}
      </div>

      {/* Assignment History */}
      <div className="space-y-3">
        <h4 className="font-bold uppercase tracking-wider text-slate-500 text-xs">
          Historial de Transportistas ({assignments.length})
        </h4>
        <div className="space-y-2">
          {assignments.map((a) => (
            <div key={a.id} className="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-3.5">
              <div>
                <span className="font-bold text-slate-800">{a.carrier_partner_name}</span>
                <span className="ml-2 font-mono text-[11px] text-slate-500">({a.carrier_partner_code})</span>
                <span className="ml-2 text-slate-400">· {a.assignment_type}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className={`rounded px-2 py-0.5 text-[10px] font-bold ${a.is_active ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-600'}`}>
                  {a.is_active ? 'Vigente' : 'Finalizado'}
                </span>
                <span className="text-[11px] text-slate-400">
                  {new Date(a.start_date).toLocaleDateString('es-PE')}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Modal Dialog */}
      {showAssignModal && (
        <ChangeVehicleCarrierDialog
          isOpen={showAssignModal}
          isSubmitting={submitting}
          currentCarrierName={activeAssignment?.carrier_partner_name}
          onAssign={handleAssignCarrier}
          onClose={() => setShowAssignModal(false)}
        />
      )}
    </div>
  )
}

interface DialogProps {
  isOpen: boolean
  isSubmitting: boolean
  currentCarrierName?: string
  onAssign: (carrierId: string, assignmentType: 'PRIMARY' | 'SECONDARY' | 'TEMPORARY', reason: string) => void
  onClose: () => void
}

export function ChangeVehicleCarrierDialog({
  isOpen,
  isSubmitting,
  currentCarrierName,
  onAssign,
  onClose,
}: DialogProps) {
  const [carriers, setCarriers] = useState<BusinessPartner[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedCarrierId, setSelectedCarrierId] = useState('')
  const [assignmentType, setAssignmentType] = useState<'PRIMARY' | 'SECONDARY' | 'TEMPORARY'>('PRIMARY')
  const [reason, setReason] = useState('')

  useEffect(() => {
    if (!isOpen) return
    setLoading(true)
    // Filter partners with CARRIER role
    businessPartnersApi.list({ role: 'CARRIER' })
      .then((res) => setCarriers(res.items || []))
      .catch(() => setCarriers([]))
      .finally(() => setLoading(false))
  }, [isOpen])

  if (!isOpen) return null

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedCarrierId || !reason.trim() || isSubmitting) return
    onAssign(selectedCarrierId, assignmentType, reason.trim())
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 text-xs"
      role="presentation"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget && !isSubmitting) onClose()
      }}
    >
      <div
        className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl space-y-4"
        role="dialog"
        aria-modal="true"
        aria-labelledby="change-carrier-title"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <h3 id="change-carrier-title" className="text-base font-bold text-slate-800">
          Asignar / Cambiar Transportista
        </h3>

        {currentCarrierName && (
          <p className="text-slate-600">
            Transportista actual: <strong>{currentCarrierName}</strong>
          </p>
        )}

        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="mb-1 block font-bold text-slate-700">Seleccionar Transportista Autorizado (CARRIER) *</label>
            <select
              value={selectedCarrierId}
              onChange={(e) => setSelectedCarrierId(e.target.value)}
              required
              disabled={loading}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 bg-white"
            >
              <option value="">Seleccionar de la lista de socios CARRIER...</option>
              {carriers.map((c) => (
                <option key={c.id} value={c.id} disabled={c.status === 'BLOCKED'}>
                  {c.legal_name} ({c.code}){c.status === 'BLOCKED' ? ' [BLOQUEADO]' : ''}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-1 block font-bold text-slate-700">Tipo de Asignación *</label>
            <select
              value={assignmentType}
              onChange={(e) => setAssignmentType(e.target.value as 'PRIMARY' | 'SECONDARY' | 'TEMPORARY')}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 bg-white"
            >
              <option value="PRIMARY">Principal</option>
              <option value="SECONDARY">Secundaria</option>
              <option value="TEMPORARY">Temporal / Contingencia</option>
            </select>
          </div>

          <div>
            <label className="mb-1 block font-bold text-slate-700">Motivo del Cambio *</label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={2}
              required
              placeholder="Justificación del cambio de asignación..."
              className="w-full resize-none rounded-lg border border-slate-300 px-3 py-2"
            />
          </div>

          <div className="flex justify-end gap-2 border-t border-slate-100 pt-3">
            <Button type="button" variant="secondary" onClick={onClose} disabled={isSubmitting}>
              Cancelar
            </Button>
            <Button
              type="submit"
              disabled={!selectedCarrierId || !reason.trim() || isSubmitting}
              isLoading={isSubmitting}
              loadingLabel="Asignando..."
            >
              Confirmar Asignación
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
