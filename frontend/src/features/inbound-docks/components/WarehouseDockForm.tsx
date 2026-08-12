import { useState } from 'react'
import { Button } from '../../../components/common/Button'
import { SectionPanel } from './ui/Primitives'
import type { DockDirection, DockType, WarehouseDock, WarehouseDockCreate, WarehouseDockUpdate } from '../types/inbound-docks'

export function WarehouseDockForm({
  initial,
  warehouses,
  onSubmit,
  onCancel,
  isSubmitting,
  errorMessage,
  title = 'Muelle',
}: {
  initial?: WarehouseDock | null
  warehouses: Array<{ id: string; label: string }>
  onSubmit: (input: WarehouseDockCreate | WarehouseDockUpdate) => void
  onCancel: () => void
  isSubmitting?: boolean
  errorMessage?: string | null
  title?: string
}) {
  const [code, setCode] = useState(initial?.code ?? '')
  const [name, setName] = useState(initial?.name ?? '')
  const [warehouseId, setWarehouseId] = useState(initial?.warehouse_id ?? warehouses[0]?.id ?? '')
  const [type, setType] = useState<DockType>(initial?.type ?? 'STANDARD')
  const [direction, setDirection] = useState<DockDirection>(initial?.direction ?? 'INBOUND')
  const [address, setAddress] = useState(initial?.address ?? '')
  const [zone, setZone] = useState(initial?.zone ?? '')
  const [timezone, setTimezone] = useState(initial?.timezone ?? 'America/Lima')
  const [maxLength, setMaxLength] = useState(initial?.capabilities?.max_length_m ?? '')
  const [maxHeight, setMaxHeight] = useState(initial?.capabilities?.max_height_m ?? '')
  const [maxWeight, setMaxWeight] = useState(initial?.capabilities?.max_weight_kg ?? '')
  const [refrigerated, setRefrigerated] = useState(initial?.capabilities?.refrigerated ?? false)
  const [hazmat, setHazmat] = useState(initial?.capabilities?.hazmat ?? false)
  const [oversized, setOversized] = useState(initial?.capabilities?.oversized ?? false)
  const [driveThrough, setDriveThrough] = useState(initial?.capabilities?.drive_through ?? false)
  const [covered, setCovered] = useState(initial?.capabilities?.covered ?? false)
  const [equipment, setEquipment] = useState((initial?.capabilities?.equipment ?? []).join(','))
  const [specialRequirements, setSpecialRequirements] = useState((initial?.capabilities?.special_requirements ?? []).join(','))
  const [vehicleTypes, setVehicleTypes] = useState((initial?.capabilities?.max_vehicle_types ?? []).join(','))
  const [notes, setNotes] = useState(initial?.notes ?? '')
  const submit = () => {
    if (initial) {
      onSubmit({
        name,
        address: address || null,
        zone: zone || null,
        timezone,
        notes: notes || null,
        capabilities: {
          refrigerated,
          hazmat,
          oversized,
          drive_through: driveThrough,
          covered,
          max_vehicle_types: vehicleTypes.split(',').map((v) => v.trim()).filter(Boolean),
          max_length_m: maxLength || null,
          max_height_m: maxHeight || null,
          max_weight_kg: maxWeight || null,
          equipment: equipment.split(',').map((v) => v.trim()).filter(Boolean),
          special_requirements: specialRequirements.split(',').map((v) => v.trim()).filter(Boolean),
        },
      })
    } else {
      onSubmit({
        code,
        name,
        warehouse_id: warehouseId,
        type,
        direction,
        address: address || null,
        zone: zone || null,
        timezone,
        notes: notes || null,
        capabilities: {
          refrigerated,
          hazmat,
          oversized,
          drive_through: driveThrough,
          covered,
          max_vehicle_types: vehicleTypes.split(',').map((v) => v.trim()).filter(Boolean),
          max_length_m: maxLength || null,
          max_height_m: maxHeight || null,
          max_weight_kg: maxWeight || null,
          equipment: equipment.split(',').map((v) => v.trim()).filter(Boolean),
          special_requirements: specialRequirements.split(',').map((v) => v.trim()).filter(Boolean),
        },
      })
    }
  }
  return (
    <SectionPanel title={title} description="Datos generales y capacidades. Las medidas se envían como string.">
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        {!initial && (
          <>
            <div>
              <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="dock-form-code">Código</label>
              <input
                id="dock-form-code"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
                value={code}
                onChange={(event) => setCode(event.target.value)}
                required
              />
            </div>
            <div>
              <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="dock-form-warehouse">Almacén</label>
              <select
                id="dock-form-warehouse"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
                value={warehouseId}
                onChange={(event) => setWarehouseId(event.target.value)}
              >
                {warehouses.map((w) => (
                  <option key={w.id} value={w.id}>{w.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="dock-form-type">Tipo</label>
              <select
                id="dock-form-type"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
                value={type}
                onChange={(event) => setType(event.target.value as DockType)}
              >
                <option value="STANDARD">Estándar</option>
                <option value="REFRIGERATED">Refrigerado</option>
                <option value="HAZMAT">Materiales peligrosos</option>
                <option value="OVERSIZED">Sobredimensionado</option>
                <option value="DRIVE_THROUGH">Pasante</option>
                <option value="COVERED">Cubierto</option>
                <option value="OUTDOOR">Exterior</option>
              </select>
            </div>
            <div>
              <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="dock-form-direction">Dirección</label>
              <select
                id="dock-form-direction"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
                value={direction}
                onChange={(event) => setDirection(event.target.value as DockDirection)}
              >
                <option value="INBOUND">Entrada</option>
                <option value="OUTBOUND">Salida</option>
                <option value="BIDIRECTIONAL">Bidireccional</option>
              </select>
            </div>
          </>
        )}
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="dock-form-name">Nombre</label>
          <input
            id="dock-form-name"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            value={name}
            onChange={(event) => setName(event.target.value)}
            required
          />
        </div>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="dock-form-timezone">Zona horaria</label>
          <input
            id="dock-form-timezone"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            value={timezone}
            onChange={(event) => setTimezone(event.target.value)}
          />
        </div>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="dock-form-address">Dirección física</label>
          <input
            id="dock-form-address"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            value={address}
            onChange={(event) => setAddress(event.target.value)}
          />
        </div>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="dock-form-zone">Zona</label>
          <input
            id="dock-form-zone"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            value={zone}
            onChange={(event) => setZone(event.target.value)}
          />
        </div>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="dock-form-length">Longitud máxima (m, string)</label>
          <input
            id="dock-form-length"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            value={maxLength}
            onChange={(event) => setMaxLength(event.target.value)}
            placeholder="ej. 12.50"
          />
        </div>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="dock-form-height">Altura máxima (m, string)</label>
          <input
            id="dock-form-height"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            value={maxHeight}
            onChange={(event) => setMaxHeight(event.target.value)}
          />
        </div>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="dock-form-weight">Peso máximo (kg, string)</label>
          <input
            id="dock-form-weight"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            value={maxWeight}
            onChange={(event) => setMaxWeight(event.target.value)}
          />
        </div>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="dock-form-vehicles">Tipos de vehículo (coma)</label>
          <input
            id="dock-form-vehicles"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            value={vehicleTypes}
            onChange={(event) => setVehicleTypes(event.target.value)}
          />
        </div>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="dock-form-equipment">Equipamiento (coma)</label>
          <input
            id="dock-form-equipment"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            value={equipment}
            onChange={(event) => setEquipment(event.target.value)}
          />
        </div>
        <div>
          <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="dock-form-req">Requisitos especiales (coma)</label>
          <input
            id="dock-form-req"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
            value={specialRequirements}
            onChange={(event) => setSpecialRequirements(event.target.value)}
          />
        </div>
      </div>
      <fieldset className="mt-3">
        <legend className="mb-1 text-[11px] font-semibold uppercase text-slate-500">Capacidades</legend>
        <div className="grid grid-cols-2 gap-2 md:grid-cols-3">
          <label className="flex items-center gap-2 text-xs text-slate-700">
            <input
              type="checkbox"
              className="h-3.5 w-3.5"
              checked={refrigerated}
              onChange={(event) => setRefrigerated(event.target.checked)}
            />
            Refrigerado
          </label>
          <label className="flex items-center gap-2 text-xs text-slate-700">
            <input
              type="checkbox"
              className="h-3.5 w-3.5"
              checked={hazmat}
              onChange={(event) => setHazmat(event.target.checked)}
            />
            Materiales peligrosos
          </label>
          <label className="flex items-center gap-2 text-xs text-slate-700">
            <input
              type="checkbox"
              className="h-3.5 w-3.5"
              checked={oversized}
              onChange={(event) => setOversized(event.target.checked)}
            />
            Sobredimensionado
          </label>
          <label className="flex items-center gap-2 text-xs text-slate-700">
            <input
              type="checkbox"
              className="h-3.5 w-3.5"
              checked={driveThrough}
              onChange={(event) => setDriveThrough(event.target.checked)}
            />
            Pasante
          </label>
          <label className="flex items-center gap-2 text-xs text-slate-700">
            <input
              type="checkbox"
              className="h-3.5 w-3.5"
              checked={covered}
              onChange={(event) => setCovered(event.target.checked)}
            />
            Cubierto
          </label>
        </div>
      </fieldset>
      <div className="mt-3">
        <label className="mb-1 block text-[11px] font-semibold text-slate-600" htmlFor="dock-form-notes">Observaciones</label>
        <textarea
          id="dock-form-notes"
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs focus:border-[#1F4E6D] focus:outline-none focus:ring-2 focus:ring-[#1F4E6D]/30"
          rows={2}
          value={notes}
          onChange={(event) => setNotes(event.target.value)}
        />
      </div>
      {errorMessage && <p className="mt-2 rounded-lg border border-rose-200 bg-rose-50/40 p-2 text-rose-700" role="alert">{errorMessage}</p>}
      <div className="mt-3 flex justify-end gap-2">
        <Button type="button" variant="secondary" onClick={onCancel} disabled={isSubmitting}>
          Cancelar
        </Button>
        <Button type="button" variant="primary" onClick={submit} disabled={isSubmitting} isLoading={isSubmitting}>
          Guardar
        </Button>
      </div>
    </SectionPanel>
  )
}
