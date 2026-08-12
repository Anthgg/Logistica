import type {
  PackagingControlConfiguration,
  WeightControlConfiguration,
  TemperatureControlConfiguration,
  GenericControlConfiguration,
} from '../types/quality-inspection-plans'

const PACKAGING_CONDITIONS = [
  'Bueno',
  'Aceptable',
  'Dañado',
  'Mojado',
  'Manchado',
  'Deformado',
  'Abierto',
  'Con sellado roto',
  'Sin etiqueta',
  'Con etiqueta dañada',
]

export function PackagingQualityControlForm({
  config,
}: {
  config?: PackagingControlConfiguration
}) {
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-3">
        <label className="flex items-center gap-2 text-xs text-slate-700">
          <input
            type="checkbox"
            checked={config?.check_primary ?? true}
            disabled
            className="h-3.5 w-3.5 rounded border-slate-300 text-[#1F4E6D]"
          />
          Embalaje primario
        </label>
        <label className="flex items-center gap-2 text-xs text-slate-700">
          <input
            type="checkbox"
            checked={config?.check_secondary ?? true}
            disabled
            className="h-3.5 w-3.5 rounded border-slate-300 text-[#1F4E6D]"
          />
          Embalaje secundario
        </label>
        <label className="flex items-center gap-2 text-xs text-slate-700">
          <input
            type="checkbox"
            checked={config?.check_transport ?? true}
            disabled
            className="h-3.5 w-3.5 rounded border-slate-300 text-[#1F4E6D]"
          />
          Embalaje de transporte
        </label>
      </div>
      <div>
        <p className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-slate-500">
          Tipos de embalaje
        </p>
        <div className="flex flex-wrap gap-1">
          {(config?.packaging_types ?? ['Caja', 'Paleta', 'CONTenedor']).map((type) => (
            <span
              key={type}
              className="inline-flex items-center rounded-full border border-slate-200 bg-slate-50 px-2 py-0.5 text-[10px] text-slate-600"
            >
              {type}
            </span>
          ))}
        </div>
      </div>
      <div>
        <p className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-slate-500">
          Condiciones permitidas
        </p>
        <div className="flex flex-wrap gap-1">
          {(config?.allowed_conditions ?? PACKAGING_CONDITIONS).map((cond) => (
            <span
              key={cond}
              className="inline-flex items-center rounded-full border border-emerald-200 bg-emerald-50 px-2 py-0.5 text-[10px] text-emerald-700"
            >
              {cond}
            </span>
          ))}
        </div>
      </div>
      <label className="flex items-center gap-2 text-xs text-slate-700">
        <input
          type="checkbox"
          checked={config?.requires_photography ?? false}
          disabled
          className="h-3.5 w-3.5 rounded border-slate-300 text-[#1F4E6D]"
        />
        Requiere fotografía
      </label>
      {config?.instructions && (
        <div className="rounded-lg bg-slate-50 px-3 py-2 text-[10px] text-slate-600">
          <p className="mb-0.5 font-semibold uppercase text-slate-500">Instrucciones</p>
          <p>{config.instructions}</p>
        </div>
      )}
    </div>
  )
}

export function WeightQualityControlForm({
  config,
}: {
  config?: WeightControlConfiguration
}) {
  return (
    <div className="space-y-3">
      <div>
        <p className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-slate-500">
          Fuente del valor esperado
        </p>
        <span className="inline-flex items-center rounded-full border border-slate-200 bg-slate-50 px-2 py-0.5 text-[10px] text-slate-600">
          {config?.expected_value_source ?? 'PRODUCT'}
        </span>
      </div>
      {config?.fixed_value && (
        <div>
          <p className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-slate-500">
            Valor fijo
          </p>
          <span className="font-mono text-xs text-slate-800">
            {config.fixed_value} {config.unit_id ?? ''}
          </span>
        </div>
      )}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <p className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-slate-500">
            Escala decimal
          </p>
          <span className="font-mono text-xs text-slate-800">
            {config?.decimal_scale ?? 2}
          </span>
        </div>
        <div>
          <p className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-slate-500">
            Tolerancia
          </p>
          <span className="text-xs text-slate-800">
            {config?.tolerance_id ?? '—'}
          </span>
        </div>
      </div>
      <div className="flex flex-wrap gap-3">
        <label className="flex items-center gap-2 text-xs text-slate-700">
          <input
            type="checkbox"
            checked={config?.requires_scale_reference ?? false}
            disabled
            className="h-3.5 w-3.5 rounded border-slate-300 text-[#1F4E6D]"
          />
          Requiere referencia de báscula
        </label>
        <label className="flex items-center gap-2 text-xs text-slate-700">
          <input
            type="checkbox"
            checked={config?.requires_calibration_reference ?? false}
            disabled
            className="h-3.5 w-3.5 rounded border-slate-300 text-[#1F4E6D]"
          />
          Requiere referencia de calibración
        </label>
      </div>
      {config?.instructions && (
        <div className="rounded-lg bg-slate-50 px-3 py-2 text-[10px] text-slate-600">
          <p className="mb-0.5 font-semibold uppercase text-slate-500">Instrucciones</p>
          <p>{config.instructions}</p>
        </div>
      )}
    </div>
  )
}

export function TemperatureQualityControlForm({
  config,
}: {
  config?: TemperatureControlConfiguration
}) {
  return (
    <div className="space-y-3">
      <div>
        <p className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-slate-500">
          Fuente del rango
        </p>
        <span className="inline-flex items-center rounded-full border border-slate-200 bg-slate-50 px-2 py-0.5 text-[10px] text-slate-600">
          {config?.range_source ?? 'PRODUCT'}
        </span>
      </div>
      <div className="grid grid-cols-3 gap-3">
        <div>
          <p className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-slate-500">
            Unidad
          </p>
          <span className="font-mono text-xs text-slate-800">
            {config?.unit === 'F' ? '°F' : '°C'}
          </span>
        </div>
        <div>
          <p className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-slate-500">
            Mínimo
          </p>
          <span className="font-mono text-xs text-slate-800">
            {config?.min_value ?? '—'}{config?.unit === 'F' ? '°F' : '°C'}
          </span>
        </div>
        <div>
          <p className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-slate-500">
            Máximo
          </p>
          <span className="font-mono text-xs text-slate-800">
            {config?.max_value ?? '—'}{config?.unit === 'F' ? '°F' : '°C'}
          </span>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <p className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-slate-500">
            Puntos de medición
          </p>
          <span className="font-mono text-xs text-slate-800">
            {config?.measurement_points ?? 1}
          </span>
        </div>
        <div>
          <p className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-slate-500">
            Tiempo de estabilización
          </p>
          <span className="font-mono text-xs text-slate-800">
            {config?.stabilization_time_seconds != null ? `${config.stabilization_time_seconds}s` : '—'}
          </span>
        </div>
      </div>
      <div className="flex flex-wrap gap-3">
        <label className="flex items-center gap-2 text-xs text-slate-700">
          <input
            type="checkbox"
            checked={config?.requires_device ?? false}
            disabled
            className="h-3.5 w-3.5 rounded border-slate-300 text-[#1F4E6D]"
          />
          Requiere dispositivo de medición
        </label>
        <label className="flex items-center gap-2 text-xs text-slate-700">
          <input
            type="checkbox"
            checked={config?.photograph_on_exception ?? false}
            disabled
            className="h-3.5 w-3.5 rounded border-slate-300 text-[#1F4E6D]"
          />
          Fotografía en excepción
        </label>
      </div>
      {config?.instructions && (
        <div className="rounded-lg bg-slate-50 px-3 py-2 text-[10px] text-slate-600">
          <p className="mb-0.5 font-semibold uppercase text-slate-500">Instrucciones</p>
          <p>{config.instructions}</p>
        </div>
      )}
    </div>
  )
}

export function GenericQualityControlForm({
  config,
}: {
  config?: GenericControlConfiguration
}) {
  return (
    <div className="space-y-3">
      <div className="rounded-lg bg-slate-50 px-3 py-2 text-[10px] text-slate-600">
        <p className="mb-0.5 font-semibold uppercase text-slate-500">Tipo genérico</p>
        <p>Este control no tiene configuración especializada. Defina las instrucciones para el inspector.</p>
      </div>
      {config?.instructions && (
        <div className="rounded-lg bg-slate-50 px-3 py-2 text-[10px] text-slate-600">
          <p className="mb-0.5 font-semibold uppercase text-slate-500">Instrucciones</p>
          <p>{config.instructions}</p>
        </div>
      )}
    </div>
  )
}
