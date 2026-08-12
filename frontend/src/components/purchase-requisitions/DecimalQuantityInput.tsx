import React from 'react'

interface QuantityInputProps {
  value: string // decimal string
  onChange: (val: string) => void
  label?: string
  placeholder?: string
  required?: boolean
  disabled?: boolean
}

export function DecimalQuantityInput({
  value,
  onChange,
  label,
  placeholder = '1.0',
  required = false,
  disabled = false,
}: QuantityInputProps) {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value
    // Allow digits and single decimal dot
    if (/^\d*\.?\d*$/.test(raw)) {
      onChange(raw)
    }
  }

  return (
    <div>
      {label && <label className="mb-1 block font-bold text-slate-700 text-xs">{label}</label>}
      <input
        type="text"
        inputMode="decimal"
        value={value}
        onChange={handleChange}
        placeholder={placeholder}
        required={required}
        disabled={disabled}
        className="w-full font-mono text-sm font-bold rounded-lg border border-slate-300 px-3 py-2 text-slate-900 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
      />
    </div>
  )
}

interface ConversionPreviewProps {
  requestedQuantity: string
  unitCode: string
  baseQuantity: string | null
  baseUnitCode: string | null
  conversionRuleSummary: string | null
}

export function UnitConversionPreview({
  requestedQuantity,
  unitCode,
  baseQuantity,
  baseUnitCode,
  conversionRuleSummary,
}: ConversionPreviewProps) {
  if (!baseQuantity || !baseUnitCode) return null

  return (
    <div className="rounded-lg border border-indigo-100 bg-indigo-50/60 p-2.5 text-[11px] text-indigo-900 flex items-center justify-between font-mono">
      <span>
        {requestedQuantity} {unitCode} = <strong>{baseQuantity} {baseUnitCode}</strong>
      </span>
      {conversionRuleSummary && (
        <span className="text-[10px] text-indigo-700 font-sans">{conversionRuleSummary}</span>
      )}
    </div>
  )
}
