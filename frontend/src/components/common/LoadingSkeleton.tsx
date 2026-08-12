export function LoadingSkeleton({
  label = 'Cargando información operativa…',
  rows = 4,
}: {
  label?: string
  rows?: number
}) {
  return (
    <div className="flex flex-col gap-3 py-6" role="status" aria-live="polite">
      <span className="sr-only">{label}</span>
      {/* Header skeleton */}
      <div className="flex gap-3 mb-1">
        <span className="skeleton-shimmer h-6 w-40 rounded-md" />
        <span className="skeleton-shimmer h-6 w-24 rounded-md" />
      </div>
      {/* KPI grid skeleton */}
      <div className="mb-1 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        {Array.from({ length: 6 }, (_, i) => (
          <span key={i} className="skeleton-shimmer h-[110px] rounded-[10px]" />
        ))}
      </div>
      {/* Content skeleton rows */}
      <div className="flex flex-col gap-2">
        {Array.from({ length: rows }, (_, index) => (
          <span key={`skeleton-${index}`} className="skeleton-shimmer h-[14px] rounded-md" style={{ width: `${85 - index * 8}%` }} />
        ))}
      </div>
    </div>
  )
}
