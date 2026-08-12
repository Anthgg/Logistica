import { useState } from 'react'
import type { FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
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

export function ApprovalPolicyCreatePage() {
  const navigate = useNavigate()
  const authorization = useLogisticsPermissions()
  const { guardSensitiveAction, requireReverification } =
    useSensitiveOperationGuard()
  const [code, setCode] = useState('')
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [subjectType, setSubjectType] = useState('PURCHASE_ORDER')
  const [priority, setPriority] = useState('100')
  const [effectiveScope, setEffectiveScope] = useState('ORGANIZATION')
  const [isFallback, setIsFallback] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const canCreate = authorization.hasPermission(
    LOGISTICS_PERMISSIONS.procurementApprovals.policiesCreate,
  )
  const parsedPriority = Number.parseInt(priority, 10)
  const valid =
    code.trim().length >= 2 &&
    name.trim().length >= 2 &&
    Number.isInteger(parsedPriority) &&
    parsedPriority >= 1 &&
    parsedPriority <= 9999

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const organizationId = authorization.context.organization_id
    const userId = authorization.userId
    if (!valid || !organizationId || !userId || !canCreate) return

    setIsSubmitting(true)
    setErrorMessage(null)
    try {
      let policyId: string | null = null
      const executed = await guardSensitiveAction(async () => {
        const policy = await procurementApprovalsApi.createPolicy(userId, {
          organization_id: organizationId,
          code: code.trim(),
          name: name.trim(),
          description: description.trim() || null,
          subject_type: subjectType,
          priority: parsedPriority,
          effective_scope: effectiveScope,
          is_fallback: isFallback,
        })
        policyId = policy.id
      })
      if (!executed) {
        setErrorMessage(
          'La creación requiere reverificación continua.',
        )
        return
      }
      if (policyId) {
        navigate(
          `/logistics/purchasing/approval-policies/${policyId}`,
          { replace: true },
        )
      }
    } catch (error: unknown) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : 'No se pudo crear la política.',
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  if (!canCreate) {
    return (
      <div
        role="alert"
        className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800"
      >
        No tienes la capability para crear políticas de aprobación.
      </div>
    )
  }

  return (
    <section className="space-y-4" aria-labelledby="new-policy-title">
      <header>
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
          id="new-policy-title"
          className="mt-1 text-xl font-bold text-slate-950"
        >
          Nueva política de aprobación
        </h1>
        <p className="mt-1 max-w-2xl text-sm text-slate-500">
          Crea la raíz de la política. El backend decide su versión y estado
          inicial.
        </p>
      </header>

      <form
        onSubmit={(event) => void submit(event)}
        className="grid gap-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm md:grid-cols-2"
      >
        <label className="block">
          <span className="mb-1 block text-xs font-semibold text-slate-700">
            Código
          </span>
          <input
            value={code}
            maxLength={50}
            onChange={(event) => setCode(event.target.value)}
            className="min-h-11 w-full rounded-lg border border-slate-300 px-3 text-sm uppercase outline-none focus:border-[#1F4E6D] focus:ring-2 focus:ring-[#1F4E6D]/20"
          />
        </label>
        <label className="block">
          <span className="mb-1 block text-xs font-semibold text-slate-700">
            Nombre
          </span>
          <input
            value={name}
            maxLength={150}
            onChange={(event) => setName(event.target.value)}
            className="min-h-11 w-full rounded-lg border border-slate-300 px-3 text-sm outline-none focus:border-[#1F4E6D] focus:ring-2 focus:ring-[#1F4E6D]/20"
          />
        </label>
        <label className="block">
          <span className="mb-1 block text-xs font-semibold text-slate-700">
            Tipo de recurso
          </span>
          <Select value={subjectType} onValueChange={setSubjectType}>
            <SelectTrigger className="min-h-11 w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="PURCHASE_ORDER">
                Orden de compra
              </SelectItem>
              <SelectItem value="PURCHASE_REQUISITION">
                Requerimiento
              </SelectItem>
            </SelectContent>
          </Select>
        </label>
        <label className="block">
          <span className="mb-1 block text-xs font-semibold text-slate-700">
            Prioridad (1–9999)
          </span>
          <input
            inputMode="numeric"
            value={priority}
            onChange={(event) =>
              setPriority(event.target.value.replace(/\D/g, ''))
            }
            className="min-h-11 w-full rounded-lg border border-slate-300 px-3 font-mono text-sm outline-none focus:border-[#1F4E6D] focus:ring-2 focus:ring-[#1F4E6D]/20"
          />
        </label>
        <label className="block">
          <span className="mb-1 block text-xs font-semibold text-slate-700">
            Alcance
          </span>
          <Select value={effectiveScope} onValueChange={setEffectiveScope}>
            <SelectTrigger className="min-h-11 w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ORGANIZATION">Organización</SelectItem>
              <SelectItem value="BRANCH">Sede</SelectItem>
            </SelectContent>
          </Select>
        </label>
        <label className="flex min-h-11 items-center gap-2 self-end rounded-lg border border-slate-200 px-3">
          <input
            type="checkbox"
            checked={isFallback}
            onChange={(event) => setIsFallback(event.target.checked)}
            className="h-4 w-4 rounded border-slate-300 text-[#1F4E6D]"
          />
          <span className="text-sm font-medium text-slate-700">
            Política fallback
          </span>
        </label>
        <label className="block md:col-span-2">
          <span className="mb-1 block text-xs font-semibold text-slate-700">
            Descripción
          </span>
          <textarea
            rows={4}
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-[#1F4E6D] focus:ring-2 focus:ring-[#1F4E6D]/20"
          />
        </label>

        {errorMessage && (
          <p
            role="alert"
            className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-800 md:col-span-2"
          >
            {errorMessage}
          </p>
        )}

        <div className="flex justify-end gap-2 md:col-span-2">
          <button
            type="button"
            disabled={isSubmitting}
            onClick={() =>
              navigate('/logistics/purchasing/approval-policies')
            }
            className="min-h-11 rounded-lg border border-slate-200 px-4 text-sm font-semibold text-slate-700"
          >
            Cancelar
          </button>
          <button
            type="submit"
            disabled={
              !valid ||
              isSubmitting ||
              requireReverification ||
              !authorization.context.organization_id ||
              !authorization.userId
            }
            className="min-h-11 rounded-lg bg-[#1F4E6D] px-4 text-sm font-semibold text-white disabled:opacity-50"
          >
            {isSubmitting ? 'Creando…' : 'Crear política'}
          </button>
        </div>
      </form>
    </section>
  )
}
