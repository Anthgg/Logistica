interface HistoryItem {
  id: string
  event_type: string
  action_description: string
  user_name: string
  created_at: string
}

interface Props {
  history: HistoryItem[]
}

export function VehicleHistoryTimeline({ history }: Props) {
  if (!history || history.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-slate-200 p-6 text-center text-xs text-slate-400">
        Sin historial de eventos registrados.
      </div>
    )
  }

  return (
    <div className="space-y-4 text-xs">
      <h4 className="font-bold uppercase tracking-wider text-slate-500 text-xs">
        Línea de Tiempo del Vehículo ({history.length})
      </h4>

      <div className="relative pl-6 space-y-4 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
        {history.map((item) => (
          <div key={item.id} className="relative flex flex-col gap-1 rounded-xl border border-slate-200 bg-white p-3.5 shadow-xs">
            <span className="absolute -left-6 top-3 h-3 w-3 rounded-full border-2 border-white bg-indigo-600 shadow-xs" />
            <div className="flex items-center justify-between text-[11px] text-slate-400">
              <span className="font-mono font-bold text-slate-700">{item.event_type}</span>
              <span>{new Date(item.created_at).toLocaleString('es-PE')}</span>
            </div>
            <p className="text-slate-800 font-medium">{item.action_description}</p>
            <p className="text-[10px] text-slate-400">Ejecutado por: {item.user_name}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
