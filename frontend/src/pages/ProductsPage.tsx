import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { productsCatalogApi } from '../api/products-catalog-api'
import { Alert } from '../components/common/Alert'
import { Button } from '../components/common/Button'
import { Input } from '../components/common/Input'
import { OperationsTable, type TableColumn } from '../components/common/OperationsTable'
import { PageHeader } from '../components/common/PageHeader'
import { Pagination } from '../components/common/Pagination'
import { QueryBar } from '../components/common/QueryBar'
import { ResourceDialog } from '../components/common/ResourceDialog'
import { StatusBadge } from '../components/common/StatusBadge'
import { LogisticsIcon } from '../components/common/LogisticsIcon'
import type { PaginatedResponse } from '../types/logistics-resources'
import type { Product, ProductCategory, ProductCreate } from '../types/products-catalog'
import { getErrorMessage } from '../utils/errors'

export function ProductsPage() {
  const navigate = useNavigate()
  const [data, setData] = useState<PaginatedResponse<Product>>({
    items: [],
    page: 1,
    page_size: 20,
    total: 0,
    total_pages: 0,
  })
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [categories, setCategories] = useState<ProductCategory[]>([])

  const [form, setForm] = useState<ProductCreate>({
    sku: '',
    name: '',
    short_name: '',
    description: '',
    product_type: 'FINISHED_GOOD',
    category_id: '',
    base_unit: 'NIU',
  })

  const load = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      setData(await productsCatalogApi.list({ page, page_size: 20, search }))
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

  useEffect(() => {
    productsCatalogApi
      .listCategories()
      .then((items) => {
        setCategories(items)
        setForm((current) => ({
          ...current,
          category_id: current.category_id || items[0]?.id || '',
        }))
      })
      .catch(() => setCategories([]))
  }, [])

  const handleCreate = async () => {
    setIsSaving(true)
    try {
      await productsCatalogApi.create(form)
      setIsCreateOpen(false)
      await load()
    } catch (err: unknown) {
      setError(getErrorMessage(err))
    } finally {
      setIsSaving(false)
    }
  }

  const columns = useMemo<TableColumn<Product>[]>(
    () => [
      {
        key: 'sku',
        label: 'SKU / Producto',
        render: (row) => (
          <div className="table-primary">
            <strong>{row.name}</strong>
            <small>{row.sku}</small>
          </div>
        ),
      },
      {
        key: 'category',
        label: 'Categoría',
        render: (row) => row.category_name || 'General',
      },
      {
        key: 'type',
        label: 'Tipo',
        render: (row) => row.product_type,
      },
      {
        key: 'tracking',
        label: 'Trazabilidad',
        render: (row) => (
          <span className="font-mono text-[10px] bg-slate-100 px-1.5 py-0.5 rounded font-bold text-slate-700">
            {row.tracking_type}
          </span>
        ),
      },
      {
        key: 'version',
        label: 'Versión Activa',
        render: (row) => `v${row.active_version}`,
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
            onClick={() => navigate(`/logistics/products/${row.id}`)}
          >
            Ficha Técnica
          </Button>
        ),
      },
    ],
    [navigate],
  )

  return (
    <div className="page">
      <PageHeader
        eyebrow="Catálogo maestro de mercaderías"
        title="Catálogo de Productos"
        description="Fichas técnicas, códigos EAN/GTIN, trazabilidad por lote/serie y condiciones de conservación."
        actions={<Button onClick={() => setIsCreateOpen(true)}>Nuevo Producto</Button>}
      />

      {/* Nota discreta de Cero Stock */}
      <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600">
        <p className="flex items-start gap-1.5">
          <LogisticsIcon name="info" size={14} aria-hidden /> <span><strong>Nota del sistema:</strong> El catálogo define las especificaciones maestras del producto. Las existencias físicas se gestionan exclusivamente en el módulo de inventario.</span>
        </p>
      </div>

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
            <p>Cargando catálogo maestro de productos…</p>
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

      <ResourceDialog
        isOpen={isCreateOpen}
        title="Registrar nuevo producto en catálogo"
        submitLabel="Crear producto"
        isSubmitting={isSaving}
        onClose={() => setIsCreateOpen(false)}
        onSubmit={() => void handleCreate()}
      >
        <div className="grid grid-cols-2 gap-3 text-xs">
          <Input
            label="Código SKU"
            value={form.sku}
            onChange={(e) => setForm((c) => ({ ...c, sku: e.target.value }))}
            required
          />
          <Input
            label="Nombre oficial"
            value={form.name}
            onChange={(e) => setForm((c) => ({ ...c, name: e.target.value }))}
            required
          />
          <div>
            <label className="font-semibold text-slate-700 block mb-1">Tipo de Producto</label>
            <select
              className="input-field"
              value={form.product_type}
              onChange={(e) =>
                setForm((c) => ({ ...c, product_type: e.target.value as ProductCreate['product_type'] }))
              }
            >
              <option value="FINISHED_GOOD">Producto Terminado</option>
              <option value="RAW_MATERIAL">Materia Prima</option>
              <option value="PACKAGING">Empaque / Embalaje</option>
              <option value="MERCHANDISE">Mercadería</option>
            </select>
          </div>
          <Input
            label="Unidad Base (ej: NIU, KGM, MTQ)"
            value={form.base_unit}
            onChange={(e) => setForm((c) => ({ ...c, base_unit: e.target.value }))}
            required
          />
          <div className="col-span-2">
            <label className="font-semibold text-slate-700 block mb-1">Categoría</label>
            <select
              className="input-field"
              value={form.category_id}
              onChange={(e) =>
                setForm((current) => ({ ...current, category_id: e.target.value }))
              }
              required
            >
              <option value="">Selecciona una categoría</option>
              {categories.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </ResourceDialog>
    </div>
  )
}
