import { useEffect, useState } from 'react'
import { vehiclesApi } from '../../api/vehicles-api'
import { Button } from '../common/Button'
import type {
  VehicleBodyType,
  VehicleCreate,
  VehicleFuelType,
  VehicleMake,
  VehicleModel,
  VehicleTransmissionType,
  VehicleType,
} from '../../types/vehicles'

interface Props {
  onSubmit: (data: VehicleCreate) => void
  isSubmitting?: boolean
  initialValues?: Partial<VehicleCreate>
  onCancel?: () => void
}

const VEHICLE_TYPES: { value: VehicleType; label: string }[] = [
  { value: 'TRUCK', label: 'Camión Rígido' },
  { value: 'TRACTOR', label: 'Tractocamión / CISTERNA' },
  { value: 'TRAILER', label: 'Remolque / Semirremolque' },
  { value: 'VAN', label: 'Furgoneta / Van' },
  { value: 'PICKUP', label: 'Camioneta Pickup' },
  { value: 'REFRIGERATED', label: 'Camión Frigorífico' },
  { value: 'CONTAINER_CHASSIS', label: 'Chasis Portacontenedor' },
  { value: 'OTHER', label: 'Otro' },
]

const BODY_TYPES: { value: VehicleBodyType; label: string }[] = [
  { value: 'CLOSED', label: 'Furgón Cerrado' },
  { value: 'OPEN', label: 'Baranda / Plataforma Abierta' },
  { value: 'REFRIGERATED', label: 'Cámara Frigorífica' },
  { value: 'TANK', label: 'Tanque / Cisterna' },
  { value: 'FLATBED', label: 'Plataforma Plana' },
  { value: 'SIDE_CURTAIN', label: 'Sider / Cortina Lateral' },
  { value: 'CONTAINER_CARRIER', label: 'Portacontenedor' },
  { value: 'OTHER', label: 'Otro' },
]

export function VehicleGeneralForm({
  onSubmit,
  isSubmitting = false,
  initialValues,
  onCancel,
}: Props) {
  const [internalCode, setInternalCode] = useState(initialValues?.internal_code || '')
  const [plateNumber, setPlateNumber] = useState(initialValues?.plate_number || '')
  const [country, setCountry] = useState(initialValues?.country_of_registration || 'PE')
  const [vin, setVin] = useState(initialValues?.vin || '')
  const [chassisNumber] = useState(initialValues?.chassis_number || '')
  const [engineNumber] = useState(initialValues?.engine_number || '')
  const [makeId, setMakeId] = useState(initialValues?.make_id || '')
  const [modelId, setModelId] = useState(initialValues?.model_id || '')
  const [year, setYear] = useState<number>(initialValues?.year_of_manufacture || new Date().getFullYear())
  const [modelYear] = useState<number | undefined>(initialValues?.model_year)
  const [vehicleType, setVehicleType] = useState<VehicleType>(initialValues?.vehicle_type || 'TRUCK')
  const [bodyType, setBodyType] = useState<VehicleBodyType>(initialValues?.body_type || 'CLOSED')
  const [fuelType, setFuelType] = useState<VehicleFuelType>(initialValues?.fuel_type || 'DIESEL')
  const [transmissionType] = useState<VehicleTransmissionType | undefined>(initialValues?.transmission_type)
  const [axlesCount] = useState<number>(initialValues?.axles_count || 2)
  const [color] = useState(initialValues?.color || '')
  const [notes] = useState(initialValues?.notes || '')

  const [makes, setMakes] = useState<VehicleMake[]>([])
  const [models, setModels] = useState<VehicleModel[]>([])
  const [loadingCatalog, setLoadingCatalog] = useState(false)

  // Load makes
  useEffect(() => {
    setLoadingCatalog(true)
    vehiclesApi.listMakes()
      .then(setMakes)
      .catch(() => setMakes([]))
      .finally(() => setLoadingCatalog(false))
  }, [])

  // Load models for selected make
  useEffect(() => {
    if (!makeId) {
      setModels([])
      setModelId('')
      return
    }
    vehiclesApi.listModels(makeId)
      .then(setModels)
      .catch(() => setModels([]))
  }, [makeId])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!plateNumber.trim() || !makeId || !modelId || isSubmitting) return

    onSubmit({
      internal_code: internalCode.trim() || undefined,
      plate_number: plateNumber.trim().toUpperCase(), // strictly string
      country_of_registration: country,
      vin: vin.trim() || undefined,
      chassis_number: chassisNumber.trim() || undefined,
      engine_number: engineNumber.trim() || undefined,
      make_id: makeId,
      model_id: modelId,
      year_of_manufacture: year,
      model_year: modelYear,
      vehicle_type: vehicleType,
      body_type: bodyType,
      fuel_type: fuelType,
      transmission_type: transmissionType,
      axles_count: axlesCount,
      color: color.trim() || undefined,
      notes: notes.trim() || undefined,
    })
  }

  const cleanPlate = plateNumber.replace(/[^a-zA-Z0-9-]/g, '').toUpperCase()

  return (
    <form onSubmit={handleSubmit} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-6 text-xs">
      <div className="border-b border-slate-100 pb-3">
        <h3 className="text-sm font-bold text-slate-800">Ficha General del Vehículo</h3>
        <p className="text-slate-500 mt-0.5">
          Ficha física y registral básica. La vigencia documental se evaluará independientemente.
        </p>
      </div>

      {/* Identification section */}
      <section className="space-y-3">
        <h4 className="font-bold uppercase tracking-wider text-slate-500 text-[11px]">Identificación Físico-Registral</h4>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <div>
            <label className="mb-1 block font-bold text-slate-700">Placa de Rodaje *</label>
            <input
              type="text"
              value={cleanPlate}
              onChange={(e) => setPlateNumber(e.target.value)}
              placeholder="Ej. ABC-123"
              required
              className="w-full font-mono text-sm font-bold rounded-lg border border-slate-300 px-3 py-2 text-slate-800 uppercase focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
            />
            <p className="mt-1 text-[10px] text-slate-400">
              Formato validado. La propiedad y vigencia registral se comprobarán en la Fase 028.
            </p>
          </div>

          <div>
            <label className="mb-1 block font-bold text-slate-700">Código Interno</label>
            <input
              type="text"
              value={internalCode}
              onChange={(e) => setInternalCode(e.target.value)}
              placeholder="Ej. VEH-042"
              className="w-full font-mono rounded-lg border border-slate-300 px-3 py-2"
            />
          </div>

          <div>
            <label className="mb-1 block font-bold text-slate-700">País de Registro</label>
            <input
              type="text"
              value={country}
              onChange={(e) => setCountry(e.target.value.toUpperCase())}
              placeholder="PE"
              className="w-full font-mono uppercase rounded-lg border border-slate-300 px-3 py-2"
            />
          </div>

          <div className="col-span-1 sm:col-span-3">
            <label className="mb-1 block font-bold text-slate-700">VIN (Nº Identificación Vehicular)</label>
            <input
              type="text"
              value={vin}
              onChange={(e) => setVin(e.target.value.toUpperCase())}
              placeholder="Ej. 9BWCA1110FP000000"
              maxLength={17}
              className="w-full font-mono uppercase rounded-lg border border-slate-300 px-3 py-2"
            />
          </div>
        </div>
      </section>

      {/* Make & Model */}
      <section className="space-y-3">
        <h4 className="font-bold uppercase tracking-wider text-slate-500 text-[11px]">Marca, Modelo y Fabricación</h4>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <div>
            <label className="mb-1 block font-bold text-slate-700">Marca *</label>
            <select
              value={makeId}
              onChange={(e) => setMakeId(e.target.value)}
              required
              disabled={loadingCatalog}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 bg-white"
            >
              <option value="">Seleccionar marca...</option>
              {makes.map((m) => (
                <option key={m.id} value={m.id}>{m.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-1 block font-bold text-slate-700">Modelo *</label>
            <select
              value={modelId}
              onChange={(e) => setModelId(e.target.value)}
              required
              disabled={!makeId || models.length === 0}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 bg-white"
            >
              <option value="">Seleccionar modelo...</option>
              {models.map((m) => (
                <option key={m.id} value={m.id}>{m.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-1 block font-bold text-slate-700">Año de Fabricación *</label>
            <input
              type="number"
              value={year}
              onChange={(e) => setYear(parseInt(e.target.value, 10) || new Date().getFullYear())}
              min={1950}
              max={new Date().getFullYear() + 2}
              required
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
            />
          </div>
        </div>
      </section>

      {/* Vehicle Type & Body */}
      <section className="space-y-3">
        <h4 className="font-bold uppercase tracking-wider text-slate-500 text-[11px]">Tipo Vehicular y Carrocería</h4>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <div>
            <label className="mb-1 block font-bold text-slate-700">Tipo Vehicular *</label>
            <select
              value={vehicleType}
              onChange={(e) => setVehicleType(e.target.value as VehicleType)}
              required
              className="w-full rounded-lg border border-slate-300 px-3 py-2 bg-white"
            >
              {VEHICLE_TYPES.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-1 block font-bold text-slate-700">Carrocería *</label>
            <select
              value={bodyType}
              onChange={(e) => setBodyType(e.target.value as VehicleBodyType)}
              required
              className="w-full rounded-lg border border-slate-300 px-3 py-2 bg-white"
            >
              {BODY_TYPES.map((b) => (
                <option key={b.value} value={b.value}>{b.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-1 block font-bold text-slate-700">Combustible</label>
            <select
              value={fuelType}
              onChange={(e) => setFuelType(e.target.value as VehicleFuelType)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 bg-white"
            >
              <option value="DIESEL">Diésel</option>
              <option value="GASOLINE">Gasolina</option>
              <option value="GLP">GLP</option>
              <option value="GNV">GNV</option>
              <option value="ELECTRIC">Eléctrico</option>
              <option value="HYBRID">Híbrido</option>
            </select>
          </div>
        </div>
      </section>

      <div className="flex justify-end gap-2 border-t border-slate-100 pt-4">
        {onCancel && (
          <Button type="button" variant="secondary" onClick={onCancel} disabled={isSubmitting}>
            Cancelar
          </Button>
        )}
        <Button type="submit" isLoading={isSubmitting} loadingLabel="Guardando...">
          Guardar Vehículo
        </Button>
      </div>
    </form>
  )
}
