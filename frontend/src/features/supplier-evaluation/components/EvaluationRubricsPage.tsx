import { useEffect, useState } from 'react'
import type { EvaluationRubric } from '../types/evaluation'
import { ErrorState, StatusPill, TableSkeleton, EmptyState } from './ui/SharedState'
import { Modal } from './ui/Overlay'
import { getCsrfToken } from '../../../api/api-client'

async function listRubrics(): Promise<EvaluationRubric[]> {
  return []
}

async function createRubric(payload: Partial<EvaluationRubric> & { code: string; name: string; scale: EvaluationRubric['scale'] }): Promise<EvaluationRubric> {
  await getCsrfToken()
  return {
    id: `rubric-${Date.now()}`,
    code: payload.code,
    name: payload.name,
    scale: payload.scale,
    version: payload.version ?? '1.0.0',
    status: 'ACTIVE',
    evidence_required: payload.evidence_required ?? false,
    levels: [],
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  }
}

export function EvaluationRubricsPage() {
  const [items, setItems] = useState<EvaluationRubric[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isError, setIsError] = useState(false)
  const [error, setError] = useState('')
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState<{ code: string; name: string; scale: EvaluationRubric['scale']; evidence_required: boolean }>({ code: '', name: '', scale: 'ORDINAL_5', evidence_required: false })
  const [submitting, setSubmitting] = useState(false)

  const load = async () => {
    setIsLoading(true)
    setIsError(false)
    try {
      setItems(await listRubrics())
    } catch (err: unknown) {
      setIsError(true)
      setError(err instanceof Error ? err.message : 'No se pudieron cargar las rúbricas.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => { void load() }, [])

  const handleCreate = async () => {
    if (!form.code.trim() || !form.name.trim()) { alert('Código y nombre obligatorios.'); return }
    setSubmitting(true)
    try {
      await createRubric({ ...form })
      setOpen(false)
      setForm({ code: '', name: '', scale: 'ORDINAL_5', evidence_required: false })
      await load()
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'No se pudo crear.')
    } finally {
      setSubmitting(false)
    }
  }

  if (isLoading) return <TableSkeleton />
  if (isError) return <ErrorState message={error} onRetry={() => void load()} />

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-bold text-slate-900">Rúbricas de evaluación</h1>
        <button type="button" onClick={() => setOpen(true)} className="rounded-lg bg-[#1F4E6D] px-3.5 py-2 text-sm font-semibold text-white hover:bg-[#173a55]">Nueva rúbrica</button>
      </div>
      {items.length === 0 ? (
        <EmptyState title="Sin rúbricas" description="Crea rúbricas con niveles, etiquetas y evidencia esperada." />
      ) : (
        <div className="space-y-2">
          {items.map((r) => (
            <div key={r.id} className="rounded-xl border border-slate-200 p-3 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-semibold">{r.code} — {r.name}</span>
                <StatusPill tone={r.status === 'ACTIVE' ? 'success' : 'muted'}>{r.status}</StatusPill>
              </div>
              <div className="mt-1 text-slate-500">Escala: {r.scale} · Niveles: {r.levels.length} · Evidencia: {r.evidence_required ? 'Sí' : 'No'}</div>
              {r.levels.length > 0 && (
                <ul className="mt-2 divide-y divide-slate-100 rounded-lg border border-slate-100">
                  {r.levels.map((l) => (
                    <li key={l.code} className="grid grid-cols-3 gap-1 px-2 py-1">
                      <span className="font-mono">{l.label}</span>
                      <span className="text-slate-500">{l.description}</span>
                      <span className="text-right font-mono">{l.score}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ))}
        </div>
      )}

      <Modal
        open={open}
        onOpenChange={setOpen}
        title="Nueva rúbrica"
        footer={
          <>
            <button type="button" onClick={() => setOpen(false)} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50">Cancelar</button>
            <button type="button" disabled={submitting} onClick={handleCreate} className="rounded-lg bg-[#1F4E6D] px-3 py-1.5 text-xs font-semibold text-white hover:bg-[#173a55] disabled:opacity-50">{submitting ? 'Creando…' : 'Crear'}</button>
          </>
        }
      >
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-xs font-bold text-slate-700">Código</label>
              <input value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} className="w-full rounded-lg border border-slate-300 px-3 py-2 font-mono text-sm" />
            </div>
            <div>
              <label className="mb-1 block text-xs font-bold text-slate-700">Nombre</label>
              <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
            </div>
          </div>
          <div>
            <label className="mb-1 block text-xs font-bold text-slate-700">Escala</label>
            <select value={form.scale} onChange={(e) => setForm({ ...form, scale: e.target.value as EvaluationRubric['scale'] })} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm">
              <option value="BINARY">Binaria</option>
              <option value="ORDINAL_3">Ordinal 3</option>
              <option value="ORDINAL_4">Ordinal 4</option>
              <option value="ORDINAL_5">Ordinal 5</option>
              <option value="POINTS_100">Puntos 100</option>
            </select>
          </div>
          <label className="inline-flex items-center gap-2 text-xs font-medium text-slate-600">
            <input type="checkbox" checked={form.evidence_required} onChange={(e) => setForm({ ...form, evidence_required: e.target.checked })} className="h-4 w-4 rounded border-slate-300 text-[#1F4E6D]" />
            Evidencia requerida
          </label>
        </div>
      </Modal>
    </div>
  )
}