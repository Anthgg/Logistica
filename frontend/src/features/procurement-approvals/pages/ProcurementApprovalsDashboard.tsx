import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { procurementApprovalsApi } from '../api/procurementApprovalsApi'

export function ProcurementApprovalsDashboard() {
  const navigate = useNavigate()
  const authorization = useLogisticsPermissions()
  const [pendingCount, setPendingCount] = useState<number | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  useEffect(() => {
    if (!authorization.userId) {
      setPendingCount(null)
      setErrorMessage('No existe user_id en el contexto de autorización.')
      return
    }

    let active = true
    procurementApprovalsApi
      .listMyPendingAssignments(authorization.userId)
      .then((items) => {
        if (active) {
          setPendingCount(items.length)
          setErrorMessage(null)
        }
      })
      .catch((error: unknown) => {
        if (active) {
          setPendingCount(null)
          setErrorMessage(
            error instanceof Error
              ? error.message
              : 'No se pudo consultar el resumen.',
          )
        }
      })

    return () => {
      active = false
    }
  }, [authorization.userId])

  return (
    <section className="space-y-5" aria-labelledby="approval-dashboard-title">
      <header>
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#1F4E6D]">
          Compras · Fase 035
        </p>
        <h1
          id="approval-dashboard-title"
          className="mt-1 text-xl font-bold text-slate-950"
        >
          Aprobaciones de compras
        </h1>
        <p className="mt-1 max-w-2xl text-sm text-slate-500">
          Panel contractual del motor de aprobaciones. Los conteos no se
          calculan desde órdenes visibles.
        </p>
      </header>

      {errorMessage && (
        <div
          role="alert"
          className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-800"
        >
          {errorMessage}
        </div>
      )}

      <div className="grid gap-3 md:grid-cols-3">
        <button
          type="button"
          onClick={() =>
            navigate('/logistics/purchasing/approvals/inbox')
          }
          className="min-h-32 rounded-2xl border border-slate-200 bg-white p-4 text-left shadow-sm transition hover:border-[#1F4E6D]/30 hover:shadow-md"
        >
          <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Pendientes de mi aprobación
          </span>
          <strong className="mt-2 block text-3xl text-slate-950">
            {pendingCount ?? '—'}
          </strong>
          <span className="mt-2 block text-xs text-slate-500">
            Conteo de la respuesta real de `my-pending`.
          </span>
        </button>

        <button
          type="button"
          onClick={() =>
            navigate('/logistics/purchasing/approval-policies')
          }
          className="min-h-32 rounded-2xl border border-slate-200 bg-white p-4 text-left shadow-sm transition hover:border-[#1F4E6D]/30 hover:shadow-md"
        >
          <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Políticas
          </span>
          <strong className="mt-2 block text-lg text-slate-950">
            Configuración
          </strong>
          <span className="mt-2 block text-xs text-slate-500">
            Listar, crear y consultar políticas publicadas.
          </span>
        </button>

        <div className="min-h-32 rounded-2xl border border-amber-200 bg-amber-50 p-4">
          <span className="text-xs font-semibold uppercase tracking-wide text-amber-700">
            Métricas pendientes
          </span>
          <strong className="mt-2 block text-lg text-amber-950">
            Sin endpoint de dashboard
          </strong>
          <span className="mt-2 block text-xs text-amber-800">
            SLA, vencidas, delegadas, escaladas e integridad no se inventan con
            la página visible.
          </span>
        </div>
      </div>
    </section>
  )
}
