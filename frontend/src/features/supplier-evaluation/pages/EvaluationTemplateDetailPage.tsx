import { useEffect, useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../../components/ui/select'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { supplierEvaluationTemplatesApi } from '../api/supplierEvaluationTemplatesApi'
import type {
  EvaluationCriterionDefinition,
  SupplierEvaluationTemplate,
  SupplierEvaluationTemplateVersion,
} from '../types/evaluation'
import {
  ErrorState,
  StatusPill,
  TableSkeleton,
  EmptyState,
} from '../components/ui/SharedState'
import { EvaluationTemplateVersionsPanel } from '../components/EvaluationTemplateVersionsPanel'
import { EvaluationCriteriaEditor } from '../components/EvaluationCriteriaEditor'
import { EvaluationWeightsEditor } from '../components/EvaluationWeightsEditor'

type Tab = 'versions' | 'criteria' | 'weights'

export function EvaluationTemplateDetailPage() {
  const { templateId } = useParams<{ templateId: string }>()
  const perms = useLogisticsPermissions()
  const canManage = perms.hasPermission(
    LOGISTICS_PERMISSIONS.supplierEvaluations.manageTemplates,
  )

  const [template, setTemplate] = useState<SupplierEvaluationTemplate | null>(null)
  const [versions, setVersions] = useState<SupplierEvaluationTemplateVersion[]>([])
  const [activeVersionId, setActiveVersionId] = useState<string | null>(null)
  const [criteria, setCriteria] = useState<EvaluationCriterionDefinition[]>([])
  const [tab, setTab] = useState<Tab>('versions')
  const [isLoading, setIsLoading] = useState(true)
  const [isError, setIsError] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')

  const activeVersion = useMemo(
    () => versions.find((v) => v.id === activeVersionId) ?? null,
    [versions, activeVersionId],
  )

  const load = async () => {
    if (!templateId) return
    setIsLoading(true)
    setIsError(false)
    try {
      const tpl = await supplierEvaluationTemplatesApi.get(templateId)
      setTemplate(tpl)
      const vs = await supplierEvaluationTemplatesApi.listVersions(templateId)
      setVersions(vs)
      const active = vs.find((v) => v.status === 'ACTIVE') ?? vs[0] ?? null
      setActiveVersionId(active?.id ?? null)
      if (active) {
        const cr = await supplierEvaluationTemplatesApi.listCriteria(templateId, active.id)
        setCriteria(cr)
      }
    } catch (err: unknown) {
      setIsError(true)
      setErrorMessage(
        err instanceof Error ? err.message : 'No se pudo cargar la plantilla.',
      )
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    void load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [templateId])

  const loadCriteriaFor = async (versionId: string) => {
    if (!templateId) return
    try {
      const cr = await supplierEvaluationTemplatesApi.listCriteria(templateId, versionId)
      setCriteria(cr)
    } catch {
      setCriteria([])
    }
  }

  if (isLoading) return <TableSkeleton />
  if (isError)
    return <ErrorState message={errorMessage} onRetry={() => void load()} />
  if (!template)
    return <EmptyState title="Plantilla no encontrada" />

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-lg font-bold text-slate-900">
            {template.code} — {template.name}
          </h1>
          <p className="text-xs text-slate-500">
            Scope: {template.scope} · {template.criteria_count} criterios
          </p>
        </div>
        <StatusPill tone="success">{template.status}</StatusPill>
      </div>

      {/* Selector de versión */}
      <div className="flex flex-wrap items-end gap-3 rounded-xl border border-slate-200 bg-white p-3 shadow-xs">
        <div className="flex-1">
          <label htmlFor="version-select" className="mb-1 block text-xs font-bold text-slate-700">
            Versión
          </label>
          <Select
            value={activeVersionId ?? undefined}
            onValueChange={async (v) => {
              setActiveVersionId(v)
              await loadCriteriaFor(v)
            }}
          >
            <SelectTrigger id="version-select">
              <SelectValue placeholder="Selecciona una versión" />
            </SelectTrigger>
            <SelectContent>
              {versions.map((v) => (
                <SelectItem key={v.id} value={v.id}>
                  {v.version} — {v.status}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        {activeVersion && (
          <div className="text-xs text-slate-500">
            Motor: <span className="font-mono">{activeVersion.engine}</span> · Política de empate: {activeVersion.tie_policy}
          </div>
        )}
      </div>

      {/* Tabs internos */}
      <div className="flex gap-1 rounded-xl border border-slate-200 bg-slate-50/60 p-1">
        {(['versions', 'criteria', 'weights'] as Tab[]).map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            className={
              tab === t
                ? 'rounded-lg bg-white px-3 py-1.5 text-xs font-semibold text-[#1F4E6D] shadow-xs'
                : 'rounded-lg px-3 py-1.5 text-xs font-medium text-slate-500 hover:text-slate-700'
            }
          >
            {t === 'versions' ? 'Versiones' : t === 'criteria' ? 'Criterios' : 'Pesos'}
          </button>
        ))}
      </div>

      {!activeVersion && tab !== 'versions' && (
        <EmptyState title="Selecciona o crea una versión para editar criterios y pesos" />
      )}

      {tab === 'versions' && (
        <EvaluationTemplateVersionsPanel
          templateId={template.id}
          versions={versions}
          canManage={canManage}
          onChanged={load}
        />
      )}

      {tab === 'criteria' && activeVersion && (
        <EvaluationCriteriaEditor
          templateId={template.id}
          version={activeVersion}
          criteria={criteria}
          canManage={canManage}
          onChanged={() => void loadCriteriaFor(activeVersion.id)}
        />
      )}

      {tab === 'weights' && activeVersion && (
        <EvaluationWeightsEditor
          templateId={template.id}
          version={activeVersion}
          criteria={criteria}
          canManage={canManage}
        />
      )}
    </div>
  )
}

// (sin re-exports)