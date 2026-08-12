import { useEffect, useState } from 'react'
import { companyProfileApi } from '../../api/company-profile-api'
import { Button } from '../../components/common/Button'
import { Input } from '../../components/common/Input'
import { StatusBadge } from '../../components/common/StatusBadge'
import { ResourceDialog } from '../../components/common/ResourceDialog'
import type { AuthorizedSigner, AuthorizedSignerCreate } from '../../types/company-profile'
import { formatDateTime } from '../../utils/date'
import { getErrorMessage } from '../../utils/errors'

interface AuthorizedSignersPanelProps {
  canManageSigners: boolean
  canUploadSignature: boolean
  canRevokeSigner: boolean
  onRevokeSigner: (signer: AuthorizedSigner) => void
}

export function AuthorizedSignersPanel({
  canManageSigners,
  canUploadSignature,
  canRevokeSigner,
  onRevokeSigner,
}: AuthorizedSignersPanelProps) {
  const [signers, setSigners] = useState<AuthorizedSigner[]>([])
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [selectedSignerForSig, setSelectedSignerForSig] = useState<AuthorizedSigner | null>(null)
  const [sigFile, setSigFile] = useState<File | null>(null)

  const [form, setForm] = useState<AuthorizedSignerCreate>({
    full_name: '',
    job_title: '',
    department: 'Operaciones',
    authorization_ref: '',
    authorization_type: 'PODER_ESCRITURA',
    valid_from: new Date().toISOString().slice(0, 10),
    all_branches: true,
    branch_ids: [],
    document_families: ['REMISSION_GUIDE', 'MANIFEST'],
    document_types: ['GRR', 'GRT', 'MANIFEST'],
  })

  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadSigners = async () => {
    setIsLoading(true)
    try {
      const res = await companyProfileApi.listSigners({ page_size: 50 })
      setSigners(res.items)
    } catch (err: unknown) {
      setError(getErrorMessage(err))
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    void loadSigners()
  }, [])

  const handleCreate = async () => {
    setIsSaving(true)
    try {
      await companyProfileApi.createSigner(form)
      setIsDialogOpen(false)
      await loadSigners()
    } catch (err: unknown) {
      setError(getErrorMessage(err))
    } finally {
      setIsSaving(false)
    }
  }

  const handleUploadSignature = async () => {
    if (!selectedSignerForSig || !sigFile) return
    setIsSaving(true)
    try {
      await companyProfileApi.uploadSignerSignature(selectedSignerForSig.id, sigFile)
      setSelectedSignerForSig(null)
      setSigFile(null)
      await loadSigners()
    } catch (err: unknown) {
      setError(getErrorMessage(err))
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="space-y-4 text-xs">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-bold text-slate-900">Firmantes autorizados para comprobantes</h3>
          <p className="text-[11px] text-slate-500">
            Representantes legales y apoderados con facultad de firma en documentos logísticos.
          </p>
        </div>
        {canManageSigners && (
          <Button size="small" onClick={() => setIsDialogOpen(true)}>
            Registrar firmante
          </Button>
        )}
      </div>

      {error && <p className="text-xs font-semibold text-rose-600">{error}</p>}

      {isLoading ? (
        <div className="loading-panel">
          <span className="spinner" />
          <p>Cargando nómina de firmantes autorizados…</p>
        </div>
      ) : (
        <div className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-xs">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50 text-[10px] uppercase font-bold text-slate-400">
                <th className="p-3">Firmante</th>
                <th className="p-3">Cargo / Área</th>
                <th className="p-3">Autorización</th>
                <th className="p-3">Vigencia</th>
                <th className="p-3">Estado</th>
                <th className="p-3 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {signers.map((row) => (
                <tr key={row.id} className="hover:bg-slate-50/50">
                  <td className="p-3">
                    <div className="table-primary">
                      <strong>{row.full_name}</strong>
                      <small>Ref: {row.authorization_ref}</small>
                    </div>
                  </td>
                  <td className="p-3">
                    {row.job_title} · <span className="text-slate-500">{row.department}</span>
                  </td>
                  <td className="p-3">
                    <span className="font-mono text-[10px] bg-slate-100 px-1.5 py-0.5 rounded">
                      {row.authorization_type}
                    </span>
                  </td>
                  <td className="p-3 text-[11px] text-slate-600">
                    Desde: {formatDateTime(row.valid_from)}
                  </td>
                  <td className="p-3">
                    <StatusBadge value={row.status?.toLowerCase() ?? ''}>{row.status}</StatusBadge>
                  </td>
                  <td className="p-3 text-right space-x-1">
                    {canUploadSignature && row.status === 'ACTIVE' && (
                      <Button
                        size="small"
                        variant="ghost"
                        onClick={() => setSelectedSignerForSig(row)}
                      >
                        Subir firma
                      </Button>
                    )}
                    {canRevokeSigner && row.status === 'ACTIVE' && (
                      <Button size="small" variant="ghost" onClick={() => onRevokeSigner(row)}>
                        Revocar
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Diálogo de registro */}
      <ResourceDialog
        isOpen={isDialogOpen}
        title="Registrar nuevo firmante autorizado"
        submitLabel="Registrar firmante"
        isSubmitting={isSaving}
        onClose={() => setIsDialogOpen(false)}
        onSubmit={() => void handleCreate()}
      >
        <div className="grid grid-cols-2 gap-3 text-xs">
          <Input
            label="Nombre completo"
            value={form.full_name}
            onChange={(e) => setForm((c) => ({ ...c, full_name: e.target.value }))}
            required
          />
          <Input
            label="Cargo oficial"
            value={form.job_title}
            onChange={(e) => setForm((c) => ({ ...c, job_title: e.target.value }))}
            required
          />
          <Input
            label="Departamento / Área"
            value={form.department}
            onChange={(e) => setForm((c) => ({ ...c, department: e.target.value }))}
            required
          />
          <Input
            label="Referencia legal (Poder / Asiento SUNARP)"
            value={form.authorization_ref}
            onChange={(e) => setForm((c) => ({ ...c, authorization_ref: e.target.value }))}
            required
          />
          <Input
            label="Vigente desde"
            type="date"
            value={form.valid_from}
            onChange={(e) => setForm((c) => ({ ...c, valid_from: e.target.value }))}
            required
          />
        </div>
      </ResourceDialog>

      {/* Diálogo de Carga de Firma */}
      <ResourceDialog
        isOpen={Boolean(selectedSignerForSig)}
        title={`Subir imagen de firma visual — ${selectedSignerForSig?.full_name}`}
        submitLabel="Cargar firma"
        isSubmitting={isSaving}
        onClose={() => setSelectedSignerForSig(null)}
        onSubmit={() => void handleUploadSignature()}
      >
        <div className="space-y-3 text-xs">
          <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-amber-900">
            <p className="font-bold">Aviso legal sobre firmas visuales:</p>
            <p className="mt-1 leading-relaxed">
              Esta imagen constituye un trazo gráfico de representación impresa. No sustituye una firma digital criptográfica de
              clave pública (PKI).
            </p>
          </div>

          <input
            type="file"
            accept="image/png,image/jpeg"
            onChange={(e) => setSigFile(e.target.files?.[0] || null)}
          />
        </div>
      </ResourceDialog>
    </div>
  )
}
