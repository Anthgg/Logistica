import { useParams } from 'react-router-dom'
import { QualityPlanVersionWizard } from '../components/QualityPlanVersionWizard'

export function QualityPlanVersionWizardPage() {
  const { planId, versionId } = useParams<{ planId: string; versionId: string }>()

  if (!planId) return <div className="p-6 text-sm text-red-500">planId requerido</div>

  return (
    <QualityPlanVersionWizard
      planId={planId}
      versionId={versionId}
      onComplete={() => window.history.back()}
      onCancel={() => window.history.back()}
    />
  )
}
