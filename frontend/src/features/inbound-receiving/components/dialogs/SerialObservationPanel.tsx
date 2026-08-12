import { useState, useRef, useCallback } from 'react'
import type { InboundSerialObservation } from '../../types/inbound-receiving'

interface SerialObservationPanelProps {
  serials: InboundSerialObservation[]
  onAddSerial: (serialCode: string) => Promise<void>
  onCompensateSerial?: (observationId: string) => void
  canCapture: boolean
  canManualEntry: boolean
  disabled?: boolean
}

export function SerialObservationPanel({
  serials,
  onAddSerial,
  onCompensateSerial,
  canCapture,
  canManualEntry,
  disabled = false,
}: SerialObservationPanelProps) {
  const [inputValue, setInputValue] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleSubmit = useCallback(async () => {
    const code = inputValue.trim()
    if (!code || submitting) return
    setSubmitting(true)
    try {
      await onAddSerial(code)
      setInputValue('')
      inputRef.current?.focus()
    } finally {
      setSubmitting(false)
    }
  }, [inputValue, submitting, onAddSerial])

  const duplicates = serials.filter((s) => s.duplicate_status !== 'UNIQUE')
  const total = serials.length
  const uniqueCount = total - duplicates.length

  return (
    <div className="space-y-3 rounded-xl border border-slate-200 bg-white p-3 text-xs">
      <div className="flex items-center justify-between">
        <h4 className="font-bold text-slate-800">Series observadas</h4>
        <div className="flex gap-2 text-[10px]">
          <span className="rounded bg-emerald-50 px-1.5 py-0.5 font-bold text-emerald-700">{uniqueCount} válidas</span>
          {duplicates.length > 0 && (
            <span className="rounded bg-rose-50 px-1.5 py-0.5 font-bold text-rose-700">{duplicates.length} duplicadas</span>
          )}
          <span className="rounded bg-slate-100 px-1.5 py-0.5 font-bold text-slate-600">{total} total</span>
        </div>
      </div>

      {(canCapture || canManualEntry) && (
        <div className="flex gap-2">
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); void handleSubmit() } }}
            placeholder="Escanear o ingresar serie…"
            className="flex-1 rounded-lg border border-slate-300 px-3 py-2 font-mono text-sm"
            disabled={disabled || submitting}
            autoComplete="off"
            aria-label="Ingreso de número de serie"
          />
          <button
            type="button"
            onClick={() => void handleSubmit()}
            disabled={!inputValue.trim() || submitting || disabled}
            className="rounded-lg bg-[#1F4E6D] px-3 py-2 font-semibold text-white hover:bg-[#173a55] disabled:opacity-50"
          >
            {submitting ? '…' : 'Agregar'}
          </button>
        </div>
      )}

      {serials.length > 0 && (
        <div className="max-h-48 overflow-y-auto">
          <table className="w-full text-left">
            <thead className="sticky top-0 bg-white">
              <tr className="border-b border-slate-100 text-[10px] text-slate-500">
                <th className="pb-1 font-semibold">#</th>
                <th className="pb-1 font-semibold">Serie</th>
                <th className="pb-1 font-semibold">Estado</th>
                <th className="pb-1 font-semibold">Fuente</th>
                {onCompensateSerial && <th className="pb-1 font-semibold" />}
              </tr>
            </thead>
            <tbody>
              {serials.map((s, i) => (
                <tr key={s.observation_id} className="border-b border-slate-50">
                  <td className="py-1 text-slate-400">{i + 1}</td>
                  <td className="py-1 font-mono">{s.serial_code}</td>
                  <td className="py-1">
                    <span className={`rounded px-1 py-0.5 text-[10px] font-bold ${
                      s.duplicate_status === 'UNIQUE' ? 'bg-emerald-50 text-emerald-700' :
                      s.duplicate_status === 'INCONCLUSIVE' ? 'bg-amber-50 text-amber-700' :
                      'bg-rose-50 text-rose-700'
                    }`}>
                      {s.duplicate_status === 'UNIQUE' ? 'Única' :
                       s.duplicate_status === 'DUPLICATE_IN_RECEIPT' ? 'Dup. recepción' :
                       s.duplicate_status === 'DUPLICATE_IN_SYSTEM' ? 'Dup. sistema' :
                       'Inconcluso'}
                    </span>
                  </td>
                  <td className="py-1 text-slate-400">{s.source}</td>
                  {onCompensateSerial && (
                    <td className="py-1">
                      <button type="button" onClick={() => onCompensateSerial(s.observation_id)} className="text-[10px] text-rose-600 hover:underline">
                        Compensar
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
