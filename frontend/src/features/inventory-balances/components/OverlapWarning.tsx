import { Alert } from '../../../components/common/Alert'

export function OverlapWarning() {
  return (
    <Alert variant="warning">
      <strong>Advertencia de métricas superpuestas:</strong> Las métricas de estado no siempre
      son aditivas. Una cantidad puede estar físicamente presente y al mismo tiempo encontrarse
      bloqueada, en cuarentena, dañada o vencida. No asuma que Físico es la suma de todas las
      demás métricas a menos que el backend lo valide explícitamente.
    </Alert>
  )
}
