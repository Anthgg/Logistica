import { useState } from 'react'
import { unitsConversionsApi } from '../../api/units-conversions-api'
import { Button } from '../../components/common/Button'
import { Input } from '../../components/common/Input'
import type { ConversionEvaluationResponse } from '../../types/units-conversions'
import { getErrorMessage } from '../../utils/errors'

export function UnitConversionSimulatorPanel() {
  const [quantity, setQuantity] = useState<string>('100.0000')
  const [sourceUnit, setSourceUnit] = useState<string>('KG')
  const [targetUnit, setTargetUnit] = useState<string>('G')
  const [result, setResult] = useState<ConversionEvaluationResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSimulate = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const res = await unitsConversionsApi.evaluateConversion({
        quantity,
        source_unit_code: sourceUnit,
        target_unit_code: targetUnit,
      })
      setResult(res)
    } catch (err: unknown) {
      setError(getErrorMessage(err))
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-4 text-xs">
      <div className="rounded-xl border border-blue-200 bg-blue-50 p-4 text-blue-900 space-y-1">
        <p className="font-bold">Motor Autoritativo Backend de Conversión:</p>
        <p className="leading-relaxed text-[11px]">
          Los cálculos y resolución de rutas de conversión se realizan de forma exacta en el servidor. La interfaz maneja
          cantidades en formato decimal `String` sin operaciones o redondeos `float`/`Number` en React.
        </p>
      </div>

      {error && <p className="text-xs font-semibold text-rose-600">{error}</p>}

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <Input
          label="Cantidad a evaluar (Decimal String)"
          value={quantity}
          onChange={(e) => setQuantity(e.target.value)}
          placeholder="Ej: 100.0000"
          required
        />

        <div>
          <label className="font-semibold text-slate-700 block mb-1">Unidad Origen</label>
          <input
            type="text"
            className="input-field uppercase font-mono"
            value={sourceUnit}
            onChange={(e) => setSourceUnit(e.target.value.toUpperCase())}
            required
          />
        </div>

        <div>
          <label className="font-semibold text-slate-700 block mb-1">Unidad Destino</label>
          <input
            type="text"
            className="input-field uppercase font-mono"
            value={targetUnit}
            onChange={(e) => setTargetUnit(e.target.value.toUpperCase())}
            required
          />
        </div>
      </div>

      <div className="flex justify-end">
        <Button onClick={() => void handleSimulate()} isLoading={isLoading}>
          Evaluar Conversión en Backend
        </Button>
      </div>

      {result && (
        <div className="rounded-xl border border-slate-200 bg-white p-4 space-y-3 shadow-xs">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <span className="font-mono text-[10px] font-bold text-slate-400 uppercase">
              Resultado de Evaluación Backend
            </span>
            <span className="text-[10px] text-slate-400 font-mono">Evaluado a las {result.evaluated_at}</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-100">
              <span className="text-[10px] uppercase font-semibold text-slate-400 block">Resultado Exacto</span>
              <span className="font-mono text-base font-bold text-blue-700">
                {result.exact_result} {result.target_unit_code}
              </span>
            </div>

            <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-100">
              <span className="text-[10px] uppercase font-semibold text-slate-400 block">Factor Efectivo</span>
              <span className="font-mono text-sm font-bold text-slate-900">{result.effective_factor}</span>
            </div>

            <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-100">
              <span className="text-[10px] uppercase font-semibold text-slate-400 block">Residual</span>
              <span className="font-mono text-sm font-bold text-slate-900">{result.residual_quantity}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
