import { useState } from 'react'
import { vehiclesApi } from '../../api/vehicles-api'
import { Button } from '../common/Button'
import { LogisticsIcon } from '../common/LogisticsIcon'
import type { VehicleCapacityProfile, VehicleCapacityProfileCreate } from '../../types/vehicles'

interface PanelProps {
  vehicleId: string
  profiles: VehicleCapacityProfile[]
  onProfileCreated?: () => void
  canManageCapacity?: boolean
}

export function VehicleCapacityPanel({
  vehicleId,
  profiles,
  onProfileCreated,
  canManageCapacity = true,
}: PanelProps) {
  const [showForm, setShowForm] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const activeProfile = profiles.find((p) => p.is_active) || profiles[0]

  const handleCreateProfile = async (data: VehicleCapacityProfileCreate) => {
    setSubmitting(true)
    try {
      await vehiclesApi.createCapacityProfile(vehicleId, data)
      setShowForm(false)
      if (onProfileCreated) onProfileCreated()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Error al registrar perfil de capacidad')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="space-y-6 text-xs">
      {/* Notice */}
      <div className="rounded-xl border border-blue-200 bg-blue-50/60 p-3.5 text-blue-900">
        <span className="flex items-start gap-1.5"><LogisticsIcon name="info" size={14} aria-hidden /> <span><strong>Nota sobre capacidad:</strong> Esta capacidad describe las especificaciones físicas del vehículo. No representa carga disponible en tiempo real ni reserva espacio de almacén.</span></span>
      </div>

      {activeProfile ? (
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <span className="font-bold uppercase tracking-wider text-slate-400 text-[10px]">
                Perfil de Capacidad Activo
              </span>
              <h3 className="text-sm font-bold text-slate-800">Versión v{activeProfile.version}</h3>
            </div>
            {canManageCapacity && (
              <Button size="small" variant="secondary" onClick={() => setShowForm(!showForm)}>
                {showForm ? 'Ocultar Formulario' : '+ Nuevo Perfil de Capacidad'}
              </Button>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <div className="rounded-xl border border-slate-100 bg-slate-50 p-3">
              <span className="font-bold uppercase tracking-wider text-slate-400 text-[10px] block mb-1">
                Peso Bruto Vehicular
              </span>
              <span className="font-mono text-base font-bold text-slate-800">
                {activeProfile.gross_weight} {activeProfile.gross_weight_unit_code}
              </span>
            </div>

            <div className="rounded-xl border border-slate-100 bg-slate-50 p-3">
              <span className="font-bold uppercase tracking-wider text-slate-400 text-[10px] block mb-1">
                Tara (Peso Vacío)
              </span>
              <span className="font-mono text-base font-bold text-slate-800">
                {activeProfile.tare_weight} {activeProfile.tare_weight_unit_code}
              </span>
            </div>

            <div className="rounded-xl border border-slate-100 bg-slate-50 p-3">
              <span className="font-bold uppercase tracking-wider text-slate-400 text-[10px] block mb-1">
                Carga Útil Máxima
              </span>
              <span className="font-mono text-base font-bold text-indigo-700">
                {activeProfile.payload_capacity} {activeProfile.payload_capacity_unit_code}
              </span>
            </div>

            <div className="rounded-xl border border-slate-100 bg-slate-50 p-3">
              <span className="font-bold uppercase tracking-wider text-slate-400 text-[10px] block mb-1">
                Volumen Útil
              </span>
              <span className="font-mono text-base font-bold text-indigo-700">
                {activeProfile.volume_capacity} {activeProfile.volume_capacity_unit_code}
              </span>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4 pt-2 border-t border-slate-100 text-slate-600">
            <div>
              <span className="font-bold uppercase text-[10px] text-slate-400 block">Posiciones Pallet:</span>
              <span className="font-mono font-bold text-slate-800">{activeProfile.pallet_positions || 'N/A'}</span>
            </div>
            <div>
              <span className="font-bold uppercase text-[10px] text-slate-400 block">Unidades Máximas:</span>
              <span className="font-mono font-bold text-slate-800">{activeProfile.max_units || 'N/A'}</span>
            </div>
            <div>
              <span className="font-bold uppercase text-[10px] text-slate-400 block">Número de Ejes:</span>
              <span className="font-mono font-bold text-slate-800">{activeProfile.axles_count || 'N/A'}</span>
            </div>
          </div>
        </div>
      ) : (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center space-y-3">
          <p className="text-slate-500 font-medium">No se ha registrado perfil de capacidad para este vehículo.</p>
          {canManageCapacity && (
            <Button onClick={() => setShowForm(true)}>+ Registrar Perfil de Capacidad</Button>
          )}
        </div>
      )}

      {showForm && (
        <VehicleCapacityProfileForm
          onSubmit={handleCreateProfile}
          isSubmitting={submitting}
          onCancel={() => setShowForm(false)}
        />
      )}
    </div>
  )
}

interface FormProps {
  onSubmit: (data: VehicleCapacityProfileCreate) => void
  isSubmitting?: boolean
  onCancel?: () => void
}

export function VehicleCapacityProfileForm({
  onSubmit,
  isSubmitting = false,
  onCancel,
}: FormProps) {
  const [grossWeight, setGrossWeight] = useState('18000')
  const [grossUnit, setGrossUnit] = useState('KG')
  const [tareWeight, setTareWeight] = useState('6000')
  const [tareUnit, setTareUnit] = useState('KG')
  const [payload, setPayload] = useState('12000')
  const [payloadUnit, setPayloadUnit] = useState('KG')
  const [volume, setVolume] = useState('45.0')
  const [volumeUnit, setVolumeUnit] = useState('M3')
  const [pallets, setPallets] = useState(14)
  const [maxUnits] = useState(1000)
  const [axles] = useState(2)
  const [reference, setReference] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!grossWeight || !payload || !volume || isSubmitting) return

    onSubmit({
      gross_weight: grossWeight.trim(), // string
      gross_weight_unit_id: grossUnit,
      tare_weight: tareWeight.trim(),
      tare_weight_unit_id: tareUnit,
      payload_capacity: payload.trim(),
      payload_capacity_unit_id: payloadUnit,
      volume_capacity: volume.trim(),
      volume_capacity_unit_id: volumeUnit,
      pallet_positions: pallets,
      max_units: maxUnits,
      axles_count: axles,
      source_reference: reference.trim() || undefined,
    })
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-4 text-xs">
      <h3 className="text-sm font-bold text-slate-800 border-b border-slate-100 pb-2">
        Registrar Perfil de Capacidad
      </h3>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div>
          <label className="mb-1 block font-bold text-slate-700">Peso Bruto Vehicular *</label>
          <div className="flex gap-2">
            <input
              type="text"
              inputMode="decimal"
              value={grossWeight}
              onChange={(e) => setGrossWeight(e.target.value)}
              required
              className="flex-1 font-mono rounded-lg border border-slate-300 px-3 py-2"
            />
            <select
              value={grossUnit}
              onChange={(e) => setGrossUnit(e.target.value)}
              className="rounded-lg border border-slate-300 px-2 py-2 bg-white font-mono"
            >
              <option value="KG">KG</option>
              <option value="TN">TN</option>
            </select>
          </div>
        </div>

        <div>
          <label className="mb-1 block font-bold text-slate-700">Tara (Peso Vacío) *</label>
          <div className="flex gap-2">
            <input
              type="text"
              inputMode="decimal"
              value={tareWeight}
              onChange={(e) => setTareWeight(e.target.value)}
              required
              className="flex-1 font-mono rounded-lg border border-slate-300 px-3 py-2"
            />
            <select
              value={tareUnit}
              onChange={(e) => setTareUnit(e.target.value)}
              className="rounded-lg border border-slate-300 px-2 py-2 bg-white font-mono"
            >
              <option value="KG">KG</option>
              <option value="TN">TN</option>
            </select>
          </div>
        </div>

        <div>
          <label className="mb-1 block font-bold text-slate-700">Carga Útil Máxima *</label>
          <div className="flex gap-2">
            <input
              type="text"
              inputMode="decimal"
              value={payload}
              onChange={(e) => setPayload(e.target.value)}
              required
              className="flex-1 font-mono rounded-lg border border-slate-300 px-3 py-2 text-indigo-700 font-bold"
            />
            <select
              value={payloadUnit}
              onChange={(e) => setPayloadUnit(e.target.value)}
              className="rounded-lg border border-slate-300 px-2 py-2 bg-white font-mono"
            >
              <option value="KG">KG</option>
              <option value="TN">TN</option>
            </select>
          </div>
        </div>

        <div>
          <label className="mb-1 block font-bold text-slate-700">Volumen Útil Máximo *</label>
          <div className="flex gap-2">
            <input
              type="text"
              inputMode="decimal"
              value={volume}
              onChange={(e) => setVolume(e.target.value)}
              required
              className="flex-1 font-mono rounded-lg border border-slate-300 px-3 py-2 text-indigo-700 font-bold"
            />
            <select
              value={volumeUnit}
              onChange={(e) => setVolumeUnit(e.target.value)}
              className="rounded-lg border border-slate-300 px-2 py-2 bg-white font-mono"
            >
              <option value="M3">M³</option>
              <option value="L">L</option>
            </select>
          </div>
        </div>

        <div>
          <label className="mb-1 block font-bold text-slate-700">Posiciones de Pallet</label>
          <input
            type="number"
            value={pallets}
            onChange={(e) => setPallets(parseInt(e.target.value, 10) || 0)}
            min={0}
            className="w-full font-mono rounded-lg border border-slate-300 px-3 py-2"
          />
        </div>

        <div>
          <label className="mb-1 block font-bold text-slate-700">Referencia Técnica / Manual</label>
          <input
            type="text"
            value={reference}
            onChange={(e) => setReference(e.target.value)}
            placeholder="Ej. Ficha de homologación MTC / Fabricante"
            className="w-full rounded-lg border border-slate-300 px-3 py-2"
          />
        </div>
      </div>

      <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
        {onCancel && (
          <Button type="button" variant="secondary" onClick={onCancel} disabled={isSubmitting}>
            Cancelar
          </Button>
        )}
        <Button type="submit" isLoading={isSubmitting} loadingLabel="Guardando...">
          Guardar Perfil
        </Button>
      </div>
    </form>
  )
}
