import { useEffect, useState } from 'react'
import { companyProfileApi } from '../../api/company-profile-api'
import { StatusBadge } from '../../components/common/StatusBadge'
import type { NumberingPolicy } from '../../types/company-profile'
import { getErrorMessage } from '../../utils/errors'

interface NumberingPoliciesPanelProps {
  canManageNumbering: boolean
}

export function NumberingPoliciesPanel({ canManageNumbering: _canManageNumbering }: NumberingPoliciesPanelProps) {
  const [policies, setPolicies] = useState<NumberingPolicy[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadPolicies = async () => {
    setIsLoading(true)
    try {
      setPolicies(await companyProfileApi.listNumberingPolicies())
    } catch (err: unknown) {
      setError(getErrorMessage(err))
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    void loadPolicies()
  }, [])

  return (
    <div className="space-y-6 text-xs">
      <div>
        <h3 className="font-bold text-slate-900">Políticas y reglas de numeración documental</h3>
        <p className="text-[11px] text-slate-500">
          Estructura de series, correlativos y patrones de formateo aprobados por sede y tipo.
        </p>
      </div>

      {error && <p className="text-xs font-semibold text-rose-600">{error}</p>}

      {/* Constructor de Patrón Visual */}
      <section className="rounded-xl border border-slate-200 bg-slate-50 p-4 space-y-3">
        <h4 className="font-bold text-slate-900 text-[11px] uppercase tracking-wider">
          Constructor de patrón con tokens autorizados
        </h4>

        <div className="flex flex-wrap items-center gap-2">
          {['TYPE', 'BRANCH', 'YEAR', 'CORRELATIVE'].map((token) => (
            <span
              key={token}
              className="rounded-lg border border-blue-200 bg-blue-50 px-2.5 py-1 font-mono font-bold text-blue-800"
            >
              [{token}]
            </span>
          ))}
        </div>

        <div className="rounded-lg border border-slate-300 bg-white p-3 space-y-1">
          <span className="text-[10px] font-bold text-slate-400 uppercase">
            Vista previa del código resultante (Ejemplo, no reserva correlativo):
          </span>
          <p className="font-mono text-sm font-bold text-slate-900">GRR-CALLAO-2026-000154</p>
        </div>
      </section>

      {/* Tabla de políticas */}
      <section className="space-y-3">
        <h4 className="font-bold text-slate-900 text-[11px] uppercase tracking-wider">
          Políticas registradas por tipo de comprobante
        </h4>

        {isLoading ? (
          <div className="loading-panel">
            <span className="spinner" />
            <p>Cargando reglas de numeración…</p>
          </div>
        ) : (
          <div className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-xs">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-100 bg-slate-50 text-[10px] uppercase font-bold text-slate-400">
                  <th className="p-3">Tipo documental</th>
                  <th className="p-3">Sede</th>
                  <th className="p-3">Patrón autorizado</th>
                  <th className="p-3">Serie externa</th>
                  <th className="p-3">Próximo correlativo</th>
                  <th className="p-3">Estado</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {policies.map((row) => (
                  <tr key={row.id} className="hover:bg-slate-50/50">
                    <td className="p-3 font-bold text-slate-900">{row.document_type}</td>
                    <td className="p-3">{row.branch_code}</td>
                    <td className="p-3">
                      <code className="font-mono text-[10px] bg-slate-100 px-1.5 py-0.5 rounded text-blue-700">
                        {row.pattern_tokens.join('-')}
                      </code>
                    </td>
                    <td className="p-3 font-mono">{row.external_series_code}</td>
                    <td className="p-3 font-mono font-bold text-slate-900">
                      {String(row.external_next_number).padStart(row.padding_length, '0')}
                    </td>
                    <td className="p-3">
                      <StatusBadge value={row.status?.toLowerCase() ?? ''}>{row.status}</StatusBadge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  )
}
