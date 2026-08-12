import { useCallback, useEffect, useState } from 'react'
import { Alert } from '../../../components/common/Alert'
import { Button } from '../../../components/common/Button'
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton'
import { PageHeader } from '../../../components/common/PageHeader'
import { getModelStatus } from '../api/continuous-auth-api'
import { ModelStatusCard } from '../components/ModelStatusCard'
import type { ModelStatus } from '../types/continuous-auth'
import { getContinuousAuthErrorMessage } from '../utils/continuous-auth-errors'

export function ModelStatusPage() {
  const [status, setStatus] = useState<ModelStatus | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [reloadKey, setReloadKey] = useState(0)

  const load = useCallback(async (signal: AbortSignal) => {
    setIsLoading(true)
    setError(null)
    try {
      setStatus(await getModelStatus(signal))
    } catch (caughtError: unknown) {
      if (!signal.aborted) {
        setError(getContinuousAuthErrorMessage(caughtError))
      }
    } finally {
      if (!signal.aborted) {
        setIsLoading(false)
      }
    }
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    void load(controller.signal)
    return () => controller.abort()
  }, [load, reloadKey])

  return (
    <div className="space-y-5">
      <PageHeader
        eyebrow="Administración"
        title="Estado de modelos"
        description="Disponibilidad y versiones sanitizadas reportadas por el backend."
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
      {error && (
        <Alert variant="warning" title="Modelos no disponibles">
          {error}
        </Alert>
      )}
      {isLoading && !status ? (
        <LoadingSkeleton rows={6} label="Cargando estado de modelos" />
      ) : (
        status && <ModelStatusCard status={status} />
      )}
    </div>
  )
}
