import { LogisticsIcon } from '../common/LogisticsIcon'

interface Props {
  originAddress: string
  originDistrict: string
  destinationAddress: string
  destinationDistrict: string
}

export function ShipmentRoute({
  originAddress,
  originDistrict,
  destinationAddress,
  destinationDistrict,
}: Props) {
  return (
    <div className="rounded-xl border border-slate-200/80 bg-slate-50/70 p-3.5 mb-4">
      <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-2">
        TRAYECTORIA DE LA RUTA
      </p>

      <div className="flex flex-col gap-3 relative pl-1">
        {/* Origen */}
        <div className="flex items-start gap-3 relative z-10">
          <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-blue-100 text-blue-700 mt-0.5">
            <span className="h-2 w-2 rounded-full bg-blue-600" />
          </span>
          <div>
            <span className="block text-[10px] font-semibold text-slate-500 uppercase tracking-wide">
              Origen
            </span>
            <p className="text-xs font-semibold text-slate-900 leading-tight">
              {originAddress}
            </p>
            <span className="text-[11px] text-slate-500">{originDistrict}</span>
          </div>
        </div>

        {/* Línea conectora */}
        <div
          className="absolute left-[11px] top-6 bottom-6 w-0.5 bg-slate-300 z-0"
          aria-hidden="true"
        />

        {/* Destino */}
        <div className="flex items-start gap-3 relative z-10">
          <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-amber-100 text-amber-700 mt-0.5">
            <LogisticsIcon name="location" size={13} className="text-amber-700" />
          </span>
          <div>
            <span className="block text-[10px] font-semibold text-slate-500 uppercase tracking-wide">
              Destino
            </span>
            <p className="text-xs font-semibold text-slate-900 leading-tight">
              {destinationAddress}
            </p>
            <span className="text-[11px] text-slate-500">{destinationDistrict}</span>
          </div>
        </div>
      </div>
    </div>
  )
}
