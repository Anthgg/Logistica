import { useCallback, useEffect, useState } from 'react'
import { Alert } from '../../../components/common/Alert'
import { Button } from '../../../components/common/Button'
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton'
import { PageHeader } from '../../../components/common/PageHeader'
import { getEvaluations } from '../api/continuous-auth-api'
import { EvaluationFilters } from '../components/EvaluationFilters'
import { EvaluationTable } from '../components/EvaluationTable'
import type {
  AdminEvaluationPage,
  EvaluationFiltersValue,
  EvaluationListQuery,
} from '../types/continuous-auth'
import { getContinuousAuthErrorMessage } from '../utils/continuous-auth-errors'

const initialFilters: EvaluationFiltersValue = {
  user_id: '',
  session_id: '',
  participant_id: '',
  risk_level: '',
  authentication_level: '',
  date_from: '',
  date_to: '',
}

function toIso(value: string): string | undefined {
  if (!value) {
    return undefined
  }

  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? undefined : date.toISOString()
}

function makeQuery(
  filters: EvaluationFiltersValue,
  page: number,
): EvaluationListQuery {
  return {
    user_id: filters.user_id.trim() || undefined,
    session_id: filters.session_id.trim() || undefined,
    participant_id: filters.participant_id.trim() || undefined,
    risk_level:
      filters.risk_level && filters.risk_level !== 'unknown'
        ? filters.risk_level
        : undefined,
    authentication_level: filters.authentication_level || undefined,
    date_from: toIso(filters.date_from),
    date_to: toIso(filters.date_to),
    page,
    page_size: 20,
  }
}

export function ContinuousAuthEvaluationsPage() {
  const [filters, setFilters] = useState(initialFilters)
  const [page, setPage] = useState(1)
  const [data, setData] = useState<AdminEvaluationPage | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [reloadKey, setReloadKey] = useState(0)

  const load = useCallback(
    async (signal: AbortSignal) => {
      setIsLoading(true)
      setError(null)
      try {
        setData(await getEvaluations(makeQuery(filters, page), signal))
      } catch (caughtError: unknown) {
        if (!signal.aborted) {
          setError(getContinuousAuthErrorMessage(caughtError))
        }
      } finally {
        if (!signal.aborted) {
          setIsLoading(false)
        }
      }
    },
    [filters, page],
  )

  useEffect(() => {
    const controller = new AbortController()
    void load(controller.signal)
    return () => controller.abort()
  }, [load, reloadKey])

  return (
    <div className="space-y-5">
      <PageHeader
        eyebrow="Administración"
        title="Evaluaciones continuas"
        description="Historial técnico paginado sin biometría cruda ni datos de evasión."
        actions={
          <Button
            variant="secondary"
            onClick={() => setReloadKey((current) => current + 1)}
            isLoading={isLoading}
          >
            Actualizar
          </Button>
        }
      />
      <EvaluationFilters
        value={filters}
        onApply={(nextFilters) => {
          setFilters(nextFilters)
          setPage(1)
        }}
      />
      {error && (
        <Alert variant="error" title="No se cargaron las evaluaciones">
          <div className="flex flex-wrap items-center gap-3">
            <span>{error}</span>
            <button
              type="button"
              className="font-bold underline"
              onClick={() => setReloadKey((current) => current + 1)}
            >
              Reintentar
            </button>
          </div>
        </Alert>
      )}
      {isLoading && !data ? (
        <LoadingSkeleton rows={8} label="Cargando evaluaciones" />
      ) : (
        data && <EvaluationTable data={data} onPageChange={setPage} />
      )}
    </div>
  )
}
