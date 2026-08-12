import React, { useState } from 'react'
import type {
  NavigationModule,
  NavigationPreferences,
} from './nav-modules.config'
import { LogisticsIcon } from '../common/LogisticsIcon'

interface NavigationSettingsProps {
  isOpen: boolean
  onClose: () => void
  preferences: NavigationPreferences
  allModules: NavigationModule[]
  onUpdatePreferences: (
    updater:
      | Partial<NavigationPreferences>
      | ((prev: NavigationPreferences) => NavigationPreferences),
  ) => void
  onResetPreferences: () => void
  onToggleFavorite: (id: string) => void
  onToggleHide: (id: string) => void
  onReorder: (newOrder: string[]) => void
}

export function NavigationSettings({
  isOpen,
  onClose,
  preferences,
  allModules,
  onUpdatePreferences,
  onResetPreferences,
  onToggleFavorite,
  onToggleHide,
  onReorder,
}: NavigationSettingsProps) {
  const [draggedId, setDraggedId] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'orden' | 'visibilidad' | 'apariencia' | 'ocultamiento'>('orden')

  if (!isOpen) return null

  // Módulos ordenados según las preferencias
  const orderedModules = preferences.orderedItems
    .map((id) => allModules.find((m) => m.id === id))
    .filter((m): m is NavigationModule => Boolean(m))

  // Módulos faltantes que podrían no estar en orderedItems
  const missingModules = allModules.filter(
    (m) => !preferences.orderedItems.includes(m.id),
  )
  const fullList = [...orderedModules, ...missingModules]

  const handleDragStart = (e: React.DragEvent, id: string) => {
    setDraggedId(id)
    e.dataTransfer.setData('text/plain', id)
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
  }

  const handleDrop = (e: React.DragEvent, targetId: string) => {
    e.preventDefault()
    if (!draggedId || draggedId === targetId) return

    const currentOrder = fullList.map((m) => m.id)
    const dragIdx = currentOrder.indexOf(draggedId)
    const targetIdx = currentOrder.indexOf(targetId)

    if (dragIdx === -1 || targetIdx === -1) return

    const newOrder = [...currentOrder]
    const [moved] = newOrder.splice(dragIdx, 1)
    newOrder.splice(targetIdx, 0, moved)

    onReorder(newOrder)
    setDraggedId(null)
  }

  const moveUp = (id: string) => {
    const currentOrder = fullList.map((m) => m.id)
    const idx = currentOrder.indexOf(id)
    if (idx <= 0) return
    const newOrder = [...currentOrder]
    ;[newOrder[idx - 1], newOrder[idx]] = [newOrder[idx], newOrder[idx - 1]]
    onReorder(newOrder)
  }

  const moveDown = (id: string) => {
    const currentOrder = fullList.map((m) => m.id)
    const idx = currentOrder.indexOf(id)
    if (idx === -1 || idx >= currentOrder.length - 1) return
    const newOrder = [...currentOrder]
    ;[newOrder[idx], newOrder[idx + 1]] = [newOrder[idx + 1], newOrder[idx]]
    onReorder(newOrder)
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-3 sm:p-4 bg-slate-950/75 backdrop-blur-sm"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label="Configuración de la barra de navegación"
    >
      <div
        className="w-full max-w-2xl rounded-2xl border border-slate-200 bg-white shadow-2xl overflow-hidden text-slate-800 flex flex-col max-h-[85vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Cabecera del Panel */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
          <div className="flex items-center gap-2.5">
            <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-orange-100 text-orange-600">
              <LogisticsIcon name="settings" size={18} />
            </span>
            <div>
              <h2 className="text-sm font-bold text-slate-900">Configurar Barra de Navegación</h2>
              <p className="text-[11px] text-slate-500">Personaliza el orden, visibilidad y comportamiento visual</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="flex h-7 w-7 items-center justify-center rounded-lg bg-slate-100 text-slate-500 hover:bg-slate-200 hover:text-slate-700 transition-colors"
            aria-label="Cerrar ventana de configuración"
          >
            <LogisticsIcon name="x" size={14} />
          </button>
        </div>

        {/* Pestañas de Navegación Internas */}
        <div className="flex border-b border-slate-100 bg-slate-50 px-4 gap-1">
          {[
            { id: 'orden', label: 'Reordenar & Favoritos' },
            { id: 'visibilidad', label: 'Módulos visibles' },
            { id: 'apariencia', label: 'Apariencia & Alineación' },
            { id: 'ocultamiento', label: 'Ocultamiento' },
          ].map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-3 py-2 text-xs font-semibold border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-orange-500 text-orange-600'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Contenido según la pestaña activa */}
        <div className="overflow-y-auto p-5 space-y-4 flex-1">
          {/* TAB 1: ORDEN Y FAVORITOS */}
          {activeTab === 'orden' && (
            <div className="space-y-3">
              <p className="text-xs text-slate-500">
                Arrastra los elementos o usa las flechas para modificar la posición. Los elementos marcados como favoritos aparecerán con prioridad.
              </p>
              <div className="space-y-1.5 max-h-[45vh] overflow-y-auto pr-1">
                {fullList.map((mod) => {
                  const isFav = preferences.favoriteItems.includes(mod.id)
                  const isHidden = preferences.hiddenItems.includes(mod.id)

                  return (
                    <div
                      key={mod.id}
                      draggable
                      onDragStart={(e) => handleDragStart(e, mod.id)}
                      onDragOver={handleDragOver}
                      onDrop={(e) => handleDrop(e, mod.id)}
                      className={`flex items-center justify-between px-3 py-2 rounded-xl border transition-colors text-xs ${
                        isHidden
                          ? 'border-slate-200 bg-slate-50 opacity-50'
                          : 'border-slate-200 bg-slate-50 hover:bg-white hover:border-slate-300'
                      }`}
                    >
                      <div className="flex items-center gap-2.5">
                        <span className="cursor-grab text-slate-400 hover:text-slate-600">⋮⋮</span>
                        <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-white border border-slate-200">
                          <LogisticsIcon name={mod.iconName} size={16} />
                        </span>
                        <div>
                          <span className="font-semibold text-slate-700">{mod.label}</span>
                          {isHidden && <span className="ml-2 text-[10px] text-rose-500">(Oculto)</span>}
                        </div>
                      </div>

                      <div className="flex items-center gap-1">
                        <button
                          type="button"
                          onClick={() => onToggleFavorite(mod.id)}
                          className={`p-1.5 rounded-lg border transition-colors ${
                            isFav
                              ? 'border-amber-300 bg-amber-50 text-amber-600'
                              : 'border-slate-200 text-slate-400 hover:text-slate-600'
                          }`}
                          title={isFav ? 'Quitar de favoritos' : 'Marcar como favorito'}
                        >
                          <LogisticsIcon name="star" size={14} />
                        </button>

                        <button
                          type="button"
                          onClick={() => moveUp(mod.id)}
                          className="px-2 py-1 rounded-lg border border-slate-200 text-slate-500 hover:bg-slate-100 hover:text-slate-700"
                          title="Subir"
                        >
                          <LogisticsIcon name="chevron" size={14} className="-rotate-90" />
                        </button>
                        <button
                          type="button"
                          onClick={() => moveDown(mod.id)}
                          className="px-2 py-1 rounded-lg border border-slate-200 text-slate-500 hover:bg-slate-100 hover:text-slate-700"
                          title="Bajar"
                        >
                          <LogisticsIcon name="chevron" size={14} className="rotate-90" />
                        </button>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* TAB 2: VISIBILIDAD */}
          {activeTab === 'visibilidad' && (
            <div className="space-y-3">
              <p className="text-xs text-slate-500">
                Selecciona qué accesos deseas ocultar de la barra horizontal para mantener una vista ultra reducida.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {allModules.map((mod) => {
                  const isHidden = preferences.hiddenItems.includes(mod.id)
                  return (
                    <label
                      key={mod.id}
                      className={`flex items-center justify-between p-2.5 rounded-xl border text-xs cursor-pointer transition-colors ${
                        !isHidden
                          ? 'border-slate-200 bg-white text-slate-700'
                          : 'border-slate-100 bg-slate-50 text-slate-400'
                      }`}
                    >
                      <div className="flex items-center gap-2.5">
                        <LogisticsIcon name={mod.iconName} size={16} />
                        <span className="font-medium">{mod.label}</span>
                      </div>
                      <input
                        type="checkbox"
                        checked={!isHidden}
                        onChange={() => onToggleHide(mod.id)}
                        className="rounded border-slate-300 bg-white text-orange-500 focus:ring-orange-500"
                      />
                    </label>
                  )
                })}
              </div>
            </div>
          )}

          {/* TAB 3: APARIENCIA */}
          {activeTab === 'apariencia' && (
            <div className="space-y-4 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Alineación de la barra</label>
                <div className="grid grid-cols-3 gap-2">
                  {(['left', 'center', 'right'] as const).map((align) => (
                    <button
                      key={align}
                      type="button"
                      onClick={() => onUpdatePreferences({ alignment: align })}
                      className={`py-2 rounded-xl border font-medium capitalize transition-colors ${
                        preferences.alignment === align
                          ? 'border-orange-500 bg-orange-50 text-orange-700'
                          : 'border-slate-200 bg-slate-50 text-slate-500 hover:text-slate-700 hover:border-slate-300'
                      }`}
                    >
                      {align === 'left' ? 'Izquierda' : align === 'right' ? 'Derecha' : 'Centrada'}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Densidad y tamaño</label>
                <div className="grid grid-cols-2 gap-2">
                  {(['compact', 'comfortable'] as const).map((dens) => (
                    <button
                      key={dens}
                      type="button"
                      onClick={() => onUpdatePreferences({ density: dens })}
                      className={`py-2 rounded-xl border font-medium capitalize transition-colors ${
                        preferences.density === dens
                          ? 'border-orange-500 bg-orange-50 text-orange-700'
                          : 'border-slate-200 bg-slate-50 text-slate-500 hover:text-slate-700 hover:border-slate-300'
                      }`}
                    >
                      {dens === 'compact' ? 'Compacto (52px)' : 'Cómodo (60px)'}
                    </button>
                  ))}
                </div>
              </div>

              <div className="pt-2 border-t border-slate-100">
                <label className="flex items-center justify-between cursor-pointer py-1">
                  <div>
                    <span className="font-semibold text-slate-700">Mostrar nombres de texto</span>
                    <p className="text-[11px] text-slate-500">Mostrar etiqueta al lado del icono si hay espacio</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={preferences.showLabels}
                    onChange={(e) => onUpdatePreferences({ showLabels: e.target.checked })}
                    className="rounded border-slate-300 bg-white text-orange-500 focus:ring-orange-500 h-4 w-4"
                  />
                </label>
              </div>
            </div>
          )}

          {/* TAB 4: OCULTAMIENTO */}
          {activeTab === 'ocultamiento' && (
            <div className="space-y-4 text-xs">
              <label className="flex items-center justify-between cursor-pointer">
                <div>
                  <span className="font-semibold text-slate-700">Activar ocultamiento automático</span>
                  <p className="text-[11px] text-slate-500">Oculta la barra tras un periodo de inactividad</p>
                </div>
                <input
                  type="checkbox"
                  checked={preferences.autoHideEnabled}
                  onChange={(e) => onUpdatePreferences({ autoHideEnabled: e.target.checked })}
                  className="rounded border-slate-300 bg-white text-orange-500 focus:ring-orange-500 h-4 w-4"
                />
              </label>

              {preferences.autoHideEnabled && (
                <div>
                  <label className="block font-semibold text-slate-700 mb-1.5">Tiempo de espera sin interacción</label>
                  <div className="grid grid-cols-4 gap-2">
                    {[
                      { label: '30 s', value: 30 },
                      { label: '1 min', value: 60 },
                      { label: '2 min', value: 120 },
                      { label: 'Nunca', value: -1 },
                    ].map((time) => (
                      <button
                        key={time.value}
                        type="button"
                        onClick={() =>
                          onUpdatePreferences({
                            autoHideDelay: time.value,
                            autoHideEnabled: time.value !== -1,
                          })
                        }
                        className={`py-2 rounded-xl border font-medium transition-colors ${
                          preferences.autoHideDelay === time.value
                            ? 'border-orange-500 bg-orange-50 text-orange-700'
                            : 'border-slate-200 bg-slate-50 text-slate-500 hover:text-slate-700 hover:border-slate-300'
                        }`}
                      >
                        {time.label}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <div className="p-3 rounded-xl border border-slate-200 bg-slate-50 text-[11px] text-slate-500 space-y-1">
                <div className="flex items-center gap-1.5 font-semibold text-slate-600">
                  <LogisticsIcon name="info" size={13} className="shrink-0" />
                  Atajo de teclado:
                </div>
                <p>Presiona <kbd className="bg-slate-100 border border-slate-200 px-1 rounded font-mono text-slate-700">Alt + M</kbd> en cualquier momento para alternar la visibilidad de la barra.</p>
              </div>
            </div>
          )}
        </div>

        {/* Footer con Restaurar */}
        <div className="flex items-center justify-between px-5 py-3 border-t border-slate-100 bg-slate-50">
          <button
            type="button"
            onClick={onResetPreferences}
            className="text-xs text-rose-500 hover:underline"
          >
            Restaurar configuración predeterminada
          </button>
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-1.5 rounded-xl bg-orange-500 hover:bg-orange-600 text-white font-semibold text-xs shadow-md transition-colors"
          >
            Guardar y cerrar
          </button>
        </div>
      </div>
    </div>
  )
}
