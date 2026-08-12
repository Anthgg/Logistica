import { useState } from 'react'
import { vehiclesApi } from '../../api/vehicles-api'
import { Button } from '../common/Button'
import type { VehicleDocument, VehicleDocumentCreate, VehicleDocumentType } from '../../types/vehicles'

interface PanelProps {
  vehicleId: string
  documents: VehicleDocument[]
  onDocumentAdded?: () => void
  canManageDocuments?: boolean
}

const DOCUMENT_TYPES: { value: VehicleDocumentType; label: string }[] = [
  { value: 'PROPERTY_CARD', label: 'Tarjeta de Propiedad' },
  { value: 'PROPERTY_TITLE', label: 'Documento de Propiedad / Título' },
  { value: 'SOAT', label: 'SOAT (Seguro Obligatorio)' },
  { value: 'INSURANCE_POLICY', label: 'Póliza de Seguro' },
  { value: 'TECHNICAL_INSPECTION', label: 'Revisión Técnica Vehicular' },
  { value: 'TRANSPORT_PERMIT', label: 'Autorización de Transporte (MTC)' },
  { value: 'OPERATIONAL_PERMIT', label: 'Permiso Operativo' },
  { value: 'REFRIGERATION_CERTIFICATE', label: 'Certificado de Refrigeración' },
  { value: 'HAZMAT_CERTIFICATE', label: 'Certificado Mercancías Peligrosas' },
  { value: 'WEIGHT_CERTIFICATE', label: 'Certificado de Peso y Medidas' },
  { value: 'OTHER', label: 'Otro Documento' },
]

export function VehicleDocumentsPanel({
  vehicleId,
  documents,
  onDocumentAdded,
  canManageDocuments = true,
}: PanelProps) {
  const [showForm, setShowForm] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const handleAddDocument = async (data: VehicleDocumentCreate) => {
    setSubmitting(true)
    try {
      await vehiclesApi.createDocument(vehicleId, data)
      setShowForm(false)
      if (onDocumentAdded) onDocumentAdded()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Error al registrar documento')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="space-y-6 text-xs">
      <div className="rounded-xl border border-slate-200 bg-slate-50 p-3.5 text-slate-700">
        ℹ️ <strong>Gestión Metadatos Documentales:</strong> Registrarás los metadatos oficiales y fechas de vencimiento del vehículo. Las evidencias y archivos centralizados se integrarán en la Fase 030.
      </div>

      <div className="flex items-center justify-between">
        <h4 className="font-bold uppercase tracking-wider text-slate-500 text-xs">
          Documentos del Vehículo ({documents.length})
        </h4>
        {canManageDocuments && (
          <Button size="small" onClick={() => setShowForm(!showForm)}>
            {showForm ? 'Ocultar Formulario' : '+ Registrar Documento'}
          </Button>
        )}
      </div>

      {showForm && (
        <VehicleDocumentForm
          onSubmit={handleAddDocument}
          isSubmitting={submitting}
          onCancel={() => setShowForm(false)}
        />
      )}

      <div className="space-y-2">
        {documents.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-200 p-6 text-center text-slate-400">
            No hay documentos registrados para este vehículo.
          </div>
        ) : (
          documents.map((doc) => (
            <div
              key={doc.id}
              className="flex flex-col gap-2 rounded-xl border border-slate-200 bg-white p-4 sm:flex-row sm:items-center sm:justify-between"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-slate-800">{doc.document_type_label || doc.document_type}</span>
                  <span className="font-mono font-bold text-slate-700 text-xs">Nº {doc.document_number}</span>
                  <span
                    className={`rounded px-2 py-0.5 text-[10px] font-bold ${
                      doc.is_expired
                        ? 'bg-rose-100 text-rose-800'
                        : 'bg-emerald-100 text-emerald-800'
                    }`}
                  >
                    {doc.is_expired ? 'Vencido' : 'Vigente'}
                  </span>
                </div>
                <div className="flex items-center gap-2 text-slate-500 text-[11px]">
                  <span>Emisor: {doc.issuer_name}</span>
                  {doc.expiration_date && (
                    <span>· Vence: {new Date(doc.expiration_date).toLocaleDateString('es-PE')}</span>
                  )}
                </div>
              </div>

              {doc.days_until_expiration !== null && (
                <div className="text-right text-[11px]">
                  <span
                    className={`font-bold ${
                      doc.is_expired
                        ? 'text-rose-600'
                        : doc.days_until_expiration <= 30
                        ? 'text-amber-600'
                        : 'text-slate-600'
                    }`}
                  >
                    {doc.is_expired
                      ? `Vencido hace ${Math.abs(doc.days_until_expiration)} días`
                      : `Vence en ${doc.days_until_expiration} días`}
                  </span>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}

interface FormProps {
  onSubmit: (data: VehicleDocumentCreate) => void
  isSubmitting?: boolean
  onCancel?: () => void
}

export function VehicleDocumentForm({
  onSubmit,
  isSubmitting = false,
  onCancel,
}: FormProps) {
  const [docType, setDocType] = useState<VehicleDocumentType>('SOAT')
  const [docNumber, setDocNumber] = useState('')
  const [issuer, setIssuer] = useState('')
  const [issueDate, setIssueDate] = useState('')
  const [effectiveDate, setEffectiveDate] = useState('')
  const [expirationDate, setExpirationDate] = useState('')
  const [notes, setNotes] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!docNumber || !issuer || isSubmitting) return

    onSubmit({
      document_type: docType,
      document_number: docNumber.trim(),
      issuer_name: issuer.trim(),
      issue_date: issueDate || undefined,
      effective_date: effectiveDate || undefined,
      expiration_date: expirationDate || undefined,
      notes: notes.trim() || undefined,
    })
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm space-y-4 text-xs">
      <h4 className="font-bold text-slate-800 border-b border-slate-100 pb-2">
        Registrar Nuevo Documento Vehicular
      </h4>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div>
          <label className="mb-1 block font-bold text-slate-700">Tipo de Documento *</label>
          <select
            value={docType}
            onChange={(e) => setDocType(e.target.value as VehicleDocumentType)}
            required
            className="w-full rounded-lg border border-slate-300 px-3 py-2 bg-white"
          >
            {DOCUMENT_TYPES.map((d) => (
              <option key={d.value} value={d.value}>{d.label}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="mb-1 block font-bold text-slate-700">Número de Documento / Póliza *</label>
          <input
            type="text"
            value={docNumber}
            onChange={(e) => setDocNumber(e.target.value)}
            placeholder="Ej. SOAT-2026-99"
            required
            className="w-full font-mono rounded-lg border border-slate-300 px-3 py-2"
          />
        </div>

        <div>
          <label className="mb-1 block font-bold text-slate-700">Emisor / Aseguradora *</label>
          <input
            type="text"
            value={issuer}
            onChange={(e) => setIssuer(e.target.value)}
            placeholder="Ej. La Positiva, Rimac, CITV..."
            required
            className="w-full rounded-lg border border-slate-300 px-3 py-2"
          />
        </div>

        <div>
          <label className="mb-1 block font-bold text-slate-700">Fecha de Emisión</label>
          <input
            type="date"
            value={issueDate}
            onChange={(e) => setIssueDate(e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2"
          />
        </div>

        <div>
          <label className="mb-1 block font-bold text-slate-700">Vigencia Desde</label>
          <input
            type="date"
            value={effectiveDate}
            onChange={(e) => setEffectiveDate(e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2"
          />
        </div>

        <div>
          <label className="mb-1 block font-bold text-slate-700">Fecha de Vencimiento *</label>
          <input
            type="date"
            value={expirationDate}
            onChange={(e) => setExpirationDate(e.target.value)}
            required
            className="w-full rounded-lg border border-slate-300 px-3 py-2"
          />
        </div>
      </div>

      <div>
        <label className="mb-1 block font-bold text-slate-700">Notas Adicionales</label>
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          rows={2}
          placeholder="Observaciones de la cobertura o resolución..."
          className="w-full resize-none rounded-lg border border-slate-300 px-3 py-2"
        />
      </div>

      <div className="flex justify-end gap-2 border-t border-slate-100 pt-3">
        {onCancel && (
          <Button type="button" variant="secondary" onClick={onCancel} disabled={isSubmitting}>
            Cancelar
          </Button>
        )}
        <Button type="submit" isLoading={isSubmitting} loadingLabel="Registrando...">
          Registrar Documento
        </Button>
      </div>
    </form>
  )
}
