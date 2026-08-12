import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '../../inbound-docks/hooks/useQuery'
import { QualityPlanScopesEditor } from '../components/QualityPlanScopesEditor'
import { QualityControlsEditor } from '../components/QualityControlsEditor'
import { QualityPlanValidationPanel } from '../components/QualityPlanValidationPanel'
import { QualityPlanConflictsPanel } from '../components/QualityPlanConflictsPanel'
import { QualityPlanIntegrityPanel } from '../components/QualityPlanIntegrityPanel'
import { QualityPlanHistoryTimeline } from '../components/QualityPlanHistoryTimeline'
import type { QualityInspectionPlanVersion, QualityControlDefinition, QualityPlanScope, QualityInspectionPlanCapabilities } from '../types/quality-inspection-plans'

const TABS = ['Resumen', 'Controles', 'Scopes', 'Validación', 'Conflictos', 'Integridad', 'Historial'] as const

export function QualityPlanVersionDetailPage() {
  const { versionId } = useParams<{ versionId: string }>()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<string>('Resumen')

  const { data: version, isLoading } = useQuery<QualityInspectionPlanVersion>(
    ['quality-plan-version', versionId],
    `/logistics/quality-plan-versions/${versionId}`,
    undefined,
    { enabled: !!versionId },
  )

  const { data: controls } = useQuery<QualityControlDefinition[]>(
    ['quality-controls', versionId],
    `/logistics/quality-controls?version_id=${versionId}`,
    undefined,
    { enabled: !!versionId && activeTab === 'Controles' },
  )

  const { data: scopes } = useQuery<QualityPlanScope[]>(
    ['quality-scopes', versionId],
    `/logistics/quality-plan-scopes?version_id=${versionId}`,
    undefined,
    { enabled: !!versionId && activeTab === 'Scopes' },
  )

  if (isLoading) return <div className="p-6 text-sm text-slate-500">Cargando versión...</div>
  if (!version) return <div className="p-6 text-sm text-red-500">Versión no encontrada</div>

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-sm font-bold text-slate-800">
            Versión {version.version_number} — {version.status}
          </h1>
          <p className="text-xs text-slate-500">
            Vigencia: {version.valid_from ?? '—'} a {version.valid_until ?? '—'} | Prioridad: {version.priority}
          </p>
        </div>
        <button onClick={() => navigate(-1)} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-600">
          Volver
        </button>
      </div>

      <div className="flex gap-1 border-b border-slate-200">
        {TABS.map((tab) => (
          <button key={tab} onClick={() => setActiveTab(tab)} className={`px-3 py-2 text-xs font-semibold transition-colors ${activeTab === tab ? 'border-b-2 border-[#1F4E6D] text-[#1F4E6D]' : 'text-slate-500 hover:text-slate-700'}`}>
            {tab}
          </button>
        ))}
      </div>

      {activeTab === 'Controles' && (
        <QualityControlsEditor versionId={versionId!} controls={controls || []} capabilities={{ can_manage_controls: true } as QualityInspectionPlanCapabilities} onRefresh={() => {}} />
      )}
      {activeTab === 'Scopes' && (
        <QualityPlanScopesEditor versionId={versionId!} scopes={scopes || []} capabilities={{ can_manage_scopes: true } as QualityInspectionPlanCapabilities} onRefresh={() => {}} />
      )}
      {activeTab === 'Validación' && (
        <QualityPlanValidationPanel validation={null} onValidate={() => {}} />
      )}
      {activeTab === 'Conflictos' && (
        <QualityPlanConflictsPanel conflicts={[]} />
      )}
      {activeTab === 'Integridad' && (
        <QualityPlanIntegrityPanel integrity={null} />
      )}
      {activeTab === 'Historial' && (
        <QualityPlanHistoryTimeline events={[]} />
      )}
    </div>
  )
}
