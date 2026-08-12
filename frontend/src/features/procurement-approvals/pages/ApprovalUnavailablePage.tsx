import { useNavigate } from 'react-router-dom'

export function ApprovalUnavailablePage({
  title,
  description,
}: {
  title: string
  description: string
}) {
  const navigate = useNavigate()

  return (
    <section className="space-y-4" aria-labelledby="approval-gap-title">
      <header>
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#1F4E6D]">
          Fase 035 · Contrato parcial
        </p>
        <h1
          id="approval-gap-title"
          className="mt-1 text-xl font-bold text-slate-950"
        >
          {title}
        </h1>
      </header>
      <div className="rounded-2xl border border-amber-200 bg-amber-50 p-5">
        <p className="max-w-3xl text-sm text-amber-900">{description}</p>
        <p className="mt-3 text-xs text-amber-800">
          No se muestran datos simulados ni se fabrican rutas REST.
        </p>
      </div>
      <button
        type="button"
        onClick={() => navigate('/logistics/purchasing/approvals')}
        className="min-h-11 rounded-lg border border-slate-200 px-4 text-sm font-semibold text-slate-700"
      >
        Volver a aprobaciones
      </button>
    </section>
  )
}
