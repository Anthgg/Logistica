
interface NavigationRevealHandleProps {
  onReveal: () => void
  isWarning?: boolean
}

export function NavigationRevealHandle({ onReveal, isWarning = false }: NavigationRevealHandleProps) {
  return (
    <div className="fixed bottom-2 left-1/2 -translate-x-1/2 z-40 pointer-events-auto">
      <button
        type="button"
        onClick={onReveal}
        onMouseEnter={onReveal}
        className={`group flex items-center gap-2 px-3.5 py-1.5 rounded-full border shadow-xl backdrop-blur-md text-xs font-semibold transition-colors duration-300 hover:scale-105 ${
          isWarning
            ? 'border-amber-500/50 bg-amber-950/80 text-amber-300 animate-pulse'
            : 'border-slate-700/80 bg-slate-900/90 text-slate-300 hover:bg-slate-800 hover:text-white hover:border-slate-600'
        }`}
        title="Mostrar barra de navegación (Alt + M)"
        aria-label="Abrir barra de navegación"
      >
        <span className="flex h-2 w-2 rounded-full bg-orange-500 animate-ping" />
        <svg className="h-4 w-4 transform group-hover:-translate-y-0.5 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
        </svg>
        <span className="text-[11px]">Navegación</span>
        <kbd className="hidden sm:inline-block text-[9px] font-mono opacity-60 bg-slate-800 px-1 rounded">Alt+M</kbd>
      </button>
    </div>
  )
}
