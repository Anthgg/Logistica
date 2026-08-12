import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Alert } from '../../../components/common/Alert'
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton'
import { PageHeader } from '../../../components/common/PageHeader'
import { getEvaluationDetail } from '../api/continuous-auth-api'
import { EvaluationDetailPanel } from '../components/EvaluationDetailPanel'
import { RiskTimeline } from '../components/RiskTimeline'
import type { AdminEvaluationDetail } from '../types/continuous-auth'
import { getContinuousAuthErrorMessage } from '../utils/continuous-auth-errors'

export function ContinuousAuthEvaluationDetailPage() {
  const { evaluationId } = useParams()
  const [detail, setDetail] = useState<AdminEvaluationDetail | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const controller = new AbortController()

    if (!evaluationId) {
      setError('El identificador de evaluación no es válido.')
      setIsLoading(false)
      return () => controller.abort()
    }

    setIsLoading(true)
    getEvaluationDetail(evaluationId, controller.signal)
      .then(setDetail)
      .catch((caughtError: unknown) => {
        if (!controller.signal.aborted) {
          setError(getContinuousAuthErrorMessage(caughtError))
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setIsLoading(false)
        }
      })

    return () => controller.abort()
  }, [evaluationId])

  return (
    <div className="space-y-5">
      <PageHeader
        eyebrow="Administración"
        title="Detalle de evaluación"
        description="Resumen autorizado de la decisión ya calculada por el backend."
        actions={
          <Link
            to="/admin/continuous-auth/evaluations"
            className="inline-flex min-h-11 items-center rounded-lg border border-slate-300 bg-white px-4 text-xs font-bold text-slate-700 no-underline"
          >
            Volver a evaluaciones
          </Link>
        }
      />
      {isLoading && (
        <LoadingSkeleton rows={7} label="Cargando detalle" />
      )}
      {error && (
        <Alert variant="error" title="No se cargó el detalle">
          {error}
        </Alert>
      )}
      {detail && (
        <>
          <EvaluationDetailPanel detail={detail} />
          <RiskTimeline detail={detail} />
        </>
      )}
    </div>
  )
}
