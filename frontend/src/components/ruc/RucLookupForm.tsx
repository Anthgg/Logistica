import { useState, type FormEvent } from 'react'
import { Button } from '../common/Button'
import type { RucLookupRequest } from '../../types/ruc-integration'

interface Props {
  onLookup: (req: RucLookupRequest) => void
  isLoading?: boolean
  initialRuc?: string
  canUseAuthorizedProvider?: boolean
}

export function RucLookupForm({
  onLookup,
  isLoading = false,
  initialRuc = '',
  canUseAuthorizedProvider = false,
}: Props) {
  const [ruc, setRuc] = useState(initialRuc)
  const [includeAnnexes, setIncludeAnnexes] = useState(false)
  const [useAuthorizedProvider, setUseAuthorizedProvider] = useState(false)

  // Clean value visually while keeping string type
  const cleanRuc = ruc.replace(/\D/g, '').slice(0, 11)

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (cleanRuc.length !== 11 || isLoading) return
    onLookup({
      ruc: cleanRuc,
      include_annexes: includeAnnexes,
      use_authorized_provider: useAuthorizedProvider,
    })
  }

  const handleClear = () => {
    setRuc('')
    setIncludeAnnexes(false)
    setUseAuthorizedProvider(false)
  }

  const isValidFormat = cleanRuc.length === 11 && (cleanRuc.startsWith('10') || cleanRuc.startsWith('20') || cleanRuc.startsWith('15') || cleanRuc.startsWith('17'))

  return (
    <form onSubmit={handleSubmit} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm space-y-4">
      <div>
        <label htmlFor="ruc-input" className="mb-1.5 block text-xs font-bold uppercase tracking-wider text-slate-700">
          Número de RUC (11 dígitos)
        </label>
        <div className="flex flex-col gap-2 sm:flex-row">
          <input
            id="ruc-input"
            type="text"
            inputMode="numeric"
            value={cleanRuc}
            onChange={(e) => setRuc(e.target.value)}
            placeholder="Ej. 20123456789"
            maxLength={11}
            disabled={isLoading}
            className="flex-1 font-mono text-base font-medium rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-slate-800 placeholder:text-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200 disabled:opacity-50"
          />
          <div className="flex gap-2">
            <Button
              type="submit"
              disabled={cleanRuc.length !== 11 || isLoading}
              isLoading={isLoading}
              loadingLabel="Consultando..."
            >
              Consultar RUC
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={handleClear}
              disabled={isLoading || !cleanRuc}
            >
              Limpiar
            </Button>
          </div>
        </div>
        {cleanRuc.length > 0 && cleanRuc.length !== 11 && (
          <p className="mt-1 text-xs text-amber-600">
            El RUC debe tener exactamente 11 dígitos ({cleanRuc.length}/11).
          </p>
        )}
        {cleanRuc.length === 11 && !isValidFormat && (
          <p className="mt-1 text-xs text-amber-600">
            Formato atípico. Los RUC peruanos suelen iniciar con 10, 15, 17 o 20.
          </p>
        )}
      </div>

      {/* Options */}
      <div className="flex flex-wrap gap-4 pt-2 border-t border-slate-100 text-xs">
        <label className="flex items-center gap-2 text-slate-700 cursor-pointer">
          <input
            type="checkbox"
            checked={includeAnnexes}
            onChange={(e) => setIncludeAnnexes(e.target.checked)}
            disabled={isLoading}
            className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
          />
          Incluir locales anexos del padrón
        </label>

        {canUseAuthorizedProvider && (
          <label className="flex items-center gap-2 text-slate-700 cursor-pointer">
            <input
              type="checkbox"
              checked={useAuthorizedProvider}
              onChange={(e) => setUseAuthorizedProvider(e.target.checked)}
              disabled={isLoading}
              className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
            />
            Usar proveedor autorizado si estuviera disponible
          </label>
        )}
      </div>
    </form>
  )
}
