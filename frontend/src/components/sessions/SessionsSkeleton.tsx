export function SessionsSkeleton() {
  return (
    <div className="flex flex-col gap-4">
      {/* Header skeleton */}
      <div className="flex items-center justify-between border-b border-border-subtle pb-3">
        <div className="flex flex-col gap-2">
          <div className="skeleton h-2.5 w-24 rounded-full" />
          <div className="skeleton h-5 w-48 rounded-full" />
          <div className="skeleton h-3 w-72 rounded-full" />
        </div>
        <div className="flex gap-2">
          <div className="skeleton h-8 w-24 rounded-lg" />
          <div className="skeleton h-8 w-32 rounded-lg" />
        </div>
      </div>

      {/* Summary skeleton */}
      <div className="grid grid-cols-3 gap-2.5">
        {[0, 1, 2].map((i) => (
          <div key={i} className="flex items-center gap-2.5 rounded-lg border border-border-subtle bg-white px-3 py-2.5">
            <div className="skeleton h-8 w-8 rounded-md" />
            <div className="flex flex-col gap-1.5">
              <div className="skeleton h-3.5 w-12 rounded-full" />
              <div className="skeleton h-2.5 w-20 rounded-full" />
            </div>
          </div>
        ))}
      </div>

      {/* Current session skeleton */}
      <div className="flex flex-col gap-2">
        <div className="skeleton h-4 w-32 rounded-full" />
        <div className="skeleton h-28 w-full rounded-xl" />
      </div>

      {/* Other sessions skeleton */}
      <div className="flex flex-col gap-1.5">
        <div className="skeleton h-4 w-48 rounded-full" />
        {[0, 1].map((i) => (
          <div key={i} className="skeleton h-14 w-full rounded-lg" />
        ))}
      </div>
    </div>
  )
}