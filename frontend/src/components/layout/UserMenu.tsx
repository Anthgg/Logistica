import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { LogisticsIcon } from '../common/LogisticsIcon'
import { useAuth } from '../../hooks/useAuth'
import { useTranslations } from '../../hooks/useTranslations'
import { getErrorMessage } from '../../utils/errors'

export function UserMenu() {
  const { user, logout } = useAuth()
  const { translate } = useTranslations()
  const navigate = useNavigate()
  const [isOpen, setIsOpen] = useState(false)
  const [isLoggingOut, setIsLoggingOut] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!user) return null

  const initials = user.full_name
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part.charAt(0).toUpperCase())
    .join('')

  const handleLogout = async () => {
    if (isLoggingOut) return
    setIsLoggingOut(true)
    setError(null)
    try {
      await logout()
      navigate('/login', { replace: true, state: { message: 'Sesión cerrada correctamente.' } })
    } catch (caughtError: unknown) {
      setError(getErrorMessage(caughtError))
    } finally {
      setIsLoggingOut(false)
    }
  }

  return (
    <div className="relative">
      <button
        type="button"
        className="flex cursor-pointer items-center gap-2 rounded-full border border-transparent bg-white p-1 text-slate-800 transition-colors hover:border-slate-200 hover:bg-slate-50 focus-visible:outline-2 focus-visible:outline-blue-600 focus-visible:outline-offset-2 md:pr-2.5"
        aria-expanded={isOpen}
        aria-haspopup="menu"
        aria-label={`Menú de ${user.full_name}`}
        onClick={() => setIsOpen((v) => !v)}
      >
        {/* Avatar */}
        <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary-xlight text-2xs font-bold text-primary">
          {initials}
        </span>
        <span className="hidden text-left md:flex md:flex-col leading-none min-w-0">
          <strong className="text-xs font-semibold text-slate-900 leading-tight max-w-[120px] truncate">{user.full_name}</strong>
          <span className="text-2xs text-slate-400 font-normal leading-tight max-w-[130px] truncate mt-0.5">
            {translate('common', user.role, user.role)}
          </span>
        </span>
        <LogisticsIcon name="chevron" size={14} className="hidden text-slate-400 md:block ml-0.5" aria-hidden="true" />
      </button>

      {isOpen && (
        <div
          className="absolute right-0 top-full mt-2 w-56 rounded-xl border border-slate-200 bg-white p-1.5 shadow-lg z-50 flex flex-col gap-0.5"
          role="menu"
        >
          {/* Heading */}
          <div className="flex items-center gap-2.5 px-2.5 py-2 border-b border-slate-100 mb-1">
            <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary-xlight text-2xs font-bold text-primary">
              {initials}
            </span>
            <div className="min-w-0 flex-1">
              <strong className="block text-xs font-semibold text-slate-900 truncate">{user.full_name}</strong>
              <small className="block text-[10px] text-slate-500 truncate">{user.email}</small>
            </div>
          </div>

          {error && (
            <p className="text-[11px] text-rose-600 px-2.5 py-1" role="alert">{error}</p>
          )}

          {[
            { label: 'Mi perfil',             icon: 'user',     path: '/profile' },
            { label: 'Dispositivos y accesos', icon: 'sessions', path: '/sessions' },
            { label: 'Seguridad de la cuenta', icon: 'key',      path: '/change-password' },
          ].map(({ label, icon, path }) => (
            <button
              key={path}
              type="button"
              role="menuitem"
              className="w-full flex items-center gap-2 px-2.5 py-2 text-xs font-medium text-slate-600 rounded-lg hover:bg-slate-50 hover:text-slate-900 transition-colors text-left border-none bg-transparent cursor-pointer"
              onClick={() => { setIsOpen(false); navigate(path) }}
            >
              <LogisticsIcon name={icon as Parameters<typeof LogisticsIcon>[0]['name']} size={15} />
              {label}
            </button>
          ))}

          <div className="h-px bg-slate-100 my-1" aria-hidden="true" />

          <button
            type="button"
            role="menuitem"
            className="w-full flex items-center gap-2 px-2.5 py-2 text-xs font-medium text-rose-600 rounded-lg hover:bg-rose-50 transition-colors text-left border-none bg-transparent cursor-pointer disabled:opacity-50"
            onClick={() => void handleLogout()}
            disabled={isLoggingOut}
          >
            <LogisticsIcon name="logout" size={15} />
            {isLoggingOut ? 'Cerrando sesión…' : 'Cerrar sesión'}
          </button>
        </div>
      )}
    </div>
  )
}
