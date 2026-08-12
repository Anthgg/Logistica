import { useCallback, useState } from 'react'
import { Button } from '../../../components/common/Button'
import { useMutation } from '../../inbound-docks/hooks/useQuery'
import { apiRequest, getCsrfToken } from '../../../api/api-client'
import { StatusPill, EmptyPanel, ErrorPanel } from '../../inbound-docks/components/ui/Primitives'
import type {
  QualityPlanScope,
  QualityInspectionPlanCapabilities,
  QualityPlanScopeType,
  QualityPlanApplicabilityAction,
  CreateQualityPlanScopeRequest,
} from '../types/quality-inspection-plans'

interface ScopeFormData {
  scope_type: QualityPlanScopeType
  action: QualityPlanApplicabilityAction
  product_id: string
  product_name: string
  category_id: string
  category_name: string
  include_descendants: boolean
  branch_id: string
  warehouse_id: string
  valid_from: string
  valid_until: string
  priority_override: string
}

const EMPTY_FORM: ScopeFormData = {
  scope_type: 'PRODUCT',
  action: 'INCLUDE',
  product_id: '',
  product_name: '',
  category_id: '',
  category_name: '',
  include_descendants: false,
  branch_id: '',
  warehouse_id: '',
  valid_from: '',
  valid_until: '',
  priority_override: '',
}

function formatDate(iso: string | null): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('es-EC', { year: 'numeric', month: 'short', day: 'numeric' })
}

export function QualityPlanScopesEditor({
  versionId,
  scopes,
  capabilities,
  onRefresh,
}: {
  versionId: string
  scopes: QualityPlanScope[]
  capabilities: QualityInspectionPlanCapabilities
  onRefresh: () => void
}) {
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState<ScopeFormData>(EMPTY_FORM)
  const [editingScopeId, setEditingScopeId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [productSearch, setProductSearch] = useState('')
  const [categorySearch, setCategorySearch] = useState('')

  const createScopeMutation = useMutation<CreateQualityPlanScopeRequest, { scope_id: string }>(
    async (input) => {
      const csrf = await getCsrfToken()
      return apiRequest<{ scope_id: string }>({
        path: `/logistics/quality/versions/${versionId}/scopes`,
        method: 'POST',
        body: input,
        headers: { 'X-CSRF-Token': csrf },
      })
    },
    {
      onSuccess: () => {
        setShowForm(false)
        setFormData(EMPTY_FORM)
        onRefresh()
      },
      onError: (err) => setError(err.message),
    },
  )

  const deleteScopeMutation = useMutation<{ scopeId: string }, void>(
    async (input) => {
      const csrf = await getCsrfToken()
      await apiRequest({
        path: `/logistics/quality/scopes/${input.scopeId}`,
        method: 'DELETE',
        headers: { 'X-CSRF-Token': csrf },
      })
    },
    { onSuccess: () => onRefresh(), onError: (err) => setError(err.message) },
  )

  const handleAddScope = useCallback(() => {
    setShowForm(true)
    setEditingScopeId(null)
    setFormData(EMPTY_FORM)
  }, [])

  const handleEditScope = useCallback((scope: QualityPlanScope) => {
    setEditingScopeId(scope.scope_id)
    setShowForm(true)
    setFormData({
      scope_type: scope.scope_type,
      action: scope.action,
      product_id: scope.product_id ?? '',
      product_name: scope.product_name ?? '',
      category_id: scope.category_id ?? '',
      category_name: scope.category_name ?? '',
      include_descendants: scope.include_descendants,
      branch_id: scope.branch_id ?? '',
      warehouse_id: scope.warehouse_id ?? '',
      valid_from: scope.valid_from ?? '',
      valid_until: scope.valid_until ?? '',
      priority_override: scope.priority_override?.toString() ?? '',
    })
  }, [])

  const handleDeleteScope = useCallback((scopeId: string) => {
    if (window.confirm('¿Eliminar este ámbito? Esta acción no se puede deshacer.')) {
      deleteScopeMutation.mutate({ scopeId })
    }
  }, [deleteScopeMutation])

  const handleSubmit = useCallback(() => {
    const payload: CreateQualityPlanScopeRequest = {
      scope_type: formData.scope_type,
      action: formData.action,
      product_id: formData.scope_type === 'PRODUCT' ? formData.product_id || undefined : undefined,
      category_id: formData.scope_type === 'CATEGORY' ? formData.category_id || undefined : undefined,
      include_descendants: formData.include_descendants,
      branch_id: formData.branch_id || undefined,
      warehouse_id: formData.warehouse_id || undefined,
      valid_from: formData.valid_from || undefined,
      valid_until: formData.valid_until || undefined,
      priority_override: formData.priority_override ? Number(formData.priority_override) : undefined,
    }

    if (!payload.product_id && !payload.category_id) {
      setError('Debe seleccionar un producto o categoría.')
      return
    }

    createScopeMutation.mutate(payload)
  }, [formData, createScopeMutation])

  const handleCancel = useCallback(() => {
    setShowForm(false)
    setEditingScopeId(null)
    setFormData(EMPTY_FORM)
    setError(null)
  }, [])

  if (error && !showForm) {
    return <ErrorPanel message={error} onRetry={() => { setError(null); onRefresh() }} />
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-bold text-slate-800">Ámbitos del plan</h3>
          <p className="text-xs text-slate-500">
            Defina a qué productos, categorías o ubicaciones aplica este plan.
          </p>
        </div>
        {capabilities.can_manage_scopes && !showForm && (
          <Button variant="primary" size="small" onClick={handleAddScope}>
            Agregar ámbito
          </Button>
        )}
      </div>

      {showForm && (
        <div className="rounded-xl border border-indigo-200 bg-indigo-50/30 p-4">
          <h4 className="mb-3 text-xs font-bold text-slate-800">
            {editingScopeId ? 'Editar ámbito' : 'Nuevo ámbito'}
          </h4>
          {error && (
            <div className="mb-3 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700">
              {error}
            </div>
          )}
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            <div>
              <label className="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                Tipo de ámbito
              </label>
              <select
                value={formData.scope_type}
                onChange={(e) => setFormData((p) => ({ ...p, scope_type: e.target.value as QualityPlanScopeType }))}
                className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-800 focus:border-[#1F4E6D] focus:outline-none focus:ring-1 focus:ring-[#1F4E6D]"
              >
                <option value="PRODUCT">Producto</option>
                <option value="CATEGORY">Categoría</option>
              </select>
            </div>
            <div>
              <label className="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                Acción
              </label>
              <select
                value={formData.action}
                onChange={(e) => setFormData((p) => ({ ...p, action: e.target.value as QualityPlanApplicabilityAction }))}
                className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-800 focus:border-[#1F4E6D] focus:outline-none focus:ring-1 focus:ring-[#1F4E6D]"
              >
                <option value="INCLUDE">Incluir</option>
                <option value="EXCLUDE">Excluir</option>
              </select>
            </div>
            {formData.scope_type === 'PRODUCT' && (
              <div>
                <label className="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                  Producto
                </label>
                <input
                  type="text"
                  placeholder="Buscar producto por SKU o nombre..."
                  value={formData.product_id ? formData.product_name : productSearch}
                  onChange={(e) => {
                    setProductSearch(e.target.value)
                    if (formData.product_id) {
                      setFormData((p) => ({ ...p, product_id: '', product_name: '' }))
                    }
                  }}
                  className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-800 focus:border-[#1F4E6D] focus:outline-none focus:ring-1 focus:ring-[#1F4E6D]"
                />
                {formData.product_id && (
                  <p className="mt-1 text-[10px] text-emerald-600">
                    Seleccionado: {formData.product_name}
                  </p>
                )}
              </div>
            )}
            {formData.scope_type === 'CATEGORY' && (
              <div>
                <label className="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                  Categoría
                </label>
                <input
                  type="text"
                  placeholder="Buscar categoría..."
                  value={formData.category_id ? formData.category_name : categorySearch}
                  onChange={(e) => {
                    setCategorySearch(e.target.value)
                    if (formData.category_id) {
                      setFormData((p) => ({ ...p, category_id: '', category_name: '' }))
                    }
                  }}
                  className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-800 focus:border-[#1F4E6D] focus:outline-none focus:ring-1 focus:ring-[#1F4E6D]"
                />
                {formData.category_id && (
                  <p className="mt-1 text-[10px] text-emerald-600">
                    Seleccionada: {formData.category_name}
                  </p>
                )}
              </div>
            )}
            {formData.scope_type === 'CATEGORY' && (
              <div className="flex items-end">
                <label className="flex items-center gap-2 text-xs text-slate-700">
                  <input
                    type="checkbox"
                    checked={formData.include_descendants}
                    onChange={(e) => setFormData((p) => ({ ...p, include_descendants: e.target.checked }))}
                    className="h-3.5 w-3.5 rounded border-slate-300 text-[#1F4E6D] focus:ring-[#1F4E6D]"
                  />
                  Incluir subcategorías
                </label>
              </div>
            )}
            <div>
              <label className="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                Sucursal
              </label>
              <input
                type="text"
                placeholder="ID de sucursal (opcional)"
                value={formData.branch_id}
                onChange={(e) => setFormData((p) => ({ ...p, branch_id: e.target.value }))}
                className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-800 focus:border-[#1F4E6D] focus:outline-none focus:ring-1 focus:ring-[#1F4E6D]"
              />
            </div>
            <div>
              <label className="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                Bodega
              </label>
              <input
                type="text"
                placeholder="ID de bodega (opcional)"
                value={formData.warehouse_id}
                onChange={(e) => setFormData((p) => ({ ...p, warehouse_id: e.target.value }))}
                className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-800 focus:border-[#1F4E6D] focus:outline-none focus:ring-1 focus:ring-[#1F4E6D]"
              />
            </div>
            <div>
              <label className="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                Válido desde
              </label>
              <input
                type="date"
                value={formData.valid_from}
                onChange={(e) => setFormData((p) => ({ ...p, valid_from: e.target.value }))}
                className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-800 focus:border-[#1F4E6D] focus:outline-none focus:ring-1 focus:ring-[#1F4E6D]"
              />
            </div>
            <div>
              <label className="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                Válido hasta
              </label>
              <input
                type="date"
                value={formData.valid_until}
                onChange={(e) => setFormData((p) => ({ ...p, valid_until: e.target.value }))}
                className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-800 focus:border-[#1F4E6D] focus:outline-none focus:ring-1 focus:ring-[#1F4E6D]"
              />
            </div>
            <div>
              <label className="mb-1 block text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                Prioridad (override)
              </label>
              <input
                type="number"
                min={0}
                max={100}
                placeholder="Heredar"
                value={formData.priority_override}
                onChange={(e) => setFormData((p) => ({ ...p, priority_override: e.target.value }))}
                className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-800 focus:border-[#1F4E6D] focus:outline-none focus:ring-1 focus:ring-[#1F4E6D]"
              />
            </div>
          </div>
          <div className="mt-4 flex items-center justify-end gap-2">
            <Button variant="ghost" size="small" onClick={handleCancel}>
              Cancelar
            </Button>
            <Button
              variant="primary"
              size="small"
              onClick={handleSubmit}
              isLoading={createScopeMutation.isPending}
            >
              {editingScopeId ? 'Guardar cambios' : 'Agregar ámbito'}
            </Button>
          </div>
        </div>
      )}

      {scopes.length === 0 && !showForm ? (
        <EmptyPanel
          title="Sin ámbitos configurados"
          description="Agregue ámbitos para definir a qué productos o categorías aplica este plan de inspección."
        />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-slate-200 text-left text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                <th className="px-2 py-2">Tipo</th>
                <th className="px-2 py-2">Acción</th>
                <th className="px-2 py-2">Recurso</th>
                <th className="px-2 py-2">Especificidad</th>
                <th className="px-2 py-2">Vigencia</th>
                <th className="px-2 py-2">Prioridad</th>
                <th className="px-2 py-2">Conflictos</th>
                <th className="px-2 py-2 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {scopes.map((scope) => (
                <tr key={scope.scope_id} className="hover:bg-slate-50/50">
                  <td className="px-2 py-2">
                    <StatusPill tone={scope.scope_type === 'PRODUCT' ? 'info' : 'warning'}>
                      {scope.scope_type === 'PRODUCT' ? 'Producto' : 'Categoría'}
                    </StatusPill>
                  </td>
                  <td className="px-2 py-2">
                    <StatusPill tone={scope.action === 'INCLUDE' ? 'success' : 'danger'}>
                      {scope.action === 'INCLUDE' ? 'Incluir' : 'Excluir'}
                    </StatusPill>
                  </td>
                  <td className="px-2 py-2">
                    <div className="text-slate-800">
                      {scope.scope_type === 'PRODUCT' ? (
                        <>
                          <span className="font-mono font-bold">{scope.product_sku}</span>
                          <span className="ml-1 text-slate-600">{scope.product_name}</span>
                        </>
                      ) : (
                        <>
                          <span className="font-mono font-bold">{scope.category_code}</span>
                          <span className="ml-1 text-slate-600">{scope.category_name}</span>
                          {scope.include_descendants && (
                            <span className="ml-1 text-[10px] text-slate-400">(con hijos)</span>
                          )}
                        </>
                      )}
                    </div>
                    {(scope.branch_name || scope.warehouse_name) && (
                      <p className="text-[10px] text-slate-400">
                        {scope.branch_name && `Sucursal: ${scope.branch_name}`}
                        {scope.branch_name && scope.warehouse_name && ' | '}
                        {scope.warehouse_name && `Bodega: ${scope.warehouse_name}`}
                      </p>
                    )}
                  </td>
                  <td className="px-2 py-2 font-mono text-slate-700">{scope.specificity}</td>
                  <td className="px-2 py-2 text-slate-600">
                    {formatDate(scope.valid_from)} — {formatDate(scope.valid_until)}
                  </td>
                  <td className="px-2 py-2 font-mono text-slate-700">
                    {scope.priority_override ?? '—'}
                  </td>
                  <td className="px-2 py-2">
                    {scope.conflict_count > 0 ? (
                      <StatusPill tone="danger">{scope.conflict_count}</StatusPill>
                    ) : (
                      <span className="text-slate-400">0</span>
                    )}
                  </td>
                  <td className="px-2 py-2">
                    <div className="flex items-center justify-end gap-1">
                      {capabilities.can_manage_scopes && (
                        <Button variant="ghost" size="small" onClick={() => handleEditScope(scope)}>
                          Editar
                        </Button>
                      )}
                      {capabilities.can_manage_scopes && (
                        <Button variant="ghost" size="small" onClick={() => handleDeleteScope(scope.scope_id)}>
                          Eliminar
                        </Button>
                      )}
                    </div>
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
