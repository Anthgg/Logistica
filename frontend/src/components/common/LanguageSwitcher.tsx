import { useEffect, useRef, useState } from 'react'
import { useTranslations } from '../../hooks/useTranslations'
import type { SupportedLanguage } from '../../types/i18n'
import { LogisticsIcon } from './LogisticsIcon'

const options: Array<{
  value: SupportedLanguage
  label: string
  shortLabel: string
}> = [
  { value: 'es-PE', label: 'Español (Perú)', shortLabel: 'ES' },
  { value: 'en-US', label: 'English (US)', shortLabel: 'EN' },
  { value: 'pt-BR', label: 'Português (Brasil)', shortLabel: 'PT' },
]

export function LanguageSwitcher({
  compact = false,
  ghost = false,
}: {
  compact?: boolean
  ghost?: boolean
}) {
  const {
    language,
    isChangingLanguage,
    error,
    changeLanguage,
  } = useTranslations()
  const [isOpen, setIsOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const buttonRef = useRef<HTMLButtonElement>(null)

  const currentOption = options.find((o) => o.value === language) ?? options[0]

  useEffect(() => {
    if (!isOpen) return undefined

    const handleClickOutside = (event: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false)
      }
    }

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsOpen(false)
        buttonRef.current?.focus()
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    document.addEventListener('keydown', handleEscape)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
      document.removeEventListener('keydown', handleEscape)
    }
  }, [isOpen])

  const handleSelect = (value: SupportedLanguage) => {
    setIsOpen(false)
    if (value !== language) {
      void changeLanguage(value).catch(() => undefined)
    }
  }

  return (
    <div ref={containerRef} className="relative">
      <button
        ref={buttonRef}
        type="button"
        onClick={() => setIsOpen((v) => !v)}
        disabled={isChangingLanguage}
        aria-expanded={isOpen}
        aria-haspopup="listbox"
        aria-label="Cambiar idioma"
        title={error ?? 'Cambiar idioma'}
        className={`flex min-h-9 items-center gap-1.5 rounded-lg px-2.5 text-xs font-semibold transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 disabled:cursor-wait disabled:opacity-60 cursor-pointer ${
          ghost
            ? 'border border-transparent text-slate-500 hover:bg-slate-100 hover:text-slate-700'
            : 'border border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-50'
        }`}
      >
        <span className="inline-flex h-4 min-w-[1.25rem] items-center justify-center rounded-sm bg-current/10 px-0.5 text-[10px] font-bold uppercase tracking-widest leading-none">
          {currentOption.shortLabel}
        </span>
        {!compact && (
          <span className="text-xs">{currentOption.label.split(' (')[0]}</span>
        )}
        <LogisticsIcon
          name="chevron"
          size={12}
          className={`text-slate-400 transition-transform ${isOpen ? 'rotate-90' : ''}`}
        />
      </button>

      {isOpen && (
        <div
          role="listbox"
          aria-label="Seleccionar idioma"
          className="absolute right-0 top-full mt-1.5 w-44 rounded-xl border border-slate-200 bg-white p-1 shadow-lg z-50"
        >
          {options.map((option) => (
            <button
              key={option.value}
              type="button"
              role="option"
              aria-selected={option.value === language}
              onClick={() => handleSelect(option.value)}
              className={`flex w-full cursor-pointer items-center gap-2.5 rounded-lg border-none px-2.5 py-2 text-left text-xs font-medium transition-colors ${
                option.value === language
                  ? 'bg-blue-50 text-blue-700 font-semibold'
                  : 'bg-transparent text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              <span className="inline-flex h-4 w-6 items-center justify-center rounded-sm bg-slate-200 text-[10px] font-bold uppercase tracking-widest text-slate-700 leading-none">
                {option.shortLabel}
              </span>
              <span className="flex-1">{option.label}</span>
              {option.value === language && (
                <LogisticsIcon name="check" size={14} className="text-blue-700" />
              )}
            </button>
          ))}
        </div>
      )}

      <span className="sr-only" aria-live="polite">
        {isChangingLanguage
          ? 'Actualizando idioma.'
          : error
            ? `No se actualizó el catálogo. ${error}`
            : ''}
      </span>
    </div>
  )
}