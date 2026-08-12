import { QualityPlanPreviewPage as PreviewComponent } from '../components/QualityPlanPreviewPage'
import { useParams } from 'react-router-dom'

export function QualityPlanPreviewPage() {
  const { planId } = useParams<{ planId: string }>()
  if (!planId) return <div className="p-6 text-sm text-red-500">planId requerido</div>
  return <PreviewComponent planId={planId} />
}
