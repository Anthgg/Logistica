import { useState } from 'react'
import type { ReceivedCondition } from '../../types/inbound-receiving'

const CONDITIONS: { value: ReceivedCondition; label: string }[] = [
  { value: 'APPARENTLY_CORRECT', label: 'Aparentemente correcto' },
  { value: 'DAMAGED_PACKAGING', label: 'Embalaje dañado' },
  { value: 'DAMAGED_PRODUCT', label: 'Producto dañado' },
  { value: 'WET', label: 'Mojado' },
  { value: 'OPENED', label: 'Abierto' },
  { value: 'POSSIBLE_CONTAMINATION', label: 'Posible contaminación' },
  { value: 'WRONG_PRODUCT', label: 'Producto incorrecto' },
  { value: 'ILLEGIBLE_LABEL', label: 'Etiqueta ilegible' },
  { value: 'TEMPERATURE_CONCERN', label: 'Preocupación de temperatura' },
  { value: 'EXPIRED', label: 'Vencido' },
  { value: 'OTHER', label: 'Otro' },
]

interface ReceivedConditionPanelProps {
  onSubmit: (condition: ReceivedCondition, comment: string) => void
  disabled?: boolean
}

export function ReceivedConditionPanel({ onSubmit, disabled = false }: ReceivedConditionPanelProps) {
  const [selected, setSelected] = useState<ReceivedCondition | null>(null)
  const [comment, setComment] = useState('')

  const handleSubmit = () => {
    if (!selected) return
    onSubmit(selected, comment)
    setSelected(null)
    setComment('')
  }

  return (
    <div className="space-y-3 rounded-xl border border-slate-200 bg-white p-3 text-xs">
      <h4 className="font-bold text-slate-800">Condición observada</h4>

      <div className="flex flex-wrap gap-1.5">
        {CONDITIONS.map((c) => (
          <button
            key={c.value}
            type="button"
            disabled={disabled}
            onClick={() => setSelected(c.value)}
            className={`rounded-lg px-2.5 py-1.5 text-xs font-semibold transition-colors ${
              selected === c.value
                ? 'bg-[#1F4E6D] text-white'
                : 'border border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
            } disabled:opacity-50`}
            aria-pressed={selected === c.value}
          >
            {c.label}
          </button>
        ))}
      </div>

      {selected && (
        <>
          <div>
            <label htmlFor="condition-comment" className="mb-1 block text-xs font-bold text-slate-700">Comentario</label>
            <input
              id="condition-comment"
              type="text"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              placeholder="Detalle opcional…"
            />
          </div>

          <p className="text-[10px] text-amber-700">
            Esta observación puede generar un candidato para revisión en la Fase 040.
          </p>

          <button
            type="button"
            onClick={handleSubmit}
            disabled={disabled}
            className="rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#173a55] disabled:opacity-50"
          >
            Registrar condición
          </button>
        </>
      )}
    </div>
  )
}
