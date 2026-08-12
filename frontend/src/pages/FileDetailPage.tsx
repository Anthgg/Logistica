import { useCallback, useEffect, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { filesApi } from '../api/files-api'
import { Button } from '../components/common/Button'
import { PageHeader } from '../components/common/PageHeader'
import { LoadingScreen } from '../components/common/LoadingScreen'
import { EmptyState } from '../components/common/EmptyState'
import { Alert } from '../components/common/Alert'
import {
  FileClassificationBadge,
  FileIntegrityBadge,
  FileLifecycleBadge,
  FileScanBadge,
} from '../components/files/FileStatusBadge'
import { formatFileSize } from '../components/files/file-utils'
import { SecurePdfViewer } from '../components/common/SecurePdfViewer'
import { useSensitiveOperationGuard } from '../features/continuous-auth/hooks/useSensitiveOperationGuard'
import { getErrorMessage } from '../utils/errors'
import type {
  FileAssociation,
  FileAssetDetail,
  FileAccessInfo,
  FileHistoryEvent,
  FileIntegrity,
  FileLegalHold,
  FileVersion,
} from '../types/files'

type FileTab =
  | 'summary'
  | 'preview'
  | 'metadata'
  | 'associations'
  | 'versions'
  | 'evidence'
  | 'access'
  | 'integrity'
  | 'retention'
  | 'history'

const TABS: { id: FileTab; label: string }[] = [
  { id: 'summary', label: 'Resumen' },
  { id: 'preview', label: 'Preview' },
  { id: 'metadata', label: 'Metadatos' },
  { id: 'associations', label: 'Asociaciones' },
  { id: 'versions', label: 'Versiones' },
  { id: 'evidence', label: 'Evidencia' },
  { id: 'access', label: 'Acceso' },
  { id: 'integrity', label: 'Integridad' },
  { id: 'retention', label: 'Retención' },
  { id: 'history', label: 'Historial' },
]

export function FileDetailPage() {
  const { fileId } = useParams<{ fileId: string }>()
  const [searchParams, setSearchParams] = useSearchParams()
  const navigate = useNavigate()
  const { guardSensitiveAction } = useSensitiveOperationGuard()

  const tab = (searchParams.get('tab') as FileTab) ?? 'summary'
  const setTab = (t: FileTab) => setSearchParams({ tab: t })

  const [file, setFile] = useState<FileAssetDetail | null>(null)
  const [associations, setAssociations] = useState<FileAssociation[]>([])
  const [versions, setVersions] = useState<FileVersion[]>([])
  const [history, setHistory] = useState<FileHistoryEvent[]>([])
  const [integrity, setIntegrity] = useState<FileIntegrity | null>(null)
  const [accessInfo, setAccessInfo] = useState<FileAccessInfo | null>(null)
  const [legalHolds, setLegalHolds] = useState<FileLegalHold[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [showPreview, setShowPreview] = useState(false)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)

  const load = useCallback(async () => {
    if (!fileId) return
    setLoading(true)
    setError(null)
    try {
      const detail = await filesApi.get(fileId)
      setFile(detail)

      const [assocRes, verRes, histRes, intRes, accRes, lhRes] = await Promise.allSettled([
        filesApi.listAssociations(fileId).catch(() => []),
        filesApi.listVersions(fileId).catch(() => []),
        filesApi.getHistory(fileId).catch(() => []),
        filesApi.getIntegrity(fileId).catch(() => null),
        filesApi.getAccess(fileId).catch(() => null),
        filesApi.listLegalHolds(fileId).catch(() => []),
      ])

      if (assocRes.status === 'fulfilled') setAssociations(assocRes.value)
      if (verRes.status === 'fulfilled') setVersions(verRes.value)
      if (histRes.status === 'fulfilled') setHistory(histRes.value)
      if (intRes.status === 'fulfilled') setIntegrity(intRes.value)
      if (accRes.status === 'fulfilled') setAccessInfo(accRes.value)
      if (lhRes.status === 'fulfilled') setLegalHolds(lhRes.value)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [fileId])

  useEffect(() => {
    void load()
  }, [load])

  // Cleanup preview URL on unmount
  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl)
    }
  }, [previewUrl])

  const handlePreview = async () => {
    if (!fileId || !file?.capabilities.can_preview) return
    void guardSensitiveAction(async () => {
      try {
        const url = await filesApi.getPreviewBlobUrl(fileId)
        setPreviewUrl(url)
        setShowPreview(true)
      } catch (err) {
        setActionError(getErrorMessage(err))
      }
    })
  }

  const handleDownload = async () => {
    if (!fileId || !file?.capabilities.can_download) return
    void guardSensitiveAction(async () => {
      try {
        const { blob, filename } = await filesApi.downloadFile(fileId)
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = filename
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
      } catch (err) {
        setActionError(getErrorMessage(err))
      }
    })
  }

  const handleArchive = async () => {
    if (!fileId || !file?.capabilities.can_archive) return
    void guardSensitiveAction(async () => {
      try {
        await filesApi.archive(fileId, 'Archivado desde interfaz')
        await load()
      } catch (err) {
        setActionError(getErrorMessage(err))
      }
    })
  }

  if (loading) return <LoadingScreen message="Cargando archivo..." />
  if (error) {
    return (
      <div className="mx-auto max-w-4xl p-6">
        <Alert variant="error">{error}</Alert>
        <div className="mt-4"><Button variant="ghost" onClick={() => navigate('/logistics/files')}>Volver</Button></div>
      </div>
    )
  }
  if (!file) {
    return (
      <div className="mx-auto max-w-4xl p-6">
        <EmptyState title="Archivo no encontrado" description="El archivo solicitado no existe o ha sido eliminado." />
      </div>
    )
  }

  const caps = file.capabilities

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <PageHeader
        eyebrow={`Código ${file.code}`}
        title={file.title}
        description={`${file.asset_type} · ${formatFileSize(file.size_bytes)} · ${file.mime_type}`}
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <FileLifecycleBadge status={file.lifecycle_status} />
            <FileScanBadge status={file.scan_status} />
            <FileIntegrityBadge status={file.integrity_status} />
            <FileClassificationBadge classification={file.classification} />
            {caps.can_preview && file.lifecycle_status === 'AVAILABLE' && (
              <Button size="small" variant="secondary" onClick={handlePreview}>Preview</Button>
            )}
            {caps.can_download && file.lifecycle_status === 'AVAILABLE' && (
              <Button size="small" onClick={handleDownload}>Descargar</Button>
            )}
            {caps.can_archive && file.lifecycle_status === 'AVAILABLE' && (
              <Button size="small" variant="ghost" onClick={handleArchive}>Archivar</Button>
            )}
          </div>
        }
      />

      {/* Quick info */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        <div className="rounded-lg border border-slate-200 bg-white px-3 py-2">
          <div className="text-xs text-slate-500">Versión actual</div>
          <div className="text-sm font-medium text-slate-900">v{file.current_version_number}</div>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white px-3 py-2">
          <div className="text-xs text-slate-500">Hash parcial</div>
          <div className="text-sm font-mono text-slate-900">{file.partial_hash.slice(0, 12)}...</div>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white px-3 py-2">
          <div className="text-xs text-slate-500">Propietario</div>
          <div className="text-sm text-slate-900">{file.owner_name ?? '—'}</div>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white px-3 py-2">
          <div className="text-xs text-slate-500">Subido por</div>
          <div className="text-sm text-slate-900">{file.uploader_name ?? '—'}</div>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white px-3 py-2">
          <div className="text-xs text-slate-500">Asociaciones</div>
          <div className="text-sm text-slate-900">{file.association_count}</div>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white px-3 py-2">
          <div className="text-xs text-slate-500">Evidencias</div>
          <div className="text-sm text-slate-900">{file.evidence_count}</div>
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
              tab === t.id ? 'border-orange-500 text-orange-600' : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="min-h-[300px]">
        {tab === 'summary' && <SummaryTab file={file} legalHolds={legalHolds} />}
        {tab === 'preview' && <PreviewTab file={file} onPreview={handlePreview} />}
        {tab === 'metadata' && <MetadataTab file={file} />}
        {tab === 'associations' && <AssociationsTab associations={associations} canManage={caps.can_associate} fileId={file.id} onRefresh={load} />}
        {tab === 'versions' && <VersionsTab versions={versions} canUpload={caps.can_upload_version} fileId={file.id} />}
        {tab === 'evidence' && <EvidenceTab file={file} />}
        {tab === 'access' && <AccessTab accessInfo={accessInfo} canManage={caps.can_manage_access} fileId={file.id} />}
        {tab === 'integrity' && <IntegrityTab integrity={integrity} />}
        {tab === 'retention' && <RetentionTab file={file} legalHolds={legalHolds} />}
        {tab === 'history' && <HistoryTab history={history} />}
      </div>

      {/* PDF Preview modal */}
      <SecurePdfViewer
        isOpen={showPreview}
        title={file.title}
        code={file.code}
        fetchBlobUrl={async () => {
          if (!fileId) throw new Error('No file ID')
          return filesApi.getPreviewBlobUrl(fileId)
        }}
        onClose={() => { setShowPreview(false); if (previewUrl) { URL.revokeObjectURL(previewUrl); setPreviewUrl(null) } }}
        onDownload={handleDownload}
      />
    </div>
  )
}

// ─── Tab Panels ─────────────────────────────────────────────────────────────

function SummaryTab({ file, legalHolds }: { file: FileAssetDetail; legalHolds: FileLegalHold[] }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <div className="rounded-xl border border-slate-200 p-4">
        <h3 className="mb-3 text-sm font-semibold text-slate-700">Información general</h3>
        <dl className="space-y-2 text-sm">
          <div className="flex justify-between"><dt className="text-slate-500">Código</dt><dd className="font-mono text-slate-900">{file.code}</dd></div>
          <div className="flex justify-between"><dt className="text-slate-500">Título</dt><dd className="text-slate-900">{file.title}</dd></div>
          <div className="flex justify-between"><dt className="text-slate-500">Tipo</dt><dd className="text-slate-900">{file.asset_type}</dd></div>
          <div className="flex justify-between"><dt className="text-slate-500">MIME</dt><dd className="text-slate-900">{file.mime_type}</dd></div>
          <div className="flex justify-between"><dt className="text-slate-500">Tamaño</dt><dd className="text-slate-900">{formatFileSize(file.size_bytes)}</dd></div>
          <div className="flex justify-between"><dt className="text-slate-500">Versión</dt><dd className="text-slate-900">v{file.current_version_number}</dd></div>
        </dl>
      </div>
      <div className="rounded-xl border border-slate-200 p-4">
        <h3 className="mb-3 text-sm font-semibold text-slate-700">Seguridad y estado</h3>
        <dl className="space-y-2 text-sm">
          <div className="flex justify-between items-center"><dt className="text-slate-500">Ciclo de vida</dt><dd><FileLifecycleBadge status={file.lifecycle_status} /></dd></div>
          <div className="flex justify-between items-center"><dt className="text-slate-500">Escaneo</dt><dd><FileScanBadge status={file.scan_status} /></dd></div>
          <div className="flex justify-between items-center"><dt className="text-slate-500">Integridad</dt><dd><FileIntegrityBadge status={file.integrity_status} /></dd></div>
          <div className="flex justify-between items-center"><dt className="text-slate-500">Clasificación</dt><dd><FileClassificationBadge classification={file.classification} /></dd></div>
          <div className="flex justify-between"><dt className="text-slate-500">Legal hold</dt><dd className="text-slate-900">{legalHolds.length > 0 ? `${legalHolds.length} activo(s)` : 'No'}</dd></div>
        </dl>
      </div>
    </div>
  )
}

function PreviewTab({ file, onPreview }: { file: FileAssetDetail; onPreview: () => void }) {
  if (!file.capabilities.can_preview) {
    return <div className="rounded-xl border border-slate-200 p-4"><p className="text-sm text-slate-500">No tienes permiso para previsualizar este archivo.</p></div>
  }
  if (file.lifecycle_status !== 'AVAILABLE') {
    return <div className="rounded-xl border border-slate-200 p-4"><p className="text-sm text-amber-600">El archivo no está disponible para previsualización (estado: {file.lifecycle_status}).</p></div>
  }
  if (file.scan_status === 'INFECTED') {
    return <div className="rounded-xl border border-rose-200 bg-rose-50 p-4"><p className="text-sm text-rose-700">No se puede previsualizar un archivo en cuarentena o infectado.</p></div>
  }
  return (
    <div className="rounded-xl border border-slate-200 p-4 text-center">
      <p className="text-sm text-slate-500 mb-4">Haz clic para previsualizar el archivo de forma segura.</p>
      <Button onClick={onPreview}>Abrir preview</Button>
    </div>
  )
}

function MetadataTab({ file }: { file: FileAssetDetail }) {
  const m = file.metadata
  return (
    <div className="rounded-xl border border-slate-200 p-4">
      <h3 className="mb-3 text-sm font-semibold text-slate-700">Metadatos</h3>
      <dl className="grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
        <div className="flex justify-between"><dt className="text-slate-500">Título</dt><dd className="text-slate-900">{m.title}</dd></div>
        <div className="flex justify-between"><dt className="text-slate-500">Descripción</dt><dd className="text-slate-900">{m.description ?? '—'}</dd></div>
        <div className="flex justify-between"><dt className="text-slate-500">N° documental</dt><dd className="text-slate-900">{m.document_number ?? '—'}</dd></div>
        <div className="flex justify-between"><dt className="text-slate-500">Emisor</dt><dd className="text-slate-900">{m.issuer_name ?? '—'}</dd></div>
        <div className="flex justify-between"><dt className="text-slate-500">Emisión</dt><dd className="text-slate-900">{m.issue_date ?? '—'}</dd></div>
        <div className="flex justify-between"><dt className="text-slate-500">Vigencia</dt><dd className="text-slate-900">{m.effective_date ?? '—'}</dd></div>
        <div className="flex justify-between"><dt className="text-slate-500">Vencimiento</dt><dd className="text-slate-900">{m.expiration_date ?? '—'}</dd></div>
        <div className="flex justify-between"><dt className="text-slate-500">Fuente</dt><dd className="text-slate-900">{m.source ?? '—'}</dd></div>
        <div className="flex justify-between"><dt className="text-slate-500">Idioma</dt><dd className="text-slate-900">{m.language ?? '—'}</dd></div>
        <div className="flex justify-between"><dt className="text-slate-500">Etiquetas</dt><dd className="text-slate-900">{m.tags.join(', ') || '—'}</dd></div>
      </dl>
    </div>
  )
}

function AssociationsTab({ associations, canManage: _canManage, fileId: _fileId, onRefresh: _onRefresh }: {
  associations: FileAssociation[]
  canManage: boolean
  fileId: string
  onRefresh: () => void
}) {
  if (associations.length === 0) {
    return <EmptyState title="Sin asociaciones" description="Este archivo no está asociado a ningún recurso." />
  }
  return (
    <div className="space-y-2">
      {associations.map((a) => (
        <div key={a.id} className="flex items-center justify-between rounded-lg border border-slate-200 px-3 py-2 text-sm">
          <div className="flex items-center gap-3">
            <span className="rounded bg-slate-100 px-2 py-0.5 text-xs">{a.resource_type}</span>
            <span className="font-medium text-slate-900">{a.resource_code}</span>
            {a.is_primary && <span className="text-xs text-amber-600">Principal</span>}
          </div>
          <span className={`text-xs ${a.status === 'ACTIVE' ? 'text-emerald-600' : 'text-slate-400'}`}>{a.status}</span>
        </div>
      ))}
    </div>
  )
}

function VersionsTab({ versions, canUpload: _canUpload, fileId: _fileId }: {
  versions: FileVersion[]
  canUpload: boolean
  fileId: string
}) {
  if (versions.length === 0) {
    return <EmptyState title="Sin versiones" description="Este archivo no tiene versiones registradas." />
  }
  return (
    <div className="space-y-2">
      {versions.map((v) => (
        <div key={v.id} className="rounded-lg border border-slate-200 px-3 py-2 text-sm">
          <div className="flex items-center justify-between">
            <span className="font-medium">v{v.version_number}</span>
            <div className="flex items-center gap-2">
              {v.is_current && <span className="rounded bg-emerald-50 px-2 py-0.5 text-xs text-emerald-700 border border-emerald-300">Actual</span>}
              <span className={`text-xs ${v.status === 'ACTIVE' ? 'text-emerald-600' : v.status === 'DRAFT' ? 'text-amber-600' : 'text-slate-400'}`}>{v.status}</span>
            </div>
          </div>
          <div className="mt-1 text-xs text-slate-500">
            {v.filename} · {formatFileSize(v.size_bytes)} · {v.mime_type}
          </div>
          <div className="text-xs text-slate-400">Hash: {v.partial_hash.slice(0, 16)}... · Escaneo: {v.scan_status} · {v.uploaded_by_name}</div>
        </div>
      ))}
    </div>
  )
}

function EvidenceTab({ file }: { file: FileAssetDetail }) {
  return (
    <div className="rounded-xl border border-slate-200 p-4">
      <h3 className="mb-3 text-sm font-semibold text-slate-700">Evidencias</h3>
      <p className="text-sm text-slate-500">
        Este archivo tiene {file.evidence_count} evidencia(s) asociada(s).
      </p>
      {!file.capabilities.can_view_custody && (
        <p className="mt-2 text-xs text-amber-600">No tienes permiso para ver la cadena de custodia.</p>
      )}
    </div>
  )
}

function AccessTab({ accessInfo, canManage: _canManage, fileId: _fileId }: {
  accessInfo: FileAccessInfo | null
  canManage: boolean
  fileId: string
}) {
  if (!accessInfo) {
    return <EmptyState title="Sin información de acceso" description="No hay datos de permisos disponibles." />
  }
  return (
    <div className="rounded-xl border border-slate-200 p-4">
      <h3 className="mb-3 text-sm font-semibold text-slate-700">Permisos de acceso</h3>
      <dl className="space-y-2 text-sm">
        <div className="flex justify-between"><dt className="text-slate-500">Scope</dt><dd className="text-slate-900">{accessInfo.scope}</dd></div>
        <div className="flex justify-between"><dt className="text-slate-500">Permisos heredados</dt><dd className="text-slate-900">{accessInfo.inherited_permissions.join(', ') || '—'}</dd></div>
        <div className="flex justify-between"><dt className="text-slate-500">Grants explícitos</dt><dd className="text-slate-900">{accessInfo.grants.length}</dd></div>
      </dl>
      {accessInfo.grants.length > 0 && (
        <div className="mt-3 space-y-1">
          {accessInfo.grants.map((g) => (
            <div key={g.id} className="flex items-center justify-between rounded bg-slate-50 px-2 py-1 text-xs">
              <span className="text-slate-700">{g.grantee_name} ({g.grantee_type})</span>
              <span className={g.is_active ? 'text-emerald-600' : 'text-slate-400'}>{g.is_active ? 'Activo' : 'Inactivo'}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function IntegrityTab({ integrity }: { integrity: FileIntegrity | null }) {
  if (!integrity) {
    return <EmptyState title="Sin datos de integridad" description="No hay información de integridad disponible." />
  }
  return (
    <div className="rounded-xl border border-slate-200 p-4">
      <h3 className="mb-3 text-sm font-semibold text-slate-700">Integridad</h3>
      <dl className="space-y-2 text-sm">
        <div className="flex justify-between items-center"><dt className="text-slate-500">Estado</dt><dd><FileIntegrityBadge status={integrity.result} /></dd></div>
        <div className="flex justify-between"><dt className="text-slate-500">SHA-256</dt><dd className="font-mono text-xs text-slate-900">{integrity.sha256.slice(0, 24)}...</dd></div>
        <div className="flex justify-between"><dt className="text-slate-500">Calculado</dt><dd className="text-slate-900">{integrity.calculated_at}</dd></div>
        <div className="flex justify-between"><dt className="text-slate-500">Verificado</dt><dd className="text-slate-900">{integrity.last_verified_at ?? '—'}</dd></div>
        <div className="flex justify-between"><dt className="text-slate-500">Object status</dt><dd className="text-slate-900">{integrity.object_status}</dd></div>
      </dl>
      {integrity.alerts.length > 0 && (
        <div className="mt-3 rounded-lg bg-rose-50 p-3 text-sm text-rose-700">
          <div className="font-medium">Alertas:</div>
          <ul className="mt-1 list-disc pl-5">{integrity.alerts.map((a) => <li key={a}>{a}</li>)}</ul>
        </div>
      )}
    </div>
  )
}

function RetentionTab({ file, legalHolds }: { file: FileAssetDetail; legalHolds: FileLegalHold[] }) {
  const r = file.retention_info
  return (
    <div className="space-y-4">
      {r && (
        <div className="rounded-xl border border-slate-200 p-4">
          <h3 className="mb-3 text-sm font-semibold text-slate-700">Retención</h3>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between"><dt className="text-slate-500">Política</dt><dd className="text-slate-900">{r.policy_name ?? '—'}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Retención mínima</dt><dd className="text-slate-900">{r.minimum_retention_days ? `${r.minimum_retention_days} días` : '—'}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Fecha inicial</dt><dd className="text-slate-900">{r.initial_date ?? '—'}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Fecha de archivo</dt><dd className="text-slate-900">{r.archive_date ?? '—'}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Eliminación potencial</dt><dd className="text-slate-900">{r.potential_deletion_date ?? '—'}</dd></div>
          </dl>
          {r.blocking_reasons.length > 0 && (
            <div className="mt-3 rounded-lg bg-amber-50 p-3 text-sm text-amber-700">
              <div className="font-medium">Motivos bloqueantes:</div>
              <ul className="mt-1 list-disc pl-5">{r.blocking_reasons.map((b) => <li key={b}>{b}</li>)}</ul>
            </div>
          )}
        </div>
      )}
      {legalHolds.length > 0 && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
          <h3 className="mb-3 text-sm font-semibold text-amber-700">Legal holds activos</h3>
          <p className="mb-3 text-xs text-amber-600">El legal hold impide la eliminación aunque haya terminado la retención ordinaria.</p>
          <div className="space-y-2">
            {legalHolds.filter((h) => h.is_active).map((h) => (
              <div key={h.id} className="rounded border border-amber-300 bg-white px-3 py-2 text-sm">
                <div className="font-medium text-slate-900">{h.reason}</div>
                <div className="text-xs text-slate-500">Aplicado por: {h.applied_by_name} · {h.applied_at}</div>
                {h.reference && <div className="text-xs text-slate-500">Ref: {h.reference}</div>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function HistoryTab({ history }: { history: FileHistoryEvent[] }) {
  if (history.length === 0) {
    return <EmptyState title="Sin historial" description="No hay eventos en el historial de este archivo." />
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