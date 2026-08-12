import React, { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  matchesNavigationQuery,
  NAVIGATION_GROUPS,
  type NavigationModule,
} from './nav-modules.config'
import { LogisticsIcon } from '../common/LogisticsIcon'

interface CommandPaletteProps {
  isOpen: boolean
  onClose: () => void
  onOpenSettings: () => void
  modules: NavigationModule[]
}

export function CommandPalette({
  isOpen,
  onClose,
  onOpenSettings,
  modules,
}: CommandPaletteProps) {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [selectedIndex, setSelectedIndex] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)

  // Escuchar atajo Ctrl + K / Cmd + K
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && (e.key === 'k' || e.key === 'K')) {
        e.preventDefault()
        if (isOpen) {
          onClose()
        } else {
          // abre la paleta
          const btn = document.getElementById('cmd-palette-trigger')
          if (btn) btn.click()
        }
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, onClose])

  useEffect(() => {
    if (!isOpen) return
    const timer = window.setTimeout(() => inputRef.current?.focus(), 50)
    setQuery('')
    setSelectedIndex(0)
    return () => window.clearTimeout(timer)
  }, [isOpen])

  if (!isOpen) return null

  // La paleta siempre trabaja sobre la lista plana de módulos permitidos:
  // agrupar la barra no puede esconder nada del buscador.
  const filteredModules = modules.filter((m) => matchesNavigationQuery(m, query))

  const handleSelect = (mod: NavigationModule) => {
    navigate(mod.route)
    onClose()
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setSelectedIndex((prev) => (prev + 1) % Math.max(1, filteredModules.length))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setSelectedIndex((prev) => (prev - 1 + filteredModules.length) % Math.max(1, filteredModules.length))
    } else if (e.key === 'Enter') {
      e.preventDefault()
      if (filteredModules[selectedIndex]) {
        handleSelect(filteredModules[selectedIndex])
      }
    } else if (e.key === 'Escape') {
      onClose()
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-20 bg-slate-950/70 backdrop-blur-sm p-4"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label="Paleta de comandos"
    >
      <div
        className="w-full max-w-xl rounded-2xl border border-slate-200 bg-white shadow-2xl overflow-hidden text-slate-800 flex flex-col max-h-[75vh]"
        onClick={(e) => e.stopPropagation()}
        onKeyDown={handleKeyDown}
      >
        {/* Input de búsqueda */}
        <div className="flex items-center gap-3 px-4 py-3.5 border-b border-slate-100">
          <LogisticsIcon name="search" size={20} className="text-slate-400" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value)
              setSelectedIndex(0)
            }}
            placeholder="Buscar módulo, ruta o acción rápida..."
            className="flex-1 bg-transparent text-sm text-slate-800 placeholder-slate-400 focus:outline-none"
          />
          <kbd className="rounded border border-slate-200 bg-slate-100 px-1.5 py-0.5 text-[10px] font-mono text-slate-500">
            ESC
          </kbd>
        </div>

        {/* Lista de resultados */}
        <div className="overflow-y-auto p-2 flex-1 space-y-1">
          {filteredModules.length === 0 ? (
            <div className="px-4 py-8 text-center text-sm text-slate-400">
              No se encontraron módulos para "{query}"
            </div>
          ) : (
            filteredModules.map((mod, idx) => {
              const isSelected = idx === selectedIndex
              return (
                <button
                  key={mod.id}
                  type="button"
                  onClick={() => handleSelect(mod)}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-left transition-colors text-xs ${
                    isSelected
                      ? 'bg-orange-50 text-orange-700 font-medium'
                      : 'text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span className={`flex h-7 w-7 items-center justify-center rounded-lg border ${isSelected ? 'bg-orange-100 border-orange-200' : 'bg-slate-100 border-slate-200'}`}>
                      <LogisticsIcon name={mod.iconName} size={16} />
                    </span>
                    <div>
                      <div className="font-semibold text-slate-800">{mod.label}</div>
                      <div className="text-[10px] text-slate-400">
                        {mod.description ?? mod.route}
                      </div>
                    </div>
                  </div>
                  <span className="text-[10px] text-slate-400 uppercase tracking-wider">
                    {mod.navigationGroup
                      ? NAVIGATION_GROUPS[mod.navigationGroup].label
                      : mod.category || 'Módulo'}
                  </span>
                </button>
              )
            })
          )}
        </div>

        {/* Footer de atajos */}
        <div className="flex items-center justify-between px-4 py-2.5 border-t border-slate-100 bg-slate-50 text-[11px] text-slate-500">
          <div className="flex items-center gap-3">
            <span><kbd className="font-mono bg-slate-100 border border-slate-200 px-1 rounded">↑↓</kbd> Navegar</span>
            <span><kbd className="font-mono bg-slate-100 border border-slate-200 px-1 rounded">↵</kbd> Seleccionar</span>
          </div>
          <button
            type="button"
            onClick={() => {
              onClose()
              onOpenSettings()
            }}
            className="text-xs text-orange-600 hover:underline flex items-center gap-1"
          >
            <LogisticsIcon name="settings" size={13} />
            <span>Configurar barra</span>
          </button>
        </div>
      </div>
    </div>
  )
}
