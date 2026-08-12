import React, { useEffect, useRef, useState } from 'react'

interface NavigationScrollerProps {
  children: React.ReactNode
  alignment?: 'left' | 'center' | 'right'
}

export function NavigationScroller({ children, alignment = 'center' }: NavigationScrollerProps) {
  const scrollRef = useRef<HTMLDivElement>(null)
  const [canScrollLeft, setCanScrollLeft] = useState(false)
  const [canScrollRight, setCanScrollRight] = useState(false)

  const checkScrollability = () => {
    const el = scrollRef.current
    if (!el) return
    const isScrollableLeft = el.scrollLeft > 2
    const isScrollableRight = el.scrollLeft < el.scrollWidth - el.clientWidth - 2
    setCanScrollLeft(isScrollableLeft)
    setCanScrollRight(isScrollableRight)
  }

  useEffect(() => {
    const el = scrollRef.current
    if (!el) return

    checkScrollability()
    const handleResize = () => checkScrollability()

    // Manejar scroll horizontal con rueda del ratón
    const handleWheel = (e: WheelEvent) => {
      if (e.deltaY !== 0) {
        e.preventDefault()
        el.scrollLeft += e.deltaY * 0.8
      }
    }

    el.addEventListener('scroll', checkScrollability, { passive: true })
    el.addEventListener('wheel', handleWheel, { passive: false })
    window.addEventListener('resize', handleResize)

    return () => {
      el.removeEventListener('scroll', checkScrollability)
      el.removeEventListener('wheel', handleWheel)
      window.removeEventListener('resize', handleResize)
    }
  }, [children])

  const scrollBy = (amount: number) => {
    if (scrollRef.current) {
      scrollRef.current.scrollBy({ left: amount, behavior: 'smooth' })
    }
  }

  const justifyClass =
    alignment === 'left'
      ? 'justify-start'
      : alignment === 'right'
      ? 'justify-end'
      : 'justify-center'

  return (
    <div className="relative flex items-center min-w-0 max-w-full group/scroller">
      {/* Botón flecha izquierda */}
      {canScrollLeft && (
        <button
          type="button"
          onClick={() => scrollBy(-180)}
          className="absolute left-1 z-20 flex h-7 w-7 items-center justify-center rounded-full bg-slate-800/90 text-slate-300 shadow-md border border-slate-700/80 hover:bg-slate-700 hover:text-white transition-colors backdrop-blur-sm"
          aria-label="Desplazar a la izquierda"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>
      )}

      {/* Contenedor desplazable sin scrollbar nativo */}
      <div
        ref={scrollRef}
        className={`flex items-center gap-1.5 overflow-x-auto scrollbar-none py-1 px-2 ${justifyClass} w-full`}
        style={{
          scrollbarWidth: 'none',
          msOverflowStyle: 'none',
          WebkitOverflowScrolling: 'touch',
        }}
      >
        {children}
      </div>

      {/* Botón flecha derecha */}
      {canScrollRight && (
        <button
          type="button"
          onClick={() => scrollBy(180)}
          className="absolute right-1 z-20 flex h-7 w-7 items-center justify-center rounded-full bg-slate-800/90 text-slate-300 shadow-md border border-slate-700/80 hover:bg-slate-700 hover:text-white transition-colors backdrop-blur-sm"
          aria-label="Desplazar a la derecha"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      )}
    </div>
  )
}
