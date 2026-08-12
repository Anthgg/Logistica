import { useCallback, useEffect, useState } from 'react'
import { logisticsApi } from '../api/logistics-api'
import { Alert } from '../components/common/Alert'
import { OperationsTable, type TableColumn } from '../components/common/OperationsTable'
import { PageHeader } from '../components/common/PageHeader'
import { QueryBar } from '../components/common/QueryBar'
import { StatusBadge } from '../components/common/StatusBadge'
import type { PermissionResponse } from '../types/logistics-resources'
import { getErrorMessage } from '../utils/errors'

export function PermissionsCatalogPage() {
  const [data, setData] = useState<PermissionResponse[]>([])
  const [search, setSearch] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const items = await logisticsApi.permissions.list({ search })
      const filtered = search
        ? items.filter(
            (p: PermissionResponse) =>
              p.code.includes(search) ||
              p.name.toLowerCase().includes(search.toLowerCase()) ||
              p.resource.includes(search),
          )
        : items
      setData(filtered)
    } catch (caught: unknown) {
      setError(getErrorMessage(caught))
    } finally {
      setIsLoading(false)
    }
  }, [search])

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 250)
    return () => window.clearTimeout(timer)
  }, [load])

  const columns: TableColumn<PermissionResponse>[] = [
    {
      key: 'code',
      label: 'Código',
      render: (row) => <code className="text-xs font-mono">{row.code}</code>,
    },
    {
      key: 'name',
      label: 'Nombre',
      render: (row) => <strong>{row.name}</strong>,
    },
    {
      key: 'resource',
      label: 'Recurso',
      render: (row) => row.resource,
    },
    {
      key: 'action',
      label: 'Acción',
      render: (row) => row.action,
    },
    {
      key: 'category',
      label: 'Categoría',
      render: (row) => row.category,
    },
    {
      key: 'risk_level',
      label: 'Riesgo',
      render: (row) => (
        <StatusBadge value={row.risk_level === 'low' ? 'active' : 'inactive'}>
          {row.risk_level}
        </StatusBadge>
      ),
    },
    {
      key: 'is_sensitive',
      label: 'Sensible',
      render: (row) => (row.is_sensitive ? 'Sí' : 'No'),
    },
    {
      key: 'requires_step_up',
      label: 'Step-up',
      render: (row) => (row.requires_step_up ? 'Sí' : 'No'),
    },
    {
      key: 'status',
      label: 'Estado',
      render: (row) => (
        <StatusBadge value={row.status === 'active' ? 'active' : 'inactive'}>
          {row.status === 'active' ? 'Activo' : row.status}
        </StatusBadge>
      ),
    },
  ]

  return (
    <div className="page">
      <PageHeader
        eyebrow="Control de acceso"
        title="Catálogo de permisos"
        description="Consulta el catálogo de permisos logísticos en modo lectura."
      />
      {error && <Alert variant="error">{error}</Alert>}
      <section className="panel operations-section">
        <QueryBar
          search={search}
          onSearch={setSearch}
        />
        {isLoading ? (
          <div className="loading-panel">
            <span className="spinner" />
            <p>Cargando permisos…</p>
          </div>
        ) : (
          <OperationsTable
            rows={data}
            columns={columns}
            getRowKey={(row) => row.id}
          />
        )}
      </section>
    </div>
  )
}