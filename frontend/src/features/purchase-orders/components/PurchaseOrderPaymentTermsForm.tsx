import { useCallback, useEffect, useState } from 'react'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../../components/ui/select'
import { purchaseOrderSchedulesApi } from '../api/purchaseOrderSchedulesApi'
import type {
  PaymentMethod,
  PaymentTermsType,
  PurchaseOrderCapabilities,
  PurchaseOrderPaymentTerms,
} from '../types/purchase-orders-v2'
import { paymentTermsTypeLabel, paymentMethodLabel } from '../format'
import { ErrorState } from './ui'
import { DecimalInput } from './ui'

const TYPES: PaymentTermsType[] = ['IMMEDIATE', 'NET_DAYS', 'ADVANCE_PLUS_BALANCE', 'MILESTONE', 'CONSIGNMENT']
const METHODS: PaymentMethod[] = ['BANK_TRANSFER', 'CHECK', 'CASH', 'CREDIT', 'LETTER_OF_CREDIT', 'OTHER']

export function PurchaseOrderPaymentTermsForm({
  purchaseOrderId,
  capabilities,
}: {
  purchaseOrderId: string
  capabilities: PurchaseOrderCapabilities
}) {
  const [terms, setTerms] = useState<PurchaseOrderPaymentTerms | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [type, setType] = useState<PaymentTermsType>('NET_DAYS')
  const [method, setMethod] = useState<PaymentMethod>('BANK_TRANSFER')
  const [creditDays, setCreditDays] = useState<number | null>(30)
  const [advance, setAdvance] = useState('')
  const [balance, setBalance] = useState('')
  const [retention, setRetention] = useState('')
  const [reference, setReference] = useState('')
  const [notes, setNotes] = useState('')

  const load = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const t = await purchaseOrderSchedulesApi.getPaymentTerms(purchaseOrderId)
      setTerms(t)
      if (t) {
        setType(t.type)
        setMethod(t.method)
        setCreditDays(t.credit_days)
        setAdvance(t.advance_percentage ?? '')
        setBalance(t.balance_percentage ?? '')
        setRetention(t.retention_percentage ?? '')
        setReference(t.reference ?? '')
        setNotes(t.notes ?? '')
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'No se pudieron cargar los términos.')
    } finally {
      setIsLoading(false)
    }
  }, [purchaseOrderId])

  useEffect(() => { void load() }, [load])

  const handleSave = async () => {
    setSaving(true)
    setError(null)
    try {
      await purchaseOrderSchedulesApi.updatePaymentTerms(purchaseOrderId, {
        type, method, credit_days: creditDays,
        advance_percentage: advance || null,
        balance_percentage: balance || null,
        retention_percentage: retention || null,
        reference: reference || null,
        notes: notes || null,
      })
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'No se pudo guardar.')
    } finally {
      setSaving(false)
    }
  }

  if (isLoading) return <div className="text-xs text-slate-500">Cargando…</div>

  const readOnly = !capabilities.can_manage_terms

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 text-xs">
      <h2 className="text-sm font-bold text-slate-800">Términos de pago</h2>
      {error && <ErrorState message={error} />}
      <div className="mt-3 grid grid-cols-2 gap-3">
        <div>
          <label className="mb-1 block text-xs font-bold text-slate-700">Tipo</label>
          <Select value={type} onValueChange={(v) => setType(v as PaymentTermsType)} disabled={readOnly}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>{TYPES.map((t) => <SelectItem key={t} value={t}>{paymentTermsTypeLabel(t)}</SelectItem>)}</SelectContent>
          </Select>
        </div>
        <div>
          <label className="mb-1 block text-xs font-bold text-slate-700">Método</label>
          <Select value={method} onValueChange={(v) => setMethod(v as PaymentMethod)} disabled={readOnly}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>{METHODS.map((m) => <SelectItem key={m} value={m}>{paymentMethodLabel(m)}</SelectItem>)}</SelectContent>
          </Select>
        </div>
        <div>
          <label className="mb-1 block text-xs font-bold text-slate-700">Días de crédito</label>
          <input type="number" min={0} value={creditDays ?? 0} onChange={(e) => setCreditDays(Number(e.target.value))} disabled={readOnly} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
        </div>
        <DecimalInput label="Adelanto (%)" value={advance} onChange={setAdvance} maxDecimals={4} disabled={readOnly} />
        <DecimalInput label="Saldo (%)" value={balance} onChange={setBalance} maxDecimals={4} disabled={readOnly} />
        <DecimalInput label="Retención referencial (%)" value={retention} onChange={setRetention} maxDecimals={4} disabled={readOnly} />
        <div>
          <label className="mb-1 block text-xs font-bold text-slate-700">Referencia</label>
          <input value={reference} onChange={(e) => setReference(e.target.value)} disabled={readOnly} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
        </div>
        <div className="col-span-2">
          <label className="mb-1 block text-xs font-bold text-slate-700">Observaciones</label>
          <textarea value={notes} onChange={(e) => setNotes(e.target.value)} disabled={readOnly} rows={2} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
        </div>
      </div>
      {terms?.offer_differs && (
        <p className="mt-2 text-amber-700">Diferencia con oferta: {terms.differences_summary ?? 'consultar backend'}</p>
      )}
      <p className="mt-2 text-[11px] text-slate-500">No se ejecutan pagos. No se piden credenciales bancarias. Los porcentajes los valida el backend.</p>
      {!readOnly && (
        <button type="button" disabled={saving} onClick={handleSave} className="mt-2 rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#173a55] disabled:opacity-50">
          {saving ? 'Guardando…' : 'Guardar términos'}
        </button>
      )}
    </div>
  )
}