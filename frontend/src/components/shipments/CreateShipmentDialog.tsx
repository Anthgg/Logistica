import { useEffect, useRef, type FormEvent } from 'react'
import type { Client, ShipmentCreate, ShipmentPriority } from '../../types/operations'
import { LogisticsIcon } from '../common/LogisticsIcon'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../ui/select'
import { ClientCombobox } from './ClientCombobox'

interface CreateShipmentDialogProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: () => void
  isSubmitting: boolean
  form: ShipmentCreate
  setForm: React.Dispatch<React.SetStateAction<ShipmentCreate>>
  clients: Client[]
}

const priorities: ShipmentPriority[] = ['low', 'normal', 'high', 'urgent']

export function CreateShipmentDialog({
  isOpen,
  onClose,
  onSubmit,
  isSubmitting,
  form,
  setForm,
  clients,
}: CreateShipmentDialogProps) {
  const dialogRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!isOpen) return undefined

    const handleKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && !isSubmitting) onClose()
    }

    document.addEventListener('keydown', handleKey)
    return () => document.removeEventListener('keydown', handleKey)
  }, [isOpen, isSubmitting, onClose])

  if (!isOpen) return null

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (isSubmitting) return
    onSubmit()
  }

  const updateText = (key: keyof ShipmentCreate, value: string) =>
    setForm((curr) => ({ ...curr, [key]: value }))

  const updateNumber = (
    key: 'package_count' | 'total_weight' | 'declared_value',
    value: string
  ) =>
    setForm((curr) => ({
      ...curr,
      [key]: value ? Number(value) : null,
    }))

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-xs animate-in fade-in-0"
      role="presentation"
      onMouseDown={() => !isSubmitting && onClose()}
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="create-shipment-title"
        onMouseDown={(e) => e.stopPropagation()}
        className="flex max-h-[calc(100vh-48px)] w-full max-w-[920px] flex-col overflow-hidden rounded-2xl bg-white shadow-2xl animate-in zoom-in-95"
      >
        {/* Cabecera Fija */}
        <div className="flex items-center justify-between border-b border-slate-200/80 px-6 py-4">
          <div>
            <p className="text-[11px] font-bold tracking-wider text-[#C85A18] uppercase">
              REGISTRO OPERATIVO
            </p>
            <h2 id="create-shipment-title" className="text-lg font-bold text-slate-900">
              Registrar nuevo envío
            </h2>
            <p className="text-xs text-slate-500">
              Completa la información necesaria para generar el despacho.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={isSubmitting}
            aria-label="Cerrar modal"
            className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition-colors disabled:opacity-50"
          >
            <LogisticsIcon name="more" size={16} className="rotate-45" />
          </button>
        </div>

        {/* Contenido Desplazable Organizado por Secciones */}
        <form onSubmit={handleSubmit} className="flex flex-1 flex-col overflow-hidden">
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {/* SECCIÓN 1: Cliente y referencia */}
            <div className="space-y-3.5 rounded-xl border border-slate-200/80 bg-slate-50/50 p-4">
              <div className="flex items-center gap-2 border-b border-slate-200/60 pb-2.5">
                <LogisticsIcon name="user" size={16} className="text-[#1F4E6D]" />
                <h3 className="text-sm font-bold text-slate-800">1. Cliente y referencia</h3>
              </div>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div className="sm:col-span-2">
                  <ClientCombobox
                    clients={clients}
                    value={form.client_id}
                    onChange={(val) => updateText('client_id', val)}
                    required
                  />
                </div>
                <div className="sm:col-span-2 flex flex-col gap-1.5">
                  <label className="text-xs font-semibold text-slate-700">
                    Descripción del envío / paquete <span className="text-rose-500">*</span>
                  </label>
                  <textarea
                    required
                    value={form.package_description}
                    onChange={(e) => updateText('package_description', e.target.value)}
                    placeholder="Detalla el contenido, tipo de mercadería o especificaciones..."
                    className="min-h-[72px] w-full rounded-lg border border-slate-200 bg-white p-2.5 text-xs text-slate-800 placeholder:text-slate-400 focus:border-[#1F4E6D] focus:outline-none"
                  />
                </div>
              </div>
            </div>

            {/* SECCIÓN 2: Ruta del despacho */}
            <div className="space-y-3.5 rounded-xl border border-slate-200/80 bg-slate-50/50 p-4">
              <div className="flex items-center gap-2 border-b border-slate-200/60 pb-2.5">
                <LogisticsIcon name="route" size={16} className="text-[#1F4E6D]" />
                <h3 className="text-sm font-bold text-slate-800">2. Ruta del despacho</h3>
              </div>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                {/* Origen */}
                <div className="space-y-3 rounded-lg border border-blue-100 bg-blue-50/30 p-3">
                  <p className="text-xs font-bold text-blue-900 flex items-center gap-1.5">
                    <span className="h-2 w-2 rounded-full bg-blue-600" />
                    Punto de Origen
                  </p>
                  <div className="space-y-2">
                    <div>
                      <label className="text-xs font-medium text-slate-700">Distrito de origen *</label>
                      <input
                        type="text"
                        required
                        value={form.origin_district}
                        onChange={(e) => updateText('origin_district', e.target.value)}
                        placeholder="Ej. San Isidro"
                        className="h-9 w-full rounded-lg border border-slate-200 bg-white px-3 text-xs text-slate-800 focus:border-[#1F4E6D] focus:outline-none"
                      />
                    </div>
                    <div>
                      <label className="text-xs font-medium text-slate-700">Dirección de origen *</label>
                      <input
                        type="text"
                        required
                        value={form.origin_address}
                        onChange={(e) => updateText('origin_address', e.target.value)}
                        placeholder="Av. Rivera Navarrete 456"
                        className="h-9 w-full rounded-lg border border-slate-200 bg-white px-3 text-xs text-slate-800 focus:border-[#1F4E6D] focus:outline-none"
                      />
                    </div>
                  </div>
                </div>

                {/* Destino */}
                <div className="space-y-3 rounded-lg border border-amber-100 bg-amber-50/30 p-3">
                  <p className="text-xs font-bold text-amber-900 flex items-center gap-1.5">
                    <span className="h-2 w-2 rounded-full bg-amber-600" />
                    Punto de Destino
                  </p>
                  <div className="space-y-2">
                    <div>
                      <label className="text-xs font-medium text-slate-700">Distrito de destino *</label>
                      <input
                        type="text"
                        required
                        value={form.destination_district}
                        onChange={(e) => updateText('destination_district', e.target.value)}
                        placeholder="Ej. Ate"
                        className="h-9 w-full rounded-lg border border-slate-200 bg-white px-3 text-xs text-slate-800 focus:border-[#1F4E6D] focus:outline-none"
                      />
                    </div>
                    <div>
                      <label className="text-xs font-medium text-slate-700">Dirección de destino *</label>
                      <input
                        type="text"
                        required
                        value={form.destination_address}
                        onChange={(e) => updateText('destination_address', e.target.value)}
                        placeholder="Av. Separadora Industrial 1230"
                        className="h-9 w-full rounded-lg border border-slate-200 bg-white px-3 text-xs text-slate-800 focus:border-[#1F4E6D] focus:outline-none"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* SECCIÓN 3: Características de la carga */}
            <div className="space-y-3.5 rounded-xl border border-slate-200/80 bg-slate-50/50 p-4">
              <div className="flex items-center gap-2 border-b border-slate-200/60 pb-2.5">
                <LogisticsIcon name="box" size={16} className="text-[#1F4E6D]" />
                <h3 className="text-sm font-bold text-slate-800">3. Características de la carga</h3>
              </div>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
                <div>
                  <label className="text-xs font-medium text-slate-700">Bultos *</label>
                  <input
                    type="number"
                    min="1"
                    required
                    value={form.package_count}
                    onChange={(e) => updateNumber('package_count', e.target.value)}
                    className="h-9 w-full rounded-lg border border-slate-200 bg-white px-3 text-xs text-slate-800 focus:border-[#1F4E6D] focus:outline-none"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-700">Peso total (kg) *</label>
                  <input
                    type="number"
                    min="0.01"
                    step="0.01"
                    required
                    value={form.total_weight}
                    onChange={(e) => updateNumber('total_weight', e.target.value)}
                    className="h-9 w-full rounded-lg border border-slate-200 bg-white px-3 text-xs text-slate-800 focus:border-[#1F4E6D] focus:outline-none"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-700">Valor declarado (S/)</label>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    value={form.declared_value ?? ''}
                    onChange={(e) => updateNumber('declared_value', e.target.value)}
                    placeholder="0.00"
                    className="h-9 w-full rounded-lg border border-slate-200 bg-white px-3 text-xs text-slate-800 focus:border-[#1F4E6D] focus:outline-none"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-700">Prioridad *</label>
                  <Select
                    value={form.priority}
                    onValueChange={(val) => updateText('priority', val)}
                  >
                    <SelectTrigger className="h-9 text-xs">
                      <SelectValue placeholder="Prioridad" />
                    </SelectTrigger>
                    <SelectContent>
                      {priorities.map((p) => (
                        <SelectItem key={p} value={p}>
                          {p === 'urgent' ? 'Urgente' : p === 'high' ? 'Alta' : p === 'normal' ? 'Normal' : 'Baja'}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>

            {/* SECCIÓN 4: Información adicional */}
            <div className="space-y-3.5 rounded-xl border border-slate-200/80 bg-slate-50/50 p-4">
              <div className="flex items-center gap-2 border-b border-slate-200/60 pb-2.5">
                <LogisticsIcon name="calendar" size={16} className="text-[#1F4E6D]" />
                <h3 className="text-sm font-bold text-slate-800">4. Planificación</h3>
              </div>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <label className="text-xs font-medium text-slate-700">Fecha y hora estimada de entrega</label>
                  <input
                    type="datetime-local"
                    value={form.expected_delivery_at ?? ''}
                    onChange={(e) => updateText('expected_delivery_at', e.target.value)}
                    className="h-9 w-full rounded-lg border border-slate-200 bg-white px-3 text-xs text-slate-800 focus:border-[#1F4E6D] focus:outline-none"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Pie Fijo */}
          <div className="flex items-center justify-between border-t border-slate-200/80 bg-slate-50 px-6 py-3.5">
            <span className="text-xs text-slate-500 font-medium">
              Los campos marcados con <span className="text-rose-500">*</span> son obligatorios
            </span>
            <div className="flex items-center gap-2.5">
              <button
                type="button"
                onClick={onClose}
                disabled={isSubmitting}
                className="h-10 px-4 rounded-lg border border-slate-200 bg-white text-xs font-semibold text-slate-700 shadow-2xs hover:bg-slate-100 transition-colors disabled:opacity-50"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={isSubmitting || !form.client_id}
                className="inline-flex h-10 items-center justify-center gap-2 rounded-lg bg-[#1F4E6D] px-5 text-xs font-semibold text-white shadow-2xs hover:bg-[#173F5F] transition-colors disabled:opacity-50"
              >
                {isSubmitting ? (
                  <>
                    <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent" />
                    <span>Registrando...</span>
                  </>
                ) : (
                  <span>Registrar envío</span>
                )}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  )
}
