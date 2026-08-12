import { QualityPlanVersionComparisonPage as ComparisonComponent } from '../components/QualityPlanVersionComparisonPage'
import { useParams, useSearchParams } from 'react-router-dom'

export function QualityPlanVersionComparisonPage() {
  const { planId } = useParams<{ planId: string }>()
  const [searchParams] = useSearchParams()
  const versionA = searchParams.get('versionA') ?? ''
  const versionB = searchParams.get('versionB') ?? ''

  if (!planId || !versionA || !versionB) {
    return <div className="p-6 text-sm text-red-500">Parámetros requeridos: planId, versionA, versionB</div>
  }

  return <ComparisonComponent planId={planId} versionA={versionA} versionB={versionB} />
}
