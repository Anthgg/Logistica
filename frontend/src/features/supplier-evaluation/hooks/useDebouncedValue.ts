import { useEffect, useRef, useState } from 'react'

/**
 * Devuelve un valor con debounce. Útil para cajas de búsqueda.
 * No almacena valores sensibles: solo texto de búsqueda ingresado por el usuario.
 */
export function useDebouncedValue<T>(value: T, delayMs: number): T {
  const [debounced, setDebounced] = useState<T>(value)
  const timeoutRef = useRef<number | null>(null)

  useEffect(() => {
    if (timeoutRef.current !== null) {
      window.clearTimeout(timeoutRef.current)
    }
    timeoutRef.current = window.setTimeout(() => {
      setDebounced(value)
    }, delayMs)

    return () => {
      if (timeoutRef.current !== null) {
        window.clearTimeout(timeoutRef.current)
      }
    }
  }, [value, delayMs])

  return debounced
}