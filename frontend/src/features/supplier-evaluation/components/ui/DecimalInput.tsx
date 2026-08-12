import type { ChangeEvent } from 'react'
import { clsx } from 'clsx'

interface DecimalInputProps {
  id?: string
  value: string
  onChange: (value: string) => void
  label?: string
  placeholder?: string
  required?: boolean
  disabled?: boolean
  invalid?: boolean
  describedBy?: string
  className?: string
  maxDecimals?: number
  allowNegative?: boolean
}

/**
 * Input de valor decimal como string. No usa Number/parseFloat para
 * almacenar el valor de negocio. El backend es la autoridad.
 */
export function DecimalInput({
  id,
  value,
  onChange,
  label,
  placeholder = '0',
  required = false,
  disabled = false,
  invalid = false,
  describedBy,
  className,
  maxDecimals = 6,
  allowNegative = false,
}: DecimalInputProps) {
  const pattern = allowNegative
    ? new RegExp(`^-?\\d{0,12}(\\.\\d{0,${maxDecimals})?$`)
    : new RegExp(`^\\d{0,12}(\\.\\d{0,${maxDecimals})?$`)

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value
    if (raw === '' || pattern.test(raw)) {
      onChange(raw)
    }
  }

  return (
    <div className={className}>
      {label && (
        <label
          htmlFor={id}
          className="mb-1 block text-xs font-bold text-slate-700"
        >
          {label}
          {required && <span className="ml-0.5 text-rose-500">*</span>}
        </label>
      )}
      <input
        id={id}
        type="text"
        inputMode="decimal"
        value={value}
        onChange={handleChange}
        placeholder={placeholder}
        required={required}
        disabled={disabled}
        aria-invalid={invalid || undefined}
        aria-describedby={describedBy}
        className={clsx(
          'w-full rounded-lg border bg-white px-3 py-2 font-mono text-sm text-slate-900 shadow-xs focus:outline-none focus:ring-2',
          invalid
            ? 'border-rose-300 focus:border-rose-500 focus:ring-rose-200'
            : 'border-slate-300 focus:border-indigo-500 focus:ring-indigo-200',
          disabled && 'cursor-not-allowed opacity-50',
        )}
      />
    </div>
  )
}