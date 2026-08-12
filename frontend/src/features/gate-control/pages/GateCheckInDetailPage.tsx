import { useCallback, useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { gateCheckInsApi } from '../api/gateCheckInsApi'
import { gateEvidenceApi } from '../api/gateEvidenceApi'
import { gateExceptionsApi } from '../api/gateExceptionsApi'
import { gateDocumentsApi } from '../api/gateDocumentsApi'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { useSensitiveActionGuard } from '../../logistics-permissions/hooks/useSensitiveActionGuard'
import type {
  DockAssignmentPreparation,
  GateCheckInCapabilities,
  GateCheckInDetail,
  GateCheckInHistoryEvent,
  GateCpvDocumentResponse,
  GateIntegrityStatus,
  GatePhotoEvidence,
  GateVerificationException,
} from '../types/gate-control'
import {
  arrivalClassificationLabel, checkInStatusLabel, decisionTypeLabel,
  formatServerTime, sealPhysicalStatusLabel, verificationStateLabel,
} from '../format'
import { EmptyState, ErrorState, StatusPill, TableSkeleton } from '../components/ui'
import { Modal } from '../components/ui'
import { GateVerificationWorkspace } from '../components/GateVerificationWorkspace'
import { GateEvidenceGallery } from '../components/GateEvidenceGallery'
import { GateControlDocumentPanel } from '../components/GateControlDocumentPanel'
import { GateCheckInHistoryTimeline } from '../components/GateCheckInHistoryTimeline'
import { DockAssignmentPreparationPanel } from '../components/DockAssignmentPreparationPanel'
import { GateCheckInIntegrityPanel } from '../components/GateCheckInIntegrityPanel'

type Tab = 'summary' | 'verification' | 'photos' | 'exceptions' | 'decision' | 'document' | 'integrity' | 'history' | 'dock'

const TABS: Array<{ key: Tab; label: string }> = [
  { key: 'summary', label: 'Resumen' },
  { key: 'verification', label: 'Verificación' },
  { key: 'photos', label: 'Fotografías' },
  { key: 'exceptions', label: 'Excepciones' },
  { key: 'decision', label: 'Decisión' },
  { key: 'document', label: 'Acta CPV' },
  { key: 'integrity', label: 'Integridad' },
  { key: 'dock', label: 'Prep. Fase 038' },
  { key: 'history', label: 'Historial' },
]

export function GateCheckInDetailPage() {
  const { checkInId } = useParams<{ checkInId: string }>()
  const [tab, setTab] = useState<Tab>('summary')
  const [detail, setDetail] = useState<GateCheckInDetail | null>(null)
  const [caps, setCaps] = useState<GateCheckInCapabilities | null>(null)
  const [document, setDocument] = useState<GateCpvDocumentResponse | null>(null)
  const [integrity, setIntegrity] = useState<GateIntegrityStatus | null>(null)
  const [history, setHistory] = useState<GateCheckInHistoryEvent[]>([])
  const [dock, setDock] = useState<DockAssignmentPreparation | null>(null)
  const [exceptions, setExceptions] = useState<GateVerificationException[]>([])
  const [photos, setPhotos] = useState<GatePhotoEvidence[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isError, setIsError] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const [arrivalOpen, setArrivalOpen] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const authorizeGuard = useSensitiveActionGuard({ permission: LOGISTICS_PERMISSIONS.gateControl.authorize })
  const denyGuard = useSensitiveActionGuard({ permission: LOGISTICS_PERMISSIONS.gateControl.deny })

  const load = useCallback(async () => {
    if (!checkInId) return
    setIsLoading(true); setIsError(false)
    try {
      const d = await gateCheckInsApi.get(checkInId)
      setDetail(d); setCaps(d.capabilities)
      gateCheckInsApi.getHistory(checkInId).then(setHistory).catch(() => setHistory([]))
      gateDocumentsApi.getDocument(checkInId).then(setDocument).catch(() => setDocument(null))
      gateCheckInsApi.getIntegrity(checkInId).then(setIntegrity).catch(() => setIntegrity(null))
      gateCheckInsApi.getDockAssignmentPreparation(checkInId).then(setDock).catch(() => setDock(null))
      gateExceptionsApi.list(checkInId).then(setExceptions).catch(() => setExceptions([]))
      gateEvidenceApi.listPhotos(checkInId).then(setPhotos).catch(() => setPhotos([]))
    } catch (err: unknown) {
      setIsError(true); setErrorMessage(err instanceof Error ? err.message : 'No se pudo cargar el check-in.')
    } finally {
      setIsLoading(false)
    }
  }, [checkInId])

  useEffect(() => { void load() }, [load])

  const handleArrival = async () => {
    if (!checkInId) return
    setSubmitting(true)
    try {
      await gateCheckInsApi.recordArrival(checkInId)
      setArrivalOpen(false)
      await load()
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'No se pudo registrar la llegada.')
    } finally {
      setSubmitting(false)
    }
  }

  const handleStartVerification = async () => {
    if (!checkInId) return
    try { await gateCheckInsApi.startVerification(checkInId); await load() } catch (e) { alert(e instanceof Error ? e.message : 'No se pudo iniciar.') }
  }

  const handleAuthorize = async () => {
    if (!checkInId) return
    setSubmitting(true)
    try {
      const executed = await authorizeGuard.run(async () => { await gateCheckInsApi.authorizeEntry(checkInId) })
      if (executed) await load()
    } finally { setSubmitting(false) }
  }

  const handleDeny = async (reason: string) => {
    if (!checkInId) return
    setSubmitting(true)
    try {
      const executed = await denyGuard.run(async () => { await gateCheckInsApi.denyEntry(checkInId, { reason }) })
      if (executed) await load()
    } finally { setSubmitting(false) }
  }

  if (isLoading) return <TableSkeleton />
  if (isError) return <ErrorState message={errorMessage} onRetry={() => void load()} />
  if (!detail) return <EmptyState title="Check-in no encontrado" />

  const canRecordArrival = caps?.can_record_arrival && detail.status === 'CREATED'
  const canStartVerification = caps?.can_start_verification && detail.status === 'ARRIVED'
  const canAuthorize = caps?.can_authorize && detail.status !== 'AUTHORIZED' && detail.status !== 'DENIED' && detail.status !== 'COMPLETED'
  const canDeny = caps?.can_deny && detail.status !== 'DENIED' && detail.status !== 'COMPLETED'

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-lg font-bold text-slate-900">{detail.cpv_code ?? detail.cit_code ?? 'Check-in'}</h1>
          <p className="text-xs text-slate-500">
            {detail.cit_code ?? 'Sin cita'} · {detail.gate_name ?? '—'} · {detail.supplier_name ?? '—'} · {detail.observed_plate ?? detail.expected_plate ?? '—'}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <StatusPill tone="info">{checkInStatusLabel(detail.status)}</StatusPill>
          {detail.decision_type && <StatusPill tone="muted">{decisionTypeLabel(detail.decision_type)}</StatusPill>}
          {detail.has_seal_issue && <StatusPill tone="danger">Precinto</StatusPill>}
          {detail.has_blocking_failures && <StatusPill tone="warning">Fallas bloqueantes</StatusPill>}
        </div>
      </div>

      {/* Hora del servidor y llegada */}
      <div className="grid grid-cols-2 gap-2 text-xs md:grid-cols-4">
        <div className="rounded-lg border border-slate-200 bg-white p-2.5">
          <div className="text-slate-500">Hora del servidor</div>
          <div className="mt-0.5 font-mono font-semibold text-slate-800">{formatServerTime(detail.server_time, detail.timezone)}</div>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-2.5">
          <div className="text-slate-500">Llegada registrada</div>
          <div className="mt-0.5 font-mono text-sm text-slate-800">{detail.arrived_at ? new Date(detail.arrived_at).toLocaleString('es-PE') : '—'}</div>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-2.5">
          <div className="text-slate-500">Clasificación</div>
          <div className="mt-0.5 text-sm text-slate-800">{arrivalClassificationLabel(detail.arrival_classification)}</div>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-2.5">
          <div className="text-slate-500">Guardia</div>
          <div className="mt-0.5 text-sm text-slate-800">{detail.guard_display_name ?? '—'}</div>
        </div>
      </div>

      {/* Acciones rápidas */}
      <div className="flex flex-wrap gap-2">
        {canRecordArrival && (
          <button type="button" onClick={() => setArrivalOpen(true)} className="rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#173a55]">Registrar llegada</button>
        )}
        {canStartVerification && (
          <button type="button" onClick={() => void handleStartVerification()} className="rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#173a55]">Iniciar verificación</button>
        )}
        {canAuthorize && (
          <button type="button" onClick={() => void handleAuthorize()} disabled={submitting || authorizeGuard.isBlocked} className="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-emerald-700 disabled:opacity-50">Autorizar ingreso</button>
        )}
        {canDeny && (
          <button type="button" onClick={() => { const r = prompt('Motivo de denegación:'); if (r && r.trim().length >= 10) void handleDeny(r.trim()) }} disabled={denyGuard.isBlocked} className="rounded-lg bg-rose-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-rose-700 disabled:opacity-50">Denegar ingreso</button>
        )}
      </div>

      {/* Tabs */}
      <div className="flex flex-wrap gap-1 rounded-xl border border-slate-200 bg-slate-50/60 p-1">
        {TABS.map((t) => (
          <button key={t.key} type="button" onClick={() => setTab(t.key)}
            className={tab === t.key ? 'rounded-lg bg-white px-3 py-1.5 text-xs font-semibold text-[#1F4E6D] shadow-xs' : 'rounded-lg px-3 py-1.5 text-xs font-medium text-slate-500 hover:text-slate-700'}>
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'summary' && (
        <div className="rounded-xl border border-slate-200 bg-white p-4 text-xs">
          <h2 className="text-sm font-bold text-slate-800">Resumen</h2>
          {detail.appointment && (
            <dl className="mt-2 grid grid-cols-2 gap-1 md:grid-cols-3">
              <dt className="text-slate-500">CIT:</dt><dd className="font-mono">{detail.appointment.cit_code}</dd>
              <dt className="text-slate-500">Proveedor:</dt><dd>{detail.appointment.supplier_name ?? '—'}</dd>
              <dt className="text-slate-500">Transportista:</dt><dd>{detail.appointment.carrier_name ?? '—'}</dd>
              <dt className="text-slate-500">Placa esperada:</dt><dd className="font-mono">{detail.appointment.vehicle_plate ?? '—'}</dd>
              <dt className="text-slate-500">Conductor:</dt><dd>{detail.appointment.driver_name_redacted ?? '—'}</dd>
              <dt className="text-slate-500">Precinto esperado:</dt><dd className="font-mono">{detail.appointment.seal_number_expected ?? '—'}</dd>
              <dt className="text-slate-500">Pallets:</dt><dd>{detail.appointment.pallets ?? '—'}</dd>
              <dt className="text-slate-500">Bultos:</dt><dd>{detail.appointment.packages ?? '—'}</dd>
              <dt className="text-slate-500">Peso:</dt><dd>{detail.appointment.weight ?? '—'}</dd>
            </dl>
          )}
          {detail.seal_inspection && (
            <div className="mt-2 border-t border-slate-100 pt-2">
              <div className="font-semibold">Precinto: {sealPhysicalStatusLabel(detail.seal_inspection.physical_status)}</div>
              <div className="text-slate-500">Coincidencia: {verificationStateLabel(detail.seal_inspection.match_status)}</div>
            </div>
          )}
        </div>
      )}

      {tab === 'verification' && (
        <GateVerificationWorkspace checkInId={detail.id} detail={detail} capabilities={caps} onChanged={() => void load()} />
      )}
      {tab === 'photos' && <GateEvidenceGallery photos={photos} capabilities={caps} checkInId={detail.id} onChanged={() => void load()} />}
      {tab === 'exceptions' && <ExceptionsList exceptions={exceptions} capabilities={caps} onChanged={() => void load()} />}
      {tab === 'decision' && (
        <div className="rounded-xl border border-slate-200 bg-white p-4 text-xs">
          <h2 className="text-sm font-bold text-slate-800">Decisión de ingreso</h2>
          {detail.decision ? (
            <dl className="mt-2 grid grid-cols-2 gap-1">
              <dt className="text-slate-500">Decisión:</dt><dd>{decisionTypeLabel(detail.decision.decision_type)}</dd>
              <dt className="text-slate-500">Condiciones:</dt><dd>{detail.decision.conditions ?? '—'}</dd>
              <dt className="text-slate-500">Observación final:</dt><dd>{detail.decision.final_observation ?? '—'}</dd>
            </dl>
          ) : <EmptyState title="Sin decisión registrada" />}
        </div>
      )}
      {tab === 'document' && <GateControlDocumentPanel checkInId={detail.id} cpvDocument={document} capabilities={caps} onChanged={() => void load()} />}
      {tab === 'integrity' && <GateCheckInIntegrityPanel integrity={integrity} />}
      {tab === 'dock' && <DockAssignmentPreparationPanel preparation={dock} queueEntryId={dock?.queue_entry_id ?? null} />}
      {tab === 'history' && <GateCheckInHistoryTimeline history={history} />}

      {/* Modal registro de llegada */}
      <Modal
        open={arrivalOpen}
        onOpenChange={setArrivalOpen}
        title="Registrar llegada"
        footer={
          <>
            <button type="button" onClick={() => setArrivalOpen(false)} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50">Cancelar</button>
            <button type="button" disabled={submitting} onClick={() => void handleArrival()} className="rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#173a55] disabled:opacity-50">{submitting ? 'Registrando…' : 'Confirmar'}</button>
          </>
        }
      >
        <div className="space-y-2 text-xs">
          <p className="rounded-lg border border-indigo-100 bg-indigo-50/40 p-2 text-indigo-700">
            Al confirmar se registrará la hora del servidor como llegada real. No se usa la hora del navegador.
          </p>
          <dl className="grid grid-cols-2 gap-1">
            <dt className="text-slate-500">CIT:</dt><dd className="font-mono">{detail.cit_code ?? '—'}</dd>
            <dt className="text-slate-500">Placa esperada:</dt><dd className="font-mono">{detail.expected_plate ?? '—'}</dd>
            <dt className="text-slate-500">Hora servidor:</dt><dd className="font-mono">{formatServerTime(detail.server_time, detail.timezone)}</dd>
          </dl>
        </div>
      </Modal>
    </div>
  )
}

function ExceptionsList({ exceptions, capabilities, onChanged }: { exceptions: GateVerificationException[]; capabilities: GateCheckInCapabilities | null; onChanged: () => void }) {
  const handleApprove = async (id: string) => {
    try { await gateExceptionsApi.approve(exceptions[0]?.check_in_id ?? '', id); onChanged() } catch (e) { alert(e instanceof Error ? e.message : 'No se pudo aprobar.') }
  }
  if (exceptions.length === 0) return <EmptyState title="Sin excepciones" />
  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200">
      <table className="min-w-full divide-y divide-slate-200 text-xs">
        <thead className="bg-slate-50/60 font-semibold uppercase text-slate-500">
          <tr><th className="px-3 py-2.5 text-left">Tipo</th><th className="px-3 py-2.5 text-left">Motivo</th><th className="px-3 py-2.5 text-left">Estado</th><th className="px-3 py-2.5 text-right">Acciones</th></tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {exceptions.map((e) => (
            <tr key={e.id}>
              <td className="px-3 py-2">{e.type}</td>
              <td className="px-3 py-2">{e.reason}</td>
              <td className="px-3 py-2"><StatusPill tone={e.status === 'APPROVED' ? 'success' : e.status === 'REJECTED' ? 'danger' : 'warning'}>{e.status}</StatusPill></td>
              <td className="px-3 py-2 text-right">
                {capabilities?.can_approve_exception && e.status === 'PENDING' && (
                  <button type="button" onClick={() => void handleApprove(e.id)} className="rounded border border-emerald-200 px-2 py-0.5 text-[11px] font-semibold text-emerald-700 hover:bg-emerald-50">Aprobar</button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}