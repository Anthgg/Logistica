import { useCallback, useEffect, useState } from 'react'
import { vehiclesApi } from '../api/vehicles-api'
import { Button } from '../components/common/Button'
import { LoadingSkeleton } from '../components/common/LoadingSkeleton'
import { PageHeader } from '../components/common/PageHeader'
import type { VehicleMake, VehicleMakeCreate } from '../types/vehicles'

export function VehicleMakesPage() {
  const [makes, setMakes] = useState<VehicleMake[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const [code, setCode] = useState('')
  const [name, setName] = useState('')
  const [country, setCountry] = useState('PE')

  const loadMakes = useCallback(async () => {
    setLoading(true)
    try {
      const items = await vehiclesApi.listMakes()
      setMakes(items)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadMakes()
  }, [loadMakes])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!code.trim() || !name.trim() || submitting) return
    setSubmitting(true)
    try {
      const data: VehicleMakeCreate = {
        code: code.trim().toUpperCase(),
        name: name.trim(),
        country_of_origin: country || undefined,
      }
      await vehiclesApi.createMake(data)
      setShowModal(false)
      setCode('')
      setName('')
      void loadMakes()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Error al crear marca')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <PageHeader
        title="Catálogo de Marcas Vehiculares"
        description="Registro y homologación de marcas vehiculares autorizadas en flota."
        actions={<Button onClick={() => setShowModal(true)}>+ Nueva Marca</Button>}
      />

      {loading ? (
        <LoadingSkeleton rows={6} />
      ) : makes.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-12 text-center text-slate-500">
          No hay marcas vehiculares registradas.
        </div>
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-xs text-xs">
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50 text-slate-600">
              <tr>
                <th className="px-4 py-3 text-left font-semibold">Código</th>
                <th className="px-4 py-3 text-left font-semibold">Nombre Marca</th>
                <th className="px-4 py-3 text-left font-semibold">Origen</th>
                <th className="px-4 py-3 text-left font-semibold">Scope</th>
                <th className="px-4 py-3 text-right font-semibold">Modelos Registrados</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {makes.map((m) => (
                <tr key={m.id} className="hover:bg-slate-50">
                  <td className="px-4 py-3 font-mono font-bold text-slate-800">{m.code}</td>
                  <td className="px-4 py-3 font-bold text-slate-900">{m.name}</td>
                  <td className="px-4 py-3 text-slate-600">{m.country_of_origin || '—'}</td>
                  <td className="px-4 py-3">
                    <span className={`rounded px-2 py-0.5 text-[10px] font-bold ${m.scope === 'SYSTEM' ? 'bg-indigo-100 text-indigo-800' : 'bg-slate-100 text-slate-700'}`}>
                      {m.scope}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right font-mono font-bold text-slate-800">
                    {m.models_count || 0}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 text-xs"
          role="presentation"
          onMouseDown={(e) => {
            if (e.target === e.currentTarget && !submitting) setShowModal(false)
          }}
        >
          <div
            className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl space-y-4"
            role="dialog"
            aria-modal="true"
            aria-labelledby="create-make-title"
            onMouseDown={(e) => e.stopPropagation()}
          >
            <h3 id="create-make-title" className="text-base font-bold text-slate-800">
              Registrar Marca Vehicular
            </h3>

            <form onSubmit={handleCreate} className="space-y-3">
              <div>
                <label className="mb-1 block font-bold text-slate-700">Código de Marca *</label>
                <input
                  type="text"
                  value={code}
                  onChange={(e) => setCode(e.target.value.toUpperCase())}
                  placeholder="Ej. VOLVO"
                  required
                  className="w-full font-mono uppercase rounded-lg border border-slate-300 px-3 py-2"
                />
              </div>

              <div>
                <label className="mb-1 block font-bold text-slate-700">Nombre Comercial de Marca *</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Ej. Volvo Trucks"
                  required
                  className="w-full rounded-lg border border-slate-300 px-3 py-2"
                />
              </div>

              <div>
                <label className="mb-1 block font-bold text-slate-700">País de Origen</label>
                <input
                  type="text"
                  value={country}
                  onChange={(e) => setCountry(e.target.value.toUpperCase())}
                  placeholder="SE"
                  className="w-full font-mono uppercase rounded-lg border border-slate-300 px-3 py-2"
                />
              </div>

              <div className="flex justify-end gap-2 border-t border-slate-100 pt-3">
                <Button type="button" variant="secondary" onClick={() => setShowModal(false)} disabled={submitting}>
                  Cancelar
                </Button>
                <Button type="submit" isLoading={submitting} loadingLabel="Guardando...">
                  Guardar Marca
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
