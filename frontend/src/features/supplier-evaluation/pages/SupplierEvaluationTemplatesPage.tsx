import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { supplierEvaluationTemplatesApi } from '../api/supplierEvaluationTemplatesApi'
import type { SupplierEvaluationTemplate } from '../types/evaluation'
import {
  EmptyState,
  ErrorState,
  StatusPill,
  TableSkeleton,
} from '../components/ui/SharedState'
import { Modal } from '../components/ui/Overlay'

export function SupplierEvaluationTemplatesPage() {
  const navigate = useNavigate()
  const perms = useLogisticsPermissions()
  const canManage = perms.hasPermission(
    LOGISTICS_PERMISSIONS.supplierEvaluations.manageTemplates,
  )

  const [items, setItems] = useState<SupplierEvaluationTemplate[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isError, setIsError] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const [createOpen, setCreateOpen] = useState(false)

  const [code, setCode] = useState('')
  const [name, setName] = useState('')
  const [scope, setScope] = useState<SupplierEvaluationTemplate['scope']>('QUOTATION')
  const [description, setDescription] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)

  const load = async () => {
    setIsLoading(true)
    setIsError(false)
    try {
      const res = await supplierEvaluationTemplatesApi.list({ page: 1, page_size: 100 })
      setItems(res.items ?? [])
    } catch (err: unknown) {
      setIsError(true)
      setErrorMessage(
        err instanceof Error ? err.message : 'No se pudieron cargar las plantillas.',
      )
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [])

  const handleCreate = async () => {
    if (!code.trim() || !name.trim()) {
      setFormError('Código y nombre son obligatorios.')
      return
    }
    setSubmitting(true)
    setFormError(null)
    try {
      await supplierEvaluationTemplatesApi.create({
        code: code.trim(),
        name: name.trim(),
        scope,
        description: description.trim() || null,
      })
      setCreateOpen(false)
      setCode('')
      setName('')
      setDescription('')
      await load()
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : 'No se pudo crear la plantilla.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-lg font-bold text-slate-900">Plantillas de evaluación</h1>
          <p className="text-xs text-slate-500">
            Define criterios, pesos y rúbricas. Las versiones activas no se editan en línea.
          </p>
        </div>
        {canManage && (
          <button
            type="button"
            onClick={() => setCreateOpen(true)}
            className="rounded-lg bg-[#1F4E6D] px-3.5 py-2 text-sm font-semibold text-white hover:bg-[#173a55]"
          >
            Nueva plantilla
          </button>
        )}
      </div>

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-xs">
        {isError ? (
          <div className="p-4">
            <ErrorState message={errorMessage} onRetry={() => void load()} />
          </div>
        ) : isLoading ? (
          <div className="p-4">
            <TableSkeleton />
          </div>
        ) : items.length === 0 ? (
          <div className="p-4">
            <EmptyState
              title="Aún no hay plantillas"
              description="Crea una plantilla para configurar criterios y pesos."
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50/60 text-xs font-semibold uppercase tracking-wide text-slate-500">
                <tr>
                  <th scope="col" className="px-3 py-2.5 text-left">Código</th>
                  <th scope="col" className="px-3 py-2.5 text-left">Nombre</th>
                  <th scope="col" className="px-3 py-2.5 text-left">Scope</th>
                  <th scope="col" className="px-3 py-2.5 text-left">Versión activa</th>
                  <th scope="col" className="px-3 py-2.5 text-right">Criterios</th>
                  <th scope="col" className="px-3 py-2.5 text-left">Estado</th>
                  <th scope="col" className="px-3 py-2.5 text-left">Vigencia</th>
                  <th scope="col" className="px-3 py-2.5 text-left">Actualización</th>
                  <th scope="col" className="px-3 py-2.5 text-right">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {items.map((t) => (
                  <tr key={t.id} className="hover:bg-slate-50/60">
                    <td className="px-3 py-2 font-mono text-xs">{t.code}</td>
                    <td className="px-3 py-2 text-xs font-medium text-slate-800">{t.name}</td>
                    <td className="px-3 py-2 text-xs text-slate-500">{t.scope}</td>
                    <td className="px-3 py-2 text-xs">
                      {t.active_version ? (
                        <span className="font-mono">{t.active_version.version}</span>
                      ) : (
                        <span className="text-slate-400">Sin versión activa</span>
                      )}
                    </td>
                    <td className="px-3 py-2 text-right font-mono text-xs">{t.criteria_count}</td>
                    <td className="px-3 py-2">
                      <StatusPill tone={templateTone(t.status)}>{t.status}</StatusPill>
                    </td>
                    <td className="px-3 py-2 text-xs text-slate-500">
                      {t.effective_from
                        ? new Date(t.effective_from).toLocaleDateString('es-PE')
                        : '—'}
                    </td>
                    <td className="px-3 py-2 text-xs text-slate-500">
                      {new Date(t.updated_at).toLocaleDateString('es-PE')}
                    </td>
                    <td className="px-3 py-2 text-right">
                      <button
                        type="button"
                        onClick={() => navigate(`/logistics/purchasing/evaluation-templates/${t.id}`)}
                        className="rounded-lg border border-slate-200 px-2.5 py-1 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                      >
                        Ver
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <Modal
        open={createOpen}
        onOpenChange={setCreateOpen}
        title="Nueva plantilla de evaluación"
        description="La cabecera es editable. Los criterios se configuran por versión."
        footer={
          <>
            <button
              type="button"
              onClick={() => setCreateOpen(false)}
              className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50"
            >
              Cancelar
            </button>
            <button
              type="button"
              disabled={submitting}
              onClick={handleCreate}
              className="rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#173a55] disabled:opacity-50"
            >
              {submitting ? 'Creando…' : 'Crear plantilla'}
            </button>
          </>
        }
      >
        <div className="space-y-3">
          {formError && (
            <p role="alert" className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700">
              {formError}
            </p>
          )}
          <div>
            <label htmlFor="tpl-code" className="mb-1 block text-xs font-bold text-slate-700">
              Código <span className="text-rose-500">*</span>
            </label>
            <input
              id="tpl-code"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
            />
          </div>
          <div>
            <label htmlFor="tpl-name" className="mb-1 block text-xs font-bold text-slate-700">
              Nombre <span className="text-rose-500">*</span>
            </label>
            <input
              id="tpl-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
            />
          </div>
          <div>
            <label htmlFor="tpl-scope" className="mb-1 block text-xs font-bold text-slate-700">
              Scope
            </label>
            <select
              id="tpl-scope"
              value={scope}
              onChange={(e) => setScope(e.target.value as SupplierEvaluationTemplate['scope'])}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
            >
              <option value="QUOTATION">Cotización</option>
              <option value="SUPPLIER">Proveedor</option>
              <option value="PRODUCT">Producto</option>
              <option value="GENERAL">General</option>
            </select>
          </div>
          <div>
            <label htmlFor="tpl-desc" className="mb-1 block text-xs font-bold text-slate-700">
              Descripción
            </label>
            <textarea
              id="tpl-desc"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
            />
          </div>
        </div>
      </Modal>
    </div>
  )
}

function templateTone(
  status: SupplierEvaluationTemplate['status'],
): 'neutral' | 'success' | 'muted' | 'warning' {
  switch (status) {
    case 'ACTIVE':
      return 'success'
    case 'DRAFT':
      return 'warning'
    case 'INACTIVE':
      return 'muted'
    case 'ARCHIVED':
      return 'muted'
    default:
      return 'neutral'
  }
}