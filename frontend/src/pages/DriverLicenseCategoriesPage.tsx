import { useCallback, useEffect, useState } from 'react'
import { driversApi } from '../api/drivers-api'
import { PageHeader } from '../components/common/PageHeader'
import { Button } from '../components/common/Button'
import { Input } from '../components/common/Input'
import { LoadingSkeleton } from '../components/common/LoadingSkeleton'
import { EmptyState } from '../components/common/EmptyState'
import { Alert } from '../components/common/Alert'
import { LOGISTICS_PERMISSIONS } from '../features/logistics-permissions/logistics-permissions-map'
import { useLogisticsPermissions } from '../features/logistics-permissions/hooks/useLogisticsPermissions'
import { getErrorMessage } from '../utils/errors'
import type { DriverLicenseCategory, DriverLicenseCategoryCreate } from '../types/drivers'

export function DriverLicenseCategoriesPage() {
  const auth = useLogisticsPermissions()
  const canManage = auth.hasPermission(LOGISTICS_PERMISSIONS.drivers.manageCategories)

  const [categories, setCategories] = useState<DriverLicenseCategory[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showCreate, setShowCreate] = useState(false)
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await driversApi.listLicenseCategories()
      setCategories(res)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const handleCreate = async (formData: DriverLicenseCategoryCreate | Record<string, unknown>) => {
    setCreating(true)
    setCreateError(null)
    try {
      await driversApi.createLicenseCategory(formData as DriverLicenseCategoryCreate)
      setShowCreate(false)
      await load()
    } catch (err) {
      setCreateError(getErrorMessage(err))
    } finally {
      setCreating(false)
    }
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-6">
      <PageHeader
        title="Categorías de licencia"
        description="Catálogo de categorías de licencia de conducir"
        actions={canManage ? <Button onClick={() => setShowCreate(true)}>+ Nueva categoría</Button> : undefined}
      />

      <div className="rounded-lg bg-blue-50 border border-blue-200 px-4 py-3 text-sm text-blue-700">
        Las categorías deben ser revisadas y aprobadas conforme a la jurisdicción aplicable.
      </div>

      {error && <Alert variant="error">{error}</Alert>}

      {loading ? (
        <LoadingSkeleton rows={6} />
      ) : categories.length === 0 ? (
        <EmptyState title="Sin categorías" description="No hay categorías de licencia registradas." />
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs font-medium uppercase text-slate-500">
              <tr>
                <th className="px-3 py-2">Código</th>
                <th className="px-3 py-2">Nombre</th>
                <th className="px-3 py-2 hidden sm:table-cell">Jurisdicción</th>
                <th className="px-3 py-2 hidden md:table-cell">Grupo</th>
                <th className="px-3 py-2 hidden lg:table-cell">Validez</th>
                <th className="px-3 py-2">Estado</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {categories.map((cat) => (
                <tr key={cat.id} className="hover:bg-slate-50">
                  <td className="px-3 py-2 font-mono text-xs text-slate-700">{cat.code}</td>
                  <td className="px-3 py-2 font-medium text-slate-900">{cat.name}</td>
                  <td className="px-3 py-2 hidden sm:table-cell text-slate-600">{cat.jurisdiction}</td>
                  <td className="px-3 py-2 hidden md:table-cell text-slate-600">{cat.group}</td>
                  <td className="px-3 py-2 hidden lg:table-cell text-slate-600">
                    {cat.validity_years ? `${cat.validity_years} años` : '—'}
                  </td>
                  <td className="px-3 py-2">
                    <span className={`text-xs ${cat.status === 'ACTIVE' ? 'text-emerald-600' : cat.status === 'DRAFT' ? 'text-amber-600' : 'text-slate-400'}`}>
                      {cat.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-4 backdrop-blur-sm" onClick={() => { setShowCreate(false); setCreateError(null) }}>
          <div className="w-full max-w-2xl rounded-2xl border border-slate-700 bg-slate-900 p-5 shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-base font-bold text-slate-100">Nueva categoría de licencia</h2>
              <button type="button" onClick={() => { setShowCreate(false); setCreateError(null) }} className="text-slate-400 hover:text-white" aria-label="Cerrar"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" aria-hidden="true"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
            </div>
            {createError && <div className="mb-4 rounded-lg bg-rose-50 border border-rose-200 px-3 py-2 text-sm text-rose-700">{createError}</div>}
            <CreateCategoryForm onSubmit={handleCreate} onCancel={() => { setShowCreate(false); setCreateError(null) }} isSubmitting={creating} />
          </div>
        </div>
      )}
    </div>
  )
}

function CreateCategoryForm({ onSubmit, onCancel, isSubmitting }: {
  onSubmit: (data: DriverLicenseCategoryCreate) => Promise<void>
  onCancel: () => void
  isSubmitting: boolean
}) {
  const [code, setCode] = useState('')
  const [name, setName] = useState('')
  const [jurisdiction, setJurisdiction] = useState('')
  const [group, setGroup] = useState('')
  const [validityYears, setValidityYears] = useState('')
  const [reference, setReference] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!code.trim() || !name.trim() || !jurisdiction.trim()) return
    void onSubmit({
      code: code.trim(),
      name: name.trim(),
      jurisdiction: jurisdiction.trim(),
      group: group.trim() || undefined,
      validity_years: validityYears ? Number(validityYears) : undefined,
      reference: reference.trim() || undefined,
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Input label="Código" value={code} onChange={(e) => setCode(e.target.value)} required />
        <Input label="Nombre" value={name} onChange={(e) => setName(e.target.value)} required />
        <Input label="Jurisdicción" value={jurisdiction} onChange={(e) => setJurisdiction(e.target.value)} required />
        <Input label="Grupo (opcional)" value={group} onChange={(e) => setGroup(e.target.value)} />
        <Input label="Validez en años (opcional)" type="number" value={validityYears} onChange={(e) => setValidityYears(e.target.value)} />
        <Input label="Referencia (opcional)" value={reference} onChange={(e) => setReference(e.target.value)} />
      </div>
      <div className="flex justify-end gap-3 pt-2">
        <Button type="button" variant="ghost" onClick={onCancel} disabled={isSubmitting}>Cancelar</Button>
        <Button type="submit" disabled={isSubmitting} isLoading={isSubmitting}>Crear categoría</Button>
      </div>
    </form>
  )
}