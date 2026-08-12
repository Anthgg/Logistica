import { useCallback, useEffect, useState } from 'react'
import { vehiclesApi } from '../api/vehicles-api'
import { Button } from '../components/common/Button'
import { LoadingSkeleton } from '../components/common/LoadingSkeleton'
import { PageHeader } from '../components/common/PageHeader'
import type { VehicleMake, VehicleModel, VehicleModelCreate } from '../types/vehicles'

export function VehicleModelsPage() {
  const [models, setModels] = useState<VehicleModel[]>([])
  const [makes, setMakes] = useState<VehicleMake[]>([])
  const [selectedMakeId, setSelectedMakeId] = useState('')
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const [makeId, setMakeId] = useState('')
  const [code, setCode] = useState('')
  const [name, setName] = useState('')

  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      const [mList, mkList] = await Promise.all([
        vehiclesApi.listModels(selectedMakeId || undefined),
        vehiclesApi.listMakes().catch(() => []),
      ])
      setModels(mList)
      setMakes(mkList)
    } finally {
      setLoading(false)
    }
  }, [selectedMakeId])

  useEffect(() => {
    void loadData()
  }, [loadData])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!makeId || !code.trim() || !name.trim() || submitting) return
    setSubmitting(true)
    try {
      const data: VehicleModelCreate = {
        make_id: makeId,
        code: code.trim().toUpperCase(),
        name: name.trim(),
      }
      await vehiclesApi.createModel(data)
      setShowModal(false)
      setCode('')
      setName('')
      void loadData()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Error al crear modelo')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <PageHeader
        title="Catálogo de Modelos Vehiculares"
        description="Registro de líneas y modelos vehiculares asociados a marcas autorizadas."
        actions={<Button onClick={() => setShowModal(true)}>+ Nuevo Modelo</Button>}
      />

      {/* Filter by Make */}
      <div className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-xs text-xs">
        <span className="font-bold text-slate-700">Filtrar por Marca:</span>
        <select
          value={selectedMakeId}
          onChange={(e) => setSelectedMakeId(e.target.value)}
          className="rounded-xl border border-slate-300 px-3 py-2 bg-white font-medium text-slate-700"
        >
          <option value="">Todas las marcas</option>
          {makes.map((mk) => (
            <option key={mk.id} value={mk.id}>{mk.name}</option>
          ))}
        </select>
      </div>

      {loading ? (
        <LoadingSkeleton rows={6} />
      ) : models.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-12 text-center text-slate-500">
          No hay modelos registrados.
        </div>
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-xs text-xs">
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50 text-slate-600">
              <tr>
                <th className="px-4 py-3 text-left font-semibold">Marca</th>
                <th className="px-4 py-3 text-left font-semibold">Código</th>
                <th className="px-4 py-3 text-left font-semibold">Modelo</th>
                <th className="px-4 py-3 text-left font-semibold">Tipo Sugerido</th>
                <th className="px-4 py-3 text-center font-semibold">Estado</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {models.map((m) => (
                <tr key={m.id} className="hover:bg-slate-50">
                  <td className="px-4 py-3 font-bold text-indigo-700">{m.make_name}</td>
                  <td className="px-4 py-3 font-mono font-bold text-slate-800">{m.code}</td>
                  <td className="px-4 py-3 font-bold text-slate-900">{m.name}</td>
                  <td className="px-4 py-3 text-slate-600">{m.suggested_vehicle_type || '—'}</td>
                  <td className="px-4 py-3 text-center">
                    <span className={`rounded px-2 py-0.5 text-[10px] font-bold ${m.is_active ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-600'}`}>
                      {m.is_active ? 'Activo' : 'Inactivo'}
                    </span>
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
            aria-labelledby="create-model-title"
            onMouseDown={(e) => e.stopPropagation()}
          >
            <h3 id="create-model-title" className="text-base font-bold text-slate-800">
              Registrar Modelo Vehicular
            </h3>

            <form onSubmit={handleCreate} className="space-y-3">
              <div>
                <label className="mb-1 block font-bold text-slate-700">Marca Vehicular *</label>
                <select
                  value={makeId}
                  onChange={(e) => setMakeId(e.target.value)}
                  required
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 bg-white"
                >
                  <option value="">Seleccionar marca...</option>
                  {makes.map((mk) => (
                    <option key={mk.id} value={mk.id}>{mk.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="mb-1 block font-bold text-slate-700">Código de Modelo *</label>
                <input
                  type="text"
                  value={code}
                  onChange={(e) => setCode(e.target.value.toUpperCase())}
                  placeholder="Ej. FH16"
                  required
                  className="w-full font-mono uppercase rounded-lg border border-slate-300 px-3 py-2"
                />
              </div>

              <div>
                <label className="mb-1 block font-bold text-slate-700">Nombre de Modelo *</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Ej. FH16 750 Globetrotter"
                  required
                  className="w-full rounded-lg border border-slate-300 px-3 py-2"
                />
              </div>

              <div className="flex justify-end gap-2 border-t border-slate-100 pt-3">
                <Button type="button" variant="secondary" onClick={() => setShowModal(false)} disabled={submitting}>
                  Cancelar
                </Button>
                <Button type="submit" isLoading={submitting} loadingLabel="Guardando...">
                  Guardar Modelo
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
