import { formatDateTime } from '../../../utils/date'
import type { ModelStatus } from '../types/continuous-auth'

function availabilityLabel(available: boolean): string {
  return available ? 'Disponible' : 'No disponible'
}

export function ModelStatusCard({ status }: { status: ModelStatus }) {
  const checks = [
    ['Modelo facial', availabilityLabel(status.facial_loaded)],
    ['Modelo PAD', availabilityLabel(status.pad_loaded)],
    ['Fusión', availabilityLabel(status.fusion_loaded)],
    ['Normalización', availabilityLabel(status.normalization_loaded)],
    [
      'Checksums',
      status.checksums_valid ? 'Válidos' : 'Revisión requerida',
    ],
    [
      'Modelos conductuales',
      `${status.behavioral_loaded_count} cargados de ${status.behavioral_available_count} disponibles`,
    ],
    ['Dispositivo', status.device],
    ['Carga', formatDateTime(status.loaded_at)],
  ]

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5">
      <div className="flex flex-col gap-2 border-b border-slate-100 pb-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-wider text-blue-700">
            Registro de modelos
          </p>
          <h2 className="mt-1 text-xl font-bold text-slate-950">
            {status.overall_status}
          </h2>
        </div>
        <span
          className={`inline-flex w-fit rounded-full border px-3 py-1 text-xs font-bold ${
            status.errors.length === 0
              ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
              : 'border-amber-200 bg-amber-50 text-amber-800'
          }`}
        >
          {status.errors.length === 0
            ? 'Sin incidencias reportadas'
            : 'Disponibilidad limitada'}
        </span>
      </div>

      <dl className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {checks.map(([label, value]) => (
          <div
            key={label}
            className="rounded-xl border border-slate-100 bg-slate-50 p-3"
          >
            <dt className="text-xs font-semibold text-slate-500">{label}</dt>
            <dd className="mt-1 text-sm font-medium text-slate-900">
              {value}
            </dd>
          </div>
        ))}
      </dl>

      <div className="mt-5 grid gap-4 lg:grid-cols-2">
        <div>
          <h3 className="text-sm font-bold text-slate-900">Versiones</h3>
          <dl className="mt-2 rounded-xl border border-slate-200 p-3">
            {Object.entries(status.versions).map(([name, version]) => (
              <div
                key={name}
                className="flex justify-between gap-3 py-1 text-xs"
              >
                <dt className="text-slate-600">{name}</dt>
                <dd className="font-mono text-slate-900">{version}</dd>
              </div>
            ))}
          </dl>
        </div>
        <div>
          <h3 className="text-sm font-bold text-slate-900">
            Errores sanitizados
          </h3>
          {status.errors.length === 0 ? (
            <p className="mt-2 rounded-xl border border-slate-200 p-3 text-sm text-slate-600">
              El backend no reporta errores.
            </p>
          ) : (
            <ul className="mt-2 space-y-2">
              {status.errors.map((error) => (
                <li
                  key={error}
                  className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-950"
                >
                  {error}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </section>
  )
}
