import { useEffect, useRef, useState } from 'react'
import type { NavigationModule } from './nav-modules.config'
import { LogisticsIcon } from '../common/LogisticsIcon'

interface NavigationContextMenuProps {
  x: number
  y: number
  module: NavigationModule
  isFavorite: boolean
  onClose: () => void
  onToggleFavorite: (id: string) => void
  onToggleHide: (id: string) => void
  onMoveToStart: (id: string) => void
  onOpenNewTab: (route: string) => void
  onShowInfo: (module: NavigationModule) => void
}

export function NavigationContextMenu({
  x,
  y,
  module,
  isFavorite,
  onClose,
  onToggleFavorite,
  onToggleHide,
  onMoveToStart,
  onOpenNewTab,
  onShowInfo,
}: NavigationContextMenuProps) {
  const menuRef = useRef<HTMLDivElement>(null)
  const [pos, setPos] = useState({ top: y, left: x })

  useEffect(() => {
    if (!menuRef.current) return
    const rect = menuRef.current.getBoundingClientRect()
    let newTop = y - rect.height - 8
    let newLeft = x

    if (newTop < 10) newTop = y + 8
    if (newLeft + rect.width > window.innerWidth - 10) {
      newLeft = window.innerWidth - rect.width - 10
    }

    setPos({ top: newTop, left: newLeft })
  }, [x, y])

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        onClose()
      }
    }
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('mousedown', handleClickOutside)
    window.addEventListener('keydown', handleKeyDown)
    return () => {
      window.removeEventListener('mousedown', handleClickOutside)
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [onClose])

  return (
    <div
      ref={menuRef}
      style={{ top: `${pos.top}px`, left: `${pos.left}px` }}
      className="fixed z-50 min-w-[200px] rounded-xl border border-slate-200 bg-white p-1.5 shadow-xl backdrop-blur-sm text-xs text-slate-700"
      role="menu"
    >
      <div className="px-2.5 py-1.5 border-b border-slate-100 text-[11px] font-semibold text-slate-500">
        {module.label}
      </div>

      <button
        type="button"
        role="menuitem"
        onClick={() => {
          onOpenNewTab(module.route)
          onClose()
        }}
        className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-left hover:bg-slate-100 hover:text-slate-900 transition-colors"
      >
        <span>Abrir en nueva pestaña</span>
        <svg className="h-3.5 w-3.5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
        </svg>
      </button>

      <button
        type="button"
        role="menuitem"
        onClick={() => {
          onToggleFavorite(module.id)
          onClose()
        }}
        className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-left hover:bg-slate-100 hover:text-slate-900 transition-colors"
      >
        <span>{isFavorite ? 'Quitar de favoritos' : 'Fijar en la barra'}</span>
        <LogisticsIcon name="star" size={14} className={isFavorite ? 'text-amber-400' : 'text-slate-400'} />
      </button>

      <button
        type="button"
        role="menuitem"
        onClick={() => {
          onMoveToStart(module.id)
          onClose()
        }}
        className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-left hover:bg-slate-100 hover:text-slate-900 transition-colors"
      >
        <span>Mover al inicio</span>
        <LogisticsIcon name="chevron" size={13} className="rotate-180 text-slate-400" />
      </button>

      <button
        type="button"
        role="menuitem"
        onClick={() => {
          onToggleHide(module.id)
          onClose()
        }}
        className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-left hover:bg-rose-50 text-rose-500 hover:text-rose-600 transition-colors"
      >
        <span>Ocultar de la barra</span>
        <LogisticsIcon name="x" size={13} className="text-slate-400" />
      </button>

      <div className="my-1 border-t border-slate-100" />

      <button
        type="button"
        role="menuitem"
        onClick={() => {
          onShowInfo(module)
          onClose()
        }}
        className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-left hover:bg-slate-100 text-slate-500 hover:text-slate-700 transition-colors"
      >
        <span>Ver información</span>
        <LogisticsIcon name="info" size={13} className="text-slate-400" />
      </button>
    </div>
  )
}
