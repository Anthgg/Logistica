import { useCallback, useEffect, useMemo, useState, type FormEvent } from 'react'
import { costCentersApi } from '../api/cost-centers-api'
import { Alert } from '../components/common/Alert'
import { Button } from '../components/common/Button'
import { LoadingSkeleton } from '../components/common/LoadingSkeleton'
import { LogisticsIcon } from '../components/common/LogisticsIcon'
import { PageHeader } from '../components/common/PageHeader'
import { useLogisticsPermissions } from '../features/logistics-permissions/hooks/useLogisticsPermissions'
import { LOGISTICS_PERMISSIONS } from '../features/logistics-permissions/logistics-permissions-map'
import { useLogisticsAccess } from '../features/logistics-me/hooks/useLogisticsAccess'
import type {
  CostCenter,
  CostCenterCreate,
  CostCenterStatus,
  CostCenterUpdate,
} from '../types/purchase-requisitions'
import { getErrorMessage } from '../utils/errors'

const STATUS_META: Record<CostCenterStatus, { label: string; className: string }> = {
  DRAFT: { label: 'Borrador', className: 'border-amber-200 bg-amber-50 text-amber-800' },
  ACTIVE: { label: 'Activo', className: 'border-emerald-200 bg-emerald-50 text-emerald-800' },
  INACTIVE: { label: 'Inactivo', className: 'border-slate-200 bg-slate-100 text-slate-700' },
  ARCHIVED: { label: 'Archivado', className: 'border-violet-200 bg-violet-50 text-violet-800' },
}

const INPUT_CLASS =
  'w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100 disabled:bg-slate-100'

function today(): string {
  return new Date().toISOString().slice(0, 10)
}

function formatDate(value: string | null): string {
  if (!value) return 'Sin vencimiento'
  return new Intl.DateTimeFormat('es-PE', { dateStyle: 'medium', timeZone: 'UTC' }).format(
    new Date(`${value.slice(0, 10)}T00:00:00Z`),
  )
}

function StatusBadge({ status }: { status: CostCenterStatus }) {
  const meta = STATUS_META[status]
  return (
    <span className={`inline-flex rounded-full border px-2.5 py-1 text-[11px] font-bold ${meta.className}`}>
      {meta.label}
    </span>
  )
}

interface CenterFormDialogProps {
  center: CostCenter | null
  centers: CostCenter[]
  branchId: string | null
  isSaving: boolean
  error: string | null
  onClose: () => void
  onCreate: (data: CostCenterCreate) => Promise<void>
  onUpdate: (id: string, data: CostCenterUpdate) => Promise<void>
}

function CenterFormDialog({
  center,
  centers,
  branchId,
  isSaving,
  error,
  onClose,
  onCreate,
  onUpdate,
}: CenterFormDialogProps) {
  const [code, setCode] = useState(center?.code ?? '')
  const [name, setName] = useState(center?.name ?? '')
  const [description, setDescription] = useState(center?.description ?? '')
  const [parentId, setParentId] = useState(center?.parent_cost_center_id ?? '')
  const [validFrom, setValidFrom] = useState(center?.valid_from ?? today())
  const [validUntil, setValidUntil] = useState(center?.valid_until ?? '')

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (center) {
      await onUpdate(center.id, {
        name: name.trim(),
        description: description.trim() || null,
        valid_until: validUntil || null,
        row_version: center.row_version,
      })
      return
    }
    await onCreate({
      code: code.trim(),
      name: name.trim(),
      description: description.trim() || null,
      branch_id: branchId,
      parent_cost_center_id: parentId || null,
      valid_from: validFrom,
      valid_until: validUntil || null,
    })
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-slate-950/45 p-0 backdrop-blur-sm sm:items-center sm:p-6">
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby="cost-center-dialog-title"
        className="max-h-[92vh] w-full overflow-y-auto rounded-t-3xl bg-white shadow-2xl sm:max-w-2xl sm:rounded-3xl"
      >
        <form onSubmit={(event) => void submit(event)}>
          <div className="flex items-start justify-between gap-5 border-b border-slate-200 px-5 py-5 sm:px-7">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.18em] text-blue-700">
                {center ? 'Edición controlada' : 'Nuevo registro maestro'}
              </p>
              <h2 id="cost-center-dialog-title" className="mt-1 text-xl font-bold text-slate-950">
                {center ? `Editar ${center.code}` : 'Crear centro de costo'}
              </h2>
              <p className="mt-1 text-sm text-slate-500">
                {center
                  ? 'El código, la sede y la jerarquía se conservan para mantener la trazabilidad.'
                  : 'El registro se crea como borrador y luego puede activarse desde el catálogo.'}
              </p>
            </div>
            <button
              type="button"
              onClick={onClose}
              aria-label="Cerrar"
              className="rounded-xl p-2 text-slate-500 transition hover:bg-slate-100 hover:text-slate-950"
            >
              <LogisticsIcon name="x" size={20} aria-hidden="true" />
            </button>
          </div>

          <div className="space-y-5 px-5 py-6 sm:px-7">
            {error && <Alert variant="error">{error}</Alert>}
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="space-y-1.5 text-sm font-semibold text-slate-700">
                Código
                <input
                  value={code}
                  onChange={(event) => setCode(event.target.value.toUpperCase().replaceAll(' ', '_'))}
                  maxLength={50}
                  required
                  disabled={Boolean(center) || isSaving}
                  placeholder="OPERACIONES_NORTE"
                  className={`${INPUT_CLASS} font-mono uppercase`}
                />
              </label>
              <label className="space-y-1.5 text-sm font-semibold text-slate-700">
                Nombre
                <input
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  maxLength={150}
                  required
                  disabled={isSaving}
                  placeholder="Operaciones zona norte"
                  className={INPUT_CLASS}
                />
              </label>
            </div>

            <label className="space-y-1.5 text-sm font-semibold text-slate-700">
              Descripción
              <textarea
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                rows={3}
                maxLength={1000}
                disabled={isSaving}
                placeholder="Alcance operativo y criterio de imputación del centro."
                className={`${INPUT_CLASS} resize-y`}
              />
            </label>

            {!center && (
              <label className="space-y-1.5 text-sm font-semibold text-slate-700">
                Centro superior
                <select
                  value={parentId}
                  onChange={(event) => setParentId(event.target.value)}
                  disabled={isSaving}
                  className={INPUT_CLASS}
                >
                  <option value="">Sin centro superior</option>
                  {centers
                    .filter((item) => item.status !== 'ARCHIVED')
                    .map((item) => (
                      <option key={item.id} value={item.id}>
                        {item.code} · {item.name}
                      </option>
                    ))}
                </select>
              </label>
            )}

            <div className="grid gap-4 sm:grid-cols-2">
              <label className="space-y-1.5 text-sm font-semibold text-slate-700">
                Vigente desde
                <input
                  type="date"
                  value={validFrom}
                  onChange={(event) => setValidFrom(event.target.value)}
                  required
                  disabled={Boolean(center) || isSaving}
                  className={INPUT_CLASS}
                />
              </label>
              <label className="space-y-1.5 text-sm font-semibold text-slate-700">
                Vigente hasta
                <input
                  type="date"
                  value={validUntil}
                  min={center?.valid_from ?? validFrom}
                  onChange={(event) => setValidUntil(event.target.value)}
                  disabled={isSaving}
                  className={INPUT_CLASS}
                />
              </label>
            </div>

            <div className="rounded-2xl border border-blue-100 bg-blue-50 px-4 py-3 text-sm leading-6 text-blue-900">
              <span className="font-bold">Alcance:</span>{' '}
              {branchId ? 'se asociará a la sede seleccionada en el encabezado.' : 'aplicará a toda la organización seleccionada.'}
            </div>
          </div>

          <div className="flex flex-col-reverse gap-3 border-t border-slate-200 bg-slate-50 px-5 py-4 sm:flex-row sm:justify-end sm:px-7">
            <Button type="button" variant="secondary" onClick={onClose} disabled={isSaving}>
              Cancelar
            </Button>
            <Button type="submit" isLoading={isSaving} loadingLabel="Guardando…">
              {center ? 'Guardar cambios' : 'Crear borrador'}
            </Button>
          </div>
        </form>
      </section>
    </div>
  )
}

type TransitionAction = 'activate' | 'deactivate' | 'archive'

interface TransitionDialogProps {
  center: CostCenter
  action: TransitionAction
  isSaving: boolean
  error: string | null
  onClose: () => void
  onConfirm: () => Promise<void>
}

function TransitionDialog({ center, action, isSaving, error, onClose, onConfirm }: TransitionDialogProps) {
  const copy = {
    activate: {
      eyebrow: 'Habilitar imputación',
      title: 'Activar centro de costo',
      description: 'Quedará disponible para nuevas requisiciones y operaciones logísticas.',
      button: 'Activar centro',
    },
    deactivate: {
      eyebrow: 'Retiro temporal',
      title: 'Desactivar centro de costo',
      description: 'Dejará de estar disponible para nuevas imputaciones, pero conservará su historial.',
      button: 'Desactivar centro',
    },
    archive: {
      eyebrow: 'Cierre del registro',
      title: 'Archivar centro de costo',
      description: 'El backend impedirá el cierre si existen requisiciones abiertas que todavía lo utilicen.',
      button: 'Archivar centro',
    },
  }[action]

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-slate-950/45 p-0 backdrop-blur-sm sm:items-center sm:p-6">
      <section role="alertdialog" aria-modal="true" className="w-full rounded-t-3xl bg-white p-6 shadow-2xl sm:max-w-md sm:rounded-3xl">
        <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-950 text-white">
          <LogisticsIcon name={action === 'activate' ? 'play' : action === 'deactivate' ? 'pause' : 'archive'} size={21} aria-hidden="true" />
        </span>
        <p className="mt-5 text-xs font-bold uppercase tracking-[0.18em] text-blue-700">{copy.eyebrow}</p>
        <h2 className="mt-1 text-xl font-bold text-slate-950">{copy.title}</h2>
        <p className="mt-2 text-sm leading-6 text-slate-600">{copy.description}</p>
        <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <p className="font-mono text-xs font-bold text-blue-700">{center.code}</p>
          <p className="mt-1 font-semibold text-slate-950">{center.name}</p>
        </div>
        {error && <div className="mt-4"><Alert variant="error">{error}</Alert></div>}
        <div className="mt-6 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
          <Button variant="secondary" onClick={onClose} disabled={isSaving}>Cancelar</Button>
          <Button
            variant={action === 'archive' ? 'danger' : 'primary'}
            isLoading={isSaving}
            loadingLabel="Aplicando…"
            onClick={() => void onConfirm()}
          >
            {copy.button}
          </Button>
        </div>
      </section>
    </div>
  )
}

export function CostCentersPage() {
  const { currentContext } = useLogisticsAccess()
  const { hasPermission } = useLogisticsPermissions()
  const organizationId = currentContext.organization_id
  const branchId = currentContext.branch_id
  const canManage = hasPermission(LOGISTICS_PERMISSIONS.costCenters.manage)
  const [centers, setCenters] = useState<CostCenter[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState<CostCenterStatus | ''>('')
  const [formCenter, setFormCenter] = useState<CostCenter | null | undefined>(undefined)
  const [transition, setTransition] = useState<{ center: CostCenter; action: TransitionAction } | null>(null)
  const [saving, setSaving] = useState(false)
  const [dialogError, setDialogError] = useState<string | null>(null)

  const loadData = useCallback(async () => {
    if (!organizationId) {
      setCenters([])
      setError(null)
      return
    }
    setLoading(true)
    setError(null)
    try {
      setCenters(await costCentersApi.list({ branch_id: branchId, limit: 100 }))
    } catch (loadError) {
      setError(getErrorMessage(loadError))
    } finally {
      setLoading(false)
    }
  }, [branchId, organizationId])

  useEffect(() => {
    void loadData()
  }, [loadData])

  const parentById = useMemo(() => new Map(centers.map((center) => [center.id, center])), [centers])
  const filteredCenters = useMemo(() => {
    const normalizedSearch = search.trim().toLocaleLowerCase('es')
    return centers.filter((center) => {
      const matchesStatus = !status || center.status === status
      const matchesSearch =
        !normalizedSearch ||
        center.code.toLocaleLowerCase('es').includes(normalizedSearch) ||
        center.name.toLocaleLowerCase('es').includes(normalizedSearch) ||
        center.description?.toLocaleLowerCase('es').includes(normalizedSearch)
      return matchesStatus && Boolean(matchesSearch)
    })
  }, [centers, search, status])

  const metrics = useMemo(
    () => ({
      total: centers.length,
      active: centers.filter((center) => center.status === 'ACTIVE').length,
      draft: centers.filter((center) => center.status === 'DRAFT').length,
      unavailable: centers.filter((center) => center.status === 'INACTIVE' || center.status === 'ARCHIVED').length,
    }),
    [centers],
  )

  const closeDialogs = () => {
    setFormCenter(undefined)
    setTransition(null)
    setDialogError(null)
  }

  const createCenter = async (data: CostCenterCreate) => {
    setSaving(true)
    setDialogError(null)
    try {
      await costCentersApi.create(data)
      closeDialogs()
      await loadData()
    } catch (saveError) {
      setDialogError(getErrorMessage(saveError))
    } finally {
      setSaving(false)
    }
  }

  const updateCenter = async (id: string, data: CostCenterUpdate) => {
    setSaving(true)
    setDialogError(null)
    try {
      await costCentersApi.update(id, data)
      closeDialogs()
      await loadData()
    } catch (saveError) {
      setDialogError(getErrorMessage(saveError))
    } finally {
      setSaving(false)
    }
  }

  const runTransition = async () => {
    if (!transition) return
    setSaving(true)
    setDialogError(null)
    try {
      await costCentersApi[transition.action](transition.center.id)
      closeDialogs()
      await loadData()
    } catch (saveError) {
      setDialogError(getErrorMessage(saveError))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-6 pb-10">
      <PageHeader
        eyebrow="Catálogo logístico · Gobierno de datos"
        title="Centros de costo"
        description="Administra la estructura de imputación usada por compras y operaciones, con vigencia, jerarquía y trazabilidad por organización."
        actions={
          <div className="flex flex-wrap gap-2">
            <Button variant="secondary" onClick={() => void loadData()} disabled={!organizationId || loading}>
              <span className="inline-flex items-center gap-2">
                <LogisticsIcon name="activity" size={16} aria-hidden="true" /> Actualizar
              </span>
            </Button>
            {canManage && organizationId && (
              <Button onClick={() => { setDialogError(null); setFormCenter(null) }}>
                <span className="inline-flex items-center gap-2">
                  <LogisticsIcon name="building" size={16} aria-hidden="true" /> Nuevo centro
                </span>
              </Button>
            )}
          </div>
        }
      />

      {!organizationId ? (
        <section className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
          <div className="grid gap-8 p-6 sm:p-8 lg:grid-cols-[1fr_0.9fr] lg:items-center">
            <div>
              <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-50 text-blue-700">
                <LogisticsIcon name="building" size={22} aria-hidden="true" />
              </span>
              <p className="mt-5 text-xs font-bold uppercase tracking-[0.18em] text-blue-700">Contexto requerido</p>
              <h2 className="mt-2 text-2xl font-bold text-slate-950">Selecciona una organización</h2>
              <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
                Usa el selector del encabezado. Los centros de costo se mantienen aislados por organización y, si eliges una sede, el catálogo se limita a ese alcance.
              </p>
            </div>
            <div className="rounded-3xl bg-slate-950 p-6 text-white">
              <p className="text-xs font-bold uppercase tracking-[0.16em] text-blue-300">Antes de consultar</p>
              <ul className="mt-4 space-y-3 text-sm text-slate-300">
                <li className="flex gap-3"><LogisticsIcon name="check" size={17} className="mt-0.5 text-emerald-300" aria-hidden="true" /> Elige la organización autorizada.</li>
                <li className="flex gap-3"><LogisticsIcon name="check" size={17} className="mt-0.5 text-emerald-300" aria-hidden="true" /> Selecciona una sede solo si necesitas filtrar su catálogo.</li>
                <li className="flex gap-3"><LogisticsIcon name="check" size={17} className="mt-0.5 text-emerald-300" aria-hidden="true" /> Las acciones de gestión aparecen según tu permiso efectivo.</li>
              </ul>
            </div>
          </div>
        </section>
      ) : (
        <>
          <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {[
              { label: 'Registros del alcance', value: metrics.total, icon: 'layers' as const, accent: 'text-blue-700 bg-blue-50' },
              { label: 'Disponibles para imputar', value: metrics.active, icon: 'check' as const, accent: 'text-emerald-700 bg-emerald-50' },
              { label: 'Pendientes de activar', value: metrics.draft, icon: 'clock' as const, accent: 'text-amber-700 bg-amber-50' },
              { label: 'Fuera de uso', value: metrics.unavailable, icon: 'archive' as const, accent: 'text-violet-700 bg-violet-50' },
            ].map((metric) => (
              <article key={metric.label} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-sm font-medium text-slate-500">{metric.label}</p>
                    <p className="mt-2 text-3xl font-bold tracking-tight text-slate-950">{loading ? '—' : metric.value}</p>
                  </div>
                  <span className={`flex h-10 w-10 items-center justify-center rounded-xl ${metric.accent}`}>
                    <LogisticsIcon name={metric.icon} size={19} aria-hidden="true" />
                  </span>
                </div>
              </article>
            ))}
          </section>

          <section className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
            <div className="border-b border-slate-200 p-4 sm:p-5">
              <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                <div>
                  <h2 className="text-lg font-bold text-slate-950">Estructura de imputación</h2>
                  <p className="mt-1 text-sm text-slate-500">Consulta vigencia, nivel jerárquico y estado operativo.</p>
                </div>
                <div className="grid gap-2 sm:grid-cols-[minmax(220px,1fr)_180px]">
                  <label className="relative block">
                    <span className="sr-only">Buscar centros de costo</span>
                    <LogisticsIcon name="search" size={17} className="pointer-events-none absolute left-3 top-3 text-slate-400" aria-hidden="true" />
                    <input
                      value={search}
                      onChange={(event) => setSearch(event.target.value)}
                      placeholder="Buscar código o nombre"
                      className={`${INPUT_CLASS} pl-10`}
                    />
                  </label>
                  <label>
                    <span className="sr-only">Filtrar por estado</span>
                    <select value={status} onChange={(event) => setStatus(event.target.value as CostCenterStatus | '')} className={INPUT_CLASS}>
                      <option value="">Todos los estados</option>
                      <option value="ACTIVE">Activos</option>
                      <option value="DRAFT">Borradores</option>
                      <option value="INACTIVE">Inactivos</option>
                      <option value="ARCHIVED">Archivados</option>
                    </select>
                  </label>
                </div>
              </div>
            </div>

            {loading ? (
              <div className="p-5"><LoadingSkeleton rows={6} /></div>
            ) : error ? (
              <div className="p-5 sm:p-8">
                <Alert variant="error">{error}</Alert>
                <div className="mt-4"><Button variant="secondary" onClick={() => void loadData()}>Reintentar</Button></div>
              </div>
            ) : filteredCenters.length === 0 ? (
              <div className="px-6 py-16 text-center">
                <span className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-100 text-slate-500">
                  <LogisticsIcon name="search" size={23} aria-hidden="true" />
                </span>
                <h3 className="mt-4 text-lg font-bold text-slate-950">
                  {centers.length === 0 ? 'El catálogo todavía está vacío' : 'No encontramos coincidencias'}
                </h3>
                <p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-slate-500">
                  {centers.length === 0
                    ? canManage
                      ? 'Crea el primer centro como borrador, revisa su vigencia y actívalo cuando esté listo para imputación.'
                      : 'No existen centros de costo registrados para el contexto seleccionado.'
                    : 'Prueba otro texto de búsqueda o cambia el filtro de estado.'}
                </p>
                {centers.length === 0 && canManage && (
                  <div className="mt-5"><Button onClick={() => { setDialogError(null); setFormCenter(null) }}>Crear primer centro</Button></div>
                )}
              </div>
            ) : (
              <>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-slate-200 text-sm">
                    <thead className="bg-slate-50 text-left text-xs font-bold uppercase tracking-wide text-slate-500">
                      <tr>
                        <th className="px-5 py-3.5">Centro</th>
                        <th className="px-5 py-3.5">Jerarquía</th>
                        <th className="px-5 py-3.5">Alcance</th>
                        <th className="px-5 py-3.5">Vigencia</th>
                        <th className="px-5 py-3.5">Estado</th>
                        {canManage && <th className="px-5 py-3.5 text-right">Acciones</th>}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {filteredCenters.map((center) => {
                        const parent = center.parent_cost_center_id ? parentById.get(center.parent_cost_center_id) : null
                        return (
                          <tr key={center.id} className="transition hover:bg-slate-50/80">
                            <td className="px-5 py-4">
                              <p className="font-mono text-xs font-bold text-blue-700">{center.code}</p>
                              <p className="mt-1 font-bold text-slate-950">{center.name}</p>
                              <p className="mt-1 max-w-sm truncate text-xs text-slate-500">{center.description || 'Sin descripción operativa'}</p>
                            </td>
                            <td className="px-5 py-4 text-slate-600">
                              {parent ? <><span className="font-mono text-xs font-bold">{parent.code}</span><span className="block text-xs">{parent.name}</span></> : 'Nivel raíz'}
                            </td>
                            <td className="px-5 py-4 text-slate-600">{center.branch_id ? 'Sede seleccionada' : 'Organización'}</td>
                            <td className="px-5 py-4 text-slate-600">
                              <span className="block">Desde {formatDate(center.valid_from)}</span>
                              <span className="mt-1 block text-xs text-slate-500">{formatDate(center.valid_until)}</span>
                            </td>
                            <td className="px-5 py-4"><StatusBadge status={center.status} /></td>
                            {canManage && (
                              <td className="px-5 py-4">
                                <div className="flex justify-end gap-1">
                                  {center.status !== 'ARCHIVED' && (
                                    <Button size="small" variant="ghost" onClick={() => { setDialogError(null); setFormCenter(center) }}>Editar</Button>
                                  )}
                                  {(center.status === 'DRAFT' || center.status === 'INACTIVE') && (
                                    <Button size="small" variant="ghost" onClick={() => { setDialogError(null); setTransition({ center, action: 'activate' }) }}>Activar</Button>
                                  )}
                                  {center.status === 'ACTIVE' && (
                                    <Button size="small" variant="ghost" onClick={() => { setDialogError(null); setTransition({ center, action: 'deactivate' }) }}>Desactivar</Button>
                                  )}
                                  {center.status !== 'ARCHIVED' && (
                                    <Button size="small" variant="ghost" onClick={() => { setDialogError(null); setTransition({ center, action: 'archive' }) }}>Archivar</Button>
                                  )}
                                </div>
                              </td>
                            )}
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>

              </>
            )}
          </section>
        </>
      )}

      {formCenter !== undefined && (
        <CenterFormDialog
          key={formCenter?.id ?? 'new'}
          center={formCenter}
          centers={centers}
          branchId={branchId}
          isSaving={saving}
          error={dialogError}
          onClose={closeDialogs}
          onCreate={createCenter}
          onUpdate={updateCenter}
        />
      )}
      {transition && (
        <TransitionDialog
          center={transition.center}
          action={transition.action}
          isSaving={saving}
          error={dialogError}
          onClose={closeDialogs}
          onConfirm={runTransition}
        />
      )}
    </div>
  )
}
