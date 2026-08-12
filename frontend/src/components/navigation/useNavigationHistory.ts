import { useEffect, useState } from 'react'

const HISTORY_KEY = 'andeslog_nav_history_v1'
const MAX_HISTORY = 3

export function useNavigationHistory(currentPath: string, currentModuleId?: string) {
  const [recentIds, setRecentIds] = useState<string[]>(() => {
    if (typeof window === 'undefined') return []
    try {
      const stored = localStorage.getItem(HISTORY_KEY)
      return stored ? JSON.parse(stored) : []
    } catch {
      return []
    }
  })

  useEffect(() => {
    if (!currentModuleId) return
    setRecentIds((prev) => {
      const filtered = prev.filter((id) => id !== currentModuleId)
      return [currentModuleId, ...filtered].slice(0, MAX_HISTORY)
    })
  }, [currentPath, currentModuleId])

  // Persistencia fuera del updater (sin side effects en la función de estado)
  useEffect(() => {
    if (recentIds.length === 0) return
    try {
      localStorage.setItem(HISTORY_KEY, JSON.stringify(recentIds))
    } catch (e) {
      console.warn('Error guardando historial de navegación:', e)
    }
  }, [recentIds])

  return { recentIds }
}
