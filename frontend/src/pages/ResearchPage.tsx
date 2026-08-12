import { useEffect, useState } from 'react'
import { Alert } from '../components/common/Alert'
import { LogisticsIcon } from '../components/common/LogisticsIcon'
import { Button } from '../components/common/Button'
import { ConfirmDialog } from '../components/common/ConfirmDialog'
import { SelectField } from '../components/common/FormControls'
import { Input } from '../components/common/Input'
import { PageHeader } from '../components/common/PageHeader'
import { StatusBadge } from '../components/common/StatusBadge'
import { useSensitiveOperationGuard } from '../features/continuous-auth/hooks/useSensitiveOperationGuard'
import { useResearchParticipant } from '../hooks/useResearchParticipant'
import { useResearchSession } from '../hooks/useResearchSession'
import type { ResearchScenario } from '../types/research'
import { formatDateTime } from '../utils/date'
import { getErrorMessage } from '../utils/errors'

const scenarios: { value: ResearchScenario; label: string }[] = [
  { value: 'register_shipment', label: 'Registrar un envío' },
  { value: 'search_shipment', label: 'Buscar un envío' },
  { value: 'update_shipment_status', label: 'Actualizar estado de envío' },
  { value: 'assign_route', label: 'Asignar una ruta' },
  { value: 'register_inventory_movement', label: 'Registrar movimiento de inventario' },
  { value: 'report_incident', label: 'Reportar una incidencia' },
  { value: 'review_dashboard', label: 'Revisar el dashboard' },
  { value: 'mixed_operations', label: 'Operaciones mixtas' },
]

export function ResearchPage() {
  const { guardSensitiveAction } = useSensitiveOperationGuard()
  const {
    participant,
    consent,
    needsEnrollment,
    needsConsent,
    isLoading: isParticipantLoading,
    isEnrolling,
    isAcceptingConsent,
    error: participantError,
    selfEnroll,
    acceptConsent,
    withdrawConsent,
    clearError: clearParticipantError,
  } = useResearchParticipant()

  const {
    isActive,
    startedAtEpoch,
    counters,
    startSession,
    finishSession,
    cancelSession,
  } = useResearchSession()

  const [scenario, setScenario] = useState<ResearchScenario>('mixed_operations')
  const [duration, setDuration] = useState(10)
  const [checkboxAccepted, setCheckboxAccepted] = useState(false)
  const [isStartingSession, setIsStartingSession] = useState(false)
  const [isEndingSession, setIsEndingSession] = useState(false)
  const [isWithdrawOpen, setIsWithdrawOpen] = useState(false)
  const [localError, setLocalError] = useState<string | null>(null)
  const [localSuccess, setSuccess] = useState<string | null>(null)
  const [elapsedSeconds, setElapsedSeconds] = useState(0)

  // Timer para tiempo transcurrido durante la recolección
  useEffect(() => {
    if (!isActive || !startedAtEpoch) {
      setElapsedSeconds(0)
      return undefined
    }
    const interval = window.setInterval(() => {
      setElapsedSeconds(Math.floor((Date.now() - startedAtEpoch) / 1000))
    }, 1000)
    return () => window.clearInterval(interval)
  }, [isActive, startedAtEpoch])

  const formatElapsed = (totalSeconds: number) => {
    const minutes = Math.floor(totalSeconds / 60)
    const seconds = totalSeconds % 60
    return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
  }

  const handleSelfEnroll = async () => {
    setLocalError(null)
    const result = await selfEnroll()
    if (result) {
      setSuccess(`Inscripción completada. Tu código seudónimo es ${result.participant_code}.`)
    }
  }

  const handleAcceptConsent = async () => {
    if (!checkboxAccepted) return
    setLocalError(null)
    const result = await acceptConsent()
    if (result) {
      setSuccess('Consentimiento registrado correctamente.')
    }
  }

  const handleWithdrawConsent = async () => {
    setLocalError(null)
    try {
      let result = null
      const executed = await guardSensitiveAction(async () => {
        if (isActive) {
          await cancelSession('Consentimiento retirado por el participante')
        }
        result = await withdrawConsent()
      })
      if (!executed) return
      if (result) {
        setIsWithdrawOpen(false)
        setSuccess('Consentimiento retirado. La captura está desactivada.')
      }
    } catch (caught: unknown) {
      setLocalError(getErrorMessage(caught))
    }
  }

  const handleStartSession = async () => {
    if (!participant?.id) return
    setIsStartingSession(true)
    setLocalError(null)
    try {
      await startSession({
        participantId: participant.id,
        scenario,
        expectedDurationMinutes: duration,
      })
      setSuccess('Recolección activa iniciada. Puedes interactuar en la plataforma mientras se capturan los datos.')
    } catch (caught: unknown) {
      if (caught instanceof DOMException && caught.name === 'NotAllowedError') {
        setLocalError('No se concedió acceso a la cámara. La sesión no fue iniciada.')
      } else {
        setLocalError(getErrorMessage(caught))
      }
    } finally {
      setIsStartingSession(false)
    }
  }

  const handleFinishSession = async () => {
    setIsEndingSession(true)
    setLocalError(null)
    try {
      await finishSession()
      setSuccess('Sesión experimental finalizada correctamente.')
    } catch (caught: unknown) {
      setLocalError(getErrorMessage(caught))
    } finally {
      setIsEndingSession(false)
    }
  }

  const handleCancelSession = async () => {
    setIsEndingSession(true)
    setLocalError(null)
    try {
      await cancelSession('Cancelado voluntariamente por el participante')
      setSuccess('Sesión cancelada.')
    } catch (caught: unknown) {
      setLocalError(getErrorMessage(caught))
    } finally {
      setIsEndingSession(false)
    }
  }

  const activeError = localError || participantError

  return (
    <div className="page">
      <PageHeader
        eyebrow="Autenticación Continua"
        title="Mi entrenamiento biométrico"
        description="Gestiona tu inscripción seudonimizada, el consentimiento informado y participa en sesiones de recolección de datos."
      />

      {activeError && (
        <Alert
          variant="error"
          onDismiss={() => {
            setLocalError(null)
            clearParticipantError()
          }}
        >
          {activeError}
        </Alert>
      )}

      {localSuccess && (
        <Alert variant="success" onDismiss={() => setSuccess(null)}>
          {localSuccess}
        </Alert>
      )}

      <section className="research-disclosure panel">
        <div className="research-disclosure__icon" aria-hidden="true">
          <LogisticsIcon name="lock" size={14} aria-hidden />
        </div>
        <div>
          <p className="eyebrow">Privacidad por diseño</p>
          <h2>Captura biométrica responsable</h2>
          <p>
            No se almacena texto escrito, contraseñas, correos ni datos de formularios.
            Únicamente se toman imágenes faciales periódicas y métricas temporales de interacción
            para entrenar modelos de autenticación continua.
          </p>
        </div>
      </section>

      {isParticipantLoading ? (
        <div className="panel loading-panel">
          <span className="spinner" />
          <p>Cargando estado biométrico…</p>
        </div>
      ) : (
        <div className="operations-grid">
          {/* ESTADO 1: Sin inscripción */}
          {needsEnrollment && (
            <section className="panel operations-section">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">Estado 1 de 4</p>
                  <h2>Configuración Biométrica</h2>
                </div>
                <StatusBadge value="draft">Sin inscripción</StatusBadge>
              </div>
              <p>
                Aún no estás inscrito como participante en la recolección biométrica.
                Genera tu código seudónimo para participar de manera anónima sin asociar tu correo o nombre.
              </p>
              <Button
                onClick={() => void handleSelfEnroll()}
                isLoading={isEnrolling}
              >
                Comenzar configuración biométrica
              </Button>
            </section>
          )}

          {/* ESTADO 2: Pendiente de consentimiento */}
          {!needsEnrollment && needsConsent && (
            <section className="panel operations-section">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">Estado 2 de 4</p>
                  <h2>Consentimiento Informado</h2>
                </div>
                <StatusBadge value="pending">Pendiente</StatusBadge>
              </div>
              <p className="participant-code-banner">
                Código asignado: <strong>{participant?.participant_code}</strong>
              </p>
              <div className="consent-copy">
                <h3>Consentimiento Versión frontend-v1</h3>
                <p>
                  Declaro haber sido informado sobre el propósito académico del estudio de autenticación continua.
                  Acepto la captura periódica de imágenes faciales y métricas de comportamiento no textuales.
                  Entiendo que puedo cancelar cualquier sesión o retirar mi consentimiento en cualquier momento.
                </p>
              </div>
              <label className="consent-check">
                <input
                  type="checkbox"
                  checked={checkboxAccepted}
                  onChange={(e) => setCheckboxAccepted(e.target.checked)}
                />
                <span>Acepto participar voluntariamente bajo estas condiciones.</span>
              </label>
              <Button
                onClick={() => void handleAcceptConsent()}
                disabled={!checkboxAccepted}
                isLoading={isAcceptingConsent}
              >
                Registrar consentimiento
              </Button>
            </section>
          )}

          {/* ESTADO 3 y 4: Recolección activa o listo para recolectar */}
          {!needsEnrollment && !needsConsent && participant && (
            <>
              <section className="panel operations-section">
                <div className="section-heading">
                  <div>
                    <p className="eyebrow">Perfil Experimental</p>
                    <h2>Participante Seudonimizado</h2>
                  </div>
                  <StatusBadge value="accepted">Consentimiento Vigente</StatusBadge>
                </div>
                <div className="participant-details">
                  <div className="detail-item">
                    <span>Código de participante</span>
                    <strong>{participant.participant_code}</strong>
                  </div>
                  <div className="detail-item">
                    <span>Fecha de inscripción</span>
                    <span>{formatDateTime(participant.enrollment_date)}</span>
                  </div>
                  <div className="detail-item">
                    <span>Versión de consentimiento</span>
                    <span>{consent?.consent_version ?? 'frontend-v1'}</span>
                  </div>
                </div>
                <Button
                  variant="secondary"
                  onClick={() => setIsWithdrawOpen(true)}
                  disabled={isActive}
                >
                  Retirar consentimiento
                </Button>
              </section>

              <section className="panel operations-section">
                <div className="section-heading">
                  <div>
                    <p className="eyebrow">Sesión Experimental</p>
                    <h2>Recolección de Datos</h2>
                  </div>
                  {isActive ? (
                    <StatusBadge value="active">Recolección Activa</StatusBadge>
                  ) : (
                    <StatusBadge value="in_transit">Listo para recolectar</StatusBadge>
                  )}
                </div>

                {isActive ? (
                  <div className="active-collection-dashboard">
                    <aside className="privacy-active-notice">
                      <LogisticsIcon name="lock" size={14} aria-hidden /> <strong>Privacidad Activa</strong>: No se almacena el texto escrito ni la pantalla.
                    </aside>
                    <div className="collection-metrics">
                      <div className="metric-card">
                        <span>Tiempo transcurrido</span>
                        <strong>{formatElapsed(elapsedSeconds)}</strong>
                      </div>
                      <div className="metric-card">
                        <span>Capturas aceptadas</span>
                        <strong>{counters.captures}</strong>
                      </div>
                      <div className="metric-card">
                        <span>Lotes enviados</span>
                        <strong>{counters.batches}</strong>
                      </div>
                      <div className="metric-card">
                        <span>Estado conexión</span>
                        <strong className="status-online">● En vivo</strong>
                      </div>
                    </div>

                    <div className="collection-actions">
                      <Button
                        onClick={() => void handleFinishSession()}
                        isLoading={isEndingSession}
                      >
                        Finalizar sesión
                      </Button>
                      <Button
                        variant="secondary"
                        onClick={() => void handleCancelSession()}
                        isLoading={isEndingSession}
                      >
                        Cancelar
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="start-collection-form">
                    <SelectField
                      label="Escenario operativo"
                      value={scenario}
                      onChange={(e) => setScenario(e.target.value as ResearchScenario)}
                    >
                      {scenarios.map((item) => (
                        <option key={item.value} value={item.value}>
                          {item.label}
                        </option>
                      ))}
                    </SelectField>

                    <Input
                      label="Duración esperada (minutos)"
                      type="number"
                      min="1"
                      max="120"
                      value={duration}
                      onChange={(e) => setDuration(Number(e.target.value))}
                    />

                    <aside className="camera-notice">
                      <strong>Permiso de cámara</strong>
                      <p>
                        Al iniciar, el navegador solicitará permiso de cámara sin micrófono.
                        Si rechazas o se interrumpe la cámara, la recolección se detendrá automáticamente.
                      </p>
                    </aside>

                    <Button
                      onClick={() => void handleStartSession()}
                      isLoading={isStartingSession}
                    >
                      Solicitar cámara e iniciar recolección
                    </Button>
                  </div>
                )}
              </section>
            </>
          )}
        </div>
      )}

      <ConfirmDialog
        isOpen={isWithdrawOpen}
        title="¿Retirar el consentimiento?"
        description="Se revocará tu participación activa en el estudio. No se realizarán nuevas capturas."
        confirmLabel="Retirar consentimiento"
        isLoading={isParticipantLoading}
        onCancel={() => setIsWithdrawOpen(false)}
        onConfirm={() => void handleWithdrawConsent()}
      />
    </div>
  )
}
