import { useCallback, useEffect, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { driversApi } from '../api/drivers-api'
import { Button } from '../components/common/Button'
import { PageHeader } from '../components/common/PageHeader'
import { LoadingScreen } from '../components/common/LoadingScreen'
import { Alert } from '../components/common/Alert'
import { EmptyState } from '../components/common/EmptyState'
import {
  DriverComplianceBadge,
  DriverEligibilityBadge,
  DriverLifecycleBadge,
  DriverLicenseBadge,
  DriverPhotoBadge,
  ExpirationChip,
} from '../components/drivers/DriverStatusBadge'
import {
  BlockDriverDialog,
  RetireDriverDialog,
  SuspendDriverDialog,
} from '../components/drivers/DriverActionDialogs'
import { useSensitiveOperationGuard } from '../features/continuous-auth/hooks/useSensitiveOperationGuard'
import { getErrorMessage } from '../utils/errors'
import type {
  Driver,
  DriverCompliance,
  DriverContact,
  DriverDocument,
  DriverEligibility,
  DriverHistoryEvent,
  DriverLicense,
  DriverOperationalRestriction,
  DriverPhoto,
  DriverVehicleCompatibilityResult,
  DriverVersion,
} from '../types/drivers'

type DriverTab =
  | 'summary'
  | 'identity'
  | 'licenses'
  | 'carrier'
  | 'contacts'
  | 'photo'
  | 'documents'
  | 'restrictions'
  | 'compliance'
  | 'compatibility'
  | 'versions'
  | 'history'

const TABS: { id: DriverTab; label: string }[] = [
  { id: 'summary', label: 'Resumen' },
  { id: 'identity', label: 'Identidad' },
  { id: 'licenses', label: 'Licencias' },
  { id: 'carrier', label: 'Transportista' },
  { id: 'contacts', label: 'Contacto' },
  { id: 'photo', label: 'Fotografía' },
  { id: 'documents', label: 'Documentos' },
  { id: 'restrictions', label: 'Restricciones' },
  { id: 'compliance', label: 'Cumplimiento' },
  { id: 'compatibility', label: 'Compatibilidad' },
  { id: 'versions', label: 'Versiones' },
  { id: 'history', label: 'Historial' },
]

export function DriverDetailPage() {
  const { driverId } = useParams<{ driverId: string }>()
  const [searchParams, setSearchParams] = useSearchParams()
  const navigate = useNavigate()
  const { guardSensitiveAction } = useSensitiveOperationGuard()

  const tab = (searchParams.get('tab') as DriverTab) ?? 'summary'
  const setTab = (t: DriverTab) => setSearchParams({ tab: t })

  const [driver, setDriver] = useState<Driver | null>(null)
  const [compliance, setCompliance] = useState<DriverCompliance | null>(null)
  const [eligibility, setEligibility] = useState<DriverEligibility | null>(null)
  const [licenses, setLicenses] = useState<DriverLicense[]>([])
  const [photos, setPhotos] = useState<DriverPhoto[]>([])
  const [restrictions, setRestrictions] = useState<DriverOperationalRestriction[]>([])
  const [versions, setVersions] = useState<DriverVersion[]>([])
  const [history, setHistory] = useState<DriverHistoryEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)

  const [showBlock, setShowBlock] = useState(false)
  const [showSuspend, setShowSuspend] = useState(false)
  const [showRetire, setShowRetire] = useState(false)
  const [actionLoading, setActionLoading] = useState(false)

  const load = useCallback(async () => {
    if (!driverId) return
    setLoading(true)
    setError(null)
    try {
      const drv = await driversApi.get(driverId)
      setDriver(drv)

      const [compRes, eligRes, licRes, photoRes, restRes, verRes, histRes] = await Promise.allSettled([
        driversApi.getCompliance(driverId).catch(() => null),
        driversApi.getEligibility(driverId).catch(() => null),
        driversApi.listLicenses(driverId).catch(() => []),
        driversApi.listPhotos(driverId).catch(() => []),
        driversApi.listRestrictions(driverId).catch(() => []),
        driversApi.listVersions(driverId).catch(() => []),
        driversApi.getHistory(driverId).catch(() => []),
      ])

      if (compRes.status === 'fulfilled') setCompliance(compRes.value)
      if (eligRes.status === 'fulfilled') setEligibility(eligRes.value)
      if (licRes.status === 'fulfilled') setLicenses(licRes.value)
      if (photoRes.status === 'fulfilled') setPhotos(photoRes.value)
      if (restRes.status === 'fulfilled') setRestrictions(restRes.value)
      if (verRes.status === 'fulfilled') setVersions(verRes.value)
      if (histRes.status === 'fulfilled') setHistory(histRes.value)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [driverId])

  useEffect(() => {
    void load()
  }, [load])

  const refreshDriver = useCallback(async () => {
    if (!driverId) return
    try {
      const drv = await driversApi.get(driverId)
      setDriver(drv)
    } catch { /* ignore */ }
  }, [driverId])

  const handleAction = async (action: () => Promise<unknown>) => {
    setActionLoading(true)
    setActionError(null)
    try {
      await action()
      await refreshDriver()
    } catch (err) {
      setActionError(getErrorMessage(err))
    } finally {
      setActionLoading(false)
    }
  }

  const guardAction = (fn: () => Promise<unknown>) => () => {
    void guardSensitiveAction(async () => {
      await handleAction(fn)
    })
  }

  if (loading) return <LoadingScreen message="Cargando conductor…" />
  if (error) {
    return (
      <div className="mx-auto max-w-4xl p-6">
        <Alert variant="error">{error}</Alert>
        <div className="mt-4">
          <Button variant="ghost" onClick={() => navigate('/logistics/drivers')}>Volver</Button>
        </div>
      </div>
    )
  }
  if (!driver) {
    return (
      <div className="mx-auto max-w-4xl p-6">
        <EmptyState title="Conductor no encontrado" description="El conductor solicitado no existe o ha sido archivado." />
      </div>
    )
  }

  const caps = driver.capabilities

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      {/* Encabezado */}
      <PageHeader
        eyebrow={`Código ${driver.internal_code}`}
        title={driver.full_name}
        description={driver.identity_document_number_redacted}
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <DriverLifecycleBadge status={driver.lifecycle_status} />
            <DriverComplianceBadge status={driver.compliance_status} />
            <DriverEligibilityBadge status={driver.eligibility_status} />
            {driver.has_photo
              ? <DriverPhotoBadge status={driver.photo_status} />
              : <span className="text-xs text-slate-400">Sin foto</span>}
            {caps.can_block && driver.lifecycle_status !== 'BLOCKED' && (
              <Button variant="danger" size="small" onClick={() => setShowBlock(true)} disabled={actionLoading}>Bloquear</Button>
            )}
            {caps.can_suspend && driver.lifecycle_status === 'ACTIVE' && (
              <Button variant="secondary" size="small" onClick={() => setShowSuspend(true)} disabled={actionLoading}>Suspender</Button>
            )}
            {caps.can_unblock && driver.lifecycle_status === 'BLOCKED' && (
              <Button size="small" onClick={() => guardAction(() => driversApi.unblock(driver.id))()} disabled={actionLoading}>Desbloquear</Button>
            )}
            {caps.can_activate && driver.lifecycle_status === 'INACTIVE' && (
              <Button size="small" onClick={() => guardAction(() => driversApi.activate(driver.id))()} disabled={actionLoading}>Activar</Button>
            )}
            {caps.can_retire && driver.lifecycle_status !== 'RETIRED' && (
              <Button variant="danger" size="small" onClick={() => setShowRetire(true)} disabled={actionLoading}>Retirar</Button>
            )}
          </div>
        }
      />

      {/* Info rápida */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        <div className="rounded-lg border border-slate-200 bg-white px-3 py-2">
          <div className="text-xs text-slate-500">Licencia</div>
          <div className="text-sm font-medium text-slate-900">{driver.primary_license_number_redacted ?? '—'}</div>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white px-3 py-2">
          <div className="text-xs text-slate-500">Vencimiento</div>
          <div className="text-sm font-medium text-slate-900">
            <ExpirationChip days={driver.primary_license_days_until_expiration} isExpired={driver.primary_license_is_expired} />
          </div>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white px-3 py-2">
          <div className="text-xs text-slate-500">Transportista</div>
          <div className="text-sm font-medium text-slate-900">{driver.carrier_partner_name ?? '—'}</div>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white px-3 py-2">
          <div className="text-xs text-slate-500">Restricciones</div>
          <div className="text-sm font-medium text-slate-900">{driver.restrictions_count}</div>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white px-3 py-2">
          <div className="text-xs text-slate-500">Versión activa</div>
          <div className="text-sm font-medium text-slate-900">v{driver.active_version_number}</div>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white px-3 py-2">
          <div className="text-xs text-slate-500">Identidad</div>
          <div className="text-sm font-medium text-slate-900">{driver.identity_verification_status}</div>
        </div>
      </div>

      {actionError && <Alert variant="error">{actionError}</Alert>}

      {/* Tabs */}
      <div className="flex flex-wrap gap-1 border-b border-slate-200">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`px-3 py-2 text-sm font-medium border-b-2 transition-colors ${
              tab === t.id
                ? 'border-orange-500 text-orange-600'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Contenido de tabs */}
      <div className="min-h-[300px]">
        {tab === 'summary' && <SummaryTab driver={driver} compliance={compliance} eligibility={eligibility} />}
        {tab === 'identity' && <IdentityTab driver={driver} />}
        {tab === 'licenses' && <LicensesTab licenses={licenses} canManage={caps.can_manage_licenses} />}
        {tab === 'carrier' && <CarrierTab driver={driver} canManage={caps.can_manage_carrier} />}
        {tab === 'contacts' && <ContactsTab driverId={driver.id} canManage={caps.can_manage_contacts} />}
        {tab === 'photo' && <PhotoTab photos={photos} canView={caps.can_view_photo} canManage={caps.can_manage_photo} />}
        {tab === 'documents' && <DocumentsTab driverId={driver.id} canManage={caps.can_manage_documents} />}
        {tab === 'restrictions' && <RestrictionsTab restrictions={restrictions} canManage={caps.can_manage_restrictions} />}
        {tab === 'compliance' && <ComplianceTab compliance={compliance} />}
        {tab === 'compatibility' && <CompatibilityTab driverId={driver.id} canEvaluate={caps.can_evaluate_vehicle_compatibility} />}
        {tab === 'versions' && <VersionsTab versions={versions} canCreate={caps.can_create_version} />}
        {tab === 'history' && <HistoryTab history={history} />}
      </div>

      {/* Diálogos */}
      <BlockDriverDialog
        open={showBlock}
        onConfirm={async (reason) => { await guardAction(() => driversApi.block(driver.id, reason))(); setShowBlock(false) }}
        onClose={() => setShowBlock(false)}
      />
      <SuspendDriverDialog
        open={showSuspend}
        onConfirm={async (reason) => { await guardAction(() => driversApi.suspend(driver.id, reason))(); setShowSuspend(false) }}
        onClose={() => setShowSuspend(false)}
      />
      <RetireDriverDialog
        open={showRetire}
        onConfirm={async (reason) => { await guardAction(() => driversApi.retire(driver.id, reason))(); setShowRetire(false) }}
        onClose={() => setShowRetire(false)}
      />
    </div>
  )
}

// ─── Tab Panels ─────────────────────────────────────────────────────────────

function SummaryTab({ driver, compliance, eligibility }: {
  driver: Driver
  compliance: DriverCompliance | null
  eligibility: DriverEligibility | null
}) {
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <div className="rounded-xl border border-slate-200 p-4">
        <h3 className="mb-3 text-sm font-semibold text-slate-700">Datos generales</h3>
        <dl className="space-y-2 text-sm">
          <div className="flex justify-between"><dt className="text-slate-500">Código</dt><dd className="font-mono text-slate-900">{driver.internal_code}</dd></div>
          <div className="flex justify-between"><dt className="text-slate-500">Nombre completo</dt><dd className="text-slate-900">{driver.full_name}</dd></div>
          <div className="flex justify-between"><dt className="text-slate-500">Documento</dt><dd className="text-slate-900">{driver.identity_document_number_redacted}</dd></div>
          <div className="flex justify-between"><dt className="text-slate-500">Nacionalidad</dt><dd className="text-slate-900">{driver.nationality ?? '—'}</dd></div>
          <div className="flex justify-between"><dt className="text-slate-500">Transportista</dt><dd className="text-slate-900">{driver.carrier_partner_name ?? '—'}</dd></div>
        </dl>
      </div>
      <div className="rounded-xl border border-slate-200 p-4">
        <h3 className="mb-3 text-sm font-semibold text-slate-700">Licencia principal</h3>
        <dl className="space-y-2 text-sm">
          <div className="flex justify-between"><dt className="text-slate-500">Número</dt><dd className="text-slate-900">{driver.primary_license_number_redacted ?? '—'}</dd></div>
          <div className="flex justify-between"><dt className="text-slate-500">Vencimiento</dt><dd><ExpirationChip days={driver.primary_license_days_until_expiration} isExpired={driver.primary_license_is_expired} /></dd></div>
          <div className="flex justify-between"><dt className="text-slate-500">Categorías</dt><dd className="text-slate-900">{driver.primary_license_categories.join(', ') || '—'}</dd></div>
        </dl>
      </div>
      {compliance && (
        <div className="rounded-xl border border-slate-200 p-4">
          <h3 className="mb-3 text-sm font-semibold text-slate-700">Cumplimiento</h3>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between"><dt className="text-slate-500">Estado</dt><dd><DriverComplianceBadge status={compliance.general_status} /></dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Docs. presentes</dt><dd className="text-slate-900">{compliance.present_documents_count}/{compliance.required_documents_count}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Docs. vencidos</dt><dd className="text-slate-900">{compliance.expired_documents_count}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Restricciones</dt><dd className="text-slate-900">{compliance.restrictions_count}</dd></div>
          </dl>
          {compliance.blocking_reasons.length > 0 && (
            <div className="mt-2 rounded-lg bg-rose-50 p-2 text-xs text-rose-700">
              {compliance.blocking_reasons.map((r) => <div key={r}>• {r}</div>)}
            </div>
          )}
        </div>
      )}
      {eligibility && (
        <div className="rounded-xl border border-slate-200 p-4">
          <h3 className="mb-3 text-sm font-semibold text-slate-700">Elegibilidad</h3>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between"><dt className="text-slate-500">Estado</dt><dd><DriverEligibilityBadge status={eligibility.status} /></dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Licencia válida</dt><dd className="text-slate-900">{eligibility.license_valid ? 'Sí' : 'No'}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Transportista válido</dt><dd className="text-slate-900">{eligibility.carrier_valid ? 'Sí' : 'No'}</dd></div>
          </dl>
          <p className="mt-2 text-xs text-slate-400">La elegibilidad del maestro no representa asignación a un viaje ni disponibilidad horaria.</p>
        </div>
      )}
    </div>
  )
}

function IdentityTab({ driver }: { driver: Driver }) {
  return (
    <div className="rounded-xl border border-slate-200 p-4">
      <h3 className="mb-3 text-sm font-semibold text-slate-700">Documentos de identidad</h3>
      <dl className="space-y-2 text-sm">
        <div className="flex justify-between"><dt className="text-slate-500">Tipo</dt><dd className="text-slate-900">{driver.identity_document_type ?? '—'}</dd></div>
        <div className="flex justify-between"><dt className="text-slate-500">Número (redactado)</dt><dd className="text-slate-900">{driver.identity_document_number_redacted}</dd></div>
        <div className="flex justify-between"><dt className="text-slate-500">Verificación</dt><dd className="text-slate-900">{driver.identity_verification_status}</dd></div>
      </dl>
      {!driver.capabilities.can_view_sensitive_identity && (
        <p className="mt-3 text-xs text-amber-600">No tienes permiso para ver el documento completo. Los valores están redactados.</p>
      )}
    </div>
  )
}

function LicensesTab({ licenses, canManage: _canManage }: {
  licenses: DriverLicense[]
  canManage: boolean
}) {
  if (licenses.length === 0) {
    return <EmptyState title="Sin licencias" description="Este conductor no tiene licencias registradas." />
  }
  return (
    <div className="space-y-3">
      {licenses.map((lic) => (
        <div key={lic.id} className="rounded-xl border border-slate-200 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <DriverLicenseBadge status={lic.status} />
              {lic.is_primary && <span className="rounded bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-700 border border-amber-300">Principal</span>}
            </div>
            <ExpirationChip days={lic.days_until_expiration} isExpired={lic.is_expired} />
          </div>
          <dl className="mt-3 grid grid-cols-2 gap-2 text-sm sm:grid-cols-4">
            <div><dt className="text-xs text-slate-500">Número</dt><dd className="text-slate-900">{lic.license_number_redacted}</dd></div>
            <div><dt className="text-xs text-slate-500">País</dt><dd className="text-slate-900">{lic.country}</dd></div>
            <div><dt className="text-xs text-slate-500">Autoridad</dt><dd className="text-slate-900">{lic.issuing_authority}</dd></div>
            <div><dt className="text-xs text-slate-500">Vencimiento</dt><dd className="text-slate-900">{lic.expiration_date ?? '—'}</dd></div>
          </dl>
          {lic.categories.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {lic.categories.map((c) => (
                <span key={c.id} className="rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-600">{c.category_code}</span>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

function CarrierTab({ driver, canManage: _canManage }: {
  driver: Driver
  canManage: boolean
}) {
  return (
    <div className="rounded-xl border border-slate-200 p-4">
      <h3 className="mb-3 text-sm font-semibold text-slate-700">Transportista asignado</h3>
      {driver.carrier_partner_id ? (
        <dl className="space-y-2 text-sm">
          <div className="flex justify-between"><dt className="text-slate-500">Transportista</dt><dd className="text-slate-900">{driver.carrier_partner_name}</dd></div>
          <div className="flex justify-between"><dt className="text-slate-500">Código</dt><dd className="font-mono text-slate-900">{driver.carrier_partner_code}</dd></div>
        </dl>
      ) : (
        <EmptyState title="Sin transportista" description="Este conductor no tiene un transportista asignado." />
      )}
    </div>
  )
}

function ContactsTab({ driverId, canManage: _canManage }: { driverId: string; canManage: boolean }) {
  const [contacts, setContacts] = useState<DriverContact[]>([])

  useEffect(() => {
    void driversApi.listContacts(driverId).then(setContacts).catch(() => setContacts([]))
  }, [driverId])

  if (contacts.length === 0) {
    return <EmptyState title="Sin contactos" description="Este conductor no tiene contactos registrados." />
  }
  return (
    <div className="space-y-2">
      {contacts.map((c) => (
        <div key={c.id} className="flex items-center justify-between rounded-lg border border-slate-200 px-3 py-2 text-sm">
          <div className="flex items-center gap-3">
            <span className="rounded bg-slate-100 px-2 py-0.5 text-xs">{c.contact_type}</span>
            <span className="text-slate-900">{c.value_redacted}</span>
            {c.is_primary && <span className="text-xs text-amber-600">Principal</span>}
          </div>
          <span className={`text-xs ${c.status === 'ACTIVE' ? 'text-emerald-600' : 'text-slate-400'}`}>{c.status}</span>
        </div>
      ))}
    </div>
  )
}

function PhotoTab({ photos, canView, canManage: _canManage }: {
  photos: DriverPhoto[]
  canView: boolean
  canManage: boolean
}) {
  const current = photos.find((p) => p.is_current)

  if (!canView) {
    return <div className="rounded-xl border border-slate-200 p-4"><p className="text-sm text-slate-500">No tienes permiso para ver la fotografía.</p></div>
  }

  return (
    <div className="rounded-xl border border-slate-200 p-4">
      <h3 className="mb-3 text-sm font-semibold text-slate-700">Fotografía</h3>
      {current ? (
        <div className="flex items-center gap-4">
          <div className="flex h-20 w-20 items-center justify-center rounded-lg bg-slate-100 text-slate-400">
            {current.file_reference_id ? 'Foto' : 'N/A'}
          </div>
          <div className="text-sm">
            <DriverPhotoBadge status={current.status} />
            <dl className="mt-2 space-y-1">
              <div className="text-slate-500">Tipo: {current.photo_type}</div>
              <div className="text-slate-500">Fecha: {current.captured_at ?? '—'}</div>
              <div className="text-slate-500">Hash parcial: {current.partial_hash ?? '—'}</div>
            </dl>
          </div>
        </div>
      ) : (
        <div className="flex items-center gap-4">
          <div className="flex h-20 w-20 items-center justify-center rounded-lg bg-slate-100 text-slate-300">
            Sin foto
          </div>
          <div className="text-sm text-slate-500">
            <p>No hay fotografía asociada.</p>
            <p className="mt-1 text-xs text-blue-600">PENDIENTE_FASE_030: La centralización de archivos se implementará en la siguiente fase.</p>
          </div>
        </div>
      )}
    </div>
  )
}

function DocumentsTab({ driverId, canManage: _canManage }: { driverId: string; canManage: boolean }) {
  const [docs, setDocs] = useState<DriverDocument[]>([])

  useEffect(() => {
    void driversApi.listDocuments(driverId).then(setDocs).catch(() => setDocs([]))
  }, [driverId])

  if (docs.length === 0) {
    return <EmptyState title="Sin documentos" description="Este conductor no tiene documentos registrados." />
  }
  return (
    <div className="space-y-2">
      {docs.map((d) => (
        <div key={d.id} className="rounded-lg border border-slate-200 px-3 py-2 text-sm">
          <div className="flex items-center justify-between">
            <span className="font-medium text-slate-900">{d.document_type_label}</span>
            <span className={`text-xs ${d.review_status === 'VERIFIED' ? 'text-emerald-600' : d.review_status === 'PENDING' ? 'text-amber-600' : 'text-rose-600'}`}>
              {d.review_status}
            </span>
          </div>
          <dl className="mt-1 grid grid-cols-2 gap-1 text-xs sm:grid-cols-3">
            <div><span className="text-slate-500">Número: </span><span className="text-slate-700">{d.document_number_redacted ?? '—'}</span></div>
            <div><span className="text-slate-500">Emisor: </span><span className="text-slate-700">{d.issuer_name ?? '—'}</span></div>
            <div><span className="text-slate-500">Vencimiento: </span><span className="text-slate-700">{d.expiration_date ?? '—'}</span></div>
          </dl>
        </div>
      ))}
    </div>
  )
}

function RestrictionsTab({ restrictions, canManage: _canManage }: {
  restrictions: DriverOperationalRestriction[]
  canManage: boolean
}) {
  if (restrictions.length === 0) {
    return <EmptyState title="Sin restricciones" description="Este conductor no tiene restricciones operativas." />
  }
  return (
    <div className="space-y-2">
      {restrictions.map((r) => (
        <div key={r.id} className="rounded-lg border border-slate-200 px-3 py-2 text-sm">
          <div className="flex items-center justify-between">
            <span className="font-medium text-slate-900">{r.type}</span>
            <div className="flex items-center gap-2">
              {r.is_blocking && <span className="rounded bg-rose-50 px-2 py-0.5 text-xs font-medium text-rose-700 border border-rose-300">Bloqueante</span>}
              <span className={`text-xs ${r.status === 'ACTIVE' ? 'text-emerald-600' : 'text-slate-400'}`}>{r.status}</span>
            </div>
          </div>
          <p className="mt-1 text-xs text-slate-500">{r.description_summary}</p>
          <div className="mt-1 text-xs text-slate-400">Severidad: {r.severity} · Desde: {r.effective_from} · Hasta: {r.effective_until ?? '—'}</div>
        </div>
      ))}
    </div>
  )
}

function ComplianceTab({ compliance }: { compliance: DriverCompliance | null }) {
  if (!compliance) {
    return <EmptyState title="Sin datos de cumplimiento" description="No hay datos de cumplimiento disponibles." />
  }
  return (
    <div className="rounded-xl border border-slate-200 p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-700">Estado de cumplimiento</h3>
        <DriverComplianceBadge status={compliance.general_status} />
      </div>
      <dl className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-3">
        <div className="rounded-lg bg-slate-50 p-2"><div className="text-xs text-slate-500">Identidad válida</div><div className="text-slate-900">{compliance.identity_valid ? 'Sí' : 'No'}</div></div>
        <div className="rounded-lg bg-slate-50 p-2"><div className="text-xs text-slate-500">Licencia válida</div><div className="text-slate-900">{compliance.license_valid ? 'Sí' : 'No'}</div></div>
        <div className="rounded-lg bg-slate-50 p-2"><div className="text-xs text-slate-500">Transportista válido</div><div className="text-slate-900">{compliance.carrier_valid ? 'Sí' : 'No'}</div></div>
        <div className="rounded-lg bg-slate-50 p-2"><div className="text-xs text-slate-500">Docs. presentes</div><div className="text-slate-900">{compliance.present_documents_count}/{compliance.required_documents_count}</div></div>
        <div className="rounded-lg bg-slate-50 p-2"><div className="text-xs text-slate-500">Docs. faltantes</div><div className="text-slate-900">{compliance.missing_documents_count}</div></div>
        <div className="rounded-lg bg-slate-50 p-2"><div className="text-xs text-slate-500">Docs. vencidos</div><div className="text-slate-900">{compliance.expired_documents_count}</div></div>
      </dl>
      {compliance.blocking_reasons.length > 0 && (
        <div className="mt-3 rounded-lg bg-rose-50 p-3 text-sm text-rose-700">
          <div className="font-medium">Motivos bloqueantes:</div>
          <ul className="mt-1 list-disc pl-5">{compliance.blocking_reasons.map((r) => <li key={r}>{r}</li>)}</ul>
        </div>
      )}
      {compliance.warnings.length > 0 && (
        <div className="mt-2 rounded-lg bg-amber-50 p-3 text-sm text-amber-700">
          <div className="font-medium">Advertencias:</div>
          <ul className="mt-1 list-disc pl-5">{compliance.warnings.map((r) => <li key={r}>{r}</li>)}</ul>
        </div>
      )}
      <p className="mt-3 text-xs text-slate-400">Evaluación: {compliance.evaluation_date}</p>
    </div>
  )
}

function CompatibilityTab({ driverId, canEvaluate }: { driverId: string; canEvaluate: boolean }) {
  const [result, setResult] = useState<DriverVehicleCompatibilityResult | null>(null)
  const [vehicleId, setVehicleId] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const evaluate = async () => {
    if (!vehicleId.trim()) return
    setLoading(true)
    setError(null)
    try {
      const res = await driversApi.evaluateVehicleCompatibility(driverId, { vehicle_id: vehicleId.trim() })
      setResult(res)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="rounded-xl border border-slate-200 p-4">
      <h3 className="mb-3 text-sm font-semibold text-slate-700">Compatibilidad con vehículo</h3>
      <p className="mb-3 text-xs text-slate-500">Evalúa si el conductor es compatible con un vehículo específico. No asigna el vehículo ni crea despachos.</p>
      {!canEvaluate && <p className="text-sm text-amber-600">No tienes permiso para evaluar compatibilidad.</p>}
      {canEvaluate && (
        <>
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="ID del vehículo"
              value={vehicleId}
              onChange={(e) => setVehicleId(e.target.value)}
              className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
            <Button onClick={evaluate} disabled={loading || !vehicleId.trim()} isLoading={loading}>Evaluar</Button>
          </div>
          {error && <div className="mt-3 rounded-lg bg-rose-50 border border-rose-200 px-3 py-2 text-sm text-rose-700">{error}</div>}
          {result && (
            <div className="mt-4 space-y-2 text-sm">
              <div className="flex items-center gap-2">
                <span className="text-slate-500">Resultado:</span>
                {result.eligible
                  ? <span className="rounded bg-emerald-50 px-2 py-0.5 text-emerald-700 border border-emerald-300">Elegible</span>
                  : result.requires_review
                    ? <span className="rounded bg-amber-50 px-2 py-0.5 text-amber-700 border border-amber-300">Requiere revisión</span>
                    : <span className="rounded bg-rose-50 px-2 py-0.5 text-rose-700 border border-rose-300">No elegible</span>}
              </div>
              {result.compatible_categories.length > 0 && <div className="text-slate-700">Categorías compatibles: {result.compatible_categories.join(', ')}</div>}
              {result.missing_categories.length > 0 && <div className="text-amber-700">Categorías faltantes: {result.missing_categories.join(', ')}</div>}
              {result.blocking_reasons.length > 0 && <div className="rounded-lg bg-rose-50 p-2 text-rose-700">{result.blocking_reasons.map((r) => <div key={r}>• {r}</div>)}</div>}
              {result.warnings.length > 0 && <div className="rounded-lg bg-amber-50 p-2 text-amber-700">{result.warnings.map((r) => <div key={r}>• {r}</div>)}</div>}
            </div>
          )}
        </>
      )}
    </div>
  )
}

function VersionsTab({ versions, canCreate }: {
  versions: DriverVersion[]
  canCreate: boolean
}) {
  return (
    <div className="space-y-3">
      {canCreate && (
        <div className="text-xs text-slate-400">Usa el botón en la ficha para crear una nueva versión.</div>
      )}
      {versions.length === 0 ? (
        <EmptyState title="Sin versiones" description="Este conductor no tiene versiones registradas." />
      ) : (
        versions.map((v) => (
          <div key={v.id} className="rounded-xl border border-slate-200 p-3 text-sm">
            <div className="flex items-center justify-between">
              <span className="font-medium">v{v.version_number}</span>
              <span className={`text-xs ${v.status === 'ACTIVE' ? 'text-emerald-600' : v.status === 'DRAFT' ? 'text-amber-600' : 'text-slate-400'}`}>{v.status}</span>
            </div>
            <div className="mt-1 text-xs text-slate-500">
              Identidad: {v.identity_redacted} · Licencia: {v.license_redacted} · Transportista: {v.carrier_partner_name ?? '—'}
            </div>
            <div className="text-xs text-slate-400">Creado por: {v.created_by_name} · {v.created_at}</div>
          </div>
        ))
      )}
    </div>
  )
}

function HistoryTab({ history }: { history: DriverHistoryEvent[] }) {
  if (history.length === 0) {
    return <EmptyState title="Sin historial" description="No hay eventos en el historial de este conductor." />
  }
  return (
    <div className="space-y-2">
      {history.map((h) => (
        <div key={h.id} className="flex gap-3 rounded-lg border border-slate-200 px-3 py-2 text-sm">
          <div className="flex-shrink-0">
            <span className="flex h-6 w-6 items-center justify-center rounded-full bg-slate-100 text-xs text-slate-500">{h.event_type[0]}</span>
          </div>
          <div className="flex-1">
            <div className="font-medium text-slate-900">{h.action_description}</div>
            <div className="text-xs text-slate-500">{h.event_type} · {h.result} · {h.user_name} · {h.created_at}</div>
            {h.reason && <div className="text-xs text-slate-400">Motivo: {h.reason}</div>}
          </div>
        </div>
      ))}
    </div>
  )
}