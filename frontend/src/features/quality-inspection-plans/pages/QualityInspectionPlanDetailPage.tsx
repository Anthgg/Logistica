import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { PageHeader } from '../../../components/common/PageHeader'
import { Button } from '../../../components/common/Button'
import { Alert } from '../../../components/common/Alert'
import { LoadingSkeleton } from '../../../components/common/LoadingSkeleton'
import { EmptyState } from '../../../components/common/EmptyState'

import { useQuery, useMutation } from '../../inbound-docks/hooks/useQuery'
import { qualityInspectionPlansApi } from '../api/qualityInspectionPlansApi'
import { getErrorMessage } from '../../../utils/errors'
import type {
  QualityInspectionPlan,
  QualityInspectionPlanCapabilities,
  QualityInspectionPlanStatus,
} from '../types/quality-inspection-plans'

type DetailTab =
  | 'summary'
  | 'versions'
  | 'scopes'
  | 'controls'
  | 'tolerances'
  | 'sampling'
  | 'certificates'
  | 'resolutions'
  | 'integrity'
  | 'history'

const DETAIL_TABS: { key: DetailTab; label: string }[] = [
  { key: 'summary', label: 'Resumen' },
  { key: 'versions', label: 'Versiones' },
  { key: 'scopes', label: 'Ámbitos' },
  { key: 'controls', label: 'Controles' },
  { key: 'tolerances', label: 'Tolerancias' },
  { key: 'sampling', label: 'Muestreo' },
  { key: 'certificates', label: 'Certificados' },
  { key: 'resolutions', label: 'Resoluciones' },
  { key: 'integrity', label: 'Integridad' },
  { key: 'history', label: 'Historial' },
]

const STATUS_LABELS: Record<QualityInspectionPlanStatus, string> = {
  DRAFT: 'Borrador',
  VALIDATED: 'Validado',
  SCHEDULED: 'Programado',
  ACTIVE: 'Activo',
  RETIRED: 'Retirado',
  ARCHIVED: 'Archivado',
}

const STATUS_TONE: Record<QualityInspectionPlanStatus, string> = {
  DRAFT: 'bg-slate-100 text-slate-700',
  VALIDATED: 'bg-blue-50 text-blue-700',
  SCHEDULED: 'bg-amber-50 text-amber-700',
  ACTIVE: 'bg-emerald-50 text-emerald-700',
  RETIRED: 'bg-slate-100 text-slate-500',
  ARCHIVED: 'bg-slate-50 text-slate-400',
}

export function QualityInspectionPlanDetailPage() {
  const { planId } = useParams<{ planId: string }>()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<DetailTab>('summary')

  const plan = useQuery<QualityInspectionPlan>(
    ['quality-inspection-plans', 'detail', planId ?? ''],
    `/logistics/quality-inspection-plans/${planId}`,
    undefined,
    { enabled: Boolean(planId) },
  )

  const capabilities = useQuery<QualityInspectionPlanCapabilities>(
    ['quality-inspection-plans', 'capabilities', planId ?? ''],
    `/logistics/quality-inspection-plans/${planId}/capabilities`,
    undefined,
    { enabled: Boolean(planId) },
  )

  const archiveMutation = useMutation(
    () => qualityInspectionPlansApi.archive(planId!),
    { onSuccess: () => void plan.refetch() },
  )

  const restoreMutation = useMutation(
    () => qualityInspectionPlansApi.deactivate(planId!),
    { onSuccess: () => void plan.refetch() },
  )

  useEffect(() => {
    setActiveTab('summary')
  }, [planId])

  const canEdit = capabilities.data?.can_update ?? false
  const canArchive = capabilities.data?.can_archive ?? false
  const canRestore = plan.data?.status === 'ARCHIVED'

  if (plan.isLoading) {
    return (
      <div className="space-y-4">
        <PageHeader title="Detalle de plan" />
        <LoadingSkeleton rows={6} />
      </div>
    )
  }

  if (plan.isError || !plan.data) {
    return (
      <div className="space-y-4">
        <PageHeader title="Detalle de plan" />
        <Alert variant="error">{plan.error ? getErrorMessage(plan.error) : 'Plan no encontrado.'}</Alert>
        <Button size="small" variant="secondary" onClick={() => navigate('/logistics/quality-inspection-plans')}>
          ← Volver
        </Button>
      </div>
    )
  }

  const p = plan.data
  return (
    <div className="space-y-4">
      <PageHeader
        eyebrow="Fase 041"
        title={`${p.code} — ${p.name}`}
        description={p.description ?? 'Sin descripción'}
        actions={
          <div className="flex gap-2">
            <Button size="small" variant="ghost" onClick={() => navigate('/logistics/quality-inspection-plans')}>
              ← Volver
            </Button>
            {canEdit && (
              <Button size="small" variant="secondary">
                Editar
              </Button>
            )}
            {canArchive && p.status !== 'ARCHIVED' && (
              <Button
                size="small"
                variant="danger"
                isLoading={archiveMutation.isPending}
                onClick={() => void archiveMutation.mutate(undefined as never)}
              >
                Archivar
              </Button>
            )}
            {canRestore && (
              <Button
                size="small"
                variant="secondary"
                isLoading={restoreMutation.isPending}
                onClick={() => void restoreMutation.mutate(undefined as never)}
              >
                Restaurar
              </Button>
            )}
          </div>
        }
      />

      {/* Header info */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-6">
        {[
          ['Familia', p.family],
          ['Estado', STATUS_LABELS[p.status]],
          ['V. activa', p.active_version_number != null ? `v${String(p.active_version_number)}` : '—'],
          ['Vigencia', p.active_version_valid_from && p.active_version_valid_until
            ? `${new Date(p.active_version_valid_from).toLocaleDateString('es-PE')} — ${new Date(p.active_version_valid_until).toLocaleDateString('es-PE')}`
            : '—'],
          ['Prioridad', String(p.priority)],
          ['Conflictos', String(p.conflict_count)],
        ].map(([label, value]) => (
          <div key={label} className="rounded-xl border border-[#EEF2F5] bg-white p-3">
            <dt className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">{label}</dt>
            <dd className="mt-1 truncate text-xs font-bold text-slate-800">{value}</dd>
          </div>
        ))}
      </div>

      {/* Status + capability badges */}
      <div className="flex flex-wrap gap-2">
        <span className={`inline-block rounded-full px-2.5 py-0.5 text-[10px] font-bold ${STATUS_TONE[p.status]}`}>
          {STATUS_LABELS[p.status]}
        </span>
        {capabilities.data?.can_validate && (
          <span className="inline-block rounded-full bg-blue-50 px-2.5 py-0.5 text-[10px] font-bold text-blue-700">Puede validar</span>
        )}
        {capabilities.data?.can_create_version && (
          <span className="inline-block rounded-full bg-amber-50 px-2.5 py-0.5 text-[10px] font-bold text-amber-700">Puede crear versión</span>
        )}
        {capabilities.data?.can_activate && (
          <span className="inline-block rounded-full bg-emerald-50 px-2.5 py-0.5 text-[10px] font-bold text-emerald-700">Puede activar</span>
        )}
        {capabilities.data?.can_detect_conflicts && (
          <span className="inline-block rounded-full bg-red-50 px-2.5 py-0.5 text-[10px] font-bold text-red-700">Detectar conflictos</span>
        )}
        {capabilities.data?.can_manage_scopes && (
          <span className="inline-block rounded-full bg-purple-50 px-2.5 py-0.5 text-[10px] font-bold text-purple-700">Gestionar ámbitos</span>
        )}
        {capabilities.data?.can_manage_controls && (
          <span className="inline-block rounded-full bg-indigo-50 px-2.5 py-0.5 text-[10px] font-bold text-indigo-700">Gestionar controles</span>
        )}
        {capabilities.data?.can_manage_tolerances && (
          <span className="inline-block rounded-full bg-teal-50 px-2.5 py-0.5 text-[10px] font-bold text-teal-700">Gestionar tolerancias</span>
        )}
        {capabilities.data?.can_manage_sampling && (
          <span className="inline-block rounded-full bg-cyan-50 px-2.5 py-0.5 text-[10px] font-bold text-cyan-700">Gestionar muestreo</span>
        )}
        {capabilities.data?.can_manage_certificates && (
          <span className="inline-block rounded-full bg-pink-50 px-2.5 py-0.5 text-[10px] font-bold text-pink-700">Gestionar certificados</span>
        )}
      </div>

      {/* Tabs */}
      <nav className="flex gap-1 rounded-xl border border-[#EEF2F5] bg-slate-50 p-1 overflow-x-auto" aria-label="Secciones del plan">
        {DETAIL_TABS.map((t) => (
          <button
            key={t.key}
            type="button"
            onClick={() => setActiveTab(t.key)}
            className={`whitespace-nowrap min-h-9 px-3 text-[11px] font-semibold rounded-lg transition-colors ${
              activeTab === t.key
                ? 'bg-white text-[#1F4E6D] shadow-sm'
                : 'text-slate-600 hover:bg-white/60'
            }`}
            aria-current={activeTab === t.key ? 'page' : undefined}
          >
            {t.label}
          </button>
        ))}
      </nav>

      {/* Tab panels */}
      {activeTab === 'summary' && (
        <SummaryPanel plan={p} capabilities={capabilities.data ?? null} />
      )}
      {activeTab === 'versions' && (
        <VersionsPanel planId={p.plan_id} />
      )}
      {activeTab === 'scopes' && (
        <ScopesPanel planId={p.plan_id} />
      )}
      {activeTab === 'controls' && (
        <ControlsPanel planId={p.plan_id} />
      )}
      {activeTab === 'tolerances' && (
        <TolerancesPanel planId={p.plan_id} />
      )}
      {activeTab === 'sampling' && (
        <SamplingPanel planId={p.plan_id} />
      )}
      {activeTab === 'certificates' && (
        <CertificatesPanel planId={p.plan_id} />
      )}
      {activeTab === 'resolutions' && (
        <ResolutionsPanel planId={p.plan_id} />
      )}
      {activeTab === 'integrity' && (
        <IntegrityPanel planId={p.plan_id} />
      )}
      {activeTab === 'history' && (
        <HistoryPanel planId={p.plan_id} />
      )}
    </div>
  )
}

/* ── Panel components ─────────────────────────────────────────────────────── */

function SummaryPanel({ plan, capabilities }: { plan: QualityInspectionPlan; capabilities: QualityInspectionPlanCapabilities | null }) {
  return (
    <div className="space-y-4">
      <section className="rounded-xl border border-[#EEF2F5] bg-white p-4">
        <h2 className="text-xs font-bold text-slate-900 mb-3">Información del plan</h2>
        <dl className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {[
            ['Código', plan.code],
            ['Nombre', plan.name],
            ['Descripción', plan.description ?? '—'],
            ['Familia', plan.family],
            ['Estado', plan.status],
            ['Prioridad', String(plan.priority)],
            ['Creado por', plan.created_by.display_name],
            ['Fecha de creación', plan.created_at ? new Date(plan.created_at).toLocaleString('es-PE') : '—'],
            ['Última actualización', plan.updated_at ? new Date(plan.updated_at).toLocaleString('es-PE') : '—'],
          ].map(([label, value]) => (
            <div key={label} className="min-w-0 rounded-lg border border-[#EEF2F5] bg-slate-50 p-2.5">
              <dt className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">{label}</dt>
              <dd className="mt-0.5 truncate text-xs font-semibold text-slate-800">{value}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section className="rounded-xl border border-[#EEF2F5] bg-white p-4">
        <h2 className="text-xs font-bold text-slate-900 mb-3">Estadísticas</h2>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {[
            ['Productos', String(plan.product_count)],
            ['Categorías', String(plan.category_count)],
            ['Controles', String(plan.control_count)],
            ['Conflictos', String(plan.conflict_count)],
            ['Embalaje', plan.has_packaging ? 'Sí' : 'No'],
            ['Peso', plan.has_weight ? 'Sí' : 'No'],
            ['Temperatura', plan.has_temperature ? 'Sí' : 'No'],
            ['Certificados', plan.has_certificates ? 'Sí' : 'No'],
            ['Muestreo', plan.has_sampling ? 'Sí' : 'No'],
          ].map(([label, value]) => (
            <div key={label} className="rounded-lg border border-[#EEF2F5] bg-slate-50 p-2.5">
              <dt className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">{label}</dt>
              <dd className="mt-0.5 text-xs font-bold text-slate-800">{value}</dd>
            </div>
          ))}
        </div>
      </section>

      {capabilities && (
        <section className="rounded-xl border border-[#EEF2F5] bg-white p-4">
          <h2 className="text-xs font-bold text-slate-900 mb-3">Permisos</h2>
          <div className="flex flex-wrap gap-1.5">
            {(Object.entries(capabilities) as [string, boolean][]).filter(([k]) => k.startsWith('can_') && capabilities[k as keyof QualityInspectionPlanCapabilities]).map(([key]) => (
              <span key={key} className="inline-block rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold text-emerald-700">
                {key.replace('can_', '').replace(/_/g, ' ')}
              </span>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}

function VersionsPanel({ planId }: { planId: string }) {
  const versions = useQuery(
    ['quality-inspection-plans', 'versions', planId],
    `/logistics/quality-inspection-plans/${planId}/versions`,
  )

  if (versions.isLoading) return <LoadingSkeleton rows={3} />
  if (versions.isError) return <Alert variant="error">{getErrorMessage(versions.error)}</Alert>

  const items = (versions.data as { items?: unknown[] } | undefined)?.items ?? []
  if (items.length === 0) {
    return <EmptyState title="Sin versiones" description="Este plan aún no tiene versiones registradas." />
  }

  return (
    <div className="space-y-2">
      {(items as Record<string, unknown>[]).map((v) => (
        <div key={String(v.version_id)} className="flex items-center justify-between rounded-xl border border-[#EEF2F5] bg-white p-3">
          <div>
            <span className="font-mono text-xs font-bold text-[#1F4E6D]">v{String(v.version_number)}</span>
            <span className="ml-2 text-[11px] text-slate-500">{String(v.status)}</span>
          </div>
          <span className="text-[10px] text-slate-400">{String(v.created_at)}</span>
        </div>
      ))}
    </div>
  )
}

function ScopesPanel({ planId }: { planId: string }) {
  const scopes = useQuery(
    ['quality-inspection-plans', 'scopes', planId],
    `/logistics/quality-inspection-plans/${planId}/scopes`,
  )

  if (scopes.isLoading) return <LoadingSkeleton rows={3} />
  if (scopes.isError) return <Alert variant="error">{getErrorMessage(scopes.error)}</Alert>

  const items = (scopes.data as { items?: unknown[] } | undefined)?.items ?? []
  if (items.length === 0) {
    return <EmptyState title="Sin ámbitos" description="No hay productos o categorías asociados a este plan." />
  }

  return (
    <div className="space-y-2">
      {(items as Record<string, unknown>[]).map((s) => (
        <div key={String(s.scope_id)} className="flex items-center justify-between rounded-xl border border-[#EEF2F5] bg-white p-3">
          <div>
            <span className="text-xs font-semibold text-slate-800">{String(s.product_name ?? s.category_name ?? '—')}</span>
            <span className="ml-2 text-[10px] text-slate-500">{String(s.scope_type)} · {String(s.action)}</span>
          </div>
          <span className="text-[10px] text-slate-400">{String(s.specificity)}</span>
        </div>
      ))}
    </div>
  )
}

function ControlsPanel({ planId }: { planId: string }) {
  const controls = useQuery(
    ['quality-inspection-plans', 'controls', planId],
    `/logistics/quality-inspection-plans/${planId}/controls`,
  )

  if (controls.isLoading) return <LoadingSkeleton rows={3} />
  if (controls.isError) return <Alert variant="error">{getErrorMessage(controls.error)}</Alert>

  const items = (controls.data as { items?: unknown[] } | undefined)?.items ?? []
  if (items.length === 0) {
    return <EmptyState title="Sin controles" description="No hay controles definidos para este plan." />
  }

  return (
    <div className="space-y-2">
      {(items as Record<string, unknown>[]).map((c) => (
        <div key={String(c.control_id)} className="flex items-center justify-between rounded-xl border border-[#EEF2F5] bg-white p-3">
          <div>
            <span className="font-mono text-xs font-bold text-[#1F4E6D]">{String(c.code)}</span>
            <span className="ml-2 text-xs font-semibold text-slate-800">{String(c.name)}</span>
            <span className="ml-2 text-[10px] text-slate-500">{String(c.control_type)}</span>
          </div>
          <div className="flex gap-1.5">
            {Boolean(c.required) && <span className="text-[9px] font-bold text-red-600">REQ</span>}
            {Boolean(c.blocking_future) && <span className="text-[9px] font-bold text-amber-600">BLOCK</span>}
          </div>
        </div>
      ))}
    </div>
  )
}

function TolerancesPanel({ planId }: { planId: string }) {
  const tolerances = useQuery(
    ['quality-inspection-plans', 'tolerances', planId],
    `/logistics/quality-inspection-plans/${planId}/tolerances`,
  )

  if (tolerances.isLoading) return <LoadingSkeleton rows={3} />
  if (tolerances.isError) return <Alert variant="error">{getErrorMessage(tolerances.error)}</Alert>

  const items = (tolerances.data as { items?: unknown[] } | undefined)?.items ?? []
  if (items.length === 0) {
    return <EmptyState title="Sin tolerancias" description="No hay tolerancias definidas para este plan." />
  }

  return (
    <div className="space-y-2">
      {(items as Record<string, unknown>[]).map((t) => (
        <div key={String(t.tolerance_id)} className="flex items-center justify-between rounded-xl border border-[#EEF2F5] bg-white p-3">
          <div>
            <span className="font-mono text-xs font-bold text-[#1F4E6D]">{String(t.code)}</span>
            <span className="ml-2 text-xs font-semibold text-slate-800">{String(t.name)}</span>
            <span className="ml-2 text-[10px] text-slate-500">{String(t.tolerance_type)} · {String(t.dimension)}</span>
          </div>
          <span className="text-[10px] text-slate-400">Target: {String(t.target_value)}</span>
        </div>
      ))}
    </div>
  )
}

function SamplingPanel({ planId }: { planId: string }) {
  const sampling = useQuery(
    ['quality-inspection-plans', 'sampling', planId],
    `/logistics/quality-inspection-plans/${planId}/sampling`,
  )

  if (sampling.isLoading) return <LoadingSkeleton rows={2} />
  if (sampling.isError) return <Alert variant="error">{getErrorMessage(sampling.error)}</Alert>

  const items = (sampling.data as { items?: unknown[] } | undefined)?.items ?? []
  if (items.length === 0) {
    return <EmptyState title="Sin planes de muestreo" description="No hay planes de muestreo asociados." />
  }

  return (
    <div className="space-y-2">
      {(items as Record<string, unknown>[]).map((s) => (
        <div key={String(s.sampling_id)} className="flex items-center justify-between rounded-xl border border-[#EEF2F5] bg-white p-3">
          <div>
            <span className="font-mono text-xs font-bold text-[#1F4E6D]">{String(s.code)}</span>
            <span className="ml-2 text-xs font-semibold text-slate-800">{String(s.name)}</span>
            <span className="ml-2 text-[10px] text-slate-500">{String(s.sampling_type)} · {String(s.sample_unit)}</span>
          </div>
          <span className="text-[10px] text-slate-400">{String(s.selection_method)}</span>
        </div>
      ))}
    </div>
  )
}

function CertificatesPanel({ planId }: { planId: string }) {
  const certificates = useQuery(
    ['quality-inspection-plans', 'certificates', planId],
    `/logistics/quality-inspection-plans/${planId}/certificates`,
  )

  if (certificates.isLoading) return <LoadingSkeleton rows={2} />
  if (certificates.isError) return <Alert variant="error">{getErrorMessage(certificates.error)}</Alert>

  const items = (certificates.data as { items?: unknown[] } | undefined)?.items ?? []
  if (items.length === 0) {
    return <EmptyState title="Sin requisitos de certificado" description="No hay requisitos de certificados definidos." />
  }

  return (
    <div className="space-y-2">
      {(items as Record<string, unknown>[]).map((c) => (
        <div key={String(c.requirement_id)} className="flex items-center justify-between rounded-xl border border-[#EEF2F5] bg-white p-3">
          <div>
            <span className="font-mono text-xs font-bold text-[#1F4E6D]">{String(c.code)}</span>
            <span className="ml-2 text-xs font-semibold text-slate-800">{String(c.name)}</span>
          </div>
          <div className="flex gap-1.5">
            {Boolean(c.required) && <span className="text-[9px] font-bold text-red-600">REQ</span>}
            {Boolean(c.file_required) && <span className="text-[9px] font-bold text-amber-600">ARCHIVO</span>}
          </div>
        </div>
      ))}
    </div>
  )
}

function ResolutionsPanel({ planId }: { planId: string }) {
  const resolutions = useQuery(
    ['quality-inspection-plans', 'resolutions', planId],
    `/logistics/quality-inspection-plans/${planId}/resolutions`,
  )

  if (resolutions.isLoading) return <LoadingSkeleton rows={3} />
  if (resolutions.isError) return <Alert variant="error">{getErrorMessage(resolutions.error)}</Alert>

  const items = (resolutions.data as { items?: unknown[] } | undefined)?.items ?? []
  if (items.length === 0) {
    return <EmptyState title="Sin resoluciones" description="No hay resoluciones de conflictos registradas." />
  }

  return (
    <div className="space-y-2">
      {(items as Record<string, unknown>[]).map((r, i) => (
        <div key={String(r.product_id ?? i)} className="rounded-xl border border-[#EEF2F5] bg-white p-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-800">{String(r.product_name ?? '—')}</span>
            <span className="font-mono text-[10px] text-slate-500">{String(r.product_sku ?? '—')}</span>
          </div>
          {Boolean(r.resolved_plan_code) && (
            <p className="mt-1 text-[10px] text-slate-500">Resuelto por: {String(r.resolved_plan_code)}</p>
          )}
          {Boolean(r.explanation) && (
            <p className="mt-1 text-[10px] text-slate-400">{String(r.explanation)}</p>
          )}
        </div>
      ))}
    </div>
  )
}

function IntegrityPanel({ planId }: { planId: string }) {
  const integrity = useQuery(
    ['quality-inspection-plans', 'integrity', planId],
    `/logistics/quality-inspection-plans/${planId}/integrity`,
  )

  if (integrity.isLoading) return <LoadingSkeleton rows={2} />
  if (integrity.isError) return <Alert variant="error">{getErrorMessage(integrity.error)}</Alert>

  const data = integrity.data as Record<string, unknown> | undefined
  if (!data) {
    return <EmptyState title="Sin datos de integridad" description="No se encontraron datos de integridad." />
  }

  return (
    <section className="rounded-xl border border-[#EEF2F5] bg-white p-4">
      <h2 className="text-xs font-bold text-slate-900 mb-3">Integridad de la versión</h2>
      <dl className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {[
          ['Algoritmo', String(data.algorithm ?? '—')],
          ['Estado', String(data.status ?? '—')],
          ['Hash versión', String(data.version_hash ?? '—')],
          ['Hash ámbitos', String(data.scopes_hash ?? '—')],
          ['Hash controles', String(data.controls_hash ?? '—')],
          ['Hash tolerancias', String(data.tolerances_hash ?? '—')],
          ['Hash muestreo', String(data.sampling_hash ?? '—')],
          ['Hash certificados', String(data.certificates_hash ?? '—')],
          ['Última verificación', String(data.last_verified_at ?? '—')],
        ].map(([label, value]) => (
          <div key={label} className="min-w-0 rounded-lg border border-[#EEF2F5] bg-slate-50 p-2.5">
            <dt className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">{label}</dt>
            <dd className="mt-0.5 truncate text-xs font-mono font-semibold text-slate-800">{value}</dd>
          </div>
        ))}
      </dl>
    </section>
  )
}

function HistoryPanel({ planId }: { planId: string }) {
  const history = useQuery(
    ['quality-inspection-plans', 'history', planId],
    `/logistics/quality-inspection-plans/${planId}/history`,
  )

  if (history.isLoading) return <LoadingSkeleton rows={4} />
  if (history.isError) return <Alert variant="error">{getErrorMessage(history.error)}</Alert>

  const items = (history.data as { items?: unknown[] } | undefined)?.items ?? []
  if (items.length === 0) {
    return <EmptyState title="Sin historial" description="No hay eventos registrados para este plan." />
  }

  return (
    <div className="space-y-2">
      {(items as Record<string, unknown>[]).map((e) => (
        <div key={String(e.event_id)} className="flex items-start gap-3 rounded-xl border border-[#EEF2F5] bg-white p-3">
          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-slate-100 text-[10px] font-bold text-slate-600">
            {String(e.event_type).slice(0, 2)}
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-slate-800">{String(e.action)}</span>
              <span className="text-[10px] text-slate-400">{String(e.timestamp)}</span>
            </div>
            <p className="mt-0.5 text-[10px] text-slate-500">
              por {(e.actor as { display_name?: string } | undefined)?.display_name ?? '—'}
            </p>
            {Boolean(e.reason) && <p className="mt-0.5 text-[10px] text-slate-400">{String(e.reason)}</p>}
          </div>
        </div>
      ))}
    </div>
  )
}
