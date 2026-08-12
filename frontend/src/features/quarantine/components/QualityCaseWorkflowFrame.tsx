import type { ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '../../../components/common/Button'
import { PageHeader } from '../../../components/common/PageHeader'
import type { QualityQuarantineCaseDetailApi } from '../types/phase042-api'
import { QualityQuarantinePhaseNav } from './QualityQuarantinePhaseNav'

interface QualityCaseWorkflowFrameProps {
  title: string
  description: string
  caseData: QualityQuarantineCaseDetailApi
  children: ReactNode
}

function humanize(value: string | null): string {
  return value ? value.replaceAll('_', ' ').toLowerCase() : 'Pendiente'
}

export function QualityCaseWorkflowFrame({
  title,
  description,
  caseData,
  children,
}: QualityCaseWorkflowFrameProps) {
  const navigate = useNavigate()

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Fase 042 · Expediente de calidad"
        title={title}
        description={description}
        actions={
          <Button
            size="small"
            variant="secondary"
            onClick={() => navigate(`/logistics/quality/quarantine/${caseData.id}`)}
          >
            Volver al caso
          </Button>
        }
      />

      <QualityQuarantinePhaseNav />

      <section className="overflow-hidden rounded-3xl border border-slate-200 bg-slate-950 text-white shadow-sm">
        <div className="grid gap-6 p-6 lg:grid-cols-[1.2fr_0.8fr] lg:p-8">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-orange-300">
              {caseData.quarantine_code}
            </p>
            <h2 className="mt-3 text-2xl font-bold sm:text-3xl">
              {humanize(caseData.quarantine_reason) || 'Control de inventario segregado'}
            </h2>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-300">
              Producto {caseData.product_id}. El expediente conserva por separado inspección,
              decisión y ejecución para mantener la trazabilidad operativa.
            </p>
          </div>
          <dl className="grid grid-cols-2 gap-3 text-sm">
            {[
              ['Estado', humanize(caseData.status)],
              ['Severidad', humanize(caseData.severity)],
              ['Resultado', humanize(caseData.quality_result)],
              ['Liberación', humanize(caseData.release_status)],
            ].map(([label, value]) => (
              <div key={label} className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <dt className="text-xs text-slate-400">{label}</dt>
                <dd className="mt-2 font-semibold capitalize text-white">{value}</dd>
              </div>
            ))}
          </dl>
        </div>
      </section>

      {children}
    </div>
  )
}
