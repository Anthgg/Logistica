import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'
import { researchApi } from '../api/research-api'
import { Alert } from '../components/common/Alert'
import { Button } from '../components/common/Button'
import {
  SelectField,
  TextareaField,
} from '../components/common/FormControls'
import { PageHeader } from '../components/common/PageHeader'
import { StatusBadge } from '../components/common/StatusBadge'
import { useTranslations } from '../hooks/useTranslations'
import type {
  ExperimentalSession,
  ExperimentalSessionAnnotation,
} from '../types/research'
import { formatDateTime } from '../utils/date'
import { getErrorMessage } from '../utils/errors'

const initialAnnotation: ExperimentalSessionAnnotation = {
  identity_label: 'genuine',
  sample_role: 'verification',
  presentation_label: 'bona_fide',
  attack_type: 'none',
  confirmed: true,
}

function toLocalDateTime(value: string | null): string | null {
  if (!value) return null
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return null
  return new Date(date.getTime() - date.getTimezoneOffset() * 60_000)
    .toISOString()
    .slice(0, 16)
}

export function ExperimentalSessionDetailPage() {
  const { sessionId = '' } = useParams()
  const { translate } = useTranslations()
  const [session, setSession] = useState<ExperimentalSession | null>(null)
  const [annotation, setAnnotation] =
    useState<ExperimentalSessionAnnotation>(initialAnnotation)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const load = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const detail = await researchApi.getSession(sessionId)
      setSession(detail)
      setAnnotation({
        identity_label: detail.identity_label,
        sample_role: detail.sample_role,
        operator_change_at: toLocalDateTime(detail.operator_change_at),
        presentation_label: detail.presentation_label,
        attack_type: detail.attack_type,
        source_device: detail.source_device,
        pad_source_id: detail.pad_source_id,
        confirmed: detail.annotation_status === 'confirmed',
      })
    } catch (caught: unknown) {
      setError(getErrorMessage(caught))
    } finally {
      setIsLoading(false)
    }
  }, [sessionId])

  useEffect(() => {
    void load()
  }, [load])

  const submitAnnotation = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!sessionId || isSaving) return

    setIsSaving(true)
    setError(null)
    setSuccess(null)
    try {
      const cleanAnnotation: ExperimentalSessionAnnotation = {
        ...annotation,
        operator_change_at:
          annotation.sample_role === 'change_operator'
            ? annotation.operator_change_at
              ? new Date(annotation.operator_change_at).toISOString()
              : null
            : null,
        attack_type:
          annotation.presentation_label === 'attack'
            ? annotation.attack_type
            : 'none',
        source_device: annotation.source_device?.trim() || null,
        pad_source_id: annotation.pad_source_id?.trim() || null,
        annotation_notes: annotation.annotation_notes?.trim() || null,
      }
      setSession(await researchApi.annotate(sessionId, cleanAnnotation))
      setSuccess('Anotación experimental guardada correctamente.')
    } catch (caught: unknown) {
      setError(getErrorMessage(caught))
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="page">
      <div className="back-link">
        <Link to="/research/sessions">← Volver a sesiones</Link>
      </div>
      <PageHeader
        eyebrow="Resumen experimental"
        title={
          session
            ? translate('common', session.scenario, session.scenario)
            : 'Sesión'
        }
        description={
          session
            ? `Iniciada ${formatDateTime(session.started_at)}`
            : 'Consultando sesión.'
        }
      />
      {error && (
        <Alert variant="error" onDismiss={() => setError(null)}>
          {error}
        </Alert>
      )}
      {success && (
        <Alert variant="success" onDismiss={() => setSuccess(null)}>
          {success}
        </Alert>
      )}
      {isLoading && (
        <div className="panel loading-panel">
          <span className="spinner" />
          <p>Cargando sesión…</p>
        </div>
      )}
      {!isLoading && session && (
        <>
          <section className="route-summary">
            <div>
              <span>Estado</span>
              <StatusBadge value={session.status} />
            </div>
            <div>
              <span>Duración</span>
              <strong>
                {session.status === 'active'
                  ? `${session.duration_seconds} s (en curso)`
                  : `${session.duration_seconds} s`}
              </strong>
            </div>
            <div>
              <span>Participante</span>
              <strong>{session.participant_id.slice(0, 8)}</strong>
            </div>
            <div>
              <span>Errores</span>
              <strong>{session.error_count}</strong>
            </div>
          </section>
          <section className="metric-grid">
            <Metric
              label="Capturas faciales"
              value={session.facial_capture_count}
            />
            <Metric
              label="Eventos de teclado"
              value={session.keyboard_event_count}
            />
            <Metric
              label="Eventos de puntero"
              value={session.mouse_event_count}
            />
            <Metric label="Lotes recibidos" value={session.batch_count} />
          </section>
          <Alert variant="info">
            Esta vista solo muestra métricas agregadas. No expone rutas internas
            de archivos ni contenido de interacción.
          </Alert>
          <section className="panel operations-section">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Dataset experimental</p>
                <h2>Anotación de la sesión</h2>
              </div>
            </div>
            <form onSubmit={submitAnnotation}>
              <div className="form-grid">
                <SelectField
                  label="Identidad"
                  value={annotation.identity_label}
                  onChange={(event) =>
                    setAnnotation((current) => ({
                      ...current,
                      identity_label: event.target.value as
                        | 'genuine'
                        | 'impostor',
                    }))
                  }
                >
                  <option value="genuine">Genuina</option>
                  <option value="impostor">Impostor</option>
                </SelectField>
                <SelectField
                  label="Rol de la muestra"
                  value={annotation.sample_role}
                  onChange={(event) =>
                    setAnnotation((current) => ({
                      ...current,
                      sample_role: event.target.value as
                        | 'enrollment'
                        | 'verification'
                        | 'change_operator',
                    }))
                  }
                >
                  <option value="enrollment">Enrolamiento</option>
                  <option value="verification">Verificación</option>
                  <option value="change_operator">Cambio de operador</option>
                </SelectField>
                {annotation.sample_role === 'change_operator' && (
                  <label className="field">
                    <span className="field__label">Momento del cambio</span>
                    <div className="field__control">
                      <input
                        className="field__input"
                        type="datetime-local"
                        value={
                          annotation.operator_change_at ?? ''
                        }
                        onChange={(event) =>
                          setAnnotation((current) => ({
                            ...current,
                            operator_change_at: event.target.value || null,
                          }))
                        }
                        required
                      />
                    </div>
                  </label>
                )}
                <SelectField
                  label="Presentación facial"
                  value={annotation.presentation_label ?? ''}
                  onChange={(event) =>
                    setAnnotation((current) => ({
                      ...current,
                      presentation_label: event.target.value as
                        | 'bona_fide'
                        | 'attack',
                    }))
                  }
                >
                  <option value="bona_fide">Bona fide</option>
                  <option value="attack">Ataque</option>
                </SelectField>
                {annotation.presentation_label === 'attack' && (
                  <SelectField
                    label="Tipo de ataque"
                    value={annotation.attack_type ?? ''}
                    onChange={(event) =>
                      setAnnotation((current) => ({
                        ...current,
                        attack_type: event.target.value as
                          | 'printed_photo'
                          | 'screen_photo'
                          | 'replayed_video',
                      }))
                    }
                    required
                  >
                    <option value="">Selecciona un tipo</option>
                    <option value="printed_photo">Fotografía impresa</option>
                    <option value="screen_photo">Fotografía en pantalla</option>
                    <option value="replayed_video">Video reproducido</option>
                  </SelectField>
                )}
                <TextareaField
                  className="form-grid__full"
                  label="Notas de anotación"
                  maxLength={500}
                  value={annotation.annotation_notes ?? ''}
                  onChange={(event) =>
                    setAnnotation((current) => ({
                      ...current,
                      annotation_notes: event.target.value,
                    }))
                  }
                />
                <label className="check-filter form-grid__full">
                  <input
                    type="checkbox"
                    checked={annotation.confirmed ?? true}
                    onChange={(event) =>
                      setAnnotation((current) => ({
                        ...current,
                        confirmed: event.target.checked,
                      }))
                    }
                  />
                  Confirmar esta anotación para el dataset
                </label>
              </div>
              <div className="table-actions">
                <Button
                  type="submit"
                  isLoading={isSaving}
                  loadingLabel="Guardando anotación…"
                >
                  Guardar anotación
                </Button>
              </div>
            </form>
          </section>
        </>
      )}
    </div>
  )
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <article className="metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
      <small>registrados por el backend</small>
    </article>
  )
}
