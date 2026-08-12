import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { filesApi } from '../api/files-api'
import { PageHeader } from '../components/common/PageHeader'
import { LoadingSkeleton } from '../components/common/LoadingSkeleton'
import { EmptyState } from '../components/common/EmptyState'
import { Pagination } from '../components/common/Pagination'
import { Alert } from '../components/common/Alert'
import { FileDeletionStatusBadge } from '../components/files/FileStatusBadge'
import { getErrorMessage } from '../utils/errors'
import type { FileDeletionRequest, FileDeletionRequestListQuery, FileDeletionRequestStatus } from '../types/files'
import type { PaginatedResponse } from '../types/logistics-resources'

export function FileDeletionRequestsPage() {
  const navigate = useNavigate()
  const [data, setData] = useState<PaginatedResponse<FileDeletionRequest>>({
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
      const query: FileDeletionRequestListQuery = {
        page,
        page_size: 20,
        status: (statusFilter || undefined) as FileDeletionRequestStatus | undefined,
      }
      const res = await filesApi.listDeletionRequests(query)
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
      <PageHeader title="Solicitudes de eliminación" description="Gestión de solicitudes de eliminación de archivos" />

      <div className="flex flex-wrap gap-2">
        <select value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1) }} className="rounded-lg border border-slate-300 px-3 py-2 text-sm">
          <option value="">Todos los estados</option>
          <option value="PENDING">Pendiente</option>
          <option value="APPROVED">Aprobada</option>
          <option value="REJECTED">Rechazada</option>
          <option value="PURGED">Purgada</option>
        </select>
      </div>

      {error && <Alert variant="error">{error}</Alert>}

      {loading ? (
        <LoadingSkeleton rows={6} />
      ) : data.items.length === 0 ? (
        <EmptyState title="Sin solicitudes" description="No hay solicitudes de eliminación." />
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs font-medium uppercase text-slate-500">
              <tr>
                <th className="px-3 py-2">Archivo</th>
                <th className="px-3 py-2 hidden sm:table-cell">Solicitante</th>
                <th className="px-3 py-2 hidden md:table-cell">Revisor</th>
                <th className="px-3 py-2 hidden lg:table-cell">Motivo</th>
                <th className="px-3 py-2 hidden lg:table-cell">Base</th>
                <th className="px-3 py-2 hidden sm:table-cell">Solicitada</th>
                <th className="px-3 py-2">Estado</th>
                <th className="px-3 py-2 hidden xl:table-cell">Purga</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.items.map((req) => (
                <tr
                  key={req.id}
                  onClick={() => navigate(`/logistics/files/${req.file_id}`)}
                  className="cursor-pointer hover:bg-slate-50"
                >
                  <td className="px-3 py-2">
                    <div className="font-mono text-xs text-slate-500">{req.file_code}</div>
                    <div className="text-slate-700">{req.file_title}</div>
                  </td>
                  <td className="px-3 py-2 hidden sm:table-cell text-slate-600">{req.requester_name}</td>
                  <td className="px-3 py-2 hidden md:table-cell text-slate-600">{req.reviewer_name ?? '—'}</td>
                  <td className="px-3 py-2 hidden lg:table-cell text-slate-500">{req.reason}</td>
                  <td className="px-3 py-2 hidden lg:table-cell text-slate-500">{req.basis}</td>
                  <td className="px-3 py-2 hidden sm:table-cell text-slate-500">{req.requested_at}</td>
                  <td className="px-3 py-2"><FileDeletionStatusBadge status={req.status} /></td>
                  <td className="px-3 py-2 hidden xl:table-cell text-slate-500">{req.purge_scheduled_at ?? '—'}</td>
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