import type { InboundScanMode } from '../../types/inbound-receiving'

const MODES: { value: InboundScanMode; label: string; description: string }[] = [
  { value: 'UNIT', label: 'Unitario', description: 'Un escaneo = una unidad' },
  { value: 'CODE_PLUS_QUANTITY', label: 'Código + cantidad', description: 'Escanear y luego ingresar cantidad' },
  { value: 'PACKAGING', label: 'Empaque', description: 'Escanear empaque con factor' },
  { value: 'SERIAL', label: 'Serie', description: 'Captura individual de series' },
  { value: 'LOT_PLUS_QUANTITY', label: 'Lote + cantidad', description: 'Lote con cantidad por lote' },
  { value: 'BLIND_COUNT', label: 'Conteo ciego', description: 'Sin orden esperado' },
  { value: 'GUIDED_COUNT', label: 'Conteo guiado', description: 'Línea por línea' },
]

interface ScanModeSelectorProps {
  value: InboundScanMode
  onChange: (mode: InboundScanMode) => void
  availableModes: InboundScanMode[]
  disabled?: boolean
}

export function ScanModeSelector({ value, onChange, availableModes, disabled = false }: ScanModeSelectorProps) {
  return (
    <div className="space-y-1">
      <span className="text-xs font-bold text-slate-700">Modo de escaneo</span>
      <div className="flex flex-wrap gap-1.5">
        {MODES.filter((m) => availableModes.includes(m.value)).map((mode) => (
          <button
            key={mode.value}
            type="button"
            disabled={disabled}
            onClick={() => onChange(mode.value)}
            className={`rounded-lg px-2.5 py-1.5 text-xs font-semibold transition-colors ${
              value === mode.value
                ? 'bg-[#1F4E6D] text-white'
                : 'border border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
            } disabled:opacity-50`}
            title={mode.description}
            aria-pressed={value === mode.value}
          >
            {mode.label}
          </button>
        ))}
      </div>
    </div>
  )
}
