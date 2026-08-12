import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { filesApi } from '../api/files-api'
import { Button } from '../components/common/Button'
import { Input } from '../components/common/Input'
import { LoadingSkeleton } from '../components/common/LoadingSkeleton'
import { EmptyState } from '../components/common/EmptyState'
import { Pagination } from '../components/common/Pagination'
import { PageHeader } from '../components/common/PageHeader'
import { Alert } from '../components/common/Alert'
import {
  FileClassificationBadge,
  FileIntegrityBadge,
  FileLifecycleBadge,
  FileScanBadge,
} from '../components/files/FileStatusBadge'
import { formatFileSize } from '../components/files/file-utils'
import { LOGISTICS_PERMISSIONS } from '../features/logistics-permissions/logistics-permissions-map'
import { useLogisticsPermissions } from '../features/logistics-permissions/hooks/useLogisticsPermissions'
import { getErrorMessage } from '../utils/errors'
import type {
  FileAssetType,
  FileClassification,
  FileLifecycleStatus,
  FileListQuery,
  FileRepositoryStats,
  FileAssetSummary,
} from '../types/files'
import type { PaginatedResponse } from '../types/logistics-resources'

const TYPE_OPTIONS: { value: FileAssetType; label: string }[] = [
  { value: 'DOCUMENT', label: 'Documento' },
  { value: 'IMAGE', label: 'Imagen' },
  { value: 'PDF', label: 'PDF' },
  { value: 'XML', label: 'XML' },
  { value: 'SIGNATURE', label: 'Firma' },
  { value: 'PHOTO', label: 'Foto' },
  { value: 'EVIDENCE', label: 'Evidencia' },
  { value: 'OTHER', label: 'Otro' },
]

const CLASSIFICATION_OPTIONS: { value: FileClassification; label: string }[] = [
  { value: 'INTERNAL', label: 'Interno' },
  { value: 'CONFIDENTIAL', label: 'Confidencial' },
  { value: 'RESTRICTED', label: 'Restringido' },
  { value: 'HIGHLY_RESTRICTED', label: 'Altamente restringido' },
  { value: 'PUBLIC_APPROVED', label: 'Público aprobado' },
]

const LIFECYCLE_OPTIONS: { value: FileLifecycleStatus; label: string }[] = [
  { value: 'UPLOADING', label: 'Cargando' },
  { value: 'PROCESSING', label: 'Procesando' },
  { value: 'QUARANTINED', label: 'En cuarentena' },
  { value: 'AVAILABLE', label: 'Disponible' },
  { value: 'REJECTED', label: 'Rechazado' },
  { value: 'ARCHIVED', label: 'Archivado' },
  { value: 'DELETED', label: 'Eliminado' },
  { value: 'CORRUPTED', label: 'Corrupto' },
  { value: 'FAILED', label: 'Fallido' },
]

function StatChip({ label, value, tone }: { label: string; value: number; tone: 'default' | 'warning' | 'danger' | 'success' }) {
  const tones = {
    default: 'border-slate-200 bg-slate-50 text-slate-700',
    warning: 'border-amber-200 bg-amber-50 text-amber-700',
    danger: 'border-rose-200 bg-rose-50 text-rose-700',
    success: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  }
  return (
    <div className={`flex items-center gap-2 rounded-lg border px-3 py-1.5 ${tones[tone]}`}>
      <span className="text-xs font-medium">{label}</span>
      <span className="text-sm font-bold tabular-nums">{value}</span>
    </div>
  )
}

export function FilesRepositoryPage() {
  const navigate = useNavigate()
  const auth = useLogisticsPermissions()
  const canUpload = auth.hasPermission(LOGISTICS_PERMISSIONS.files.upload)

  const [data, setData] = useState<PaginatedResponse<FileAssetSummary>>({
    items: [],
    page: 1,
    page_size: 20,
    total: 0,
    total_pages: 0,
  })
  const [stats, setStats] = useState<FileRepositoryStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [page, setPage] = useState(1)
  const [typeFilter, setTypeFilter] = useState('')
  const [classFilter, setClassFilter] = useState('')
  const [lifecycleFilter, setLifecycleFilter] = useState('')

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search)
      setPage(1)
    }, 400)
    return () => clearTimeout(timer)
  }, [search])

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const query: FileListQuery = {
        page,
        page_size: 50,
        search: debouncedSearch || undefined,
        asset_type: (typeFilter || undefined) as FileAssetType | undefined,
        classification: (classFilter || undefined) as FileClassification | undefined,
        lifecycle_status: (lifecycleFilter || undefined) as FileLifecycleStatus | undefined,
      }
      const [listRes, statsRes] = await Promise.all([
        filesApi.list(query),
        filesApi.getStats().catch(() => null),
      ])
      setData(listRes)
      if (statsRes) setStats(statsRes)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [page, debouncedSearch, typeFilter, classFilter, lifecycleFilter])

  useEffect(() => {
    void load()
  }, [load])

  const clearFilters = () => {
    setSearch('')
    setTypeFilter('')
    setClassFilter('')
    setLifecycleFilter('')
    setPage(1)
  }

  const hasFilters = useMemo(
    () => Boolean(search || typeFilter || classFilter || lifecycleFilter),
    [search, typeFilter, classFilter, lifecycleFilter],
  )

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <PageHeader
        title="Repositorio de archivos"
        description="Archivos centralizados, evidencias y cadena de custodia"
        actions={canUpload ? (
          <Button onClick={() => navigate('/logistics/files/upload')}>+ Subir archivo</Button>
        ) : undefined}
      />

      {stats && !loading && (
        <div className="flex flex-wrap gap-2">
          <StatChip label="Disponibles" value={stats.available_count} tone="success" />
          <StatChip label="Procesando" value={stats.processing_count} tone="warning" />
          <StatChip label="En cuarentena" value={stats.quarantined_count} tone="danger" />
          <StatChip label="Rechazados" value={stats.rejected_count} tone="danger" />
          <StatChip label="Evidencias aceptadas" value={stats.evidence_accepted_count} tone="success" />
          <StatChip label="Integridad fallida" value={stats.integrity_failed_count} tone="danger" />
          <StatChip label="Legal holds" value={stats.legal_holds_count} tone="warning" />
          <StatChip label="Eliminaciones pendientes" value={stats.deletion_pending_count} tone="warning" />
        </div>
      )}

      {/* Search */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
        <div className="flex-1">
          <Input
            label="Buscar"
            placeholder="Código, título, tipo, recurso, propietario, hash..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2">
        <select value={typeFilter} onChange={(e) => { setTypeFilter(e.target.value); setPage(1) }} className="rounded-lg border border-slate-300 px-3 py-2 text-sm">
          <option value="">Tipo</option>
          {TYPE_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
        <select value={classFilter} onChange={(e) => { setClassFilter(e.target.value); setPage(1) }} className="rounded-lg border border-slate-300 px-3 py-2 text-sm">
          <option value="">Clasificación</option>
          {CLASSIFICATION_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
        <select value={lifecycleFilter} onChange={(e) => { setLifecycleFilter(e.target.value); setPage(1) }} className="rounded-lg border border-slate-300 px-3 py-2 text-sm">
          <option value="">Estado</option>
          {LIFECYCLE_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
        {hasFilters && <Button variant="ghost" onClick={clearFilters}>Limpiar</Button>}
      </div>

      {error && <Alert variant="error">{error}</Alert>}

      {loading ? (
        <LoadingSkeleton rows={8} />
      ) : data.items.length === 0 ? (
        <EmptyState title="Sin archivos" description={hasFilters ? 'No se encontraron archivos con los filtros aplicados.' : 'No hay archivos en el repositorio.'} />
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs font-medium uppercase text-slate-500">
              <tr>
                <th className="px-3 py-2">Código</th>
                <th className="px-3 py-2">Título</th>
                <th className="px-3 py-2 hidden sm:table-cell">Tipo</th>
                <th className="px-3 py-2 hidden md:table-cell">Tamaño</th>
                <th className="px-3 py-2 hidden lg:table-cell">Clasificación</th>
                <th className="px-3 py-2">Estado</th>
                <th className="px-3 py-2 hidden sm:table-cell">Escaneo</th>
                <th className="px-3 py-2 hidden lg:table-cell">Integridad</th>
                <th className="px-3 py-2 hidden md:table-cell">Recurso</th>
                <th className="px-3 py-2 hidden xl:table-cell">Subido por</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.items.map((file) => (
                <tr
                  key={file.id}
                  onClick={() => navigate(`/logistics/files/${file.id}`)}
                  className="cursor-pointer hover:bg-slate-50 transition-colors"
                >
                  <td className="px-3 py-2 font-mono text-xs text-slate-500">{file.code}</td>
                  <td className="px-3 py-2 font-medium text-slate-900">{file.title}</td>
                  <td className="px-3 py-2 hidden sm:table-cell text-slate-600">{file.asset_type}</td>
                  <td className="px-3 py-2 hidden md:table-cell text-slate-600">{formatFileSize(file.size_bytes)}</td>
                  <td className="px-3 py-2 hidden lg:table-cell"><FileClassificationBadge classification={file.classification} /></td>
                  <td className="px-3 py-2"><FileLifecycleBadge status={file.lifecycle_status} /></td>
                  <td className="px-3 py-2 hidden sm:table-cell"><FileScanBadge status={file.scan_status} /></td>
                  <td className="px-3 py-2 hidden lg:table-cell"><FileIntegrityBadge status={file.integrity_status} /></td>
                  <td className="px-3 py-2 hidden md:table-cell text-slate-600">{file.resource_code ?? '—'}</td>
                  <td className="px-3 py-2 hidden xl:table-cell text-slate-500">{file.uploader_name}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {!loading && data.total > 0 && (
        <Pagination page={data.page} totalPages={data.total_pages} total={data.total} onPageChange={setPage} />
      )}
    </div>
  )
}