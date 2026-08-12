import { useState } from 'react'
import { Alert } from '../common/Alert'
import { Button } from '../common/Button'
import { LogisticsIcon } from '../common/LogisticsIcon'
import { StatusBadge } from '../common/StatusBadge'
import type { ShipmentStatus } from '../../types/operations'
import { ALL_SHIPMENT_STATUSES, SHIPMENT_TRANSITIONS } from '../../features/shipments/shipmentTransitions'
import { getShipmentStatusLabel } from '../../features/shipments/shipmentStatusLabels'
import { useTranslations } from '../../hooks/useTranslations'

interface Props {
  isOpen: boolean
  currentStatus: ShipmentStatus
  isSaving: boolean
  error: string | null
  onClose: () => void
  onSubmit: (data: { status: ShipmentStatus; location: string; description: string }) => void
}

const MAX_LOCATION_CHARS = 100
const MAX_DESCRIPTION_CHARS = 300

export function ChangeShipmentStatusDialog({
  isOpen,
  currentStatus,
  isSaving,
  error,
  onClose,
  onSubmit,
}: Props) {
  const { language } = useTranslations()
  const [selectedStatus, setSelectedStatus] = useState<ShipmentStatus | null>(null)
  const [location, setLocation] = useState('')
  const [description, setDescription] = useState('')

  if (!isOpen) return null

  const allowedNext = SHIPMENT_TRANSITIONS[currentStatus] || []
  const isFinalState = currentStatus === 'cancelled' || currentStatus === 'returned'

  const handleSelectStatus = (target: ShipmentStatus) => {
    if (isSaving || target === currentStatus || !allowedNext.includes(target)) return
    setSelectedStatus(target)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (isSaving || !selectedStatus || !allowedNext.includes(selectedStatus)) return
    onSubmit({
      status: selectedStatus,
      location: location.trim(),
      description: description.trim(),
    })
  }

  const isCriticalCancel = selectedStatus === 'cancelled'
  const isCriticalDeliver = selectedStatus === 'delivered'

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/45 backdrop-blur-xs animate-in fade-in-0 duration-200 overflow-y-auto">
      <div
        className="relative w-full max-w-[620px] rounded-2xl border border-slate-200 bg-white p-5 shadow-2xl animate-in zoom-in-95 duration-200 my-auto"
        role="dialog"
        aria-modal="true"
        aria-labelledby="dialog-status-title"
      >
        {/* Encabezado */}
        <div className="flex items-start justify-between border-b border-slate-100 pb-3.5 mb-4">
          <div className="flex items-start gap-3">
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-[#1F4E6D]">
              <LogisticsIcon name="activity" size={18} />
            </span>
            <div>
              <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400 leading-none">
                REGISTRO OPERATIVO
              </p>
              <h2 id="dialog-status-title" className="text-base font-bold text-slate-900 leading-tight mt-0.5">
                Siguiente estado del envío
              </h2>
              <p className="text-xs text-slate-500 leading-none mt-1">
                Las opciones disponibles dependen del estado actual.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={isSaving}
            className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition-colors cursor-pointer border-none bg-transparent"
            aria-label="Cerrar"
          >
            <LogisticsIcon name="x" size={16} />
          </button>
        </div>

        {error && (
          <div className="mb-4">
            <Alert variant="error">{error}</Alert>
          </div>
        )}

        {isFinalState ? (
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-center my-4">
            <p className="text-xs font-semibold text-slate-700">
              Este envío se encuentra en un estado final (
              <span className="font-bold text-slate-900">
                {getShipmentStatusLabel(currentStatus, language)}
              </span>
              ) y no admite más cambios.
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            {/* Lista interactiva de los 10 estados */}
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-semibold text-slate-700">
                Selecciona el nuevo estado <span className="text-rose-500">*</span>
              </label>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-[260px] overflow-y-auto pr-1">
                {ALL_SHIPMENT_STATUSES.map((status) => {
                  const isCurrent = status === currentStatus
                  const isAllowed = allowedNext.includes(status)
                  const isSelected = status === selectedStatus
                  const label = getShipmentStatusLabel(status, language)

                  let stateClasses = 'border-slate-200 bg-white hover:border-slate-300 cursor-pointer'
                  if (isCurrent) {
                    stateClasses = 'border-blue-400 bg-blue-50/70 ring-1 ring-blue-400 cursor-default'
                  } else if (isSelected) {
                    stateClasses = 'border-[#1F4E6D] bg-blue-50/40 ring-2 ring-[#1F4E6D] cursor-pointer'
                  } else if (!isAllowed) {
                    stateClasses = 'border-slate-100 bg-slate-50/60 opacity-60 cursor-not-allowed'
                  }

                  const currentLabelName = getShipmentStatusLabel(currentStatus, language)

                  return (
                    <button
                      key={status}
                      type="button"
                      disabled={isSaving || isCurrent || !isAllowed}
                      onClick={() => handleSelectStatus(status)}
                      className={`flex flex-col text-left p-2.5 rounded-xl border text-xs transition-colors relative ${stateClasses}`}
                    >
                      <div className="flex items-center justify-between w-full mb-1">
                        <StatusBadge value={status}>{label}</StatusBadge>
                        {isCurrent && (
                          <span className="text-[10px] font-bold text-blue-700 bg-blue-100 px-1.5 py-0.5 rounded-md">
                            Actual
                          </span>
                        )}
                        {isSelected && !isCurrent && (
                          <span className="text-[10px] font-bold text-[#1F4E6D] bg-blue-100 px-1.5 py-0.5 rounded-md">
                            Seleccionado
                          </span>
                        )}
                      </div>

                      {!isCurrent && !isAllowed && (
                        <p className="text-[10px] text-slate-500 mt-1 leading-tight">
                          No se puede cambiar directamente de {currentLabelName} a {label}.
                        </p>
                      )}
                      {isAllowed && !isCurrent && (
                        <p className="flex items-center gap-0.5 text-[10px] text-emerald-700 font-medium mt-1 leading-tight">
                          <LogisticsIcon name="check" size={11} aria-hidden /> Transición disponible
                        </p>
                      )}
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Advertencia para estados críticos */}
            {isCriticalCancel && (
              <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800">
                <strong className="flex items-center gap-1 font-bold mb-0.5"><LogisticsIcon name="alert" size={13} aria-hidden /> Confirmación de cancelación</strong>
                Este cambio puede afectar el seguimiento del envío. Confirma que deseas marcarlo como cancelado.
              </div>
            )}

            {isCriticalDeliver && (
              <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-xs text-emerald-800">
                <strong className="flex items-center gap-1 font-bold mb-0.5"><LogisticsIcon name="check" size={13} aria-hidden /> Confirmación de entrega</strong>
                Se registrará el envío como completado y entregado al destinatario final.
              </div>
            )}

            {/* Ubicación (opcional) */}
            <div className="flex flex-col gap-1.5">
              <div className="flex justify-between items-center">
                <label htmlFor="modal-location" className="text-xs font-semibold text-slate-700">
                  Ubicación <span className="font-normal text-slate-400">(opcional)</span>
                </label>
                <span className="text-[10px] text-slate-400">
                  {location.length}/{MAX_LOCATION_CHARS}
                </span>
              </div>
              <div className="relative">
                <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none">
                  <LogisticsIcon name="location" size={15} />
                </span>
                <input
                  id="modal-location"
                  type="text"
                  maxLength={MAX_LOCATION_CHARS}
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="Ej. Almacén Ate o Av. Central"
                  disabled={isSaving}
                  className="h-11 w-full rounded-xl border border-slate-200 bg-white pl-10 pr-3.5 text-xs text-slate-800 placeholder:text-slate-400 focus:border-[#1F4E6D] focus:outline-none focus:ring-1 focus:ring-[#1F4E6D]"
                />
              </div>
            </div>

            {/* Descripción (opcional) */}
            <div className="flex flex-col gap-1.5">
              <div className="flex justify-between items-center">
                <label htmlFor="modal-description" className="text-xs font-semibold text-slate-700">
                  Descripción <span className="font-normal text-slate-400">(opcional)</span>
                </label>
                <span className="text-[10px] text-slate-400">
                  {description.length}/{MAX_DESCRIPTION_CHARS}
                </span>
              </div>
              <textarea
                id="modal-description"
                rows={3}
                maxLength={MAX_DESCRIPTION_CHARS}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe una incidencia o detalle relevante"
                disabled={isSaving}
                className="w-full rounded-xl border border-slate-200 bg-white p-3 text-xs text-slate-800 placeholder:text-slate-400 focus:border-[#1F4E6D] focus:outline-none focus:ring-1 focus:ring-[#1F4E6D] resize-y min-h-[80px]"
              />
            </div>

            {/* Pie del modal */}
            <div className="flex flex-col-reverse sm:flex-row sm:items-center sm:justify-end gap-2.5 pt-3 border-t border-slate-100 mt-1">
              <Button
                type="button"
                variant="secondary"
                onClick={onClose}
                disabled={isSaving}
                className="w-full sm:w-auto h-10 px-4 text-xs font-medium border-slate-300 bg-white text-slate-700 hover:bg-slate-50"
              >
                Cancelar
              </Button>
              <button
                type="submit"
                disabled={isSaving || !selectedStatus || !allowedNext.includes(selectedStatus)}
                className="w-full sm:w-auto inline-flex h-10 items-center justify-center gap-2 rounded-xl bg-[#1F4E6D] px-4 text-xs font-medium text-white shadow-xs transition-colors hover:bg-[#173E58] disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer border-none"
              >
                {isSaving ? (
                  <>
                    <span
                      className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent"
                      aria-hidden="true"
                    />
                    Guardando...
                  </>
                ) : (
                  <>
                    <LogisticsIcon name="check" size={15} />
                    Confirmar cambio
                  </>
                )}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
