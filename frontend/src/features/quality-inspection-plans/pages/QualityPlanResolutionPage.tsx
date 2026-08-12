import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { QualityPlanApplicabilityPanel } from '../components/QualityPlanApplicabilityPanel'
import { QualityPlanPreviewPage as PreviewComponent } from '../components/QualityPlanPreviewPage'
import { ReceptionDifferenceQualityPlanPreviewPanel } from '../components/ReceptionDifferenceQualityPlanPreviewPanel'

type Tab = 'producto' | 'categoria' | 'preview' | 'diferencia'

export function QualityPlanResolutionPage() {
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<Tab>('producto')
  const [productId, setProductId] = useState('')
  const [categoryId, setCategoryId] = useState('')
  const [caseId, setCaseId] = useState('')

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-sm font-bold text-slate-800">Resolución de planes de calidad</h1>
        <button onClick={() => navigate(-1)} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-600">
          Volver
        </button>
      </div>

      <div className="flex gap-1 border-b border-slate-200">
        {(['producto', 'categoria', 'preview', 'diferencia'] as const).map((tab) => (
          <button key={tab} onClick={() => setActiveTab(tab)} className={`px-3 py-2 text-xs font-semibold capitalize transition-colors ${activeTab === tab ? 'border-b-2 border-[#1F4E6D] text-[#1F4E6D]' : 'text-slate-500 hover:text-slate-700'}`}>
            {tab}
          </button>
        ))}
      </div>

      {activeTab === 'producto' && (
        <div className="space-y-4">
          <div>
            <label className="text-xs text-slate-600">Product ID</label>
            <input value={productId} onChange={(e) => setProductId(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-xs" placeholder="Ingrese product_id" />
          </div>
          {productId && <QualityPlanApplicabilityPanel productId={productId} />}
        </div>
      )}

      {activeTab === 'preview' && (
        <div className="space-y-4">
          <div>
            <label className="text-xs text-slate-600">Plan ID</label>
            <input value={categoryId} onChange={(e) => setCategoryId(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-xs" placeholder="Ingrese plan_id" />
          </div>
          {categoryId && <PreviewComponent planId={categoryId} />}
        </div>
      )}

      {activeTab === 'diferencia' && (
        <div className="space-y-4">
          <div>
            <label className="text-xs text-slate-600">Case ID (recepción)</label>
            <input value={caseId} onChange={(e) => setCaseId(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-xs" placeholder="Ingrese case_id" />
          </div>
          {caseId && <ReceptionDifferenceQualityPlanPreviewPanel caseId={caseId} />}
        </div>
      )}
    </div>
  )
}
