import { useState } from 'react'
import { useMutation } from '../../inbound-docks/hooks/useQuery'
import { receptionDifferenceCasesApi } from '../api/receptionDifferenceCasesApi'
import type { EligibleReceiptForDifference } from '../types/reception-differences'

interface ReceptionDifferenceCaseWizardProps {
  eligibleReceipts: EligibleReceiptForDifference[]
  onSuccess: (caseId: string) => void
  onCancel: () => void
}

type WizardStep = 'select-receipt' | 'select-products' | 'define-types' | 'describe' | 'severity' | 'evidence' | 'responsibility' | 'validate' | 'confirm' | 'submit'

const STEPS: { key: WizardStep; label: string }[] = [
  { key: 'select-receipt', label: 'Recepción' },
  { key: 'select-products', label: 'Productos' },
  { key: 'define-types', label: 'Tipos' },
  { key: 'describe', label: 'Descripción' },
  { key: 'severity', label: 'Severidad' },
  { key: 'evidence', label: 'Evidencia' },
  { key: 'responsibility', label: 'Responsable' },
  { key: 'validate', label: 'Validación' },
  { key: 'confirm', label: 'Confirmar' },
  { key: 'submit', label: 'Enviar' },
]

const DIFFERENCE_TYPES = [
  { value: 'SHORTAGE', label: 'Faltante', desc: 'Cantidad menor a la ordenada' },
  { value: 'OVERAGE', label: 'Sobrante', desc: 'Cantidad mayor a la ordenada' },
  { value: 'DAMAGE', label: 'Daño', desc: 'Producto dañado' },
  { value: 'WRONG_PRODUCT', label: 'Producto incorrecto', desc: 'No coincide con la orden' },
  { value: 'MISSING_DOCUMENT', label: 'Documento faltante', desc: 'Sin documentación requerida' },
  { value: 'BROKEN_SEAL', label: 'Precinto roto', desc: 'Precinto no coincide' },
] as const

const SEVERITY_OPTIONS = [
  { value: 'LOW', label: 'Baja', desc: 'Sin impacto significativo' },
  { value: 'MEDIUM', label: 'Media', desc: 'Requiere atención' },
  { value: 'HIGH', label: 'Alta', desc: 'Impacto significativo' },
  { value: 'CRITICAL', label: 'Crítica', desc: 'Requiere acción inmediata' },
] as const

export function ReceptionDifferenceCaseWizard({ eligibleReceipts, onSuccess, onCancel }: ReceptionDifferenceCaseWizardProps) {
  const [step, setStep] = useState<WizardStep>('select-receipt')
  const [selectedReceipt, setSelectedReceipt] = useState<EligibleReceiptForDifference | null>(null)
  const [selectedProducts, setSelectedProducts] = useState<string[]>([])
  const [differenceTypes, setDifferenceTypes] = useState<Record<string, string[]>>({})
  const [descriptions, setDescriptions] = useState<Record<string, string>>({})
  const [severity, setSeverity] = useState<string>('MEDIUM')
  const [evidenceNotes, setEvidenceNotes] = useState('')
  const [responsibleParty, setResponsibleParty] = useState('')

  const createMutation = useMutation(
    (data: Parameters<typeof receptionDifferenceCasesApi.create>[0]) =>
      receptionDifferenceCasesApi.create(data),
    {
      onSuccess: (result) => {
        onSuccess(result.case_id)
      },
    }
  )

  const currentStepIndex = STEPS.findIndex((s) => s.key === step)

  const canProceed = (): boolean => {
    switch (step) {
      case 'select-receipt':
        return selectedReceipt !== null
      case 'select-products':
        return selectedProducts.length > 0
      case 'define-types':
        return selectedProducts.every((p) => differenceTypes[p]?.length > 0)
      case 'describe':
        return selectedProducts.every((p) => descriptions[p]?.trim().length > 0)
      case 'severity':
        return severity !== ''
      default:
        return true
    }
  }

  const goNext = () => {
    const idx = STEPS.findIndex((s) => s.key === step)
    if (idx < STEPS.length - 1) {
      setStep(STEPS[idx + 1].key)
    }
  }

  const goBack = () => {
    const idx = STEPS.findIndex((s) => s.key === step)
    if (idx > 0) {
      setStep(STEPS[idx - 1].key)
    }
  }

  const handleSubmit = () => {
    if (!selectedReceipt) return

    const items = selectedProducts.map((productId) => ({
      product_id: productId,
      difference_types: differenceTypes[productId] || [],
      description: descriptions[productId] || '',
      observed_quantity: '0',
      unit_id: selectedReceipt.units?.[0]?.unit_id ?? '',
    }))

    createMutation.mutate({
      receipt_id: selectedReceipt.receipt_id,
      severity: (severity as any) || undefined,
      summary: `Caso creado con ${selectedProducts.length} productos`,
      items,
    })
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-sm font-bold text-slate-800">Crear caso de diferencia</h1>
            <p className="text-xs text-slate-500">Paso {currentStepIndex + 1} de {STEPS.length}: {STEPS[currentStepIndex].label}</p>
          </div>
          <button
            type="button"
            onClick={onCancel}
            className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-600"
          >
            Cancelar
          </button>
        </div>
      </header>

      {/* Progress bar */}
      <div className="border-b border-slate-200 bg-white px-6 py-2">
        <div className="flex gap-1">
          {STEPS.map((s, i) => (
            <div
              key={s.key}
              className={`h-1.5 flex-1 rounded-full ${
                i < currentStepIndex ? 'bg-[#1F4E6D]' : i === currentStepIndex ? 'bg-[#1F4E6D]/60' : 'bg-slate-200'
              }`}
            />
          ))}
        </div>
      </div>

      <div className="mx-auto max-w-3xl p-6">
        <div className="rounded-xl border border-slate-200 bg-white p-6">
          {step === 'select-receipt' && (
            <SelectReceiptStep
              receipts={eligibleReceipts}
              selected={selectedReceipt}
              onSelect={setSelectedReceipt}
            />
          )}
          {step === 'select-products' && selectedReceipt && (
            <SelectProductsStep
              receipt={selectedReceipt}
              selected={selectedProducts}
              onToggle={(id) => {
                setSelectedProducts((prev) =>
                  prev.includes(id) ? prev.filter((p) => p !== id) : [...prev, id]
                )
              }}
            />
          )}
          {step === 'define-types' && (
            <DefineTypesStep
              products={selectedProducts}
              types={differenceTypes}
              onChange={(productId, types) => {
                setDifferenceTypes((prev) => ({ ...prev, [productId]: types }))
              }}
            />
          )}
          {step === 'describe' && (
            <DescribeStep
              products={selectedProducts}
              descriptions={descriptions}
              onChange={(productId, desc) => {
                setDescriptions((prev) => ({ ...prev, [productId]: desc }))
              }}
            />
          )}
          {step === 'severity' && (
            <SeverityStep value={severity} onChange={setSeverity} />
          )}
          {step === 'evidence' && (
            <EvidenceStep value={evidenceNotes} onChange={setEvidenceNotes} />
          )}
          {step === 'responsibility' && (
            <ResponsibilityStep value={responsibleParty} onChange={setResponsibleParty} />
          )}
          {step === 'validate' && (
            <ValidateStep
              receipt={selectedReceipt}
              products={selectedProducts}
              types={differenceTypes}
              descriptions={descriptions}
              severity={severity}
            />
          )}
          {step === 'confirm' && (
            <ConfirmStep
              receipt={selectedReceipt}
              products={selectedProducts}
              types={differenceTypes}
              descriptions={descriptions}
              severity={severity}
              evidenceNotes={evidenceNotes}
              responsibleParty={responsibleParty}
            />
          )}
          {step === 'submit' && (
            <div className="text-center text-xs text-slate-500">
              {createMutation.isPending ? 'Creando caso...' : createMutation.error ? `Error: ${String(createMutation.error)}` : 'Caso creado'}
            </div>
          )}
        </div>

        {/* Navigation */}
        {step !== 'submit' && (
          <div className="mt-4 flex justify-between">
            <button
              type="button"
              onClick={currentStepIndex === 0 ? onCancel : goBack}
              className="rounded-lg border border-slate-200 px-4 py-2 text-xs font-semibold text-slate-600"
            >
              {currentStepIndex === 0 ? 'Cancelar' : 'Atrás'}
            </button>
            <button
              type="button"
              onClick={step === 'confirm' ? handleSubmit : goNext}
              disabled={!canProceed() || createMutation.isPending}
              className="rounded-lg bg-[#1F4E6D] px-4 py-2 text-xs font-semibold text-white hover:bg-[#173a55] disabled:opacity-50"
            >
              {step === 'confirm' ? (createMutation.isPending ? 'Creando...' : 'Crear caso') : 'Siguiente'}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

function SelectReceiptStep({ receipts, selected, onSelect }: { receipts: EligibleReceiptForDifference[]; selected: EligibleReceiptForDifference | null; onSelect: (r: EligibleReceiptForDifference) => void }) {
  return (
    <div className="space-y-3">
      <h2 className="text-sm font-bold text-slate-800">Seleccionar recepción</h2>
      <p className="text-xs text-slate-500">Solo recepciones completas con evidencia fotográfica.</p>
      {receipts.length === 0 ? (
        <p className="text-xs text-slate-400">No hay recepciones elegibles.</p>
      ) : (
        <div className="space-y-2">
          {receipts.map((r) => (
            <button
              key={r.receipt_id}
              type="button"
              onClick={() => onSelect(r)}
              className={`w-full rounded-lg border p-3 text-left text-xs transition-colors ${
                selected?.receipt_id === r.receipt_id
                  ? 'border-[#1F4E6D] bg-[#1F4E6D]/5'
                  : 'border-slate-200 hover:bg-slate-50'
              }`}
            >
              <p className="font-semibold text-slate-800">{r.code}</p>
              <p className="text-slate-500">{r.supplier_name} · {r.warehouse_name}</p>
              <p className="text-slate-400">{r.completed_at} · {r.items_count} ítems</p>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

function SelectProductsStep({ receipt, selected, onToggle }: { receipt: EligibleReceiptForDifference; selected: string[]; onToggle: (id: string) => void }) {
  return (
    <div className="space-y-3">
      <h2 className="text-sm font-bold text-slate-800">Seleccionar productos con diferencia</h2>
      <p className="text-xs text-slate-500">Recepción: {receipt.code} · {receipt.supplier_name}</p>
      <div className="space-y-2">
        {(receipt.products ?? []).map((p) => (
          <button
            key={p.product_id}
            type="button"
            onClick={() => onToggle(p.product_id)}
            className={`w-full rounded-lg border p-3 text-left text-xs transition-colors ${
              selected.includes(p.product_id)
                ? 'border-[#1F4E6D] bg-[#1F4E6D]/5'
                : 'border-slate-200 hover:bg-slate-50'
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="font-semibold text-slate-800">{p.name}</span>
              <span className="text-[10px] text-slate-400">SKU: {p.sku}</span>
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}

function DefineTypesStep({ products, types, onChange }: { products: string[]; types: Record<string, string[]>; onChange: (productId: string, types: string[]) => void }) {
  return (
    <div className="space-y-4">
      <h2 className="text-sm font-bold text-slate-800">Definir tipos de diferencia</h2>
      {products.map((productId) => (
        <div key={productId} className="rounded-lg border border-slate-200 p-3">
          <p className="mb-2 text-xs font-semibold text-slate-700">Producto: {productId}</p>
          <div className="flex flex-wrap gap-1.5">
            {DIFFERENCE_TYPES.map((dt) => {
              const isSelected = types[productId]?.includes(dt.value) ?? false
              return (
                <button
                  key={dt.value}
                  type="button"
                  onClick={() => {
                    const current = types[productId] || []
                    const next = isSelected ? current.filter((t) => t !== dt.value) : [...current, dt.value]
                    onChange(productId, next)
                  }}
                  className={`rounded-lg px-2 py-1 text-[10px] font-semibold transition-colors ${
                    isSelected
                      ? 'bg-[#1F4E6D] text-white'
                      : 'border border-slate-200 bg-white text-slate-600'
                  }`}
                  title={dt.desc}
                >
                  {dt.label}
                </button>
              )
            })}
          </div>
        </div>
      ))}
    </div>
  )
}

function DescribeStep({ products, descriptions, onChange }: { products: string[]; descriptions: Record<string, string>; onChange: (productId: string, desc: string) => void }) {
  return (
    <div className="space-y-4">
      <h2 className="text-sm font-bold text-slate-800">Describir cada diferencia</h2>
      {products.map((productId) => (
        <label key={productId} className="block text-xs text-slate-600">
          Descripción para {productId} *
          <textarea
            value={descriptions[productId] || ''}
            onChange={(e) => onChange(productId, e.target.value)}
            className="mt-1 w-full rounded-lg border border-slate-300 p-2 text-xs"
            rows={2}
            placeholder="Describa la diferencia observada..."
          />
        </label>
      ))}
    </div>
  )
}

function SeverityStep({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return (
    <div className="space-y-3">
      <h2 className="text-sm font-bold text-slate-800">Severidad general</h2>
      <div className="grid grid-cols-2 gap-2">
        {SEVERITY_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            type="button"
            onClick={() => onChange(opt.value)}
            className={`rounded-lg border p-3 text-left text-xs transition-colors ${
              value === opt.value
                ? 'border-[#1F4E6D] bg-[#1F4E6D]/5'
                : 'border-slate-200 hover:bg-slate-50'
            }`}
          >
            <p className="font-semibold text-slate-800">{opt.label}</p>
            <p className="text-slate-500">{opt.desc}</p>
          </button>
        ))}
      </div>
    </div>
  )
}

function EvidenceStep({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return (
    <div className="space-y-3">
      <h2 className="text-sm font-bold text-slate-800">Evidencia</h2>
      <p className="text-xs text-slate-500">Las fotos se suben después del registro. Este paso es opcional.</p>
      <label className="block text-xs text-slate-600">
        Notas adicionales (opcional)
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="mt-1 w-full rounded-lg border border-slate-300 p-2 text-xs"
          rows={3}
        />
      </label>
    </div>
  )
}

function ResponsibilityStep({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return (
    <div className="space-y-3">
      <h2 className="text-sm font-bold text-slate-800">Responsable provisional</h2>
      <p className="text-xs text-slate-500">Opcional. La determinación formal se hace después.</p>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-lg border border-slate-300 p-2 text-xs"
        placeholder="Nombre del responsable..."
      />
    </div>
  )
}

function ValidateStep({ receipt, products, types, descriptions, severity }: {
  receipt: EligibleReceiptForDifference | null
  products: string[]
  types: Record<string, string[]>
  descriptions: Record<string, string>
  severity: string
}) {
  return (
    <div className="space-y-3">
      <h2 className="text-sm font-bold text-slate-800">Validación</h2>
      <div className="rounded-lg border border-slate-200 p-3 text-xs">
        <InfoCell label="Recepción" value={receipt?.code ?? '—'} />
        <InfoCell label="Productos" value={String(products.length)} />
        <InfoCell label="Severidad" value={severity} />
        {products.map((p) => (
          <div key={p} className="mt-2 border-t border-slate-100 pt-2">
            <InfoCell label="Producto" value={p} />
            <InfoCell label="Tipos" value={(types[p] || []).join(', ')} />
            <InfoCell label="Descripción" value={descriptions[p] || '—'} />
          </div>
        ))}
      </div>
    </div>
  )
}

function ConfirmStep({ receipt, products, types, descriptions, severity, evidenceNotes, responsibleParty }: {
  receipt: EligibleReceiptForDifference | null
  products: string[]
  types: Record<string, string[]>
  descriptions: Record<string, string>
  severity: string
  evidenceNotes: string
  responsibleParty: string
}) {
  return (
    <div className="space-y-3">
      <h2 className="text-sm font-bold text-slate-800">Confirmar creación</h2>
      <div className="rounded-lg border border-slate-200 p-3 text-xs">
        <InfoCell label="Recepción" value={receipt?.code ?? '—'} />
        <InfoCell label="Proveedor" value={receipt?.supplier_name ?? '—'} />
        <InfoCell label="Productos" value={String(products.length)} />
        <InfoCell label="Severidad" value={severity} />
        <InfoCell label="Responsable" value={responsibleParty || '—'} />
        {evidenceNotes && <InfoCell label="Notas evidencia" value={evidenceNotes} />}
        {products.map((p) => (
          <div key={p} className="mt-2 border-t border-slate-100 pt-2">
            <p className="font-semibold text-slate-700">Producto {p}</p>
            <p className="text-slate-500">Tipos: {(types[p] || []).join(', ')}</p>
            <p className="text-slate-500">Descripción: {descriptions[p] || '—'}</p>
          </div>
        ))}
      </div>
      <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800">
        Al crear el caso, este se registrará como Borrador con integridad verificada.
      </div>
    </div>
  )
}

function InfoCell({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center gap-2 py-0.5">
      <span className="w-28 font-semibold text-slate-600">{label}:</span>
      <span className="text-slate-800">{value}</span>
    </div>
  )
}
