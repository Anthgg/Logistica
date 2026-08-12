import { useNavigate, useParams } from 'react-router-dom'
import { PageHeader } from '../../../components/common/PageHeader'
import { Button } from '../../../components/common/Button'
import { Alert } from '../../../components/common/Alert'
import { LogisticsIcon } from '../../../components/common/LogisticsIcon'
import { PutawayPhaseNav } from '../components/PutawayPhaseNav'

export function PutawayExceptionDetailPage() {
  const navigate = useNavigate()
  const { exceptionId = '' } = useParams()
  return <div className="space-y-6 pb-10"><PageHeader eyebrow="Fase 043 · Excepción" title="Expediente de excepción" description="Las excepciones se consultan dentro de su tarea de ubicación." actions={<Button variant="secondary" onClick={() => navigate('/logistics/putaway/exceptions')}>Volver</Button>} /><PutawayPhaseNav /><section className="grid gap-6 lg:grid-cols-[1fr_0.65fr]"><div className="rounded-3xl border border-orange-200 bg-orange-50 p-7 shadow-sm md:p-10"><span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-orange-600 text-white"><LogisticsIcon name="alert" size={25} aria-hidden="true" /></span><p className="mt-6 text-xs font-semibold uppercase tracking-[0.16em] text-orange-700">Ruta heredada protegida</p><h2 className="mt-2 text-2xl font-bold text-orange-950">Abre la tarea que originó esta excepción</h2><p className="mt-3 max-w-xl text-sm leading-6 text-orange-900">El backend no publica un GET global por exception_id. Para evitar una solicitud 404 o una mutación accidental, selecciona la tarea afectada desde la bandeja.</p><Button className="mt-7" onClick={() => navigate('/logistics/putaway/exceptions')}>Ir a tareas afectadas</Button></div><aside className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"><h2 className="font-bold text-slate-950">Referencia recibida</h2><p className="mt-3 break-all font-mono text-xs text-slate-500">{exceptionId || 'Sin identificador'}</p><Alert variant="info">Resolver sigue disponible desde el detalle de tarea, donde el backend conoce el vínculo y valida permisos.</Alert></aside></section></div>
}
