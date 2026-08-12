import { useEffect, useState } from 'react'
import { companyProfileApi } from '../../api/company-profile-api'
import { Button } from '../../components/common/Button'
import { StatusBadge } from '../../components/common/StatusBadge'
import type { ProfileVersionItem } from '../../types/company-profile'
import { formatDateTime } from '../../utils/date'
import { getErrorMessage } from '../../utils/errors'

interface CompanyProfileVersionsPanelProps {
  canActivateProfile: boolean
  onActivateVersion: (versionId: string) => Promise<void>
}

export function CompanyProfileVersionsPanel({
  canActivateProfile,
  onActivateVersion,
}: CompanyProfileVersionsPanelProps) {
  const [versions, setVersions] = useState<ProfileVersionItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadVersions = async () => {
    setIsLoading(true)
    try {
      setVersions(await companyProfileApi.listVersions())
    } catch (err: unknown) {
      setError(getErrorMessage(err))
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    void loadVersions()
  }, [])

  return (
    <div className="space-y-4 text-xs">
      <div>
        <h3 className="font-bold text-slate-900">Historial de versiones institucionales</h3>
        <p className="text-[11px] text-slate-500">
          Inmutabilidad y registro de cambios aplicados a la ficha de la empresa.
        </p>
      </div>

      {error && <p className="text-xs font-semibold text-rose-600">{error}</p>}

      {isLoading ? (
        <div className="loading-panel">
          <span className="spinner" />
          <p>Cargando versiones institucionales…</p>
        </div>
      ) : (
        <div className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-xs">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50 text-[10px] uppercase font-bold text-slate-400">
                <th className="p-3">Versión</th>
                <th className="p-3">Estado</th>
                <th className="p-3">Creado por</th>
                <th className="p-3">Activado el</th>
                <th className="p-3">Resumen de cambios</th>
                <th className="p-3 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {versions.map((row) => (
                <tr key={row.id} className="hover:bg-slate-50/50">
                  <td className="p-3 font-bold text-slate-900">v{row.version_number}</td>
                  <td className="p-3">
                    <StatusBadge value={row.status?.toLowerCase() ?? ''}>{row.status}</StatusBadge>
                  </td>
                  <td className="p-3">{row.created_by_user_name}</td>
                  <td className="p-3 text-[11px] text-slate-600">
                    {row.activated_at ? formatDateTime(row.activated_at) : '—'}
                  </td>
                  <td className="p-3 text-[11px] text-slate-600">{row.changes_summary}</td>
                  <td className="p-3 text-right">
                    {row.status === 'DRAFT' && canActivateProfile && (
                      <Button
                        size="small"
                        variant="ghost"
                        onClick={() => void onActivateVersion(row.id)}
                      >
                        Activar versión
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
