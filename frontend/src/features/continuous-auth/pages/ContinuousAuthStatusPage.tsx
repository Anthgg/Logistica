import { Alert } from '../../../components/common/Alert'
import { Button } from '../../../components/common/Button'
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton'
import { PageHeader } from '../../../components/common/PageHeader'
import { ComponentAvailabilityList } from '../components/ComponentAvailabilityList'
import { ContinuousAuthStatusCard } from '../components/ContinuousAuthStatusCard'
import { DegradedModeAlert } from '../components/DegradedModeAlert'
import { useContinuousAuth } from '../hooks/useContinuousAuth'

export function ContinuousAuthStatusPage() {
  const {
    status,
    isLoading,
    isEvaluating,
    isPolling,
    error,
    notice,
    refreshStatus,
    requestReverification,
    clearError,
    clearNotice,
  } = useContinuousAuth()
  const shouldReverify =
    status?.authentication_level === 'verification_required' ||
    status?.authentication_level === 'restricted' ||
    status?.risk_level === 'high' ||
    status?.risk_level === 'critical'

  return (
    <div className="space-y-5">
      <PageHeader
        eyebrow="Seguridad"
        title="Estado de autenticación continua"
        description="Consulta el nivel comunicado por el backend y la disponibilidad de los componentes de verificación."
        actions={
          <>
            {shouldReverify && (
              <Button onClick={requestReverification}>
                Reverificar identidad
              </Button>
            )}
            <Button
              variant="secondary"
              onClick={() => void refreshStatus().catch(() => undefined)}
              isLoading={isLoading}
            >
              Actualizar estado
            </Button>
          </>
        }
      />

      {notice && (
        <Alert variant="success" onDismiss={clearNotice}>
          {notice}
        </Alert>
      )}

      {error && (
        <Alert variant="warning" title="Estado temporal" onDismiss={clearError}>
          {error}
        </Alert>
      )}

      {!status && isLoading && (
        <LoadingSkeleton rows={5} label="Cargando estado de seguridad" />
      )}

      {!status && !isLoading && (
        <section className="rounded-2xl border border-slate-200 bg-white p-8 text-center">
          <h2 className="font-bold text-slate-950">
            El estado no está disponible
          </h2>
          <p className="mt-2 text-sm text-slate-600">
            No se interpreta este fallo como un riesgo de identidad. Reintenta
            cuando el servicio vuelva a estar disponible.
          </p>
          <Button
            className="mt-4"
            onClick={() => void refreshStatus().catch(() => undefined)}
          >
            Reintentar
          </Button>
        </section>
      )}

      {status && (
        <>
          {(status.degraded || (error && !isPolling)) && (
            <DegradedModeAlert
              reason={status.degraded_reason ?? error}
            />
          )}

          {status.risk_level === 'medium' && (
            <Alert variant="warning" title="Supervisión reforzada">
              La sesión continúa disponible. El backend indicó que se
              incrementó la supervisión.
            </Alert>
          )}

          {(status.risk_level === 'high' ||
            status.risk_level === 'critical') && (
            <Alert variant="error" title="Acción de seguridad requerida">
              Reverifica tu identidad antes de realizar operaciones sensibles.
            </Alert>
          )}

          <ContinuousAuthStatusCard status={status} />

          <section
            className="rounded-2xl border border-slate-200 bg-slate-50 p-5"
            aria-labelledby="available-components-title"
          >
            <div className="mb-4">
              <h2
                id="available-components-title"
                className="text-lg font-bold text-slate-950"
              >
                Componentes disponibles
              </h2>
              <p className="mt-1 text-sm text-slate-600">
                Una ausencia técnica no significa que la identidad haya
                fallado.
              </p>
            </div>
            <ComponentAvailabilityList
              components={status.components_available}
            />
          </section>

          <div className="sr-only" aria-live="polite">
            {isEvaluating
              ? 'Evaluación de seguridad en curso.'
              : 'Sin evaluación en curso.'}
          </div>
        </>
      )}
    </div>
  )
}
