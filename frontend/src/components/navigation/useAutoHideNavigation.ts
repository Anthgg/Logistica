import { useCallback, useEffect, useRef, useState } from 'react'

interface UseAutoHideNavigationOptions {
  autoHideEnabled: boolean
  autoHideDelay: number // segundos
  isSettingsOpen: boolean
  isCommandPaletteOpen: boolean
  isContextMenuOpen: boolean
}

export function useAutoHideNavigation({
  autoHideEnabled,
  autoHideDelay,
  isSettingsOpen,
  isCommandPaletteOpen,
  isContextMenuOpen,
}: UseAutoHideNavigationOptions) {
  const [isHidden, setIsHidden] = useState(false)
  const [isWarning, setIsWarning] = useState(false)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const warningTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const hasLock = isSettingsOpen || isCommandPaletteOpen || isContextMenuOpen

  const resetTimer = useCallback(() => {
    if (timerRef.current) clearTimeout(timerRef.current)
    if (warningTimerRef.current) clearTimeout(warningTimerRef.current)

    setIsHidden(false)
    setIsWarning(false)

    if (!autoHideEnabled || autoHideDelay <= 0 || hasLock) {
      return
    }

    const warningMs = Math.max(0, (autoHideDelay - 10) * 1000)
    const hideMs = autoHideDelay * 1000

    warningTimerRef.current = setTimeout(() => {
      setIsWarning(true)
    }, warningMs)

    timerRef.current = setTimeout(() => {
      setIsHidden(true)
      setIsWarning(false)
    }, hideMs)
  }, [autoHideEnabled, autoHideDelay, hasLock])

  useEffect(() => {
    const events = ['mousemove', 'mousedown', 'keydown', 'touchstart', 'scroll']
    const handleUserActivity = () => {
      resetTimer()
    }

    events.forEach((event) => window.addEventListener(event, handleUserActivity, { passive: true }))
    resetTimer()

    return () => {
      events.forEach((event) => window.removeEventListener(event, handleUserActivity))
      if (timerRef.current) clearTimeout(timerRef.current)
      if (warningTimerRef.current) clearTimeout(warningTimerRef.current)
    }
  }, [resetTimer])

  // Atajo Alt + M para alternar visibilidad
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.altKey && (e.key === 'm' || e.key === 'M')) {
        e.preventDefault()
        setIsHidden((prev) => !prev)
        resetTimer()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [resetTimer])

  // Detectar cursor en la parte inferior de la pantalla (zona caliente de 40px)
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (window.innerHeight - e.clientY < 40) {
        if (isHidden) {
          setIsHidden(false)
          resetTimer()
        }
      }
    }
    window.addEventListener('mousemove', handleMouseMove)
    return () => window.removeEventListener('mousemove', handleMouseMove)
  }, [isHidden, resetTimer])

  return {
    isHidden: autoHideEnabled && !hasLock && isHidden,
    isWarning: autoHideEnabled && !hasLock && isWarning,
    resetTimer,
    showBar: () => {
      setIsHidden(false)
      resetTimer()
    },
  }
}
