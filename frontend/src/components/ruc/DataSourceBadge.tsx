import type { RucSourceType } from '../../types/ruc-integration'

interface Props {
  source: RucSourceType
  label?: string
  size?: 'sm' | 'md'
}

const SOURCE_CONFIG: Record<RucSourceType, { label: string; className: string }> = {
  OFFICIAL_PADRON: {
    label: 'Padrón reducido oficial',
    className: 'bg-emerald-100 text-emerald-800 border-emerald-300',
  },
  ANNEX_PADRON: {
    label: 'Padrón de locales anexos',
    className: 'bg-teal-100 text-teal-800 border-teal-300',
  },
  AUTHORIZED_PROVIDER: {
    label: 'Proveedor autorizado',
    className: 'bg-blue-100 text-blue-800 border-blue-300',
  },
  ASSISTED_REVIEW: {
    label: 'Validación asistida',
    className: 'bg-amber-100 text-amber-800 border-amber-300',
  },
  PARTNER_DECLARED: {
    label: 'Declarado por socio',
    className: 'bg-purple-100 text-purple-800 border-purple-300',
  },
  HERITAGE: {
    label: 'Heredado',
    className: 'bg-slate-100 text-slate-700 border-slate-300',
  },
  UNKNOWN: {
    label: 'Desconocido',
    className: 'bg-gray-100 text-gray-600 border-gray-300',
  },
}

export function DataSourceBadge({ source, label, size = 'md' }: Props) {
  const cfg = SOURCE_CONFIG[source] ?? SOURCE_CONFIG.UNKNOWN
  const textLabel = label || cfg.label
  const sizeClass = size === 'sm' ? 'text-xs px-2 py-0.5' : 'text-sm px-2.5 py-1'

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full font-medium border ${sizeClass} ${cfg.className}`}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {textLabel}
    </span>
  )
}
