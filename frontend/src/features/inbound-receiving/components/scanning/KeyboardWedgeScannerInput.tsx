import { useCallback, useEffect, useRef, useState } from 'react'

interface KeyboardWedgeScannerInputProps {
  onScan: (code: string) => void
  disabled?: boolean
  maxLength?: number
  terminator?: 'Enter' | 'Tab'
  placeholder?: string
  autoFocus?: boolean
}

export function KeyboardWedgeScannerInput({
  onScan,
  disabled = false,
  maxLength = 256,
  terminator = 'Enter',
  placeholder = 'Escanee un código de barras…',
  autoFocus = true,
}: KeyboardWedgeScannerInputProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [value, setValue] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const lastSubmitRef = useRef(0)

  const refocus = useCallback(() => {
    if (inputRef.current && !disabled) {
      inputRef.current.focus()
    }
  }, [disabled])

  useEffect(() => {
    if (autoFocus) refocus()
  }, [autoFocus, refocus])

  const handleSubmit = useCallback(async () => {
    const code = value.trim()
    if (!code || submitting) return

    const now = Date.now()
    if (now - lastSubmitRef.current < 300) return
    lastSubmitRef.current = now

    setSubmitting(true)
    try {
      await onScan(code)
    } finally {
      setValue('')
      setSubmitting(false)
      refocus()
    }
  }, [value, submitting, onScan, refocus])

  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === terminator || (terminator === 'Enter' && e.key === 'Enter')) {
      e.preventDefault()
      void handleSubmit()
    }
    if (e.key === 'Tab' && terminator === 'Tab') {
      e.preventDefault()
      void handleSubmit()
    }
  }, [terminator, handleSubmit])

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const v = e.target.value
    if (v.length <= maxLength) {
      setValue(v)
    }
  }, [maxLength])

  return (
    <div className="relative">
      <label htmlFor="wedge-scanner-input" className="sr-only">
        Entrada de escáner
      </label>
      <input
        ref={inputRef}
        id="wedge-scanner-input"
        type="text"
        value={value}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        onBlur={refocus}
        disabled={disabled || submitting}
        placeholder={submitting ? 'Enviando…' : placeholder}
        autoComplete="off"
        autoCorrect="off"
        autoCapitalize="off"
        spellCheck={false}
        className="w-full rounded-xl border-2 border-[#1F4E6D] bg-white px-4 py-3 font-mono text-base text-slate-900 shadow-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#1F4E6D] focus:ring-offset-2 disabled:opacity-50 md:text-sm"
        aria-label="Campo de escaneo por código de barras"
      />
      {value && (
        <div className="absolute right-3 top-1/2 -translate-y-1/2 text-[11px] text-slate-400">
          {value.length}/{maxLength}
        </div>
      )}
      {submitting && (
        <div className="absolute inset-0 flex items-center justify-center rounded-xl bg-white/70">
          <span className="text-xs font-semibold text-[#1F4E6D]">Procesando…</span>
        </div>
      )}
    </div>
  )
}
