import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { evidenceApi } from '../api/files-api'
import { PageHeader } from '../components/common/PageHeader'
import { LoadingSkeleton } from '../components/common/LoadingSkeleton'
import { EmptyState } from '../components/common/EmptyState'
import { Pagination } from '../components/common/Pagination'
import { Alert } from '../components/common/Alert'
import { EvidenceStatusBadge } from '../components/files/FileStatusBadge'
import { FileIntegrityBadge } from '../components/files/FileStatusBadge'
import { getErrorMessage } from '../utils/errors'
import type { EvidenceRecord } from '../types/files'
import type { PaginatedResponse } from '../types/logistics-resources'

export function EvidencePage() {
  const navigate = useNavigate()
  const [data, setData] = useState<PaginatedResponse<EvidenceRecord>>({
    items: [],
    page: 1,
    page_size: 20,
    total: 0,
    total_pages: 0,
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await evidenceApi.list({ page, page_size: 20, status: statusFilter || undefined })
      setData(res)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [page, statusFilter])

  useEffect(() => {
    void load()
  }, [load])

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <PageHeader title="Evidencias" description="Registro de evidencias con cadena de custodia" />

      <div className="flex flex-wrap gap-2">
        <select value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1) }} className="rounded-lg border border-slate-300 px-3 py-2 text-sm">
          <option value="">Todos los estados</option>
          <option value="DRAFT">Borrador</option>
          <option value="PENDING">Pendiente</option>
          <option value="ACCEPTED">Aceptada</option>
          <option value="REJECTED">Rechazada</option>
          <option value="REVOKED">Revocada</option>
          <option value="SUPERSEDED">Sustituida</option>
        </select>
      </div>

      {error && <Alert variant="error">{error}</Alert>}

      {loading ? (
        <LoadingSkeleton rows={6} />
      ) : data.items.length === 0 ? (
        <EmptyState title="Sin evidencias" description="No hay evidencias registradas." />
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs font-medium uppercase text-slate-500">
              <tr>
                <th className="px-3 py-2">Código</th>
                <th className="px-3 py-2">Tipo</th>
                <th className="px-3 py-2 hidden sm:table-cell">Sujeto</th>
                <th className="px-3 py-2 hidden md:table-cell">Archivo</th>
                <th className="px-3 py-2 hidden lg:table-cell">Captura</th>
                <th className="px-3 py-2">Estado</th>
                <th className="px-3 py-2 hidden lg:table-cell">Integridad</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.items.map((ev) => (
                <tr
                  key={ev.id}
                  onClick={() => navigate(`/logistics/files/${ev.file_id}?tab=evidence`)}
                  className="cursor-pointer hover:bg-slate-50"
                >
                  <td className="px-3 py-2 font-mono text-xs text-slate-500">{ev.code}</td>
                  <td className="px-3 py-2 text-slate-700">{ev.evidence_type}</td>
                  <td className="px-3 py-2 hidden sm:table-cell text-slate-600">{ev.subject_code}</td>
                  <td className="px-3 py-2 hidden md:table-cell text-slate-600">{ev.file_code}</td>
                  <td className="px-3 py-2 hidden lg:table-cell text-slate-500">{ev.captured_at}</td>
                  <td className="px-3 py-2"><EvidenceStatusBadge status={ev.status} /></td>
                  <td className="px-3 py-2 hidden lg:table-cell"><FileIntegrityBadge status={ev.integrity_status} /></td>
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