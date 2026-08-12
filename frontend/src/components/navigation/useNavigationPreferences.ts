import { useCallback, useEffect, useState } from 'react'
import {
  DEFAULT_PREFERENCES,
  type NavigationPreferences,
} from './nav-modules.config'

const STORAGE_KEY = 'andeslog_navigation_preferences_v3'
const OLD_STORAGE_KEY = 'andeslog_navigation_preferences_v2'

function mergeNavigationPreferences(parsed: Partial<NavigationPreferences>): NavigationPreferences {
  const currentOrdered = Array.isArray(parsed.orderedItems) ? parsed.orderedItems : []
  const missingDefaults = DEFAULT_PREFERENCES.orderedItems.filter(
    (id) => !currentOrdered.includes(id),
  )
  const mergedOrdered = [...currentOrdered, ...missingDefaults]

  return {
    ...DEFAULT_PREFERENCES,
    ...parsed,
    orderedItems: mergedOrdered,
  }
}

export function useNavigationPreferences() {
  const [preferences, setPreferencesState] = useState<NavigationPreferences>(() => {
    if (typeof window === 'undefined') return DEFAULT_PREFERENCES
    try {
      let stored = localStorage.getItem(STORAGE_KEY)
      if (!stored) {
        stored = localStorage.getItem(OLD_STORAGE_KEY)
      }
      if (!stored) return DEFAULT_PREFERENCES
      const parsed = JSON.parse(stored)
      return mergeNavigationPreferences(parsed)
    } catch {
      return DEFAULT_PREFERENCES
    }
  })

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(preferences))
    } catch (e) {
      console.warn('Error guardando preferencias de navegación:', e)
    }
  }, [preferences])

  const updatePreferences = useCallback(
    (updater: Partial<NavigationPreferences> | ((prev: NavigationPreferences) => NavigationPreferences)) => {
      setPreferencesState((prev) => {
        const next = typeof updater === 'function' ? updater(prev) : { ...prev, ...updater }
        return next
      })
    },
    [],
  )

  const toggleFavorite = useCallback((id: string) => {
    setPreferencesState((prev) => {
      const isFav = prev.favoriteItems.includes(id)
      const nextFavs = isFav
        ? prev.favoriteItems.filter((item) => item !== id)
        : [...prev.favoriteItems, id]
      return { ...prev, favoriteItems: nextFavs }
    })
  }, [])

  const toggleHide = useCallback((id: string) => {
    setPreferencesState((prev) => {
      const isHidden = prev.hiddenItems.includes(id)
      const nextHidden = isHidden
        ? prev.hiddenItems.filter((item) => item !== id)
        : [...prev.hiddenItems, id]
      return { ...prev, hiddenItems: nextHidden }
    })
  }, [])

  const resetPreferences = useCallback(() => {
    setPreferencesState(DEFAULT_PREFERENCES)
  }, [])

  const reorderItems = useCallback((newOrder: string[]) => {
    setPreferencesState((prev) => ({ ...prev, orderedItems: newOrder }))
  }, [])

  return {
    preferences,
    updatePreferences,
    toggleFavorite,
    toggleHide,
    resetPreferences,
    reorderItems,
  }
}
