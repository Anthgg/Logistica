import { LogisticsIcon } from '../../../components/common/LogisticsIcon'

export function DegradedModeAlert({
  reason,
}: {
  reason?: string | null
}) {
  const title = reason?.toLowerCase().includes('modelo')
    ? 'Modelos no disponibles'
    : 'Autenticación degradada'

  return (
    <div
      className="flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 p-4 text-amber-950"
      role="status"
    >
      <LogisticsIcon
        name="alert"
        size={20}
        className="mt-0.5 shrink-0"
      />
      <div>
        <p className="font-bold">{title}</p>
        <p className="mt-1 text-sm">
          La autenticación continua funciona de manera limitada. Algunas
          verificaciones todavía no están disponibles.
        </p>
        {reason && <p className="mt-1 text-xs opacity-80">{reason}</p>}
      </div>
    </div>
  )
}
