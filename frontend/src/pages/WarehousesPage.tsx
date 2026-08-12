import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { warehousesApi } from '../api/warehouses-modeling-api'
import { Alert } from '../components/common/Alert'
import { Button } from '../components/common/Button'
import { OperationsTable, type TableColumn } from '../components/common/OperationsTable'
import { PageHeader } from '../components/common/PageHeader'
import { Pagination } from '../components/common/Pagination'
import { QueryBar } from '../components/common/QueryBar'
import { StatusBadge } from '../components/common/StatusBadge'
import type { PaginatedResponse } from '../types/logistics-resources'
import type { Warehouse } from '../types/warehouse-modeling'
import { getErrorMessage } from '../utils/errors'

export function WarehousesPage() {
  const navigate = useNavigate()
  const [data, setData] = useState<PaginatedResponse<Warehouse>>({
    items: [],
    page: 1,
    page_size: 20,
    total: 0,
    total_pages: 0,
  })
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      setData(await warehousesApi.list({ page, page_size: 20, search }))
    } catch (err: unknown) {
      setError(getErrorMessage(err))
    } finally {
      setIsLoading(false)
    }
  }, [page, search])

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 250)
    return () => window.clearTimeout(timer)
  }, [load])

  const columns = useMemo<TableColumn<Warehouse>[]>(
    () => [
      {
        key: 'name',
        label: 'Almacén',
        render: (row) => (
          <div className="table-primary">
            <strong>{row.name}</strong>
            <small>{row.code}</small>
          </div>
        ),
      },
      {
        key: 'branch',
        label: 'Sede',
        render: (row) => row.branch_name || 'Sede Central',
      },
      {
        key: 'type',
        label: 'Tipo',
        render: (row) => row.warehouse_type,
      },
      {
        key: 'locations',
        label: 'Ubicaciones Mapeadas',
        render: (row) => (
          <span className="font-mono font-bold text-slate-900">
            {row.total_locations} ({row.active_locations} activas)
          </span>
        ),
      },
      {
        key: 'layout',
        label: 'Versión Layout',
        render: (row) =>
          row.active_layout_version ? `v${row.active_layout_version}` : 'Sin activar',
      },
      {
        key: 'status',
        label: 'Estado',
        render: (row) => (
          <StatusBadge value={row.status.toLowerCase()}>{row.status}</StatusBadge>
        ),
      },
      {
        key: 'actions',
        label: 'Acciones',
        align: 'right',
        render: (row) => (
          <Button
            size="small"
            variant="ghost"
            onClick={() => navigate(`/logistics/settings/warehouses/${row.id}`)}
          >
            Ficha & Estructura
          </Button>
        ),
      },
    ],
    [navigate],
  )

  return (
    <div className="page">
      <PageHeader
        eyebrow="Red logística y distribución"
        title="Catálogo y Modelado de Almacenes"
        description="Gestión física, árbol jerárquico de ubicaciones, capacidades, layout 2D y etiquetas QR."
      />

      {error && <Alert variant="error">{error}</Alert>}

      <section className="panel operations-section space-y-3">
        <QueryBar
          search={search}
          onSearch={(val) => {
            setSearch(val)
            setPage(1)
          }}
        />

        {isLoading ? (
          <div className="loading-panel">
            <span className="spinner" />
            <p>Cargando catálogo de almacenes…</p>
          </div>
        ) : (
          <OperationsTable rows={data.items} columns={columns} getRowKey={(row) => row.id} />
        )}

        <Pagination
          page={data.page}
          totalPages={data.total_pages}
          total={data.total}
          onPageChange={setPage}
        />
      </section>
    </div>
  )
}

