import { useEffect, useState } from 'react'
import { Button } from '../common/Button'
import { ResourceDialog } from '../common/ResourceDialog'
import { SelectField } from '../common/FormControls'
import { useResearchSession } from '../../hooks/useResearchSession'
import { useTranslations } from '../../hooks/useTranslations'
import { getErrorMessage } from '../../utils/errors'

export function CaptureBar() {
  const { configuration, startedAtEpoch, counters, hasCamera, finishSession, cancelSession } = useResearchSession()
  const { translate } = useTranslations()
  const [elapsed, setElapsed] = useState(0)
  const [isFinishing, setIsFinishing] = useState(false)
  const [isCancelOpen, setIsCancelOpen] = useState(false)
  const [reason, setReason] = useState('user_cancelled')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const tick = () => setElapsed(startedAtEpoch ? Date.now() - startedAtEpoch : 0)
    tick()
    const timer = window.setInterval(tick, 1000)
    return () => window.clearInterval(timer)
  }, [startedAtEpoch])

  if (!configuration) return null
  const minutes = Math.floor(elapsed / 60000)
  const seconds = Math.floor((elapsed % 60000) / 1000)
  const finish = async () => {
    setIsFinishing(true); setError(null)
    try { await finishSession() } catch (caught: unknown) { setError(getErrorMessage(caught)); setIsFinishing(false) }
  }
  const cancel = async () => {
    setIsFinishing(true); setError(null)
    try { await cancelSession(reason) } catch (caught: unknown) { setError(getErrorMessage(caught)); setIsFinishing(false) }
  }
  return <>
    <aside className="capture-bar" aria-live="polite">
      <div className="capture-bar__status"><span className="recording-dot" /><div><strong>Sesión experimental activa</strong><small>{translate('common', configuration.scenario, configuration.scenario)} · {minutes}:{seconds.toString().padStart(2, '0')}</small></div></div>
      <div className="capture-bar__counters"><span>Cámara {hasCamera ? 'activa' : 'inactiva'}</span><span>{counters.captures} capturas</span><span>{counters.batches} lotes</span>{error && <span className="capture-error">{error}</span>}</div>
      <div className="capture-bar__actions"><Button size="small" variant="ghost" onClick={() => setIsCancelOpen(true)} disabled={isFinishing}>Cancelar</Button><Button size="small" onClick={() => void finish()} isLoading={isFinishing}>Finalizar</Button></div>
    </aside>
    <ResourceDialog isOpen={isCancelOpen} title="Cancelar sesión experimental" description="La captura se detendrá y la sesión quedará marcada como cancelada." submitLabel="Cancelar sesión" isSubmitting={isFinishing} onClose={() => setIsCancelOpen(false)} onSubmit={() => void cancel()}>
      <SelectField label="Motivo" value={reason} onChange={(e) => setReason(e.target.value)}><option value="user_cancelled">Cancelada por el participante</option><option value="camera_problem">Problema con la cámara</option><option value="task_interrupted">Tarea interrumpida</option><option value="other">Otro motivo</option></SelectField>
    </ResourceDialog>
  </>
}
