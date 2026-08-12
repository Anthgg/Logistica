import { useState } from 'react'
import type { FormEvent } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../../components/ui/select'
import { useSensitiveOperationGuard } from '../../continuous-auth/hooks/useSensitiveOperationGuard'
import { LOGISTICS_PERMISSIONS } from '../../logistics-permissions/logistics-permissions-map'
import { useLogisticsPermissions } from '../../logistics-permissions/hooks/useLogisticsPermissions'
import { procurementApprovalsApi } from '../api/procurementApprovalsApi'

function digits(value: string): string {
  return value.replace(/\D/g, '')
}

export function ApprovalPolicyVersionPage() {
  const { versionId } = useParams<{ versionId: string }>()
  const navigate = useNavigate()
  const authorization = useLogisticsPermissions()
  const { guardSensitiveAction, requireReverification } =
    useSensitiveOperationGuard()
  const [conditionField, setConditionField] = useState('amount')
  const [conditionOperator, setConditionOperator] = useState('GTE')
  const [conditionValue, setConditionValue] = useState('')
  const [conditionGroup, setConditionGroup] = useState('ALL')
  const [stepCode, setStepCode] = useState('')
  const [stepName, setStepName] = useState('')
  const [stepOrder, setStepOrder] = useState('1')
  const [executionMode, setExecutionMode] = useState('SEQUENTIAL')
  const [completionMode, setCompletionMode] = useState('ALL')
  const [minimumApprovals, setMinimumApprovals] = useState('1')
  const [requiredApprovals, setRequiredApprovals] = useState('1')
  const [approverSource, setApproverSource] =
    useState('COST_CENTER_OWNER')
  const [approverReference, setApproverReference] = useState('')
  const [distinctFromCreator, setDistinctFromCreator] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const canUpdate = authorization.hasPermission(
    LOGISTICS_PERMISSIONS.procurementApprovals.policiesUpdate,
  )
  const canActivate = authorization.hasPermission(
    LOGISTICS_PERMISSIONS.procurementApprovals.policiesActivate,
  )

  const addCondition = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!versionId || !canUpdate || !conditionValue.trim()) return
    setIsSubmitting('condition')
    setMessage(null)
    setErrorMessage(null)
    try {
      await procurementApprovalsApi.addCondition(versionId, {
        condition_group: conditionGroup,
        field_code: conditionField,
        operator: conditionOperator,
        value_data: ['IN', 'NOT_IN'].includes(conditionOperator)
          ? {
              values: conditionValue
                .split(',')
                .map((value) => value.trim())
                .filter(Boolean),
            }
          : { value: conditionValue.trim() },
        order_index: 1,
      })
      setConditionValue('')
      setMessage('Condición agregada por el backend.')
    } catch (error: unknown) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : 'No se pudo agregar la condición.',
      )
    } finally {
      setIsSubmitting(null)
    }
  }

  const addStep = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!versionId || !canUpdate || !stepCode.trim() || !stepName.trim()) {
      return
    }
    setIsSubmitting('step')
    setMessage(null)
    setErrorMessage(null)
    try {
      await procurementApprovalsApi.addStep(versionId, {
        step_code: stepCode.trim(),
        name: stepName.trim(),
        order_index: Number.parseInt(stepOrder, 10) || 1,
        execution_mode: executionMode,
        completion_mode: completionMode,
        minimum_approvals:
          Number.parseInt(minimumApprovals, 10) || 1,
        required_approvals:
          Number.parseInt(requiredApprovals, 10) || 1,
        approver_source_type: approverSource,
        approver_source_config: approverReference.trim()
          ? { reference_id: approverReference.trim() }
          : {},
        step_up_level: 'HIGH',
        distinct_from_creator: distinctFromCreator,
      })
      setStepCode('')
      setStepName('')
      setApproverReference('')
      setMessage('Paso agregado por el backend.')
    } catch (error: unknown) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : 'No se pudo agregar el paso.',
      )
    } finally {
      setIsSubmitting(null)
    }
  }

  const activate = async () => {
    if (!versionId || !authorization.userId || !canActivate) return
    setIsSubmitting('activate')
    setMessage(null)
    setErrorMessage(null)
    try {
      const executed = await guardSensitiveAction(async () => {
        await procurementApprovalsApi.activateVersion(
          versionId,
          authorization.userId!,
        )
      })
      if (!executed) {
        setErrorMessage('La activación requiere reverificación continua.')
        return
      }
      setMessage('Versión activada por el backend.')
    } catch (error: unknown) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : 'No se pudo activar la versión.',
      )
    } finally {
      setIsSubmitting(null)
    }
  }

  if (!versionId) {
    return (
      <div role="alert" className="text-sm text-rose-700">
        Falta el identificador de versión.
      </div>
    )
  }

  return (
    <section className="space-y-4" aria-labelledby="policy-version-title">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <button
            type="button"
            onClick={() =>
              navigate('/logistics/purchasing/approval-policies')
            }
            className="min-h-10 text-xs font-semibold text-[#1F4E6D] hover:underline"
          >
            ← Volver a políticas
          </button>
          <h1
            id="policy-version-title"
            className="mt-1 text-xl font-bold text-slate-950"
          >
            Configurar versión de política
          </h1>
          <p className="mt-1 font-mono text-xs text-slate-500">
            {versionId}
          </p>
        </div>
        {canActivate && (
          <button
            type="button"
            disabled={
              isSubmitting !== null ||
              requireReverification ||
              !authorization.userId
            }
            onClick={() => void activate()}
            className="min-h-11 rounded-lg bg-[#1F4E6D] px-4 text-sm font-semibold text-white disabled:opacity-50"
          >
            {isSubmitting === 'activate'
              ? 'Activando…'
              : 'Activar versión'}
          </button>
        )}
      </header>

      <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
        El backend no publica lectura, validación, simulación ni detección de
        conflictos de la versión. Los formularios siguientes solo agregan
        condiciones y pasos; no reconstruyen una cadena local.
      </div>

      {message && (
        <div
          role="status"
          className="rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800"
        >
          {message}
        </div>
      )}
      {errorMessage && (
        <div
          role="alert"
          className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-800"
        >
          {errorMessage}
        </div>
      )}

      {!canUpdate ? (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">
          No tienes la capability para modificar versiones.
        </div>
      ) : (
        <div className="grid gap-4 xl:grid-cols-2">
          <form
            onSubmit={(event) => void addCondition(event)}
            className="space-y-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
          >
            <div>
              <h2 className="text-base font-bold text-slate-900">
                Agregar condición
              </h2>
              <p className="mt-1 text-xs text-slate-500">
                El valor se envía como string; el backend interpreta y valida.
              </p>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <label>
                <span className="mb-1 block text-xs font-semibold text-slate-700">
                  Grupo
                </span>
                <Select
                  value={conditionGroup}
                  onValueChange={setConditionGroup}
                >
                  <SelectTrigger className="min-h-11 w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ALL">Todas (AND)</SelectItem>
                    <SelectItem value="ANY">Cualquiera (OR)</SelectItem>
                  </SelectContent>
                </Select>
              </label>
              <label>
                <span className="mb-1 block text-xs font-semibold text-slate-700">
                  Campo
                </span>
                <Select
                  value={conditionField}
                  onValueChange={setConditionField}
                >
                  <SelectTrigger className="min-h-11 w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="amount">Monto</SelectItem>
                    <SelectItem value="currency_code">Moneda</SelectItem>
                    <SelectItem value="cost_center_id">
                      Centro de costo
                    </SelectItem>
                    <SelectItem value="category_id">Categoría</SelectItem>
                    <SelectItem value="branch_id">Sede</SelectItem>
                  </SelectContent>
                </Select>
              </label>
              <label>
                <span className="mb-1 block text-xs font-semibold text-slate-700">
                  Operador
                </span>
                <Select
                  value={conditionOperator}
                  onValueChange={setConditionOperator}
                >
                  <SelectTrigger className="min-h-11 w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="EQ">Igual</SelectItem>
                    <SelectItem value="NEQ">Distinto</SelectItem>
                    <SelectItem value="GTE">Mayor o igual</SelectItem>
                    <SelectItem value="LTE">Menor o igual</SelectItem>
                    <SelectItem value="IN">En lista</SelectItem>
                    <SelectItem value="NOT_IN">
                      Fuera de lista
                    </SelectItem>
                  </SelectContent>
                </Select>
              </label>
              <label>
                <span className="mb-1 block text-xs font-semibold text-slate-700">
                  Valor
                </span>
                <input
                  value={conditionValue}
                  onChange={(event) => setConditionValue(event.target.value)}
                  placeholder={
                    ['IN', 'NOT_IN'].includes(conditionOperator)
                      ? 'Valores separados por coma'
                      : 'Valor'
                  }
                  className="min-h-11 w-full rounded-lg border border-slate-300 px-3 text-sm outline-none focus:border-[#1F4E6D] focus:ring-2 focus:ring-[#1F4E6D]/20"
                />
              </label>
            </div>
            <button
              type="submit"
              disabled={
                !conditionValue.trim() || isSubmitting !== null
              }
              className="min-h-11 rounded-lg bg-[#1F4E6D] px-4 text-sm font-semibold text-white disabled:opacity-50"
            >
              {isSubmitting === 'condition'
                ? 'Agregando…'
                : 'Agregar condición'}
            </button>
          </form>

          <form
            onSubmit={(event) => void addStep(event)}
            className="space-y-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
          >
            <div>
              <h2 className="text-base font-bold text-slate-900">
                Agregar paso
              </h2>
              <p className="mt-1 text-xs text-slate-500">
                No se aceptan correos como autoridad; usa códigos o IDs del
                origen de aprobadores.
              </p>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <label>
                <span className="mb-1 block text-xs font-semibold text-slate-700">
                  Código
                </span>
                <input
                  value={stepCode}
                  onChange={(event) => setStepCode(event.target.value)}
                  className="min-h-11 w-full rounded-lg border border-slate-300 px-3 text-sm"
                />
              </label>
              <label>
                <span className="mb-1 block text-xs font-semibold text-slate-700">
                  Nombre
                </span>
                <input
                  value={stepName}
                  onChange={(event) => setStepName(event.target.value)}
                  className="min-h-11 w-full rounded-lg border border-slate-300 px-3 text-sm"
                />
              </label>
              <label>
                <span className="mb-1 block text-xs font-semibold text-slate-700">
                  Orden
                </span>
                <input
                  inputMode="numeric"
                  value={stepOrder}
                  onChange={(event) => setStepOrder(digits(event.target.value))}
                  className="min-h-11 w-full rounded-lg border border-slate-300 px-3 font-mono text-sm"
                />
              </label>
              <label>
                <span className="mb-1 block text-xs font-semibold text-slate-700">
                  Ejecución
                </span>
                <Select
                  value={executionMode}
                  onValueChange={setExecutionMode}
                >
                  <SelectTrigger className="min-h-11 w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="SEQUENTIAL">Secuencial</SelectItem>
                    <SelectItem value="PARALLEL">Paralela</SelectItem>
                  </SelectContent>
                </Select>
              </label>
              <label>
                <span className="mb-1 block text-xs font-semibold text-slate-700">
                  Finalización
                </span>
                <Select
                  value={completionMode}
                  onValueChange={setCompletionMode}
                >
                  <SelectTrigger className="min-h-11 w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ALL">Todas</SelectItem>
                    <SelectItem value="QUORUM">Quórum</SelectItem>
                    <SelectItem value="ANY">Cualquiera</SelectItem>
                  </SelectContent>
                </Select>
              </label>
              <label>
                <span className="mb-1 block text-xs font-semibold text-slate-700">
                  Fuente de aprobador
                </span>
                <Select
                  value={approverSource}
                  onValueChange={setApproverSource}
                >
                  <SelectTrigger className="min-h-11 w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="COST_CENTER_OWNER">
                      Responsable de centro
                    </SelectItem>
                    <SelectItem value="REQUESTER_MANAGER">
                      Responsable del solicitante
                    </SelectItem>
                    <SelectItem value="ROLE">Rol autorizado</SelectItem>
                    <SelectItem value="USER">Usuario por ID</SelectItem>
                  </SelectContent>
                </Select>
              </label>
              <label>
                <span className="mb-1 block text-xs font-semibold text-slate-700">
                  Aprobaciones mínimas
                </span>
                <input
                  inputMode="numeric"
                  value={minimumApprovals}
                  onChange={(event) =>
                    setMinimumApprovals(digits(event.target.value))
                  }
                  className="min-h-11 w-full rounded-lg border border-slate-300 px-3 font-mono text-sm"
                />
              </label>
              <label>
                <span className="mb-1 block text-xs font-semibold text-slate-700">
                  Aprobaciones requeridas
                </span>
                <input
                  inputMode="numeric"
                  value={requiredApprovals}
                  onChange={(event) =>
                    setRequiredApprovals(digits(event.target.value))
                  }
                  className="min-h-11 w-full rounded-lg border border-slate-300 px-3 font-mono text-sm"
                />
              </label>
              <label className="sm:col-span-2">
                <span className="mb-1 block text-xs font-semibold text-slate-700">
                  ID o código de referencia del origen
                </span>
                <input
                  value={approverReference}
                  onChange={(event) =>
                    setApproverReference(event.target.value)
                  }
                  className="min-h-11 w-full rounded-lg border border-slate-300 px-3 text-sm"
                />
              </label>
              <label className="flex min-h-11 items-center gap-2 rounded-lg border border-slate-200 px-3 sm:col-span-2">
                <input
                  type="checkbox"
                  checked={distinctFromCreator}
                  onChange={(event) =>
                    setDistinctFromCreator(event.target.checked)
                  }
                  className="h-4 w-4 rounded border-slate-300 text-[#1F4E6D]"
                />
                <span className="text-sm font-medium text-slate-700">
                  Aprobador distinto del creador (SoD)
                </span>
              </label>
            </div>
            <button
              type="submit"
              disabled={
                !stepCode.trim() ||
                !stepName.trim() ||
                isSubmitting !== null
              }
              className="min-h-11 rounded-lg bg-[#1F4E6D] px-4 text-sm font-semibold text-white disabled:opacity-50"
            >
              {isSubmitting === 'step' ? 'Agregando…' : 'Agregar paso'}
            </button>
          </form>
        </div>
      )}
    </section>
  )
}
