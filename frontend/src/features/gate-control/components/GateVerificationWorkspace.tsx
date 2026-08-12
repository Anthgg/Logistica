import { useState } from 'react'
import type { GateCheckInCapabilities, GateCheckInDetail, GateCheckResultValue } from '../types/gate-control'
import { gateInspectionsApi } from '../api/gateInspectionsApi'
import { LogisticsIcon } from '../../../components/common/LogisticsIcon'
import { checkResultLabel, normalizePlate, plateMatchStatusLabel, licenseStatusLabel, sealPhysicalStatusLabel, verificationStateLabel } from '../format'
import { EmptyState, StatusPill } from './ui'
import { SecureGatePhotoCapture } from './SecureGatePhotoCapture'

const RESULT_OPTIONS: GateCheckResultValue[] = ['COMPLIANT', 'COMPLIANT_WITH_OBSERVATION', 'NON_COMPLIANT', 'NOT_APPLICABLE', 'NOT_VERIFIED', 'REQUIRES_REVIEW']

export function GateVerificationWorkspace({
  checkInId, detail, capabilities, onChanged,
}: {
  checkInId: string
  detail: GateCheckInDetail
  capabilities: GateCheckInCapabilities | null
  onChanged: () => void
}) {
  const [step, setStep] = useState(0)
  const [observedPlate, setObservedPlate] = useState(detail.vehicle_inspection?.observed_plate ?? '')
  const [sealNumber, setSealNumber] = useState(detail.seal_inspection?.observed_number ?? '')
  const [sealStatus, setSealStatus] = useState(detail.seal_inspection?.physical_status ?? 'INTACT')

  const steps = ['Vehículo', 'Conductor', 'Documentos', 'Precinto', 'Fotografías', 'Checklist', 'Decisión']

  const savePlate = async () => {
    try {
      await gateInspectionsApi.updateVehicleInspection(checkInId, { observed_plate: normalizePlate(observedPlate) })
      onChanged()
    } catch (e) { alert(e instanceof Error ? e.message : 'No se pudo guardar.') }
  }

  const saveSeal = async () => {
    try {
      if (detail.seal_inspection) {
        await gateInspectionsApi.updateSealInspection(checkInId, { observed_number: sealNumber, physical_status: sealStatus })
      } else {
        await gateInspectionsApi.createSealInspection(checkInId, { observed_number: sealNumber, physical_status: sealStatus })
      }
      onChanged()
    } catch (e) { alert(e instanceof Error ? e.message : 'No se pudo guardar.') }
  }

  const setCheckResult = async (checkId: string, result: GateCheckResultValue) => {
    try {
      await gateInspectionsApi.updateCheckResult(checkInId, checkId, { result })
      onChanged()
    } catch (e) { alert(e instanceof Error ? e.message : 'No se pudo guardar.') }
  }

  return (
    <div className="space-y-3">
      {/* Stepper */}
      <ol className="flex flex-wrap gap-2 text-xs">
        {steps.map((label, i) => (
          <li key={label}>
            <button type="button" onClick={() => setStep(i)}
              className={step === i ? 'rounded-full bg-[#1F4E6D] px-3 py-1 font-semibold text-white' : 'rounded-full bg-slate-100 px-3 py-1 text-slate-500 hover:bg-slate-200'}>
              {i + 1}. {label}
            </button>
          </li>
        ))}
      </ol>

      {/* Vehículo */}
      {step === 0 && (
        <div className="rounded-xl border border-slate-200 bg-white p-4 text-xs">
          <h2 className="text-sm font-bold text-slate-800">Inspección del vehículo</h2>
          <div className="mt-2 grid grid-cols-2 gap-3">
            <div>
              <div className="font-semibold text-slate-600">Esperado</div>
              <dl className="mt-1 space-y-0.5">
                <dt className="text-slate-500">Placa:</dt><dd className="font-mono">{detail.expected_plate ?? '—'}</dd>
                <dt className="text-slate-500">Vehículo:</dt><dd>{detail.vehicle_inspection?.expected_vehicle_summary?.make ?? '—'} {detail.vehicle_inspection?.expected_vehicle_summary?.model ?? ''}</dd>
              </dl>
            </div>
            <div>
              <div className="font-semibold text-slate-600">Observado</div>
              <div className="mt-1">
                <label className="mb-1 block font-bold text-slate-700">Placa observada</label>
                <input value={observedPlate} onChange={(e) => setObservedPlate(e.target.value.toUpperCase())} className="w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-sm" autoComplete="off" />
                {detail.vehicle_inspection && (
                  <div className="mt-1">Coincidencia: <StatusPill tone={detail.vehicle_inspection.plate_match_status === 'MATCH' ? 'success' : 'warning'}>{plateMatchStatusLabel(detail.vehicle_inspection.plate_match_status)}</StatusPill></div>
                )}
                <button type="button" onClick={() => void savePlate()} className="mt-1 rounded-lg bg-[#1F4E6D] px-3 py-1 text-[11px] font-semibold text-white hover:bg-[#173a55]">Guardar placa</button>
              </div>
            </div>
          </div>
          {capabilities?.can_capture_photo && (
            <div className="mt-3">
              <SecureGatePhotoCapture checkInId={checkInId} evidenceType="VEHICLE" instructions="Fotografía del vehículo." onAssociated={onChanged} />
              <SecureGatePhotoCapture checkInId={checkInId} evidenceType="PLATE" instructions="Fotografía de la placa." onAssociated={onChanged} />
            </div>
          )}
        </div>
      )}

      {/* Conductor */}
      {step === 1 && (
        <div className="rounded-xl border border-slate-200 bg-white p-4 text-xs">
          <h2 className="text-sm font-bold text-slate-800">Inspección del conductor</h2>
          <div className="mt-2 grid grid-cols-2 gap-3">
            <div>
              <div className="font-semibold text-slate-600">Esperado</div>
              <dl className="mt-1 space-y-0.5">
                <dt className="text-slate-500">Nombre:</dt><dd>{detail.driver_inspection?.expected_driver_summary?.full_name ?? '—'}</dd>
                <dt className="text-slate-500">Documento:</dt><dd className="font-mono">{detail.driver_inspection?.expected_driver_summary?.document_number_redacted ?? '—'}</dd>
                <dt className="text-slate-500">Licencia:</dt><dd className="font-mono">{detail.driver_inspection?.expected_driver_summary?.license_number_redacted ?? '—'}</dd>
              </dl>
            </div>
            <div>
              <div className="font-semibold text-slate-600">Observado</div>
              {detail.driver_inspection && (
                <dl className="mt-1 space-y-0.5">
                  <dt className="text-slate-500">Coincidencia:</dt><dd><StatusPill tone={detail.driver_inspection.driver_match_status === 'MATCH' ? 'success' : 'warning'}>{detail.driver_inspection.driver_match_status}</StatusPill></dd>
                  <dt className="text-slate-500">Licencia:</dt><dd><StatusPill tone={detail.driver_inspection.license_status === 'VALID' ? 'success' : 'danger'}>{licenseStatusLabel(detail.driver_inspection.license_status)}</StatusPill></dd>
                </dl>
              )}
            </div>
          </div>
          <p className="mt-2 text-[11px] text-slate-500">No se realiza reconocimiento facial ni se crean embeddings.</p>
        </div>
      )}

      {/* Documentos */}
      {step === 2 && (
        <div className="rounded-xl border border-slate-200 bg-white p-4 text-xs">
          <h2 className="text-sm font-bold text-slate-800">Documentos y guías</h2>
          {detail.presented_documents.length === 0 ? <EmptyState title="Sin documentos presentados" /> : (
            <table className="mt-2 min-w-full divide-y divide-slate-100">
              <thead className="bg-slate-50 text-slate-500"><tr>
                <th className="px-2 py-1.5 text-left">Tipo</th><th className="px-2 py-1.5 text-left">Presentado</th><th className="px-2 py-1.5 text-left">Verificación</th>
              </tr></thead>
              <tbody className="divide-y divide-slate-100">
                {detail.presented_documents.map((d) => (
                  <tr key={d.id}>
                    <td className="px-2 py-1.5">{d.document_type}</td>
                    <td className="px-2 py-1.5">{d.presented ? 'Sí' : 'No'}</td>
                    <td className="px-2 py-1.5">{verificationStateLabel(d.verification_state)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Precinto */}
      {step === 3 && (
        <div className="rounded-xl border border-slate-200 bg-white p-4 text-xs">
          <h2 className="text-sm font-bold text-slate-800">Control de precinto</h2>
          <div className="mt-2 grid grid-cols-2 gap-3">
            <div>
              <div className="font-semibold text-slate-600">Esperado</div>
              <div className="mt-1 font-mono">{detail.seal_inspection?.expected_number ?? '—'}</div>
            </div>
            <div>
              <div className="font-semibold text-slate-600">Observado</div>
              <input value={sealNumber} onChange={(e) => setSealNumber(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-sm" placeholder="Número del precinto" />
              <select value={sealStatus} onChange={(e) => setSealStatus(e.target.value as never)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm">
                {['INTACT', 'BROKEN', 'TAMPERED', 'DAMAGED', 'ABSENT', 'ILLEGIBLE', 'NOT_APPLICABLE'].map((s) => <option key={s} value={s}>{sealPhysicalStatusLabel(s as never)}</option>)}
              </select>
              <button type="button" onClick={() => void saveSeal()} className="mt-1 rounded-lg bg-[#1F4E6D] px-3 py-1 text-[11px] font-semibold text-white hover:bg-[#173a55]">Guardar precinto</button>
            </div>
          </div>
          {detail.seal_inspection?.is_critical && (
            <p className="mt-2 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-rose-700">Alerta crítica: precinto roto/manipulado. No autorización ordinaria.</p>
          )}
          {capabilities?.can_capture_photo && (
            <div className="mt-3">
              <SecureGatePhotoCapture checkInId={checkInId} evidenceType="SEAL" required={detail.seal_inspection?.is_critical ?? false} instructions="Fotografía del precinto." onAssociated={onChanged} />
            </div>
          )}
        </div>
      )}

      {/* Fotografías */}
      {step === 4 && (
        <div className="space-y-3">
          <SecureGatePhotoCapture checkInId={checkInId} evidenceType="EXTERIOR_CONDITION" instructions="Condición exterior del vehículo." onAssociated={onChanged} />
          <SecureGatePhotoCapture checkInId={checkInId} evidenceType="SECURITY" instructions="Evidencia de seguridad." onAssociated={onChanged} />
        </div>
      )}

      {/* Checklist */}
      {step === 5 && (
        <div className="rounded-xl border border-slate-200 bg-white p-4 text-xs">
          <h2 className="text-sm font-bold text-slate-800">Checklist</h2>
          {detail.check_results.length === 0 ? <EmptyState title="Sin checks definidos" /> : (
            <ul className="mt-2 divide-y divide-slate-100">
              {detail.check_results.map((c) => (
                <li key={c.id} className="grid grid-cols-3 items-center gap-2 py-1.5">
                  <span>{c.check_name}{c.is_blocking && <span className="ml-1 text-rose-500"><LogisticsIcon name="alert" size={14} aria-hidden /></span>}</span>
                  <span>{c.result ? checkResultLabel(c.result) : 'No verificado'}</span>
                  <select value={c.result ?? ''} onChange={(e) => void setCheckResult(c.id, e.target.value as GateCheckResultValue)} disabled={!capabilities?.can_manage_checks}
                    className="rounded-lg border border-slate-300 px-2 py-1 text-xs">
                    <option value="">No verificado</option>
                    {RESULT_OPTIONS.map((r) => <option key={r} value={r}>{checkResultLabel(r)}</option>)}
                  </select>
                </li>
              ))}
            </ul>
          )}
          {detail.progress && (
            <div className="mt-2 rounded-lg border border-slate-100 bg-slate-50 p-2">
              <div className="font-semibold">Progreso (backend)</div>
              <div className="text-slate-500">Completados: {detail.progress.completed}/{detail.progress.total_checks} · Fallidos: {detail.progress.failed} · Bloqueantes: {detail.progress.blocking} · Excepciones pendientes: {detail.progress.exceptions_pending}</div>
              <div className="text-[11px] text-slate-400">El resultado final lo valida el backend.</div>
            </div>
          )}
        </div>
      )}

      {/* Decisión */}
      {step === 6 && (
        <div className="rounded-xl border border-slate-200 bg-white p-4 text-xs">
          <h2 className="text-sm font-bold text-slate-800">Decisión</h2>
          <p className="mt-1 text-slate-500">La autorización la valida el backend. No se marca autorizado localmente.</p>
          {detail.progress && (
            <div className="mt-2">
              {detail.progress.can_proceed_to_decision
                ? <StatusPill tone="success">Listo para decisión (según backend)</StatusPill>
                : <StatusPill tone="warning">No listo para decisión</StatusPill>}
            </div>
          )}
        </div>
      )}
    </div>
  )
}