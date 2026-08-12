import React, { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { LogisticsIcon } from '../common/LogisticsIcon'
import { useLogisticsPermissions } from '../../features/logistics-permissions/hooks/useLogisticsPermissions'
import {
  ALL_NAVIGATION_MODULES,
  groupNavigationModules,
  resolveActiveModuleId,
  type NavigationModule,
  type NavigationDisplayItem,
} from './nav-modules.config'
import { useNavigationPreferences } from './useNavigationPreferences'
import { NavigationScroller } from './NavigationScroller'
import { NavigationTooltip } from './NavigationTooltip'
import { NavigationContextMenu } from './NavigationContextMenu'
import { NavigationSettings } from './NavigationSettings'
import { CommandPalette } from './CommandPalette'

export function FloatingNavigationBar() {
  const auth = useLogisticsPermissions()
  const location = useLocation()
  const navigate = useNavigate()

  const {
    preferences,
    updatePreferences,
    toggleFavorite,
    toggleHide,
    resetPreferences,
    reorderItems,
  } = useNavigationPreferences()

  const [isSettingsOpen, setIsSettingsOpen] = useState(false)
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false)
  const [openGroupId, setOpenGroupId] = useState<string | null>(null)
  const groupMenuRef = useRef<HTMLDivElement>(null)
  const groupTriggerRef = useRef<HTMLButtonElement>(null)
  // Cuando el desplegable se abre con teclado hay que enfocar la primera opción;
  // abriéndolo con el ratón se deja el foco donde está.
  const focusFirstItemRef = useRef(false)

  // Estado para el menú contextual del clic derecho
  const [contextMenu, setContextMenu] = useState<{
    x: number
    y: number
    module: NavigationModule
  } | null>(null)

  // Estado para modal de información del módulo
  const [infoModalModule, setInfoModalModule] = useState<NavigationModule | null>(null)

  // Visibilidad basada en proximidad al borde inferior
  const [isNearBottom, setIsNearBottom] = useState(false)
  const rafRef = useRef<number | null>(null)

  useEffect(() => {
    const hasHover = window.matchMedia('(hover: hover)').matches
    if (!hasHover) {
      setIsNearBottom(true)
      return
    }

    const handleMouseMove = (e: MouseEvent) => {
      if (rafRef.current !== null) return
      rafRef.current = requestAnimationFrame(() => {
        rafRef.current = null
        setIsNearBottom(window.innerHeight - e.clientY < 150)
      })
    }

    window.addEventListener('mousemove', handleMouseMove, { passive: true })
    return () => {
      window.removeEventListener('mousemove', handleMouseMove)
      if (rafRef.current !== null) {
        cancelAnimationFrame(rafRef.current)
        rafRef.current = null
      }
    }
  }, [])

  const isVisible = isNearBottom || isSettingsOpen || isCommandPaletteOpen || Boolean(contextMenu) || Boolean(openGroupId)

  useEffect(() => {
    if (!openGroupId) return

    const closeOnOutsideClick = (event: PointerEvent) => {
      if (!groupMenuRef.current?.contains(event.target as Node)) {
        setOpenGroupId(null)
      }
    }
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key !== 'Escape') return
      setOpenGroupId(null)
      groupTriggerRef.current?.focus()
    }

    document.addEventListener('pointerdown', closeOnOutsideClick)
    document.addEventListener('keydown', closeOnEscape)
    return () => {
      document.removeEventListener('pointerdown', closeOnOutsideClick)
      document.removeEventListener('keydown', closeOnEscape)
    }
  }, [openGroupId])

  // Al abrir con teclado, el foco entra al primer elemento del menú.
  useEffect(() => {
    if (!openGroupId || !focusFirstItemRef.current) return
    focusFirstItemRef.current = false
    const first = groupMenuRef.current?.querySelector<HTMLElement>('[role="menuitem"]')
    first?.focus()
  }, [openGroupId])

  useEffect(() => {
    setOpenGroupId(null)
  }, [location.pathname])

  /** Flechas arriba/abajo y Home/End dentro del desplegable abierto. */
  const handleGroupMenuKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    const keys = ['ArrowDown', 'ArrowUp', 'Home', 'End']
    if (!keys.includes(event.key)) return

    const items = Array.from(
      groupMenuRef.current?.querySelectorAll<HTMLElement>('[role="menuitem"]') ?? [],
    )
    if (items.length === 0) return

    event.preventDefault()
    const current = items.indexOf(document.activeElement as HTMLElement)
    const next =
      event.key === 'Home' ? 0
      : event.key === 'End' ? items.length - 1
      : event.key === 'ArrowDown' ? (current + 1) % items.length
      : (current - 1 + items.length) % items.length

    items[next]?.focus()
  }



  // Filtrar módulos visibles según permisos RBAC y preferencias de oculto
  const allowedModules = useMemo(() => {
    return ALL_NAVIGATION_MODULES.filter((item) => {
      if (item.legacyAlwaysAllowed) return true
      if (auth.isLoading) return false
      if (item.permission && auth.hasPermission(item.permission)) return true
      if (item.anyOfPermissions && item.anyOfPermissions.length > 0 && auth.hasAnyPermission(item.anyOfPermissions)) return true
      return false
    })
  }, [auth])

  // Módulos ordenados según las preferencias del usuario + favoritos + recientes
  const displayModules = useMemo(() => {
    const visible = allowedModules.filter(
      (m) => !preferences.hiddenItems.includes(m.id),
    )

    // Mapa de orden según preferences.orderedItems
    const orderMap = new Map<string, number>()
    preferences.orderedItems.forEach((id, idx) => orderMap.set(id, idx))

    return visible.toSorted((a, b) => {
      const aIsFav = preferences.favoriteItems.includes(a.id)
      const bIsFav = preferences.favoriteItems.includes(b.id)

      if (aIsFav && !bIsFav) return -1
      if (!aIsFav && bIsFav) return 1

      const orderA = orderMap.has(a.id) ? orderMap.get(a.id)! : 999
      const orderB = orderMap.has(b.id) ? orderMap.get(b.id)! : 999
      return orderA - orderB
    })
  }, [allowedModules, preferences.hiddenItems, preferences.favoriteItems, preferences.orderedItems])

  const handleContextMenu = (e: React.MouseEvent, module: NavigationModule) => {
    e.preventDefault()
    setContextMenu({
      x: e.clientX,
      y: e.clientY,
      module,
    })
  }

  const handleMoveToStart = (id: string) => {
    const newOrder = [id, ...preferences.orderedItems.filter((i) => i !== id)]
    reorderItems(newOrder)
  }

  const handleOpenNewTab = (route: string) => {
    window.open(route, '_blank')
  }

  const navigationItems = useMemo(
    () => groupNavigationModules(displayModules),
    [displayModules],
  )

  // Solo la ruta más específica queda marcada como activa: así `/logistics/putaway`
  // deja de encenderse cuando el usuario está en `/logistics/putaway/mobile`.
  const activeModuleId = useMemo(
    () => resolveActiveModuleId(location.pathname, displayModules),
    [location.pathname, displayModules],
  )

  if (navigationItems.length === 0) {
    return null
  }

  const isCompactHeight = preferences.density === 'compact'

  return (
    <>
      {/* BARRA DE NAVEGACIÓN FLOTANTE HORIZONTAL */}
      <nav
        className={`fixed bottom-3 sm:bottom-4 left-0 right-0 z-40 pointer-events-none flex justify-center px-2 sm:px-4 transition-all duration-300 ${
          isVisible ? 'translate-y-0 opacity-100' : 'translate-y-20 opacity-0'
        }`}
        aria-label="Navegación principal flotante"
      >
        <div
          className={`pointer-events-auto flex items-center gap-1.5 rounded-[20px] border border-slate-200 bg-white/97 p-1.5 shadow-lg backdrop-blur-sm transition-colors duration-200 ${
            isCompactHeight ? 'h-[52px]' : 'h-[60px]'
          } max-w-[95vw] sm:max-w-[85vw] md:max-w-[80vw] lg:max-w-[75vw] xl:max-w-[1200px] w-auto`}
          role="toolbar"
          aria-label="Módulos del sistema logístico"
        >
          {/* BOTÓN BUSCADOR RÁPIDO (Ctrl+K) */}
          <NavigationTooltip label="Buscar módulo o acción" shortcut="Ctrl+K">
            <button
              id="cmd-palette-trigger"
              type="button"
              onClick={() => setIsCommandPaletteOpen(true)}
              className="flex h-9 w-9 items-center justify-center rounded-xl bg-slate-100 text-slate-500 hover:bg-slate-200 hover:text-slate-800 border border-slate-200 transition-colors flex-shrink-0"
              aria-label="Abrir buscador rápido (Ctrl+K)"
            >
              <LogisticsIcon name="search" size={18} />
            </button>
          </NavigationTooltip>

          <div className="h-5 w-[1px] bg-slate-200 flex-shrink-0" aria-hidden="true" />

          {/* CONTENEDOR CON SCROLL HORIZONTAL DISCRETO */}
          <NavigationScroller alignment={preferences.alignment}>
            {navigationItems.map((navigationItem: NavigationDisplayItem) => {
              if (navigationItem.type === 'group') {
                const { group, modules } = navigationItem
                const isActive = modules.some((item) => item.id === activeModuleId)
                const isOpen = openGroupId === group.id
                const hasFavorite = modules.some((item) => preferences.favoriteItems.includes(item.id))
                const badgeCount = modules.reduce((total, item) => total + (item.badge ?? 0), 0)

                return (
                  <div
                    key={`group-${group.id}`}
                    ref={isOpen ? groupMenuRef : undefined}
                    className="relative flex-shrink-0"
                  >
                    <NavigationTooltip
                      label={`${group.label} · ${modules.length} opciones`}
                      showLabelPermanent={preferences.showLabels}
                    >
                      <button
                        type="button"
                        ref={isOpen ? groupTriggerRef : undefined}
                        onClick={() => setOpenGroupId(isOpen ? null : group.id)}
                        onKeyDown={(event) => {
                          if (event.key !== 'ArrowUp' && event.key !== 'ArrowDown') return
                          event.preventDefault()
                          focusFirstItemRef.current = true
                          setOpenGroupId(group.id)
                        }}
                        aria-label={`${group.ariaLabel} (${modules.length} opciones)`}
                        aria-haspopup="menu"
                        aria-expanded={isOpen}
                        aria-controls={`navigation-group-${group.id}`}
                        className={`group relative flex items-center gap-2 rounded-xl text-xs font-semibold transition-colors duration-200 select-none flex-shrink-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-500 focus-visible:ring-offset-2 ${
                          isCompactHeight ? 'h-9 px-2.5' : 'h-10 px-3'
                        } ${
                          isActive || isOpen
                            ? 'bg-orange-50 text-orange-700 border border-orange-200'
                            : 'text-slate-500 hover:bg-slate-100 hover:text-slate-800 border border-transparent'
                        }`}
                      >
                        <span className="relative flex items-center justify-center">
                          <LogisticsIcon
                            name={group.iconName}
                            size={20}
                            className={isActive ? 'text-orange-600' : 'text-slate-500'}
                          />
                          {hasFavorite && (
                            <span
                              className="absolute -top-1 -right-1 h-2 w-2 rounded-full bg-amber-400 ring-2 ring-white"
                              title="Contiene módulos favoritos"
                            />
                          )}
                          {badgeCount > 0 && (
                            <span className="absolute -top-1.5 -right-2 flex h-4 min-w-4 items-center justify-center rounded-full bg-rose-500 px-1 text-[9px] font-bold text-white shadow-sm">
                              {badgeCount}
                            </span>
                          )}
                        </span>
                        <LogisticsIcon
                          name="chevron"
                          size={13}
                          className={`transition-transform ${isOpen ? '-rotate-90' : 'rotate-90'}`}
                        />
                        {isActive && (
                          <span className="absolute bottom-0.5 left-1/2 -translate-x-1/2 h-0.5 w-4 rounded-full bg-orange-500" />
                        )}
                      </button>
                    </NavigationTooltip>

                    {isOpen && (
                      <div
                        id={`navigation-group-${group.id}`}
                        role="menu"
                        aria-label={group.label}
                        onKeyDown={handleGroupMenuKeyDown}
                        className="absolute bottom-[calc(100%+12px)] left-1/2 z-50 w-[min(21rem,calc(100vw-1rem))] max-w-[calc(100vw-1rem)] -translate-x-1/2 overflow-hidden rounded-2xl border border-slate-200 bg-white p-2 shadow-2xl"
                      >
                        <div className="border-b border-slate-100 px-3 py-2.5">
                          <p className="text-sm font-bold text-slate-900">{group.label}</p>
                          <p className="mt-0.5 text-[11px] leading-4 text-slate-500">{group.description}</p>
                        </div>
                        <div className="max-h-[min(24rem,60vh)] overflow-y-auto py-1">
                          {modules.map((item) => {
                            const childActive = item.id === activeModuleId
                            return (
                              <Link
                                key={item.id}
                                to={item.route}
                                role="menuitem"
                                aria-current={childActive ? 'page' : undefined}
                                onContextMenu={(event) => handleContextMenu(event, item)}
                                className={`flex min-h-11 items-center gap-3 rounded-xl px-3 py-2.5 no-underline transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-500 ${
                                  childActive
                                    ? 'bg-orange-50 text-orange-800'
                                    : 'text-slate-700 hover:bg-slate-50 hover:text-slate-950'
                                }`}
                              >
                                <span className={`flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg ${childActive ? 'bg-orange-100 text-orange-700' : 'bg-slate-100 text-slate-500'}`}>
                                  <LogisticsIcon name={item.iconName} size={17} />
                                </span>
                                <span className="min-w-0 flex-1">
                                  <span className="block truncate text-xs font-semibold">{item.label}</span>
                                  <span className="block truncate text-[10px] text-slate-400">
                                    {item.description ?? item.route}
                                  </span>
                                </span>
                                {preferences.favoriteItems.includes(item.id) && (
                                  <LogisticsIcon name="star" size={12} className="text-amber-400" />
                                )}
                                <LogisticsIcon name="chevron" size={14} className="text-slate-300" />
                              </Link>
                            )
                          })}
                        </div>
                      </div>
                    )}
                  </div>
                )
              }

              const item = navigationItem.module
              const isActive = item.id === activeModuleId
              const isFav = preferences.favoriteItems.includes(item.id)

              return (
                <NavigationTooltip
                  key={item.id}
                  label={item.label}
                  showLabelPermanent={preferences.showLabels}
                >
                  <Link
                    to={item.route}
                    aria-label={item.label}
                    aria-current={isActive ? 'page' : undefined}
                    className={`group relative flex items-center gap-2 rounded-xl text-xs font-semibold no-underline transition-colors duration-200 select-none flex-shrink-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-500 focus-visible:ring-offset-2 ${
                      isCompactHeight ? 'h-9 px-2.5' : 'h-10 px-3'
                    } ${
                      isActive
                        ? 'bg-orange-50 text-orange-700 border border-orange-200'
                        : 'text-slate-500 hover:bg-slate-100 hover:text-slate-800 border border-transparent'
                    }`}
                    onContextMenu={(e) => handleContextMenu(e, item)}
                  >
                    <span className="relative flex items-center justify-center">
                      <LogisticsIcon
                        name={item.iconName}
                        size={20}
                        className={isActive ? 'text-orange-600' : 'text-slate-500'}
                      />
                      {/* Badge pequeño de indicador de estado/favorito */}
                      {isFav && (
                        <span
                          className="absolute -top-1 -right-1 h-2 w-2 rounded-full bg-amber-400 ring-2 ring-white"
                          title="Módulo Favorito"
                        />
                      )}
                      {item.badge && item.badge > 0 && (
                        <span className="absolute -top-1.5 -right-2 flex h-4 min-w-4 items-center justify-center rounded-full bg-rose-500 px-1 text-[9px] font-bold text-white shadow-sm">
                          {item.badge}
                        </span>
                      )}
                    </span>

                    {/* Solo icono en la barra principal; el nombre se despliega en el tooltip al pasar el cursor */}

                    {/* Indicador inferior fino de módulo activo */}
                    {isActive && (
                      <span className="absolute bottom-0.5 left-1/2 -translate-x-1/2 h-0.5 w-4 rounded-full bg-orange-500" />
                    )}
                  </Link>
                </NavigationTooltip>
              )
            })}
          </NavigationScroller>

          <div className="h-5 w-[1px] bg-slate-200 flex-shrink-0" aria-hidden="true" />

          {/* BOTÓN DE CONFIGURACIÓN DE BARRA */}
          <NavigationTooltip label="Configurar barra de navegación">
            <button
              type="button"
              onClick={() => setIsSettingsOpen(true)}
              className={`flex h-9 w-9 items-center justify-center rounded-xl transition-colors flex-shrink-0 ${
                isSettingsOpen
                  ? 'bg-orange-50 text-orange-700 border border-orange-200'
                  : 'bg-slate-100 text-slate-500 hover:bg-slate-200 hover:text-slate-800 border border-slate-200'
              }`}
              aria-label="Abrir opciones de personalización de la barra"
              aria-expanded={isSettingsOpen}
            >
              <LogisticsIcon name="more" size={18} />
            </button>
          </NavigationTooltip>
        </div>
      </nav>

      {/* MENÚ CONTEXTUAL AL HACER CLIC DERECHO */}
      {contextMenu && (
        <NavigationContextMenu
          x={contextMenu.x}
          y={contextMenu.y}
          module={contextMenu.module}
          isFavorite={preferences.favoriteItems.includes(contextMenu.module.id)}
          onClose={() => setContextMenu(null)}
          onToggleFavorite={toggleFavorite}
          onToggleHide={toggleHide}
          onMoveToStart={handleMoveToStart}
          onOpenNewTab={handleOpenNewTab}
          onShowInfo={(mod) => setInfoModalModule(mod)}
        />
      )}

      {/* PALETA DE COMANDOS (Ctrl + K) */}
      <CommandPalette
        isOpen={isCommandPaletteOpen}
        onClose={() => setIsCommandPaletteOpen(false)}
        onOpenSettings={() => setIsSettingsOpen(true)}
        modules={allowedModules}
      />

      {/* PANEL DE CONFIGURACIÓN DE LA BARRA */}
      <NavigationSettings
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        preferences={preferences}
        allModules={allowedModules}
        onUpdatePreferences={updatePreferences}
        onResetPreferences={resetPreferences}
        onToggleFavorite={toggleFavorite}
        onToggleHide={toggleHide}
        onReorder={reorderItems}
      />

      {/* MODAL DE INFORMACIÓN DEL MÓDULO */}
      {infoModalModule && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-sm"
          onClick={() => setInfoModalModule(null)}
        >
          <div
            className="w-full max-w-sm rounded-2xl border border-slate-200 bg-white p-5 shadow-2xl text-slate-800 space-y-3 text-xs"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <div className="flex items-center gap-2 font-bold text-sm text-orange-600">
                <LogisticsIcon name={infoModalModule.iconName} size={18} />
                <span>{infoModalModule.label}</span>
              </div>
              <button
                type="button"
                onClick={() => setInfoModalModule(null)}
                className="text-slate-400 hover:text-slate-700"
                aria-label="Cerrar"
              >
                <LogisticsIcon name="x" size={16} />
              </button>
            </div>
            <div className="space-y-1 text-slate-600">
              <p><strong className="text-slate-700">Ruta:</strong> <code className="bg-slate-100 px-1 rounded text-orange-700">{infoModalModule.route}</code></p>
              <p><strong className="text-slate-700">Categoría:</strong> <span className="capitalize">{infoModalModule.category || 'General'}</span></p>
              <p><strong className="text-slate-700">Permiso Backend:</strong> {infoModalModule.permission || 'Ninguno (Acceso estándar)'}</p>
            </div>
            <div className="pt-2 flex justify-end">
              <button
                type="button"
                onClick={() => {
                  navigate(infoModalModule.route)
                  setInfoModalModule(null)
                }}
                className="px-3 py-1.5 rounded-xl bg-orange-500 hover:bg-orange-600 text-white font-semibold"
              >
                Ir al módulo
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
