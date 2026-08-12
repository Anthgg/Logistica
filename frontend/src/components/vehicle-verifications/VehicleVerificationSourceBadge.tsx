import type {
  VehicleVerificationMethod,
  VehicleVerificationSourceType,
} from '../../types/vehicle-verifications'

interface SourceProps {
  sourceType: VehicleVerificationSourceType
  sourceName?: string
  size?: 'sm' | 'md'
}

interface MethodProps {
  method: VehicleVerificationMethod
  size?: 'sm' | 'md'
}

const SOURCE_CONFIG: Record<VehicleVerificationSourceType, { label: string; className: string }> = {
  SUNARP: { label: 'SUNARP Registral', className: 'bg-emerald-100 text-emerald-800 border-emerald-300' },
  MTC: { label: 'MTC Oficial', className: 'bg-blue-100 text-blue-800 border-blue-300' },
  SBS: { label: 'SBS / Seguros', className: 'bg-indigo-100 text-indigo-800 border-indigo-300' },
  AUTHORIZED_PROVIDER: { label: 'Proveedor Autorizado', className: 'bg-purple-100 text-purple-800 border-purple-300' },
  ASSISTED_MANUAL: { label: 'Validación Asistida', className: 'bg-amber-100 text-amber-800 border-amber-300' },
  DOCUMENTARY_REVIEW: { label: 'Revisión Documental', className: 'bg-slate-100 text-slate-700 border-slate-300' },
  INTERNAL: { label: 'Heredada / Interna', className: 'bg-gray-100 text-gray-700 border-gray-300' },
}

const METHOD_CONFIG: Record<VehicleVerificationMethod, { label: string; className: string }> = {
  AUTHORIZED_API: { label: 'API Autorizada', className: 'bg-emerald-100 text-emerald-800 border-emerald-300' },
  AUTHORIZED_BATCH: { label: 'Lote Autorizado', className: 'bg-blue-100 text-blue-800 border-blue-300' },
  ASSISTED_MANUAL: { label: 'Validación Asistida', className: 'bg-amber-100 text-amber-800 border-amber-300' },
  DOCUMENTARY_REVIEW: { label: 'Revisión Documental', className: 'bg-slate-100 text-slate-700 border-slate-300' },
}

export function VehicleVerificationSourceBadge({ sourceType, sourceName, size = 'md' }: SourceProps) {
  const cfg = SOURCE_CONFIG[sourceType] ?? {
    label: sourceName || sourceType,
    className: 'bg-slate-100 text-slate-700 border-slate-300',
  }
  const sizeClass = size === 'sm' ? 'text-[10px] px-2 py-0.5' : 'text-xs px-2.5 py-1'

  return (
    <span className={`inline-flex items-center rounded-full font-bold border ${sizeClass} ${cfg.className}`}>
      {sourceName || cfg.label}
    </span>
  )
}

export function VehicleVerificationMethodBadge({ method, size = 'md' }: MethodProps) {
  const cfg = METHOD_CONFIG[method] ?? {
    label: method,
    className: 'bg-slate-100 text-slate-700 border-slate-300',
  }
  const sizeClass = size === 'sm' ? 'text-[10px] px-2 py-0.5' : 'text-xs px-2.5 py-1'

  return (
    <span className={`inline-flex items-center rounded-full font-medium border ${sizeClass} ${cfg.className}`}>
      {cfg.label}
    </span>
  )
}
