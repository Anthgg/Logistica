import { useCallback, useEffect, useState } from 'react'
import { vehicleVerificationsApi } from '../api/vehicle-verifications-api'
import { LoadingSkeleton } from '../components/common/LoadingSkeleton'
import { PageHeader } from '../components/common/PageHeader'
import type { VehicleVerificationReviewTask } from '../types/vehicle-verifications'

export function VehicleVerificationReviewTasksPage() {
  const [tasks, setTasks] = useState<VehicleVerificationReviewTask[]>([])
  const [loading, setLoading] = useState(true)

  const loadTasks = useCallback(async () => {
    setLoading(true)
    try {
      const res = await vehicleVerificationsApi.listReviewTasks()
      setTasks(res)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadTasks()
  }, [loadTasks])

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <PageHeader
        title="Cola de Tareas de Revisión Manual"
        description="Gestión de asignaciones de verificación asistida y revisiones documentales pendientes."
      />

      {loading ? (
        <LoadingSkeleton rows={6} />
      ) : tasks.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-12 text-center text-slate-500 text-xs">
          No hay tareas de revisión pendientes.
        </div>
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-xs text-xs">
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50 text-slate-600">
              <tr>
                <th className="px-4 py-3 text-left font-semibold">Placa</th>
                <th className="px-4 py-3 text-left font-semibold">Dominio</th>
                <th className="px-4 py-3 text-left font-semibold">Razón / Motivo</th>
                <th className="px-4 py-3 text-center font-semibold">Prioridad</th>
                <th className="px-4 py-3 text-left font-semibold">Vencimiento</th>
                <th className="px-4 py-3 text-center font-semibold">Estado</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {tasks.map((t) => (
                <tr key={t.id} className="hover:bg-slate-50">
                  <td className="px-4 py-3 font-mono font-bold text-slate-900">{t.plate_number}</td>
                  <td className="px-4 py-3 font-bold text-slate-800">{t.domain}</td>
                  <td className="px-4 py-3 text-slate-700">{t.reason}</td>
                  <td className="px-4 py-3 text-center">
                    <span className="rounded bg-amber-100 px-2 py-0.5 font-bold text-[10px] text-amber-800">
                      {t.priority}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-600">{new Date(t.due_date).toLocaleDateString('es-PE')}</td>
                  <td className="px-4 py-3 text-center">
                    <span className="rounded bg-slate-100 px-2 py-0.5 text-[10px] font-bold text-slate-700">
                      {t.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
